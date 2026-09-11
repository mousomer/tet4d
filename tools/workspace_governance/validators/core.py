from __future__ import annotations

import fnmatch
import hashlib
import json
import os
import re
import shutil
import subprocess
import tomllib
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

DIAGNOSTIC_CLASSES = {
    "DUPLICATE_AUTHORITY",
    "CONFLICTING_VALUE",
    "AMBIGUOUS_AUTHORITY",
    "BROKEN_REFERENCE",
    "PACK_DRIFT",
    "ENVIRONMENT_MISMATCH",
}
SCHEMA_FILES = {
    "workspace": "schemas/workspace.schema.json",
    "project": "schemas/project.schema.json",
    "local": "schemas/workspace-local.schema.json",
}
SUPPORTED_COMMANDS = {"check", "resolve", "explain", "doctor", "sync"}
REQUIRED_STABLE_AUTHORITIES = {"native-and-platform", "authority-transfer"}


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


def _diag(
    code: str,
    fact: str,
    owner: str,
    sources: list[str],
    reason: str,
    repair: str,
) -> Diagnostic:
    return Diagnostic(code, fact, owner, tuple(sources), reason, repair)


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


def _type_matches(value: object, expected: str) -> bool:
    return {
        "object": isinstance(value, dict),
        "array": isinstance(value, list),
        "string": isinstance(value, str),
        "integer": isinstance(value, int) and not isinstance(value, bool),
        "boolean": isinstance(value, bool),
    }.get(expected, True)


def _schema_issues(  # noqa: C901 - bounded recursive schema evaluator
    value: object,
    schema: dict[str, Any],
    *,
    path: str,
    source: str,
) -> list[Diagnostic]:
    issues: list[Diagnostic] = []

    def fail(reason: str) -> None:
        issues.append(
            _diag(
                "CONFLICTING_VALUE",
                path or "manifest",
                "schema",
                [source],
                reason,
                "change the manifest to satisfy its versioned schema",
            )
        )

    expected = schema.get("type")
    if isinstance(expected, str) and not _type_matches(value, expected):
        fail(f"expected {expected}, got {type(value).__name__}")
        return issues
    if "const" in schema and value != schema["const"]:
        fail(f"value must equal {schema['const']!r}")
    if "enum" in schema and value not in schema["enum"]:
        fail(f"value is not one of {schema['enum']!r}")
    if isinstance(value, str) and len(value) < schema.get("minLength", 0):
        fail("string is shorter than minLength")
    if (
        isinstance(value, int)
        and not isinstance(value, bool)
        and "minimum" in schema
        and value < schema["minimum"]
    ):
        fail(f"integer is below minimum {schema['minimum']}")
    if isinstance(value, list):
        if len(value) < schema.get("minItems", 0):
            fail("array has too few items")
        if "maxItems" in schema and len(value) > schema["maxItems"]:
            fail("array has too many items")
        if schema.get("uniqueItems") and len(
            {json.dumps(v, sort_keys=True) for v in value}
        ) != len(value):
            fail("array items must be unique")
        item_schema = schema.get("items")
        if isinstance(item_schema, dict):
            for index, item in enumerate(value):
                issues.extend(
                    _schema_issues(
                        item, item_schema, path=f"{path}[{index}]", source=source
                    )
                )
    if isinstance(value, dict):
        required = schema.get("required", [])
        for key in required:
            if key not in value:
                issues.append(
                    _diag(
                        "BROKEN_REFERENCE",
                        f"{path}.{key}".strip("."),
                        "schema",
                        [source],
                        "required field is missing",
                        "add the field required by the versioned schema",
                    )
                )
        properties = schema.get("properties", {})
        additional = schema.get("additionalProperties", True)
        for key, nested in value.items():
            nested_schema = (
                properties.get(key) if isinstance(properties, dict) else None
            )
            if nested_schema is None and additional is False:
                fail(f"undeclared field is not allowed: {key}")
            elif nested_schema is None and isinstance(additional, dict):
                nested_schema = additional
            if isinstance(nested_schema, dict):
                issues.extend(
                    _schema_issues(
                        nested,
                        nested_schema,
                        path=f"{path}.{key}".strip("."),
                        source=source,
                    )
                )
        if len(value) < schema.get("minProperties", 0):
            fail("object has too few properties")
        if "maxProperties" in schema and len(value) > schema["maxProperties"]:
            fail("reserved object must remain empty")
    return issues


