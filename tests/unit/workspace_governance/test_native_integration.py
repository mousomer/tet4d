"""Exercise the native shell graph with synthetic phases and the real safe wrapper."""

from __future__ import annotations

import ast
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
PACK = Path(
    os.environ.get("POLICY_KIT_RUNTIME_ROOT", str(ROOT / "tools/workspace_governance"))
).resolve()
SOURCE_ROOT = Path(os.environ.get("POLICY_KIT_NATIVE_SOURCE_ROOT", str(ROOT))).resolve()
PRIVATE = "SYNTHETIC_MATCHED_SOURCE_NEVER_DISPLAY"


def _synthetic_gate(tmp_path):
    shutil.copytree(
        PACK,
        tmp_path / "tools/workspace_governance",
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".ruff_cache"),
    )
    (tmp_path / "scripts").mkdir()
    for name in (
        "verify.sh",
        "verify-governance.sh",
        "check_policy_compliance_repo.sh",
        "check_policy_compliance_extensions_repo.sh",
    ):
        shutil.copy2(ROOT / "scripts" / name, tmp_path / "scripts" / name)
    (tmp_path / "config/project").mkdir(parents=True)
    shutil.copy2(
        ROOT / "config/project/policy_pack.json",
        tmp_path / "config/project/policy_pack.json",
    )
    trace = tmp_path / "trace.jsonl"
    python = tmp_path / "fixture_python"
    python.write_text(
        "#!"
        + sys.executable
        + "\n"
        + """import json,os,subprocess,sys
from pathlib import Path
args=sys.argv[1:]
trace=Path(os.environ['FIXTURE_TRACE'])
def record(value):
    with trace.open('a') as stream: stream.write(json.dumps(value)+'\\n')
if args and args[0].endswith('/diagnostics.py'):
    os.execv(sys.executable,[sys.executable,*args])
if args[:1]==['-c']:
    raise SystemExit(0)
if args==['-']:
    record(['phase','legacy_imports'])
    os.execv(sys.executable,[sys.executable,'-'])
if args[:1]==['-']:
    print('tools tests')
    raise SystemExit(0)
if args[:1]==['fixture_step']:
    phase=args[1]
else:
    phase=args[0] if args else 'no-args'
record(['phase',phase])
if args[:3]==['-m','ruff','check'] and os.environ.get('FIXTURE_REAL_RUFF')=='1':
    os.execv(sys.executable,[sys.executable,*args])
if os.environ.get('FIXTURE_FAIL')==phase:
    if phase in {'git_sanitation','git_sanitation_repo','tools/workspace_governance/sanitation.py','tools/governance/scan_secrets.py'}:
        print('SYNTHETIC_MATCHED_SOURCE_NEVER_DISPLAY')
    else:
        print('fixture failure: '+phase)
    raise SystemExit(71)
if phase=='tools/governance/validate_governance.py':
    status=subprocess.run([sys.executable,__file__,'tools/governance/validate_project_contracts.py'],check=False).returncode
    raise SystemExit(status)
if phase=='git_sanitation':
    print('WARN: absolute Unix paths found in git-visible text files')
    print('tracked.txt:1:SYNTHETIC_MATCHED_SOURCE_NEVER_DISPLAY')
    print('WARN: absolute Windows paths found in git-visible text files')
    print('tracked.txt:2:SYNTHETIC_MATCHED_SOURCE_NEVER_DISPLAY')
    print("WARN: '../' patterns found in git-visible text files")
    print('WARN: filenames with spaces detected (tracked or untracked, excluding ignored)')
    print('WARN: sanitation checks reported 4 issue class(es)')
if phase=='tools/workspace_governance/sanitation.py':
    print(json.dumps({'profile':'git-visible-text-patterns-v1','inspected_files':1,'finding_count':0,'skipped_count':100000,'error_count':0,'findings':[],'errors':[],'skipped':[{'path':'SYNTHETIC_MATCHED_SOURCE_NEVER_DISPLAY','reason':'binary'}]*50}))
"""
    )
    python.chmod(0o755)
    gov = tmp_path / "gov"
    gov.write_text(
        "#!"
        + sys.executable
        + "\n"
        + """import json,os,sys
from pathlib import Path
args=sys.argv[1:]
with Path(os.environ['FIXTURE_TRACE']).open('a') as stream: stream.write(json.dumps(['gov',*args])+'\\n')
if args[0]=='env':
    if os.environ.get('FIXTURE_FAIL')=='environment_resolution':
        print('SYNTHETIC_MATCHED_SOURCE_NEVER_DISPLAY',file=sys.stderr)
        raise SystemExit(73)
    print('export PYTHON_BIN='+os.environ['FIXTURE_PYTHON'])
else:
    print(json.dumps({'status':'ok','diagnostics':[]}))
"""
    )
    gov.chmod(0o755)
    names = [
        "check_policy_compliance",
        "check_git_sanitation_repo",
        "check_git_sanitation",
        "check_policy_template_drift",
        "check_architecture_metrics_soft_gate",
        "check_architecture_metric_budgets",
        "check_engine_core_purity",
        "check_architecture_boundaries",
    ]
    for name in names:
        phase = (
            "git_sanitation"
            if name == "check_git_sanitation"
            else name.removeprefix("check_")
        )
        script = tmp_path / "scripts" / (name + ".sh")
        script.write_text(
            "#!/bin/sh\nexec "
            + shlex.quote(str(python))
            + " fixture_step "
            + shlex.quote(phase)
            + "\n"
        )
        script.chmod(0o755)
    text = (ROOT / "scripts/check_policy_compliance_extensions_repo.sh").read_text()
    required = shlex.split(
        re.search(r"required_files=\(\n(.*?)\n\)", text, re.DOTALL)[1]
    )
    for name in required:
        path = tmp_path / name
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("Controlled required policy source.\n")
    environment = _environment(trace, python)
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, env=environment, check=True)
    subprocess.run(["git", "add", "."], cwd=tmp_path, env=environment, check=True)
    return trace, python


