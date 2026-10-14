from __future__ import annotations

import copy
import importlib.metadata
import json
import os
import subprocess
import sys
import tomllib
from pathlib import Path

import pytest
from support import ROOT, build_checkout, scrubbed_environment, write

from tools.workspace_governance.resolver.core import GovernanceResolver
from tools.workspace_governance.validators import core


def environment(**updates: str) -> dict[str, str]:
    return scrubbed_environment(**updates)


def run(
    root: Path, *args: str, env: dict[str, str] | None = None
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        cwd=root,
        env=environment() if env is None else env,
        text=True,
        capture_output=True,
        check=False,
    )


def wrapper(root: Path, *, no_site: bool = False) -> Path:
    path = root / "selected-python"
    path.write_text(
        f'#!/bin/sh\nexec "{sys.executable}" ' + ("-S " if no_site else "") + '"$@"\n'
    )
    path.chmod(0o755)
    return path


def execution_mode() -> str:
    """Ask the resolver, which reads the declaration rather than the environment."""
    _, project, _ = GovernanceResolver.for_root(ROOT).load()
    mode, _, issues = core.resolve_execution_mode(project, dict(os.environ))
    assert not issues, [item.to_dict() for item in issues]
    return mode


def test_packaging_is_declared_once_by_the_dependency_authority() -> None:
    """pyproject declares dependencies in every mode; only the check differs."""
    from packaging.requirements import Requirement
    from packaging.specifiers import SpecifierSet

    deps = tomllib.loads((ROOT / "pyproject.toml").read_text())["project"][
        "dependencies"
    ]
    declared = [Requirement(d) for d in deps if Requirement(d).name == "packaging"]
    assert len(declared) == 1
    assert importlib.metadata.version("packaging") in declared[0].specifier
    assert str(SpecifierSet(">=3.11")) == ">=3.11"


def test_installed_mode_carries_the_declaration_into_distribution_metadata() -> None:
    """Installed metadata is a separate claim from importability.

    A dependency can be present transitively and import fine while never being
    declared, which is exactly what this guards.
    """
    from packaging.requirements import Requirement

    if execution_mode() != "installed":
        pytest.skip("source mode declares no tet4d distribution")
    installed = [Requirement(d) for d in importlib.metadata.requires("tet4d") or []]
    assert any(item.name == "packaging" for item in installed)


def test_source_mode_keeps_the_environment_free_of_a_tet4d_distribution() -> None:
    """The invariant a shared environment exists to hold: no source binding.

    An installed distribution would make one checkout authoritative for every
    other, so in source mode none may be discoverable at all.
    """
    if execution_mode() != "source":
        pytest.skip("installed mode declares a tet4d distribution")
    with pytest.raises(importlib.metadata.PackageNotFoundError):
        importlib.metadata.distribution("tet4d")


def test_dependency_light_bootstrap_and_missing_project_dependency(
    checkout: Path,
) -> None:
    selected = wrapper(checkout, no_site=True)
    env = environment(GOVERNANCE_PYTHON=str(selected), TET4D_PYTHON=str(selected))
    checked = run(checkout, "./gov", "check", "--json", env=env)
    assert checked.returncode == 0, checked.stdout + checked.stderr
    generated = run(checkout, "./gov", "check", "--generated", "--json", env=env)
    assert generated.returncode == 1
    assert "ENVIRONMENT_MISMATCH" in generated.stdout + generated.stderr
    for args in (("./gov", "doctor", "--json"), ("./scripts/verify.sh",)):
        result = run(checkout, *args, env=env)
        assert result.returncode != 0
        if args[0] == "./gov":
            assert "ENVIRONMENT_MISMATCH" in result.stdout + result.stderr
        else:
            assert "environment_resolution: failed" in result.stdout + result.stderr
            assert "declared interpreter" in result.stdout + result.stderr
        assert "Traceback" not in result.stdout + result.stderr
    diagnosed = run(checkout, "./gov", "doctor", "--json", env=env)
    assert json.loads(diagnosed.stdout)["status"] == "ENVIRONMENT_INVALID"