def _schema_field_usage_issues(schema: dict[str, Any], source: str) -> list[Diagnostic]:
    issues: list[Diagnostic] = []
    allowed = {"consumed", "validation-only", "reserved-for-future-use"}
    registry = load_manifest_json(Path(source).parent.parent / "field-usage.json")

    def visit(node: object, path: str) -> None:
        if not isinstance(node, dict):
            return
        properties = node.get("properties")
        if isinstance(properties, dict):
            for key, child in properties.items():
                child_path = f"{path}.{key}".strip(".")
                usage = (
                    child.get("x-governance-use") if isinstance(child, dict) else None
                )
                behavior = registry.get(child.get("x-governance-behavior"), {})
                reserved_empty = usage != "reserved-for-future-use" or (
                    child.get("type") == "object"
                    and child.get("maxProperties") == 0
                    or child.get("type") == "array"
                    and child.get("maxItems") == 0
                )
                if (
                    usage not in allowed
                    or behavior.get("classification") != usage
                    or not behavior.get("handler")
                    or not behavior.get("test")
                    or not reserved_empty
                ):
                    issues.append(
                        _diag(
                            "BROKEN_REFERENCE",
                            child_path,
                            "schema",
                            [source],
                            "declared field lacks a valid use classification",
                            "classify it as consumed, validation-only, or reserved-for-future-use",
                        )
                    )
                visit(child, child_path)
        visit(node.get("items"), f"{path}[]")
        additional = node.get("additionalProperties")
        if isinstance(additional, dict):
            visit(additional, f"{path}.*")

    visit(schema, "")
    return issues


def _load_schemas(
    pack_root: Path,
) -> tuple[dict[str, dict[str, Any]], list[Diagnostic]]:
    schemas: dict[str, dict[str, Any]] = {}
    issues: list[Diagnostic] = []
    for layer, rel in SCHEMA_FILES.items():
        try:
            schema = load_manifest_json(pack_root / rel)
            usage_issues = _schema_field_usage_issues(schema, str(pack_root / rel))
        except (OSError, ValueError, TypeError) as exc:
            issues.append(
                _diag(
                    "BROKEN_REFERENCE",
                    f"schema:{layer}",
                    "shared_pack",
                    [rel],
                    str(exc),
                    "restore the versioned schema",
                )
            )
            continue
        schemas[layer] = schema
        issues.extend(usage_issues)
    return schemas, issues


def _json_pointer(document: object, pointer: str) -> object:
    if not pointer.startswith("/"):
        raise ValueError("JSON pointer must begin with /")
    value = document
    for token in pointer[1:].split("/"):
        if not isinstance(value, dict):
            raise KeyError(token)
        value = value[token.replace("~1", "/").replace("~0", "~")]
    return value


def _split_reference(root: Path, reference: str) -> tuple[Path, str]:
    raw_path, marker, pointer = reference.partition("#")
    path = root / raw_path
    return path, pointer if marker else ""


def _route_facade(project: dict[str, Any]) -> dict[str, Any]:
    authorities = {item["authority_id"]: item for item in project["authorities"]}
    facade: dict[str, Any] = {}
    for route_id, route in project["routes"].items():
        entry: dict[str, Any] = {}
        if route["dispatch_paths"]:
            entry["dispatch_paths"] = route["dispatch_paths"]
        entry["authority_keys"] = sorted(
            authorities[item]["legacy_key"] for item in route["authority_refs"]
        )
        entry["typical_verification_requirements"] = route[
            "typical_verification_requirements"
        ]
        facade[route_id] = entry
    return facade


def _valid_authority_source(
    root: Path, entry: dict[str, Any], by_id: dict[str, Any]
) -> bool:
    source, pointer = _split_reference(root, entry["source"])
    kind = entry["source_type"]
    valid = source.is_dir() if kind == "directory" else source.is_file()
    if kind == "json_pointer" and valid:
        try:
            _json_pointer(load_manifest_json(source), pointer)
            valid = bool(pointer)
        except (OSError, ValueError, KeyError, TypeError):
            valid = False
    elif pointer:
        valid = False
    if kind == "alias":
        target = by_id.get(entry.get("alias_of"))
        valid = bool(
            target
            and target["source_type"] != "alias"
            and target["source"] == entry["source"]
            and not entry["exclusive"]
            and not entry["canonical_governance"]
        )
    elif "alias_of" in entry or entry["authority_type"] == "alias":
        valid = False
    return valid