def _environment(trace, python):
    environment = {
        key: value
        for key, value in os.environ.items()
        if not key.startswith("GIT_")
        and key
        not in {
            "PYTHONPATH",
            "PYTHONHOME",
            "BASH_ENV",
            "ENV",
            "MAKEFLAGS",
            "MAKEFILES",
            "MFLAGS",
            "GNUMAKEFLAGS",
            "TET4D_STATE_ROOT",
        }
    }
    environment.update(
        CODEX_MODE="1",
        FIXTURE_TRACE=str(trace),
        FIXTURE_PYTHON=str(python),
        GIT_CONFIG_GLOBAL=os.devnull,
        GIT_CONFIG_SYSTEM=os.devnull,
    )
    return environment


def _run(tmp_path, argv, fail=None, *, alter=None):
    trace, python = _synthetic_gate(tmp_path)
    environment = _environment(trace, python)
    if alter is not None:
        alter(tmp_path, environment)
    if fail:
        environment["FIXTURE_FAIL"] = fail
    result = subprocess.run(
        ["bash", *argv],
        cwd=tmp_path,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    return result, [json.loads(line) for line in trace.read_text().splitlines()]


@pytest.mark.parametrize("verbose", [False, True])
def test_full_native_gate_checks_once_and_never_displays_matches(tmp_path, verbose):
    argv = ["scripts/verify.sh", *(["--verbose"] if verbose else [])]
    result, trace = _run(tmp_path, argv)
    assert result.returncode == 0, result.stderr
    output = result.stdout + result.stderr
    assert PRIVATE not in output and len(output.encode()) <= 8192
    assert len([row for row in trace if row[:2] == ["gov", "doctor"]]) == 1
    assert len([row for row in trace if row[:2] == ["gov", "check"]]) == 1
    assert ["gov", "check", "--generated", "--summary", "--json"] in trace
    assert (
        sum(
            row == ["phase", "tools/governance/export_governance_inventory.py"]
            for row in trace
        )
        == 1
    )
    assert sum(row == ["phase", "policy_compliance"] for row in trace) == 1
    assert sum(row == ["phase", "git_sanitation"] for row in trace) == 1
    assert sum(row == ["phase", "policy_template_drift"] for row in trace) == 1
    assert (
        sum(
            row == ["phase", "tools/workspace_governance/sanitation.py"]
            for row in trace
        )
        == 1
    )
    assert not any(
        row == ["phase", "tools/governance/generate_configuration_reference.py"]
        for row in trace
    )
    assert "warnings=4" in output and "skipped_count=100000" in output
    for phase in (
        "engine_core_purity",
        "architecture_boundaries",
        "legacy_imports",
        "tools/governance/validate_project_contracts.py",
        "tools/governance/scan_secrets.py",
    ):
        assert trace.count(["phase", phase]) == 1


@pytest.mark.parametrize("verbose", [False, True])
@pytest.mark.canonical_gate_environment
def test_ordinary_failure_preserves_status_and_checker_diagnostics(tmp_path, verbose):
    result, trace = _run(
        tmp_path,
        ["scripts/verify.sh", *(["--verbose"] if verbose else [])],
        fail="policy_compliance",
    )
    assert result.returncode == 71
    output = result.stdout + result.stderr
    assert "fixture failure: policy_compliance" in output
    assert "checker.failed" not in output and PRIVATE not in output
    assert not any(row == ["phase", "-m"] for row in trace)


@pytest.mark.parametrize("verbose", [False, True])
@pytest.mark.canonical_gate_environment
def test_real_ruff_failure_displays_rule_and_relative_location(tmp_path, verbose):
    def alter(root, environment):
        (root / "tests").mkdir()
        (root / "tests/bad_lint.py").write_text("import os\n")
        environment["FIXTURE_REAL_RUFF"] = "1"

    result, trace = _run(
        tmp_path,
        ["scripts/verify.sh", *(["--verbose"] if verbose else [])],
        alter=alter,
    )
    output = result.stdout + result.stderr
    assert result.returncode == 1
    assert "F401" in output and "tests/bad_lint.py:1:8" in output
    assert "checker.failed" not in output
    assert trace.count(["phase", "-m"]) == 1


@pytest.mark.parametrize("verbose", [False, True])
@pytest.mark.parametrize(
    ("phase", "checker"),
    [
        ("git_sanitation", "git_sanitation_baseline"),
        ("git_sanitation_repo", "git_sanitation_repo"),
        ("tools/workspace_governance/sanitation.py", "pack_sanitation"),
        ("tools/governance/scan_secrets.py", "secret_scan"),
    ],
)
@pytest.mark.canonical_gate_environment
def test_scanner_failures_preserve_status_without_matches(
    tmp_path, verbose, phase, checker
):
    result, trace = _run(
        tmp_path,
        ["scripts/verify.sh", *(["--verbose"] if verbose else [])],
        fail=phase,
    )
    output = result.stdout + result.stderr
    assert result.returncode == 71
    assert f"{checker}: failed" in output and "checker.failed" in output
    assert PRIVATE not in output
    assert trace.count(["phase", phase]) == 1


def test_standalone_baseline_certifies_once_without_product_phases(tmp_path):
    result, trace = _run(tmp_path, ["scripts/verify-governance.sh"])
    assert result.returncode == 0, result.stderr
    assert len([row for row in trace if row[:2] == ["gov", "doctor"]]) == 1
    assert len([row for row in trace if row[:2] == ["gov", "check"]]) == 1
    assert PRIVATE not in result.stdout + result.stderr
    assert not any(row == ["phase", "-m"] for row in trace)


@pytest.mark.parametrize(
    "argv",
    [
        ["scripts/verify.sh"],
        ["scripts/verify.sh", "--verbose"],
        ["scripts/verify-governance.sh"],
    ],
)
def test_environment_bootstrap_failure_is_safe_and_preserves_status(tmp_path, argv):
    result, trace = _run(tmp_path, argv, fail="environment_resolution")
    assert result.returncode == 73
    assert "environment_resolution: failed (exit=73)" in result.stderr
    assert PRIVATE not in result.stdout + result.stderr
    assert trace == [["gov", "env"]]


def test_native_managed_section_and_provenance_register_real_families():
    text = (ROOT / "scripts/verify.sh").read_text()
    first = text.index("# BEGIN workspace-governance managed verification")
    assert first > text.index("prepare_verify_runtime\n")
    assert text.count("# BEGIN workspace-governance managed verification") == 1
    assert "scripts/verify-governance.sh" not in text
    assert not re.search(
        r'run_(?:governance_)?step "config_reference"[^\n]*generate_configuration_reference.py',
        text,
    )
    families = set(
        re.findall(r'^run_governance_step "([a-z][a-z0-9_]*)"', text, re.MULTILINE)
    )
    policy = json.loads((ROOT / "config/project/policy_pack.json").read_text())
    assert families <= policy["governance_surface"]["validator_provenance"].keys()
    assert {
        "environment_doctor",
        "config_reference",
        "governance_inventory",
        "git_sanitation_baseline",
        "template_drift",
        "pack_sanitation",
    } <= families
    assert (
        'run_governance_step "policy_compliance_repo" ./scripts/check_policy_compliance_extensions_repo.sh'
        in text
    )


def test_native_aggregate_really_owns_the_factored_contract_leaf():
    tree = ast.parse(
        (SOURCE_ROOT / "tools/governance/validate_governance.py").read_text()
    )
    registry = next(
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "_checks"
    )
    checks = [
        node
        for node in ast.walk(registry)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "GovernanceCheck"
    ]
    contracts = [
        node
        for node in checks
        if isinstance(node.args[0], ast.Constant) and node.args[0].value == "contracts"
    ]
    assert len(contracts) == 1
    assert ast.unparse(contracts[0].args[1]) == "validate_project_contracts.main"


def test_standalone_full_policy_wrapper_retains_extensions_and_shared_leaves(tmp_path):
    result, trace = _run(tmp_path, ["scripts/check_policy_compliance_repo.sh"])
    assert result.returncode == 0, result.stderr
    assert trace.count(["gov", "env"]) == 1
    for phase in (
        "engine_core_purity",
        "architecture_boundaries",
        "legacy_imports",
        "tools/governance/validate_project_contracts.py",
        "tools/governance/scan_secrets.py",
    ):
        assert trace.count(["phase", phase]) == 1


@pytest.mark.parametrize(
    "phase",
    [
        "tools/governance/validate_project_contracts.py",
        "tools/governance/scan_secrets.py",
    ],
)
@pytest.mark.parametrize(
    "wrapper", ["scripts/check_policy_compliance_repo.sh", "scripts/verify.sh"]
)
def test_shared_leaf_failure_rejects_standalone_and_native_gate(
    tmp_path, phase, wrapper
):
    result, trace = _run(tmp_path, [wrapper], fail=phase)
    assert result.returncode != 0
    assert trace.count(["phase", phase]) == 1
    if wrapper == "scripts/verify.sh":
        assert result.returncode == 71
        assert PRIVATE not in result.stdout + result.stderr
        assert not any(row == ["phase", "-m"] for row in trace)


@pytest.mark.parametrize("phase", ["engine_core_purity", "architecture_boundaries"])
def test_extension_guard_failure_remains_accepting_gate_obligation(tmp_path, phase):
    result, trace = _run(tmp_path, ["scripts/verify.sh"], fail=phase)
    assert result.returncode == 71 and trace.count(["phase", phase]) == 1
    assert PRIVATE not in result.stdout + result.stderr
    assert not any(
        row == ["phase", "tools/governance/validate_project_contracts.py"]
        for row in trace
    )


def test_extension_required_source_failure_still_rejects_native_gate(tmp_path):
    result, trace = _run(
        tmp_path,
        ["scripts/verify.sh"],
        alter=lambda root, env: (root / "AGENTS.md").unlink(),
    )
    assert result.returncode == 2
    assert "Missing required policy file: AGENTS.md" in result.stderr
    assert not any(row == ["phase", "engine_core_purity"] for row in trace)


def test_extension_untracked_source_failure_still_rejects_native_gate(tmp_path):
    def alter(root, environment):
        subprocess.run(
            ["git", "rm", "--cached", "--quiet", "AGENTS.md"],
            cwd=root,
            env=environment,
            check=True,
        )

    result, trace = _run(tmp_path, ["scripts/verify.sh"], alter=alter)
    assert result.returncode == 2
    assert "Required policy file must be tracked in git: AGENTS.md" in result.stderr
    assert not any(row == ["phase", "engine_core_purity"] for row in trace)


def test_extension_legacy_import_guard_still_rejects_native_gate(tmp_path):
    def alter(root, environment):
        (root / "forbidden.py").write_text(f"import tetris_nd  # {PRIVATE}\n")
        subprocess.run(
            ["git", "add", "forbidden.py"], cwd=root, env=environment, check=True
        )

    result, trace = _run(tmp_path, ["scripts/verify.sh"], alter=alter)
    assert result.returncode == 1 and trace.count(["phase", "legacy_imports"]) == 1
    output = result.stdout + result.stderr
    assert "forbidden.py:1: legacy import" in output
    assert "import tetris_nd" not in output and PRIVATE not in output


def test_wrapper_and_extensions_have_mechanical_source_contracts():
    policy = json.loads((ROOT / "config/project/policy_pack.json").read_text())
    paths = policy["maintenance_contract"]["required_paths"]["ci_scripts"]
    rules = policy["maintenance_contract"]["content_rules"]
    for name in (
        "scripts/check_policy_compliance_repo.sh",
        "scripts/check_policy_compliance_extensions_repo.sh",
    ):
        assert name in paths
        rule = next(row for row in rules if row["file"] == name)
        text = (ROOT / name).read_text()
        assert all(token in text for token in rule["must_contain"])
    extensions = (
        ROOT / "scripts/check_policy_compliance_extensions_repo.sh"
    ).read_text()
    assert (
        '"$PYTHON_BIN" tools/governance/validate_project_contracts.py' not in extensions
    )
    assert '"$PYTHON_BIN" tools/governance/scan_secrets.py' not in extensions