def test_system_bootstrap_diagnoses_missing_environment_without_becoming_project_python(
    checkout: Path,
) -> None:
    # System Python on PATH is not an approved bootstrap: refuse it, never adopt it.
    refused = run(checkout, "./gov", "doctor", "--json")
    assert refused.returncode == 1
    assert "ENVIRONMENT_MISMATCH" in refused.stderr
    assert "bootstrap.interpreter" in refused.stderr
    assert "Traceback" not in refused.stdout + refused.stderr
    # With an approved bootstrap and no project environment, doctor still diagnoses,
    # and that bootstrap is equally incapable of becoming project authority.
    result = run(
        checkout,
        "./gov",
        "doctor",
        "--json",
        env=environment(GOVERNANCE_PYTHON=sys.executable),
    )
    assert result.returncode == 1
    data = json.loads(result.stdout)
    assert data["status"] == "ENVIRONMENT_INVALID"
    assert data["interpreter"] is None
    assert data["diagnostics"][0]["fact"] == "python.interpreter"


def test_bootstrap_floor_is_derived_from_pack_metadata(checkout: Path) -> None:
    path = checkout / "tools/workspace_governance/MANIFEST.json"
    manifest = json.loads(path.read_text())
    manifest["runtime"] = {"python_requires": ">=99.0"}
    write(path, manifest)
    result = run(
        checkout, "./gov", "doctor", env=environment(GOVERNANCE_PYTHON=sys.executable)
    )
    assert result.returncode == 1
    assert ">=99.0" in result.stderr and "bootstrap.interpreter" in result.stderr
    assert "Traceback" not in result.stderr