def _authority_graph_issues(root: Path, project: dict[str, Any]) -> list[Diagnostic]:
    issues: list[Diagnostic] = []
    authorities = project["authorities"]
    by_id = {item["authority_id"]: item for item in authorities}
    sources: dict[str, list[str]] = {}
    for entry in authorities:
        valid = _valid_authority_source(root, entry, by_id)
        if not valid:
            issues.append(
                _diag(
                    "BROKEN_REFERENCE",
                    "authority:" + entry["authority_id"],
                    "project",
                    [entry["source"]],
                    "invalid typed authority source or alias",
                    "correct the source type; aliases must be nonexclusive references",
                )
            )
        if entry["exclusive"]:
            path, pointer = _split_reference(root, entry["source"])
            identity = path.resolve().as_posix() + ("#" + pointer if pointer else "")
            sources.setdefault(identity, []).append(entry["authority_id"])
    for source, identities in sources.items():
        if len(identities) > 1:
            issues.append(
                _diag(
                    "AMBIGUOUS_AUTHORITY",
                    "authority.source",
                    "project",
                    [source],
                    "exclusive identities share a source: " + ", ".join(identities),
                    "use a nonexclusive alias or distinct typed source",
                )
            )
    return issues + _canonical_owner_issues(root, project, by_id)


def _canonical_owner_issues(
    root: Path, project: dict[str, Any], by_id: dict[str, Any]
) -> list[Diagnostic]:
    issues: list[Diagnostic] = []
    authorities = project["authorities"]
    try:
        ref = project["canonical_owner_set"]
        owner_source = by_id[ref["authority_ref"]]["source"]
        owner_set = _json_pointer(
            load_manifest_json(root / owner_source), ref["json_pointer"]
        )
        if (
            not isinstance(owner_set, dict)
            or not owner_set
            or not all(isinstance(v, str) for v in owner_set.values())
        ):
            raise ValueError(
                "canonical owner set must be a nonempty domain-to-source mapping"
            )
        canonical = [a for a in authorities if a["canonical_governance"]]
        for domain, source in owner_set.items():
            matches = [
                a
                for a in canonical
                if a["source"] == source
                and a["authority_type"] == "human"
                and a["exclusive"]
                and a["source_type"] == "file"
            ]
            if len(matches) != 1:
                issues.append(
                    _diag(
                        "BROKEN_REFERENCE",
                        "canonical_owner:" + domain,
                        "project",
                        [source],
                        "canonical owner requires exactly one applicable human authority",
                        "restore the canonical authority identity and flag",
                    )
                )
        if any(a["source"] not in owner_set.values() for a in canonical):
            raise ValueError("canonical authority is outside the defined owner set")
    except (OSError, ValueError, KeyError, TypeError) as exc:
        issues.append(
            _diag(
                "BROKEN_REFERENCE",
                "canonical_owner_set",
                "project",
                ["config/governance/project.json"],
                str(exc),
                "restore the existing owner-set reference",
            )
        )
    return issues


