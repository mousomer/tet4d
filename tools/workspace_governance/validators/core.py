from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

DIAGNOSTIC_CLASSES = {
    "DUPLICATE_AUTHORITY",
    "CONFLICTING_VALUE",
    "AMBIGUOUS_AUTHORITY",
    "BROKEN_REFERENCE",
    "STALE_GENERATED_SURFACE",
    "PACK_DRIFT",
    "ENVIRONMENT_MISMATCH",
}


@dataclass(frozen=True)
class Diagnostic:
    code: str
    fact: str
    owner: str
    sources: tuple[str, ...]
    reason: str
    repair: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def load_manifest_json(path: Path) -> dict[str, Any]:
    def reject(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"duplicate JSON key: {key}")
            result[key] = value
        return result

    value = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=reject)
    if not isinstance(value, dict):
        raise TypeError("top-level value must be an object")
    return value


def content_hash(root: Path, files: list[str]) -> str:
    digest = hashlib.sha256()
    for rel in sorted(files):
        digest.update(rel.encode() + b"\0")
        digest.update((root / rel).read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def pack_hash(pack_root: Path) -> tuple[str, list[str]]:
    files = sorted(
        p.relative_to(pack_root).as_posix()
        for p in pack_root.rglob("*")
        if p.is_file() and "__pycache__" not in p.parts
    )
    return content_hash(pack_root, files), files


def _diag(
    code: str, fact: str, owner: str, sources: list[str], reason: str, repair: str
) -> Diagnostic:
    return Diagnostic(code, fact, owner, tuple(sources), reason, repair)


def validate_manifests(  # noqa: C901 - each independent rule emits a stable diagnostic
    root: Path,
    workspace: dict[str, Any],
    project: dict[str, Any],
    local: dict[str, Any] | None,
) -> list[Diagnostic]:
    issues: list[Diagnostic] = []
    workspace_allowed = {
        "schema_version",
        "workspace_id",
        "governance_pack",
        "projects",
        "relationships",
        "defaults",
    }
    project_allowed = {
        "schema_version",
        "project",
        "authorities",
        "routes",
        "verification",
        "execution",
        "generated_surfaces",
        "environment",
        "sanitation",
        "compatibility",
    }
    local_allowed = {
        "schema_version",
        "interpreter",
        "tool_paths",
        "checkout_locations",
        "cache_locations",
    }
    for layer, payload, allowed, source in (
        ("workspace", workspace, workspace_allowed, ".governance/workspace.json"),
        ("project", project, project_allowed, "config/governance/project.json"),
    ):
        for key in sorted(set(payload) - allowed):
            issues.append(
                _diag(
                    "CONFLICTING_VALUE",
                    key,
                    layer,
                    [source],
                    f"field is not owned by the {layer} layer",
                    "move the fact to its owning layer or reference its authority",
                )
            )
    if local is not None:
        for key in sorted(set(local) - local_allowed):
            issues.append(
                _diag(
                    "CONFLICTING_VALUE",
                    key,
                    "local",
                    [".governance/workspace.local.json"],
                    "local overlay attempted to define semantic governance",
                    "remove the semantic field; local overlays may contain execution locations only",
                )
            )

    required_workspace = workspace_allowed
    required_project = project_allowed
    for key in sorted(required_workspace - set(workspace)):
        issues.append(
            _diag(
                "BROKEN_REFERENCE",
                key,
                "workspace",
                [".governance/workspace.json"],
                "required workspace field is missing",
                "add the field to the workspace manifest",
            )
        )
    for key in sorted(required_project - set(project)):
        issues.append(
            _diag(
                "BROKEN_REFERENCE",
                key,
                "project",
                ["config/governance/project.json"],
                "required project field is missing",
                "add the field to the project manifest",
            )
        )

    for layer, payload, source in (
        ("workspace", workspace, ".governance/workspace.json"),
        ("project", project, "config/governance/project.json"),
    ):
        if payload.get("schema_version") != 1:
            issues.append(
                _diag(
                    "CONFLICTING_VALUE",
                    "schema_version",
                    layer,
                    [source],
                    "manifest schema version is not supported by this pack",
                    "sync a compatible pack or migrate the manifest explicitly",
                )
            )
    if local is not None and local.get("schema_version") != 1:
        issues.append(
            _diag(
                "CONFLICTING_VALUE",
                "schema_version",
                "local",
                [".governance/workspace.local.json"],
                "local overlay schema version is unsupported",
                "update or remove the local overlay",
            )
        )

    workspace_projects = workspace.get("projects", [])
    project_claims: dict[str, list[dict[str, Any]]] = {}
    repository_claims: dict[str, list[dict[str, Any]]] = {}
    if isinstance(workspace_projects, list):
        for entry in workspace_projects:
            if not isinstance(entry, dict):
                continue
            project_id = entry.get("id")
            repository = entry.get("repository")
            if isinstance(project_id, str):
                project_claims.setdefault(project_id, []).append(entry)
            if isinstance(repository, str):
                repository_claims.setdefault(repository, []).append(entry)
    for fact, entries in sorted({**project_claims, **repository_claims}.items()):
        if len(entries) > 1:
            issues.append(
                _diag(
                    "AMBIGUOUS_AUTHORITY",
                    f"workspace-project:{fact}",
                    "workspace",
                    [".governance/workspace.json"],
                    "multiple project entries claim the same routing identity",
                    "assign unique project IDs and repository roots",
                )
            )
    selected_project = (
        project.get("project", {}).get("id")
        if isinstance(project.get("project"), dict)
        else None
    )
    if selected_project not in project_claims:
        issues.append(
            _diag(
                "BROKEN_REFERENCE",
                "project.id",
                "workspace/project",
                [".governance/workspace.json", "config/governance/project.json"],
                "project manifest ID is not a workspace member",
                "add a unique workspace project entry referencing this manifest",
            )
        )

    authorities = project.get("authorities", [])
    by_id: dict[str, list[dict[str, Any]]] = {}
    if isinstance(authorities, list):
        for entry in authorities:
            if isinstance(entry, dict) and isinstance(entry.get("authority_id"), str):
                by_id.setdefault(entry["authority_id"], []).append(entry)
    for authority_id, entries in sorted(by_id.items()):
        if len(entries) > 1:
            issues.append(
                _diag(
                    "DUPLICATE_AUTHORITY",
                    authority_id,
                    "project",
                    [str(e.get("source", "<missing>")) for e in entries],
                    "stable authority ID is declared more than once",
                    "deduplicate identical declarations or assign distinct scoped IDs",
                )
            )
        for entry in entries:
            source = entry.get("source")
            if not isinstance(source, str) or not (root / source).exists():
                issues.append(
                    _diag(
                        "BROKEN_REFERENCE",
                        f"authority:{authority_id}",
                        "project",
                        [str(source or "<missing>")],
                        "authority source does not exist",
                        "restore the authority or correct its repo-relative source",
                    )
                )

    scope_claims: dict[str, list[dict[str, Any]]] = {}
    for entries in by_id.values():
        for entry in entries:
            if entry.get("exclusive") is True and isinstance(entry.get("scope"), str):
                scope_claims.setdefault(entry["scope"], []).append(entry)
    for scope, entries in sorted(scope_claims.items()):
        ids = sorted(str(e.get("authority_id")) for e in entries)
        if len(set(ids)) > 1:
            issues.append(
                _diag(
                    "AMBIGUOUS_AUTHORITY",
                    scope,
                    "human/project",
                    [str(e.get("source", "<missing>")) for e in entries],
                    f"exclusive scope has candidate authority IDs: {', '.join(ids)}",
                    "resolve the human governance contradiction explicitly; do not choose by discovery order",
                )
            )

    known = set(by_id)
    reference_specs: list[tuple[str, object]] = []
    verification = project.get("verification", {})
    if isinstance(verification, dict):
        reference_specs.extend(
            (f"verification.{key}", value)
            for key, value in verification.items()
            if isinstance(value, dict)
        )
    environment = project.get("environment", {})
    if isinstance(environment, dict):
        reference_specs.extend(
            (f"environment.{key}", value)
            for key, value in environment.items()
            if isinstance(value, dict) and "authority_ref" in value
        )
    for fact, spec in reference_specs:
        authority_id = spec.get("authority_ref")
        if authority_id not in known:
            issues.append(
                _diag(
                    "BROKEN_REFERENCE",
                    fact,
                    "project",
                    ["config/governance/project.json"],
                    f"fact references missing authority ID {authority_id}",
                    "declare the authority or correct the typed reference",
                )
            )
    routes = project.get("routes", {})
    if isinstance(routes, dict):
        for route_id, route in sorted(routes.items()):
            if not isinstance(route, dict):
                continue
            for authority_id in route.get("authority_refs", []):
                if authority_id not in known:
                    issues.append(
                        _diag(
                            "BROKEN_REFERENCE",
                            f"route:{route_id}",
                            "project",
                            ["config/governance/project.json"],
                            f"route references missing authority ID {authority_id}",
                            "declare the authority or correct the typed reference",
                        )
                    )
    known_routes = set(routes) if isinstance(routes, dict) else set()
    execution = project.get("execution", {})
    profiles = execution.get("profiles", {}) if isinstance(execution, dict) else {}
    if isinstance(profiles, dict):
        for profile_id, profile in profiles.items():
            if not isinstance(profile, dict):
                continue
            for route_id in profile.get("routes", []):
                if route_id not in known_routes:
                    issues.append(
                        _diag(
                            "BROKEN_REFERENCE",
                            f"profile:{profile_id}",
                            "project",
                            ["config/governance/project.json"],
                            f"execution profile references missing route {route_id}",
                            "declare the route or correct the typed reference",
                        )
                    )
    scenarios = (
        execution.get("representative_scenarios", [])
        if isinstance(execution, dict)
        else []
    )
    if isinstance(scenarios, list):
        for scenario in scenarios:
            if not isinstance(scenario, dict):
                continue
            for route_id in scenario.get("routes", []):
                if route_id not in known_routes:
                    issues.append(
                        _diag(
                            "BROKEN_REFERENCE",
                            f"scenario:{scenario.get('id', '<missing>')}",
                            "project",
                            ["config/governance/project.json"],
                            f"scenario references missing route {route_id}",
                            "declare the route or correct the typed reference",
                        )
                    )

    for surface in project.get("generated_surfaces", []):
        if not isinstance(surface, dict):
            continue
        source = surface.get("source")
        target = surface.get("target")
        expected = surface.get("source_sha256")
        if not isinstance(source, str) or not isinstance(target, str):
            issues.append(
                _diag(
                    "BROKEN_REFERENCE",
                    "generated_surface",
                    "project",
                    ["config/governance/project.json"],
                    "generated surface lacks a source or target reference",
                    "declare repo-relative source and target paths",
                )
            )
            continue
        source_path = root / source
        target_path = root / target
        if not source_path.is_file() or not target_path.is_file():
            issues.append(
                _diag(
                    "BROKEN_REFERENCE",
                    target,
                    "project",
                    [source, target],
                    "generated source relationship points to a missing file",
                    "restore the source/target or remove the relationship",
                )
            )
        elif (
            isinstance(expected, str)
            and hashlib.sha256(source_path.read_bytes()).hexdigest() != expected
        ):
            is_facade = surface.get("kind") == "compatibility_facade"
            issues.append(
                _diag(
                    "CONFLICTING_VALUE" if is_facade else "STALE_GENERATED_SURFACE",
                    target,
                    "project",
                    [source, target],
                    "compatibility facade disagrees with canonical authority"
                    if is_facade
                    else "recorded source hash no longer matches its authority",
                    "update the compatibility facade from its canonical authority"
                    if is_facade
                    else "regenerate the surface from the declared source",
                )
            )

    unix_user_roots = "/" + "Users/|/" + "home/"
    machine_path = re.compile(rf"(?:^|[\s\"'])(?:{unix_user_roots}|[A-Za-z]:[\\/])")
    for rel, payload in (
        (".governance/workspace.json", workspace),
        ("config/governance/project.json", project),
    ):
        if machine_path.search(json.dumps(payload)):
            issues.append(
                _diag(
                    "CONFLICTING_VALUE",
                    "machine_local_path",
                    "local",
                    [rel],
                    "tracked semantic manifest contains a machine-local absolute path",
                    "move the value to the ignored local overlay",
                )
            )
    return issues


def validate_pack(root: Path, workspace: dict[str, Any]) -> list[Diagnostic]:
    lock_rel = (
        workspace.get("governance_pack", {}).get("lock")
        if isinstance(workspace.get("governance_pack"), dict)
        else None
    )
    if not isinstance(lock_rel, str):
        return [
            _diag(
                "BROKEN_REFERENCE",
                "governance_pack.lock",
                "workspace",
                [".governance/workspace.json"],
                "pack lock reference is missing",
                "declare a repo-relative lock path",
            )
        ]
    try:
        lock = load_manifest_json(root / lock_rel)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return [
            _diag(
                "BROKEN_REFERENCE",
                "governance_pack.lock",
                "workspace",
                [lock_rel],
                str(exc),
                "restore a valid pack lock",
            )
        ]
    pack_rel = lock.get("pack_path")
    expected = lock.get("content_sha256")
    if not isinstance(pack_rel, str) or not isinstance(expected, str):
        return [
            _diag(
                "BROKEN_REFERENCE",
                "governance_pack.lock",
                "workspace",
                [lock_rel],
                "lock lacks pack_path or content_sha256",
                "regenerate the lock with gov sync",
            )
        ]
    pack_root = root / pack_rel
    try:
        version = (pack_root / "VERSION").read_text(encoding="utf-8").strip()
        manifest = load_manifest_json(pack_root / "MANIFEST.json")
    except (OSError, ValueError, TypeError) as exc:
        return [
            _diag(
                "PACK_DRIFT",
                pack_rel,
                "shared_pack",
                [lock_rel, pack_rel],
                f"pack identity is incomplete: {exc}",
                "restore the pinned pack contents before syncing",
            )
        ]
    if lock.get("version") != version or manifest.get("version") != version:
        return [
            _diag(
                "PACK_DRIFT",
                pack_rel,
                "shared_pack",
                [lock_rel, f"{pack_rel}/VERSION", f"{pack_rel}/MANIFEST.json"],
                "pack version identities disagree",
                "install one coherent pack revision, then run gov sync",
            )
        ]
    actual, actual_files = pack_hash(pack_root)
    if lock.get("files") != actual_files:
        return [
            _diag(
                "PACK_DRIFT",
                pack_rel,
                "shared_pack",
                [lock_rel, pack_rel],
                "locked file inventory does not match vendored pack contents",
                "inspect the pack update, then run gov sync to accept it",
            )
        ]
    if actual != expected:
        return [
            _diag(
                "PACK_DRIFT",
                pack_rel,
                "shared_pack",
                [lock_rel, pack_rel],
                f"locked hash {expected} does not match content hash {actual}",
                "inspect the pack update, then run gov sync to accept it",
            )
        ]
    return []


def resolve_interpreter(
    root: Path,
    project: dict[str, Any],
    local: dict[str, Any] | None,
    environ: dict[str, str] | None = None,
) -> tuple[Path | None, str, list[Diagnostic]]:
    env = os.environ if environ is None else environ
    candidates: list[tuple[str, str]] = []
    override_name = project.get("environment", {}).get("interpreter_override")
    if isinstance(override_name, str) and env.get(override_name):
        candidates.append((f"explicit override {override_name}", env[override_name]))
    if local and isinstance(local.get("interpreter"), str):
        candidates.append(("approved local overlay", local["interpreter"]))
    preferred = project.get("environment", {}).get("preferred", ".venv/bin/python")
    if isinstance(preferred, str):
        candidates.append(("repository-local environment", preferred))
    selected: tuple[Path, str] | None = None
    for reason, raw in candidates:
        path = Path(raw).expanduser()
        if not path.is_absolute():
            path = root / path
        if path.is_file() and os.access(path, os.X_OK):
            selected = (path.absolute(), reason)
            break
    if selected is None:
        return (
            None,
            "none",
            [
                _diag(
                    "ENVIRONMENT_MISMATCH",
                    "python.interpreter",
                    "environment",
                    [str(c[1]) for c in candidates],
                    "no approved interpreter is executable",
                    "set the approved override or create the repository-local environment",
                )
            ],
        )
    return selected[0], selected[1], []


def doctor(  # noqa: C901 - environment probes remain one deterministic transaction
    root: Path,
    project: dict[str, Any],
    local: dict[str, Any] | None,
    environ: dict[str, str] | None = None,
    route: str | None = None,
) -> tuple[dict[str, Any], list[Diagnostic]]:
    env = os.environ if environ is None else environ
    interpreter, reason, issues = resolve_interpreter(root, project, local, environ)
    dependency_spec = project.get("environment", {}).get("dependency_authority")
    dependency_ref = (
        dependency_spec.get("authority_ref")
        if isinstance(dependency_spec, dict)
        else None
    )
    dependency_entry = next(
        (
            item
            for item in project.get("authorities", [])
            if isinstance(item, dict) and item.get("authority_id") == dependency_ref
        ),
        None,
    )
    result: dict[str, Any] = {
        "status": "ENVIRONMENT_INVALID" if issues else "ok",
        "interpreter": str(interpreter) if interpreter else None,
        "selection_reason": reason,
        "dependency_authority": dependency_entry.get("source")
        if dependency_entry
        else dependency_spec,
    }
    if interpreter is None:
        return result, issues
    environment = project.get("environment", {})
    package_import = environment.get("package_import")
    editable_source = environment.get("editable_source")
    critical = environment.get("critical_packages", [])
    if (
        not isinstance(package_import, str)
        or not package_import.isidentifier()
        or not isinstance(editable_source, str)
    ):
        issues.append(
            _diag(
                "BROKEN_REFERENCE",
                "environment.package_import",
                "project",
                ["config/governance/project.json"],
                "package import or editable source metadata is invalid",
                "declare a Python identifier and repo-relative source path",
            )
        )
        result["status"] = "ENVIRONMENT_INVALID"
        return result, issues
    module_names = [package_import] + [
        name
        for name in critical
        if isinstance(name, str) and name.isidentifier() and name != package_import
    ]
    probe = (
        "import importlib,json,sys,pathlib; mods=[importlib.import_module(n) for n in "
        + repr(module_names)
        + "]; root=importlib.import_module("
        + repr(package_import)
        + "); print(json.dumps({'version':list(sys.version_info[:3]),'package':str(pathlib.Path(root.__file__).resolve()),'critical_packages':"
        + repr(module_names)
        + "}))"
    )
    try:
        proc = subprocess.run(
            [str(interpreter), "-c", probe],
            cwd=root,
            text=True,
            capture_output=True,
            timeout=20,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        issues.append(
            _diag(
                "ENVIRONMENT_MISMATCH",
                "python.probe",
                "environment",
                [str(interpreter)],
                str(exc),
                "repair or replace the selected environment",
            )
        )
        result["status"] = "ENVIRONMENT_INVALID"
        return result, issues
    if proc.returncode != 0:
        issues.append(
            _diag(
                "ENVIRONMENT_MISMATCH",
                "project.import",
                "environment",
                [str(interpreter)],
                "project package or critical dependencies cannot be imported",
                "install the current checkout with its declared development dependencies",
            )
        )
    else:
        data = json.loads(proc.stdout)
        result.update(data)
        requires_source = environment.get("python_requires", {})
        authority_id = (
            requires_source.get("authority_ref")
            if isinstance(requires_source, dict)
            else None
        )
        authority = next(
            (
                item
                for item in project.get("authorities", [])
                if isinstance(item, dict) and item.get("authority_id") == authority_id
            ),
            None,
        )
        authority_source = authority.get("source") if authority else None
        source_text = (
            (root / authority_source).read_text(encoding="utf-8")
            if isinstance(authority_source, str) and (root / authority_source).is_file()
            else ""
        )
        version_match = re.search(
            r'^requires-python\s*=\s*">=(\d+)\.(\d+)"',
            source_text,
            re.MULTILINE,
        )
        if not version_match:
            issues.append(
                _diag(
                    "BROKEN_REFERENCE",
                    "environment.python_requires",
                    "project_metadata",
                    [str(authority_source or "<missing>")],
                    "supported Python reference cannot be resolved",
                    "declare an authority containing project.requires-python in >=major.minor form",
                )
            )
            minimum = (sys.version_info.major + 1, 0)
        else:
            minimum = tuple(int(item) for item in version_match.groups())
        if tuple(data["version"][:2]) < tuple(minimum):
            issues.append(
                _diag(
                    "ENVIRONMENT_MISMATCH",
                    "python.version",
                    "project",
                    [str(interpreter), "config/governance/project.json"],
                    f"resolved Python {data['version'][0]}.{data['version'][1]} is below supported minimum",
                    "recreate the environment with a supported Python",
                )
            )
        expected = (root / editable_source).resolve()
        actual = Path(data["package"]).parent
        if actual != expected:
            issues.append(
                _diag(
                    "ENVIRONMENT_MISMATCH",
                    "editable_install",
                    "project",
                    [str(actual), str(expected)],
                    "editable install targets another checkout",
                    "reinstall the selected environment editable from the current checkout",
                )
            )
    result["status"] = "ENVIRONMENT_INVALID" if issues else "ok"
    if route is not None:
        route_spec = project.get("routes", {}).get(route)
        if not isinstance(route_spec, dict):
            issues.append(
                _diag(
                    "BROKEN_REFERENCE",
                    f"route:{route}",
                    "project",
                    ["config/governance/project.json"],
                    "requested doctor route is unknown",
                    "select a declared route",
                )
            )
        else:
            route_tools = project.get("environment", {}).get("route_tools", {})
            observed: dict[str, str] = {}
            for tool_id in route_spec.get("environment_tools", []):
                spec = (
                    route_tools.get(tool_id, {})
                    if isinstance(route_tools, dict)
                    else {}
                )
                override = spec.get("override")
                candidates = spec.get("candidates", [])
                raw = env.get(override) if isinstance(override, str) else None
                executable = raw or next(
                    (
                        shutil.which(item)
                        for item in candidates
                        if isinstance(item, str) and shutil.which(item)
                    ),
                    None,
                )
                if not executable:
                    issues.append(
                        _diag(
                            "ENVIRONMENT_MISMATCH",
                            f"tool:{tool_id}",
                            "environment",
                            [str(override or tool_id)],
                            "route-required tool is unavailable",
                            "set the approved tool override or install the declared tool",
                        )
                    )
                    continue
                try:
                    version = subprocess.run(
                        [executable, *spec.get("version_args", ["--version"])],
                        cwd=root,
                        text=True,
                        capture_output=True,
                        timeout=20,
                        check=False,
                    )
                except (OSError, subprocess.TimeoutExpired) as exc:
                    issues.append(
                        _diag(
                            "ENVIRONMENT_MISMATCH",
                            f"tool:{tool_id}",
                            "environment",
                            [executable],
                            str(exc),
                            "repair the route tool installation",
                        )
                    )
                    continue
                if version.returncode != 0:
                    issues.append(
                        _diag(
                            "ENVIRONMENT_MISMATCH",
                            f"tool:{tool_id}",
                            "environment",
                            [executable],
                            "route tool version probe failed",
                            "repair the route tool installation",
                        )
                    )
                else:
                    observed[tool_id] = (
                        (version.stdout or version.stderr).strip().splitlines()[0]
                    )
            if observed:
                result["route_tools"] = observed
    result["status"] = "ENVIRONMENT_INVALID" if issues else "ok"
    return result, issues