def test_resolver_is_print_only_and_documented_command_executes(checkout: Path) -> None:
    env = environment(TET4D_PYTHON=sys.executable, GOVERNANCE_PYTHON=sys.executable)
    rejected = run(checkout, "./scripts/resolve_python_env.sh", "ignored.py", env=env)
    assert rejected.returncode == 2 and not rejected.stdout
    result = run(
        checkout,
        "bash",
        "-c",
        '"$(./scripts/resolve_python_env.sh)" -c "print(42)"',
        env=env,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "42"


@pytest.mark.parametrize("operation", ["unflag", "remove"])
def test_each_canonical_owner_is_protected(checkout: Path, operation: str) -> None:
    resolver = GovernanceResolver.for_root(checkout)
    workspace, project, _ = resolver.load()
    owners = [a for a in project["authorities"] if a["canonical_governance"]]
    assert owners
    for owner in owners:
        changed = copy.deepcopy(project)
        entry = next(
            a
            for a in changed["authorities"]
            if a["authority_id"] == owner["authority_id"]
        )
        if operation == "unflag":
            entry["canonical_governance"] = False
        else:
            changed["authorities"].remove(entry)
        issues = core.validate_manifests(
            checkout,
            workspace,
            changed,
            None,
            pack_root=checkout / "tools/workspace_governance",
        )
        assert any(i.fact.startswith("canonical_owner:") for i in issues), owner


def test_route_tool_fields_and_local_tool_override_are_consumed(checkout: Path) -> None:
    _, project, _ = GovernanceResolver.for_root(checkout).load()
    tool = checkout / "fake-godot"
    tool.write_text('#!/bin/sh\nprintf "test-tool:%s\\n" "$1"\n')
    tool.chmod(0o755)
    env = {
        "TET4D_PYTHON": sys.executable,
        "TET4D_ENVIRONMENT_MODE": execution_mode(),
    }
    local = {"tool_paths": {"godot": str(tool)}}
    data, issues = core.doctor(
        checkout, project, local, env, route="godot_product_shell"
    )
    assert not issues and data["route_tools"]["godot"] == "test-tool:--version"
    project["environment"]["route_tools"]["godot"]["version_args"] = ["--changed"]
    data, issues = core.doctor(
        checkout, project, local, env, route="godot_product_shell"
    )
    assert not issues and data["route_tools"]["godot"] == "test-tool:--changed"


@pytest.mark.parametrize("entrypoint", ["as_declared", "declared_native"])
@pytest.mark.canonical_gate_environment
def test_verify_and_project_test_use_the_doctor_selected_interpreter(
    checkout: Path,
    entrypoint: str,
) -> None:
    # Real verify startup and module checks; stop at the first policy boundary
    # so this regression does not recursively run the full test suite.
    selected = checkout / "traced-python"
    # Runtime instrumentation belongs outside protected checkout inputs.
    log = checkout.parent / (checkout.name + ".calls.jsonl")
    selected.write_text(
        f'#!/bin/sh\nprintf "%s\\n" "$*" >> "{log}"\nexec "{sys.executable}" "$@"\n'
    )
    selected.chmod(0o755)
    runner = checkout / "scripts/verify.sh"
    if entrypoint == "declared_native":
        from tools.workspace_governance.fleet_support import (
            digest,
            verification_binding,
        )

        reviewed = runner.read_bytes()
        name, rendered, mode = verification_binding(
            {
                "verification": {
                    "argv": ["./scripts/verify.sh"],
                    "runner": {
                        "path": "scripts/verify.sh",
                        "kind": "shell",
                        "integration": "native",
                        "native_sha256": digest(reviewed),
                    },
                }
            },
            checkout,
        )
        assert name == "scripts/verify.sh" and rendered == reviewed
        assert mode == 0o755
    inventory = checkout / "tools/governance/export_governance_inventory.py"
    inventory.write_text(
        "import sys\nprint('intentional-test-boundary', file=sys.stderr)\nraise SystemExit(79)\n"
    )
    env = environment(
        TET4D_PYTHON=str(selected),
        GOVERNANCE_PYTHON=sys.executable,
        PYTHON_BIN="/ignored/legacy",
    )
    diagnosed = run(checkout, "./gov", "doctor", "--print-interpreter", env=env)
    assert diagnosed.stdout.strip() == str(selected)
    verified = run(checkout, "./scripts/verify.sh", env=env)
    assert verified.returncode == 79, verified.stdout + verified.stderr
    assert "== FAILED: governance_inventory ==" in verified.stderr
    assert "intentional-test-boundary" in verified.stderr
    # The project-test invocation uses the same resolved executable.
    test = checkout / "test_interpreter.py"
    test.write_text(
        f"import sys\ndef test_identity():\n    assert sys.executable == {sys.executable!r}\n"
    )
    result = run(
        checkout, diagnosed.stdout.strip(), "-m", "pytest", "-q", str(test), env=env
    )
    assert result.returncode == 0, result.stdout + result.stderr
    calls = log.read_text()
    assert "import ruff" in calls and "import pytest" in calls
    assert "tools/governance/export_governance_inventory.py --check" in calls
    assert "-m pytest -q" in calls


@pytest.mark.parametrize(
    "script,override",
    [("bootstrap_env.sh", "PYTHON_BOOTSTRAP_BIN")],
)
def test_environment_creators_reject_unsupported_bootstrap_before_creating_venv(
    checkout: Path, script: str, override: str
) -> None:
    (checkout / "pyproject.toml").write_text('[project]\nrequires-python = ">=99"\n')
    result = run(
        checkout, "./scripts/" + script, env=environment(**{override: sys.executable})
    )
    assert result.returncode == 1
    assert "bootstrap.interpreter" in result.stderr and ">=99" in result.stderr
    assert not (checkout / ".venv").exists()
    assert "Traceback" not in result.stdout + result.stderr


def test_verify_local_owns_no_environment(checkout: Path) -> None:
    """It reports an unready environment; it never creates or repairs one.

    Owning a venv made verification a process that could change the environment
    it was about to verify, so the whole path is gone along with the
    `--rebuild-venv` flag that deleted one.
    """
    result = run(checkout, "./scripts/verify_local.sh", env=environment())

    assert result.returncode == 1
    assert "bootstrap_env.sh" in result.stderr
    assert not (checkout / ".venv").exists()
    assert "Traceback" not in result.stdout + result.stderr


def test_verify_local_rejects_the_flag_that_rebuilt_an_environment(
    checkout: Path,
) -> None:
    result = run(
        checkout, "./scripts/verify_local.sh", "--rebuild-venv", env=environment()
    )

    assert result.returncode == 2
    assert "Usage" in result.stderr
    assert not (checkout / ".venv").exists()


def recording_interpreter(path: Path, calls: Path, source_root: Path) -> Path:
    """A Python that records environment mutation instead of performing it.

    `-m pip` and `-m venv` are the only boundaries that change an environment;
    everything else passes through to a real interpreter so `gov` and `doctor`
    behave exactly as they would. That keeps these cases about shell control
    flow and the derived prefix rather than about pip, and keeps them off the
    gate's critical path -- a real editable install costs a minute per run.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "#!/bin/sh\n"
        f'CALLS="{calls}"\n'
        'if [ "$1" = "-m" ] && [ "$2" = "pip" ]; then\n'
        '  printf "pip\\n" >> "$CALLS"\n'
        "  exit 0\n"
        "fi\n"
        'if [ "$1" = "-m" ] && [ "$2" = "venv" ]; then\n'
        '  printf "venv %s\\n" "$3" >> "$CALLS"\n'
        '  mkdir -p "$3/bin"\n'
        '  cp "$0" "$3/bin/python"\n'
        '  chmod +x "$3/bin/python"\n'
        "  exit 0\n"
        "fi\n"
        f'PYTHONPATH="{source_root}" exec "{sys.executable}" "$@"\n'
    )
    path.chmod(0o755)
    return path


def without_hook_installation(checkout: Path) -> None:
    """Stop bootstrap at the environment boundary these cases are about.

    Hook installation resolves paths against the enclosing git repository, and
    under CODEX_MODE the temporary checkout sits inside this one, so the real
    script would report on a tree that is not under test.
    """
    (checkout / "scripts/install_git_hooks.sh").write_text("#!/bin/sh\nexit 0\n")


@pytest.mark.canonical_gate_environment
def test_installed_bootstrap_reuses_an_existing_interpreter(checkout: Path) -> None:
    """An interpreter that already exists must not be rebuilt over.

    Regression: the prefix was derived only inside the branch that creates an
    environment, so every re-run installed dependencies, wrote the git hooks,
    and then died reporting an unset variable.
    """
    calls = checkout / "mutation-calls.txt"
    calls.write_text("")
    stub = recording_interpreter(
        checkout / "existing-env/bin/python", calls, checkout / "src"
    )
    without_hook_installation(checkout)

    result = run(
        checkout,
        "./scripts/bootstrap_env.sh",
        env=environment(
            PYTHON_BOOTSTRAP_BIN=str(stub),
            GOVERNANCE_PYTHON=sys.executable,
            TET4D_PYTHON=str(stub),
            TET4D_ENVIRONMENT_MODE="installed",
        ),
    )

    assert result.returncode == 0, result.stdout + result.stderr
    recorded = calls.read_text()
    assert "venv " not in recorded, recorded
    assert "pip" in recorded, recorded
    # The prefix is still derived and reported on the path that creates nothing.
    assert str(checkout / "existing-env") in result.stdout


@pytest.mark.canonical_gate_environment
def test_installed_bootstrap_creates_at_exactly_the_derived_prefix(
    checkout: Path,
) -> None:
    calls = checkout / "mutation-calls.txt"
    calls.write_text("")
    stub = recording_interpreter(checkout / "seed/bin/python", calls, checkout / "src")
    without_hook_installation(checkout)

    # No interpreter override and no overlay, so the repository-local tier names
    # a path that does not exist yet.
    result = run(
        checkout,
        "./scripts/bootstrap_env.sh",
        env=environment(
            PYTHON_BOOTSTRAP_BIN=str(stub),
            GOVERNANCE_PYTHON=sys.executable,
            TET4D_ENVIRONMENT_MODE="installed",
        ),
    )

    assert result.returncode == 0, result.stdout + result.stderr
    recorded = calls.read_text()
    assert f"venv {checkout / '.venv'}\n" in recorded, recorded
    assert recorded.count("venv ") == 1, recorded
    assert "pip" in recorded, recorded


@pytest.mark.canonical_gate_environment
def test_shared_bootstrap_never_falls_back_to_building_a_local_environment(
    checkout: Path,
) -> None:
    """Source mode has no interpreter of its own to build.

    Silently creating a worktree `.venv` here would reintroduce exactly the
    per-checkout environment the shared toolchain replaces.
    """
    result = run(
        checkout,
        "./scripts/bootstrap_env.sh",
        env=environment(
            PYTHON_BOOTSTRAP_BIN=sys.executable,
            TET4D_ENVIRONMENT_MODE="source",
        ),
    )

    assert result.returncode == 1
    assert "bootstrap.interpreter" in result.stderr
    assert not (checkout / ".venv").exists()


@pytest.mark.canonical_gate_environment
def test_source_bootstrap_mutates_the_explicitly_governed_interpreter(
    checkout: Path,
) -> None:
    """An override outranks an overlay for both `gov env` and bootstrap."""
    overlay = wrapper(checkout)
    selected = checkout / "explicit-python"
    prefix = checkout / "explicit-prefix"
    prefix.mkdir()
    calls = checkout / "explicit-python.calls"
    selected.write_text(
        "#!/bin/sh\n"
        f'printf "%s\\n" "$*" >> "{calls}"\n'
        'if [ "$1" = "-c" ] && case "$2" in *"print(sys.prefix)"*) true;; *) false;; esac; then\n'
        f'  printf "%s\\n" "{prefix}"\n'
        "  exit 0\n"
        "fi\n"
        'if [ "$1" = "-m" ] && [ "$2" = "pip" ]; then exit 0; fi\n'
        f'exec "{sys.executable}" "$@"\n'
    )
    selected.chmod(0o755)
    (checkout / ".governance/workspace.local.json").write_text(
        json.dumps({"schema_version": 1, "interpreter": str(overlay)}),
        encoding="utf-8",
    )
    hooks = checkout / "scripts/install_git_hooks.sh"
    hooks.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    hooks.chmod(0o755)
    env = environment(
        GOVERNANCE_PYTHON=sys.executable,
        PYTHON_BOOTSTRAP_BIN=sys.executable,
        TET4D_ENVIRONMENT_MODE="source",
        TET4D_PYTHON=str(selected),
    )

    resolved = run(checkout, "./gov", "env", "--json", env=env)
    assert resolved.returncode == 0, resolved.stdout + resolved.stderr
    assert json.loads(resolved.stdout)["PYTHON_BIN"] == str(selected)

    bootstrapped = run(checkout, "./scripts/bootstrap_env.sh", env=env)
    assert bootstrapped.returncode == 0, bootstrapped.stdout + bootstrapped.stderr
    assert "-m pip install" in calls.read_text(encoding="utf-8")


def _dependency_probe_interpreter(
    checkout: Path, prefix: Path, *, installs: str
) -> Path:
    """A stub interpreter whose only modelled distribution is `bootstrap-probe`.

    `installs` is the version its `pip install` leaves behind, so a test can
    model pip exiting zero while the declaration stays unsatisfied. Everything
    else passes through to a real interpreter, which keeps the cost at a
    subprocess rather than an editable install.
    """
    version = prefix / "installed-version"
    calls = prefix / "pip-calls"
    selected = checkout / "selected-python"
    selected.write_text(
        f"#!{sys.executable}\n"
        "import importlib.metadata as metadata, pathlib, sys\n"
        f"prefix = pathlib.Path({str(prefix)!r})\n"
        f"version = pathlib.Path({str(version)!r})\n"
        f"calls = pathlib.Path({str(calls)!r})\n"
        "if sys.argv[1:3] == ['-m', 'pip']:\n"
        "    calls.write_text(calls.read_text() + 'install\\n' if calls.exists() else 'install\\n')\n"
        f"    version.write_text({installs!r})\n"
        "    sys.exit(0)\n"
        "if sys.argv[1] == '-c':\n"
        "    code = sys.argv[2]\n"
        "    if 'print(sys.prefix)' in code:\n"
        "        print(prefix); sys.exit(0)\n"
        "    real_version = metadata.version\n"
        "    def probe_version(name):\n"
        "        if name != 'bootstrap-probe': return real_version(name)\n"
        "        value = version.read_text() if version.exists() else ''\n"
        "        if not value: raise metadata.PackageNotFoundError(name)\n"
        "        return value\n"
        "    metadata.version = probe_version\n"
        "    exec(code)\n"
    )
    selected.chmod(0o755)
    return selected


def _probe_environment(selected: Path) -> dict[str, str]:
    return environment(
        GOVERNANCE_PYTHON=sys.executable,
        PYTHON_BOOTSTRAP_BIN=sys.executable,
        TET4D_ENVIRONMENT_MODE="source",
        TET4D_PYTHON=str(selected),
    )


@pytest.mark.canonical_gate_environment
@pytest.mark.parametrize("installed_version", ["", "0.5", "1.0"])
def test_source_bootstrap_checks_contents_on_cache_hit(
    checkout: Path, installed_version: str
) -> None:
    (checkout / "pyproject.toml").write_text(
        '[project]\nrequires-python = ">=3.11"\ndependencies = ["bootstrap-probe>=1"]\n'
    )
    prefix = checkout / "shared-prefix"
    prefix.mkdir()
    version = prefix / "installed-version"
    calls = prefix / "pip-calls"
    selected = _dependency_probe_interpreter(checkout, prefix, installs="1.0")
    hooks = checkout / "scripts/install_git_hooks.sh"
    hooks.write_text("#!/bin/sh\nexit 0\n")
    env = _probe_environment(selected)
    first = run(checkout, "./scripts/bootstrap_env.sh", env=env)
    assert first.returncode == 0, first.stdout + first.stderr
    fingerprint = (prefix / ".tet4d-dependency-fingerprint").read_text()
    version.write_text(installed_version)
    second = run(checkout, "./scripts/bootstrap_env.sh", env=env)
    assert second.returncode == 0, second.stdout + second.stderr
    assert version.read_text() == "1.0"
    assert len(calls.read_text().splitlines()) == (
        1 if installed_version == "1.0" else 2
    )
    assert (prefix / ".tet4d-dependency-fingerprint").read_text() == fingerprint


@pytest.mark.canonical_gate_environment
def test_source_bootstrap_refuses_an_installation_that_does_not_satisfy(
    checkout: Path,
) -> None:
    """`pip install` can exit zero and still leave a declaration unsatisfied.

    A shared toolchain is the case that produces it: another project's pin wins
    the resolution and pip reports a conflict warning rather than a failure. The
    fingerprint is the cache key every later run consults, so recording it here
    would turn one bad installation into a permanently skipped check.
    """
    (checkout / "pyproject.toml").write_text(
        '[project]\nrequires-python = ">=3.11"\ndependencies = ["bootstrap-probe>=1"]\n'
    )
    prefix = checkout / "shared-prefix"
    prefix.mkdir()
    selected = _dependency_probe_interpreter(checkout, prefix, installs="0.5")
    hooks = checkout / "scripts/install_git_hooks.sh"
    hooks.write_text("#!/bin/sh\nexit 0\n")

    result = run(
        checkout, "./scripts/bootstrap_env.sh", env=_probe_environment(selected)
    )

    assert result.returncode != 0, result.stdout + result.stderr
    assert (prefix / "pip-calls").exists(), "installation must have been attempted"
    assert "bootstrap-probe>=1: installed 0.5" in result.stderr, (
        "the failure must name the requirement and what is installed, "
        f"not exit silently: {result.stderr!r}"
    )
    assert not (prefix / ".tet4d-dependency-fingerprint").exists(), (
        "an unsatisfied installation must not record a cache hit for later runs"
    )
    assert not (prefix / ".tet4d-sync.lock").exists(), (
        "the shared-environment lock must be released so a retry is not blocked"
    )


@pytest.mark.canonical_gate_environment
def test_shared_bootstrap_certifies_synthetic_checkout_dependencies(
    tmp_path: Path,
) -> None:
    """The shared snapshot compares declarations, never Python metadata.

    These are separate mutable checkouts sharing one synthetic prefix.  The
    third checkout is the negative control: reversing the compatibility result
    would let its contradictory declaration reach mutation.
    """
    first, second, incompatible = (
        build_checkout(tmp_path / name) for name in ("first", "second", "bad")
    )
    prefix = tmp_path / "shared-prefix"
    prefix.mkdir()

    def prepare(
        checkout: Path, requirement: str, python_requires: str
    ) -> dict[str, str]:
        (checkout / "pyproject.toml").write_text(
            "[project]\n"
            f'requires-python = "{python_requires}"\n'
            f'dependencies = ["{requirement}"]\n',
            encoding="utf-8",
        )
        selected = _dependency_probe_interpreter(checkout, prefix, installs="1.0")
        hooks = checkout / "scripts/install_git_hooks.sh"
        hooks.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
        hooks.chmod(0o755)
        return _probe_environment(selected)

    first_env = prepare(first, "bootstrap-probe>=1", ">=3.11")
    second_env = prepare(second, "bootstrap-probe>=1", ">=3.10")
    incompatible_env = prepare(incompatible, "bootstrap-probe<1", ">=3.11")
    assert run(first, "./scripts/bootstrap_env.sh", env=first_env).returncode == 0
    # Changing only Python metadata must not become the compatibility signal.
    accepted = run(second, "./scripts/bootstrap_env.sh", env=second_env)
    assert accepted.returncode == 0, accepted.stdout + accepted.stderr
    rejected = run(incompatible, "./scripts/bootstrap_env.sh", env=incompatible_env)
    assert rejected.returncode != 0
    assert "not certifiably compatible" in rejected.stderr
    assert "contradictory" in rejected.stderr

    # Negative control: temporarily bypass the copied checkout's guard. The
    # assertion above must then fail because mutation reaches the later content
    # check instead of being stopped by declaration compatibility.
    bootstrap = incompatible / "scripts/bootstrap_env.sh"
    guarded = (
        'if ! report="$(compatibility_report "$PYTHON_BOOTSTRAP_BIN" '
        '"$SNAPSHOT_PATH" "$requested_snapshot")"; then'
    )
    bootstrap.write_text(
        bootstrap.read_text(encoding="utf-8").replace(guarded, "if false; then"),
        encoding="utf-8",
    )
    bypassed = run(incompatible, "./scripts/bootstrap_env.sh", env=incompatible_env)
    assert "installation did not satisfy" in bypassed.stderr
    with pytest.raises(AssertionError):
        assert "not certifiably compatible" in bypassed.stderr


@pytest.mark.canonical_gate_environment
def test_shared_bootstrap_lock_recovers_only_proven_stale_local_owners(
    tmp_path: Path,
) -> None:
    checkout = build_checkout(tmp_path / "checkout")
    (checkout / "pyproject.toml").write_text(
        '[project]\nrequires-python = ">=3.11"\ndependencies = ["bootstrap-probe>=1"]\n',
        encoding="utf-8",
    )
    prefix = tmp_path / "shared-prefix"
    prefix.mkdir()
    selected = _dependency_probe_interpreter(checkout, prefix, installs="1.0")
    hooks = checkout / "scripts/install_git_hooks.sh"
    hooks.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    hooks.chmod(0o755)
    lock = prefix / ".tet4d-sync.lock"
    lock.mkdir()
    host = subprocess.check_output(["hostname"], text=True).strip()
    (lock / "owner").write_text(
        f"pid=99999999\nhost={host}\nstart=unavailable\n", encoding="utf-8"
    )
    recovered = run(
        checkout, "./scripts/bootstrap_env.sh", env=_probe_environment(selected)
    )
    assert recovered.returncode == 0, recovered.stdout + recovered.stderr
    assert "stale; recovering" in recovered.stderr
    assert not lock.exists()

    lock.mkdir()
    (lock / "owner").write_text(
        f"pid={os.getpid()}\nhost={host}\nstart=unavailable\n", encoding="utf-8"
    )
    live = run(checkout, "./scripts/bootstrap_env.sh", env=_probe_environment(selected))
    assert live.returncode != 0
    assert "live owner" in live.stderr
    (lock / "owner").write_text(
        "pid=99999999\nhost=another-host\nstart=unavailable\n", encoding="utf-8"
    )
    foreign = run(
        checkout, "./scripts/bootstrap_env.sh", env=_probe_environment(selected)
    )
    assert foreign.returncode != 0
    assert "foreign, refusing recovery" in foreign.stderr