def _semantic_manifest_issues(  # noqa: C901 - cross-field integrity transaction
    root: Path, workspace: dict[str, Any], project: dict[str, Any]
) -> list[Diagnostic]:
    issues: list[Diagnostic] = []
    authorities = project["authorities"]
    by_id: dict[str, list[dict[str, Any]]] = {}
    for entry in authorities:
        by_id.setdefault(entry["authority_id"], []).append(entry)
    for authority_id, entries in sorted(by_id.items()):
        if len(entries) > 1:
            issues.append(
                _diag(
                    "DUPLICATE_AUTHORITY",
                    authority_id,
                    "project",
                    [item["source"] for item in entries],
                    "stable authority ID is declared more than once",
                    "deduplicate declarations",
                )
            )
        for entry in entries:
            if not _split_reference(root, entry["source"])[0].exists():
                issues.append(
                    _diag(
                        "BROKEN_REFERENCE",
                        f"authority:{authority_id}",
                        "project",
                        [entry["source"]],
                        "authority source does not exist",
                        "restore or correct the authority source",
                    )
                )
    for required in sorted(REQUIRED_STABLE_AUTHORITIES - set(by_id)):
        issues.append(
            _diag(
                "BROKEN_REFERENCE",
                f"authority:{required}",
                "project",
                ["config/governance/project.json"],
                "required stable authority ID is missing",
                "restore the stable authority ID",
            )
        )
    scopes: dict[str, list[dict[str, Any]]] = {}
    for entry in authorities:
        if entry["exclusive"]:
            scopes.setdefault(entry["scope"], []).append(entry)
        alias = entry.get("alias_of")
        if alias is not None and alias not in by_id:
            issues.append(
                _diag(
                    "BROKEN_REFERENCE",
                    f"authority:{entry['authority_id']}",
                    "project",
                    ["config/governance/project.json"],
                    f"alias target is missing: {alias}",
                    "restore or correct the alias",
                )
            )
    for scope, entries in scopes.items():
        if len(entries) > 1:
            issues.append(
                _diag(
                    "AMBIGUOUS_AUTHORITY",
                    scope,
                    "project",
                    [item["source"] for item in entries],
                    "exclusive scope has multiple owners",
                    "resolve the authority conflict explicitly",
                )
            )
    reached: set[str] = set()
    for route_id, route in project["routes"].items():
        for authority_id in route["authority_refs"]:
            if authority_id not in by_id:
                issues.append(
                    _diag(
                        "BROKEN_REFERENCE",
                        f"route:{route_id}",
                        "project",
                        ["config/governance/project.json"],
                        f"route references missing authority {authority_id}",
                        "correct the typed authority reference",
                    )
                )
            reached.add(authority_id)
            if authority_id in by_id and "legacy_key" not in by_id[authority_id][0]:
                issues.append(
                    _diag(
                        "BROKEN_REFERENCE",
                        f"route:{route_id}",
                        "project",
                        ["config/governance/project.json"],
                        f"routed authority lacks compatibility identity: {authority_id}",
                        "add its legacy_key before exposing it through the route facade",
                    )
                )
        for path in route["dispatch_paths"]:
            if not (root / path).exists():
                issues.append(
                    _diag(
                        "BROKEN_REFERENCE",
                        f"route:{route_id}",
                        "project",
                        [path],
                        "dispatch path does not exist",
                        "restore or correct the dispatch path",
                    )
                )
        for tool_id in route.get("environment_tools", []):
            if tool_id not in project["environment"]["route_tools"]:
                issues.append(
                    _diag(
                        "BROKEN_REFERENCE",
                        f"route:{route_id}",
                        "project",
                        ["config/governance/project.json"],
                        f"route references missing environment tool {tool_id}",
                        "declare the route tool or correct the reference",
                    )
                )
    aliases = {
        item["authority_id"]: item["alias_of"]
        for item in authorities
        if "alias_of" in item
    }
    reached.update(alias for alias, target in aliases.items() if target in reached)
    for entry in authorities:
        if (
            entry["authority_type"] not in {"project_metadata"}
            and entry["authority_id"] not in reached
        ):
            issues.append(
                _diag(
                    "BROKEN_REFERENCE",
                    f"authority:{entry['authority_id']}",
                    "project",
                    [entry["source"]],
                    "authority is unreachable from every project route",
                    "add it to an applicable route or declare a reachable alias",
                )
            )
    for profile_id, profile in project["execution"]["profiles"].items():
        for route in profile["routes"]:
            if route not in project["routes"]:
                issues.append(
                    _diag(
                        "BROKEN_REFERENCE",
                        f"profile:{profile_id}",
                        "project",
                        ["config/governance/project.json"],
                        f"unknown route {route}",
                        "correct the route reference",
                    )
                )
    for scenario in project["execution"]["representative_scenarios"]:
        for route in scenario["routes"]:
            if route not in project["routes"]:
                issues.append(
                    _diag(
                        "BROKEN_REFERENCE",
                        f"scenario:{scenario['id']}",
                        "project",
                        ["config/governance/project.json"],
                        f"unknown route {route}",
                        "correct the route reference",
                    )
                )
    selectable = {
        route
        for profile in project["execution"]["profiles"].values()
        for route in profile["routes"]
    } | {
        route
        for scenario in project["execution"]["representative_scenarios"]
        for route in scenario["routes"]
    }
    for route_id in sorted(set(project["routes"]) - selectable):
        issues.append(
            _diag(
                "BROKEN_REFERENCE",
                f"route:{route_id}",
                "project",
                ["config/governance/project.json"],
                "route is unreachable from every execution profile and scenario",
                "add the route to a profile or declare a representative scenario",
            )
        )
    if project["execution"]["default_mode"] not in project["execution"]["profiles"]:
        issues.append(
            _diag(
                "BROKEN_REFERENCE",
                "execution.default_mode",
                "project",
                ["config/governance/project.json"],
                "default mode has no profile",
                "declare the profile or correct the default",
            )
        )
    for fact in ("canonical", "full"):
        authority_id = project["verification"][fact]["authority_ref"]
        if authority_id not in by_id:
            issues.append(
                _diag(
                    "BROKEN_REFERENCE",
                    f"verification.{fact}",
                    "project",
                    ["config/governance/project.json"],
                    f"verification fact references missing authority {authority_id}",
                    "correct the authority reference",
                )
            )
    for fact in ("python_requires", "dependency_authority"):
        authority_id = project["environment"][fact]["authority_ref"]
        if authority_id not in by_id:
            issues.append(
                _diag(
                    "BROKEN_REFERENCE",
                    f"environment.{fact}",
                    "project",
                    ["config/governance/project.json"],
                    f"environment fact references missing authority {authority_id}",
                    "correct the authority reference",
                )
            )
    dependency = project["environment"]["dependency_authority"]
    target = by_id.get(dependency["authority_ref"], [])
    if target and dependency["source"] != target[0]["source"]:
        issues.append(
            _diag(
                "CONFLICTING_VALUE",
                "environment.dependency_authority",
                "project",
                [dependency["source"], target[0]["source"]],
                "dependency source disagrees with authority",
                "use the referenced dependency authority source",
            )
        )
    default_id = workspace["defaults"]["project"]
    members = [item for item in workspace["projects"] if item["id"] == default_id]
    if len(members) != 1:
        issues.append(
            _diag(
                "AMBIGUOUS_AUTHORITY",
                "workspace.default_project",
                "workspace",
                [".governance/workspace.json"],
                "default project must resolve to exactly one member",
                "declare one unique default project",
            )
        )
    return issues


def _normalized_facade(value: object) -> dict[str, Any] | None:
    if not isinstance(value, dict):
        return None
    result = {}
    for key, route in value.items():
        if not isinstance(route, dict):
            return None
        keys = route.get("authority_keys")
        if not isinstance(keys, list) or not all(
            isinstance(item, str) for item in keys
        ):
            return None
        result[key] = {**route, "authority_keys": sorted(keys)}
    return result


def _generated_surface_issues(root: Path, project: dict[str, Any]) -> list[Diagnostic]:
    issues: list[Diagnostic] = []
    for surface in project["generated_surfaces"]:
        source_path, source_pointer = _split_reference(root, surface["source"])
        target_path, target_pointer = _split_reference(root, surface["target"])
        if not source_path.is_file() or not target_path.is_file():
            issues.append(
                _diag(
                    "BROKEN_REFERENCE",
                    surface["surface_id"],
                    "project",
                    [surface["source"], surface["target"]],
                    "generated relationship references a missing file",
                    "restore the declared source and target",
                )
            )
            continue
        try:
            source_value = _json_pointer(
                load_manifest_json(source_path), source_pointer
            )
            target_value = _json_pointer(
                load_manifest_json(target_path), target_pointer
            )
        except (ValueError, KeyError, TypeError) as exc:
            issues.append(
                _diag(
                    "BROKEN_REFERENCE",
                    surface["surface_id"],
                    "project",
                    [surface["source"], surface["target"]],
                    f"generated relationship pointer failed: {exc}",
                    "correct the source or target pointer",
                )
            )
            continue
        if surface["transform"] == "authority-legacy-key-route-v1":
            expected = _route_facade(project)
            normalized = _normalized_facade(target_value)
            if source_value != project["routes"] or normalized != expected:
                issues.append(
                    _diag(
                        "CONFLICTING_VALUE",
                        surface["surface_id"],
                        "project",
                        [surface["source"], surface["target"]],
                        "legacy route compatibility facade diverges from canonical project routes",
                        "regenerate or update the compatibility facade from project routes",
                    )
                )
    return issues


def validate_manifests(
    root: Path,
    workspace: dict[str, Any],
    project: dict[str, Any],
    local: dict[str, Any] | None,
    *,
    pack_root: Path,
) -> list[Diagnostic]:
    schemas, issues = _load_schemas(pack_root)
    for layer, value, source in (
        ("workspace", workspace, ".governance/workspace.json"),
        ("project", project, "config/governance/project.json"),
        ("local", local, ".governance/workspace.local.json"),
    ):
        if value is not None and layer in schemas:
            issues.extend(_schema_issues(value, schemas[layer], path="", source=source))
    if issues:
        return issues
    issues.extend(_semantic_manifest_issues(root, workspace, project))
    issues.extend(_authority_graph_issues(root, project))
    if not issues:
        issues.extend(_generated_surface_issues(root, project))
    for rel in (
        project["sanitation"]["secret_scanner"],
        project["sanitation"]["repository_check"],
    ):
        if not (root / rel).is_file():
            issues.append(
                _diag(
                    "BROKEN_REFERENCE",
                    "sanitation",
                    "project",
                    [rel],
                    "declared sanitation entrypoint does not exist",
                    "restore or correct the entrypoint",
                )
            )
    machine_path = re.compile(r'(?:^|[\s"\'])(?:/Users/|/home/|[A-Za-z]:[\\/])')
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
                    "tracked manifest contains a machine-local absolute path",
                    "move the path to the ignored local overlay",
                )
            )
    return issues


def _pack_files(pack_root: Path, exclusions: list[str]) -> list[str]:
    files: list[str] = []
    for path in pack_root.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(pack_root).as_posix()
        if any(
            fnmatch.fnmatch(rel, pattern) or fnmatch.fnmatch(f"/{rel}", pattern)
            for pattern in exclusions
        ):
            continue
        files.append(rel)
    return sorted(files)


def content_hash(
    root: Path, files: list[str], algorithm: str = "sha256-path-and-content-v1"
) -> str:
    if algorithm != "sha256-path-and-content-v1":
        raise ValueError(f"unsupported pack hash algorithm: {algorithm}")
    digest = hashlib.sha256()
    for rel in sorted(files):
        digest.update(rel.encode() + b"\0")
        digest.update((root / rel).read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def pack_hash(pack_root: Path) -> tuple[str, list[str]]:
    manifest = load_manifest_json(pack_root / "MANIFEST.json")
    files = _pack_files(pack_root, manifest["pack_hash_excludes"])
    return content_hash(pack_root, files, manifest["lock_algorithm"]), files


def validate_pack(root: Path, workspace: dict[str, Any]) -> list[Diagnostic]:
    lock_rel = workspace["governance_pack"]["lock"]
    try:
        lock = load_manifest_json(root / lock_rel)
        pack_root = root / lock["pack_path"]
        manifest = load_manifest_json(pack_root / "MANIFEST.json")
        version = (
            (pack_root / manifest["version_file"]).read_text(encoding="utf-8").strip()
        )
        actual, files = pack_hash(pack_root)
    except (OSError, ValueError, TypeError, KeyError) as exc:
        return [
            _diag(
                "PACK_DRIFT",
                "governance_pack",
                "shared_pack",
                [lock_rel],
                str(exc),
                "restore a coherent pack and lock",
            )
        ]
    usage = manifest.get("field_usage")
    allowed_usage = {"consumed", "validation-only", "reserved-for-future-use"}
    if (
        not isinstance(usage, dict)
        or set(usage) != set(manifest)
        or set(usage.values()) - allowed_usage
    ):
        return [
            _diag(
                "PACK_DRIFT",
                "MANIFEST.field_usage",
                "shared_pack",
                [f"{lock['pack_path']}/MANIFEST.json"],
                "pack manifest fields are not completely classified",
                "classify every manifest field",
            )
        ]
    identity = {
        "pack_name": manifest["name"],
        "version": manifest["version"],
        "revision": manifest["revision"],
        "content_sha256": actual,
        "files": files,
        "lock_algorithm": manifest["lock_algorithm"],
    }
    for key, expected in identity.items():
        if lock.get(key) != expected:
            return [
                _diag(
                    "PACK_DRIFT",
                    f"governance_pack.{key}",
                    "shared_pack",
                    [lock_rel, f"{lock['pack_path']}/MANIFEST.json"],
                    "pack lock identity does not match the pack manifest/content",
                    "run gov sync after reviewing the pack update",
                )
            ]
    if (
        version != manifest["version"]
        or workspace["governance_pack"]["required_schema"] != manifest["schema_version"]
    ):
        return [
            _diag(
                "PACK_DRIFT",
                "governance_pack.version",
                "shared_pack",
                [lock_rel],
                "pack version or required schema disagrees",
                "install a compatible pack or update the workspace contract",
            )
        ]
    if (
        set(manifest["commands"]) != SUPPORTED_COMMANDS
        or set(manifest["diagnostics"]) != DIAGNOSTIC_CLASSES
    ):
        return [
            _diag(
                "PACK_DRIFT",
                "MANIFEST.capabilities",
                "shared_pack",
                [f"{lock['pack_path']}/MANIFEST.json"],
                "declared commands or diagnostics do not match implementation",
                "align the manifest with implemented capabilities",
            )
        ]
    return []


def _python_specifier(root: Path, project: dict[str, Any]) -> tuple[str, str]:
    environment = project["environment"]
    authority_id = environment["python_requires"]["authority_ref"]
    authority = next(
        item for item in project["authorities"] if item["authority_id"] == authority_id
    )
    payload = tomllib.loads((root / authority["source"]).read_text(encoding="utf-8"))
    value: object = payload
    for token in environment["python_requires"]["source_field"].split("."):
        value = value[token]
    if not isinstance(value, str):
        raise TypeError("Python requirement must be a string")
    return value, authority["source"]


def resolve_interpreter(
    root: Path,
    project: dict[str, Any],
    local: dict[str, Any] | None,
    environ: dict[str, str] | None = None,
) -> tuple[Path | None, str, list[Diagnostic]]:
    env = os.environ if environ is None else environ
    override = project["environment"]["interpreter_override"]
    if env.get(override):
        raw, reason = env[override], f"explicit override {override}"
    elif local and local.get("interpreter"):
        raw, reason = local["interpreter"], "approved local overlay"
    else:
        raw, reason = (
            project["environment"]["preferred"],
            "repository-local environment",
        )
    path = Path(raw).expanduser()
    if not path.is_absolute():
        path = root / path
    if not path.is_file() or not os.access(path, os.X_OK):
        return (
            None,
            reason,
            [
                _diag(
                    "ENVIRONMENT_MISMATCH",
                    "python.interpreter",
                    "environment",
                    [str(path)],
                    "highest-priority approved interpreter is not executable",
                    "repair or remove that override; no fallback is permitted",
                )
            ],
        )
    try:
        specifier_text, source = _python_specifier(root, project)
        probe = subprocess.run(
            [
                str(path),
                "-c",
                "import platform; from packaging.specifiers import SpecifierSet; "
                "from packaging.version import Version; v=platform.python_version(); "
                "print(v); raise SystemExit(0 if Version(v) in SpecifierSet("
                + repr(specifier_text)
                + ") else 1)",
            ],
            cwd=root,
            text=True,
            capture_output=True,
            timeout=20,
            check=False,
        )
        version = probe.stdout.strip()
        if probe.returncode != 0:
            return (
                None,
                reason,
                [
                    _diag(
                        "ENVIRONMENT_MISMATCH",
                        "python.version",
                        "project_metadata",
                        [str(path), source],
                        f"interpreter version {version or '<unknown>'} cannot certify {specifier_text}; packaging must be installed in the selected environment",
                        "select an approved interpreter satisfying project metadata",
                    )
                ],
            )
    except (
        OSError,
        ValueError,
        TypeError,
        KeyError,
        StopIteration,
        ImportError,
        subprocess.TimeoutExpired,
    ) as exc:
        return (
            None,
            reason,
            [
                _diag(
                    "ENVIRONMENT_MISMATCH",
                    "python.version",
                    "environment",
                    [str(path)],
                    str(exc),
                    "repair project metadata or the selected interpreter",
                )
            ],
        )
    return path.absolute(), reason, []


def doctor(  # noqa: C901 - environment probes remain one deterministic transaction
    root: Path,
    project: dict[str, Any],
    local: dict[str, Any] | None,
    environ: dict[str, str] | None = None,
    route: str | None = None,
) -> tuple[dict[str, Any], list[Diagnostic]]:
    env = os.environ if environ is None else environ
    interpreter, reason, issues = resolve_interpreter(root, project, local, env)
    try:
        requirement, requirement_source = _python_specifier(root, project)
    except (
        OSError,
        ValueError,
        TypeError,
        KeyError,
        StopIteration,
        ImportError,
    ) as exc:
        requirement, requirement_source = None, None
        issues.append(
            _diag(
                "ENVIRONMENT_MISMATCH",
                "python.metadata",
                "project_metadata",
                [],
                str(exc),
                "repair the Python requirement authority",
            )
        )
    result: dict[str, Any] = {
        "status": "ENVIRONMENT_INVALID" if issues else "ok",
        "interpreter": str(interpreter) if interpreter else None,
        "selection_reason": reason,
        "python_requires": requirement,
        "python_requires_source": requirement_source,
        "dependency_authority": project["environment"]["dependency_authority"][
            "source"
        ],
    }
    if interpreter is None:
        return result, issues
    package_import = project["environment"]["package_import"]
    modules = list(
        dict.fromkeys([package_import, *project["environment"]["critical_packages"]])
    )
    probe_code = (
        "import importlib,json,pathlib,platform; mods=[importlib.import_module(n) for n in "
        + repr(modules)
        + "]; root=importlib.import_module("
        + repr(package_import)
        + "); print(json.dumps({'version':platform.python_version(),'package':str(pathlib.Path(root.__file__).resolve()),'critical_packages':"
        + repr(modules)
        + "}))"
    )
    try:
        probe = subprocess.run(
            [str(interpreter), "-c", probe_code],
            cwd=root,
            text=True,
            capture_output=True,
            timeout=20,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        probe = None
        issues.append(
            _diag(
                "ENVIRONMENT_MISMATCH",
                "python.probe",
                "environment",
                [str(interpreter)],
                str(exc),
                "repair the selected environment",
            )
        )
    if probe is not None and probe.returncode != 0:
        issues.append(
            _diag(
                "ENVIRONMENT_MISMATCH",
                "project.import",
                "environment",
                [str(interpreter)],
                "project or critical package import failed",
                "install current-checkout development dependencies",
            )
        )
    elif probe is not None:
        try:
            data = json.loads(probe.stdout)
            actual = Path(data["package"]).parent
        except (ValueError, KeyError, TypeError) as exc:
            issues.append(
                _diag(
                    "ENVIRONMENT_MISMATCH",
                    "python.probe",
                    "environment",
                    [str(interpreter)],
                    str(exc),
                    "repair the environment probe output",
                )
            )
            result["status"] = "ENVIRONMENT_INVALID"
            return result, issues
        result.update(data)
        expected = (root / project["environment"]["editable_source"]).resolve()
        if actual != expected:
            issues.append(
                _diag(
                    "ENVIRONMENT_MISMATCH",
                    "editable_install",
                    "project",
                    [str(actual), str(expected)],
                    "editable install targets another checkout",
                    "reinstall editable from the current checkout",
                )
            )
    if route is not None:
        route_spec = project["routes"].get(route)
        if route_spec is None:
            issues.append(
                _diag(
                    "BROKEN_REFERENCE",
                    f"route:{route}",
                    "project",
                    ["config/governance/project.json"],
                    "requested route is unknown",
                    "select a declared route",
                )
            )
        else:
            observed: dict[str, str] = {}
            local_tools = local.get("tool_paths", {}) if local else {}
            for tool_id in route_spec.get("environment_tools", []):
                spec = project["environment"]["route_tools"][tool_id]
                executable = (
                    local_tools.get(tool_id)
                    or env.get(spec["override"])
                    or next(
                        (
                            shutil.which(item)
                            for item in spec["candidates"]
                            if shutil.which(item)
                        ),
                        None,
                    )
                )
                if not executable:
                    issues.append(
                        _diag(
                            "ENVIRONMENT_MISMATCH",
                            f"tool:{tool_id}",
                            "environment",
                            [spec["override"]],
                            "route-required tool is unavailable",
                            "configure local tool_paths, the approved override, or install it",
                        )
                    )
                    continue
                version = subprocess.run(
                    [executable, *spec["version_args"]],
                    cwd=root,
                    text=True,
                    capture_output=True,
                    timeout=20,
                    check=False,
                )
                if version.returncode:
                    issues.append(
                        _diag(
                            "ENVIRONMENT_MISMATCH",
                            f"tool:{tool_id}",
                            "environment",
                            [executable],
                            "route tool version probe failed",
                            "repair the tool",
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
