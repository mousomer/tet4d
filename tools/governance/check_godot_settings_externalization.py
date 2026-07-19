from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


POLICY_PACK_PATH = Path("config/project/policy_pack.json")
SETTING_TOKEN_RE = re.compile(r"""["']([a-z][a-z0-9_]*\.[a-z][a-z0-9_]*)["']""")


def _load_json(path: Path, issues: list[str], label: str) -> dict[str, Any]:
    try:
        parsed = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        issues.append(f"{label} is not readable JSON: {exc}")
        return {}
    if not isinstance(parsed, dict):
        issues.append(f"{label} must be a JSON object")
        return {}
    return parsed


def _source_constant(source: str, name: str) -> str | None:
    match = re.search(
        rf"""^\s*const\s+{re.escape(name)}\s*:=\s*["']([^"']+)["']""",
        source,
        re.MULTILINE,
    )
    return match.group(1) if match else None


def _source_integer_constant(source: str, name: str) -> int | None:
    match = re.search(
        rf"^\s*const\s+{re.escape(name)}\s*:=\s*(\d+)\s*$",
        source,
        re.MULTILINE,
    )
    return int(match.group(1)) if match else None


def _expected_resource_path(registry_path: str) -> str:
    marker = "godot/Tet4D.Godot/"
    if not registry_path.startswith(marker):
        return ""
    return f"res://{registry_path.removeprefix(marker)}"


def _validate_persistence(
    spec: dict[str, Any],
    setting_id: str,
    persistent_policy: Any,
    non_persistent_policies: set[Any],
    issues: list[str],
) -> None:
    persistence = spec.get("persistence")
    persist = spec.get("persist")
    if not isinstance(persist, bool):
        issues.append(f"setting {setting_id} persist must be boolean")
    elif persistence == persistent_policy and not persist:
        issues.append(
            f"setting {setting_id} uses {persistent_policy} but persist is false"
        )
    elif persistence in non_persistent_policies and persist:
        issues.append(f"setting {setting_id} uses {persistence} but persist is true")
    elif (
        persistence != persistent_policy and persistence not in non_persistent_policies
    ):
        issues.append(
            f"setting {setting_id} has unsupported persistence {persistence!r}"
        )


def _validate_enum_default(
    spec: dict[str, Any], setting_id: str, issues: list[str]
) -> None:
    if spec.get("value_type") != "enum":
        return
    options = spec.get("options")
    option_values = (
        [option.get("value") for option in options if isinstance(option, dict)]
        if isinstance(options, list)
        else []
    )
    if spec.get("default") not in option_values:
        issues.append(f"setting {setting_id} default is absent from enum options")


def _validate_registry(
    registry: dict[str, Any], contract: dict[str, Any], issues: list[str]
) -> dict[str, Any]:
    required_fields = contract.get("required_setting_fields", [])
    persistent_policy = contract.get("persistent_policy")
    non_persistent_policies = set(contract.get("non_persistent_policies", []))
    raw_settings = registry.get("settings")
    if not isinstance(raw_settings, list):
        issues.append("settings registry must contain a settings array")
        return {}

    settings_by_id: dict[str, Any] = {}
    for index, raw_spec in enumerate(raw_settings):
        if not isinstance(raw_spec, dict):
            issues.append(f"registry setting at index {index} must be an object")
            continue
        missing = [field for field in required_fields if field not in raw_spec]
        setting_id = raw_spec.get("id")
        label = setting_id if isinstance(setting_id, str) else f"index {index}"
        if missing:
            issues.append(f"setting {label} is missing required fields: {missing}")
        if not isinstance(setting_id, str) or not setting_id:
            issues.append(f"registry setting at index {index} has no valid id")
            continue
        if setting_id in settings_by_id:
            issues.append(f"duplicate setting id: {setting_id}")
            continue
        settings_by_id[setting_id] = raw_spec
        _validate_persistence(
            raw_spec,
            setting_id,
            persistent_policy,
            non_persistent_policies,
            issues,
        )
        _validate_enum_default(raw_spec, setting_id, issues)

    return settings_by_id


def _validate_paths_and_store(
    root: Path,
    registry: dict[str, Any],
    contract: dict[str, Any],
    issues: list[str],
) -> None:
    registry_loader_path = root / str(contract.get("registry_loader_path", ""))
    store_path = root / str(contract.get("store_path", ""))
    try:
        registry_loader = registry_loader_path.read_text(encoding="utf-8")
    except OSError as exc:
        issues.append(f"settings registry loader is unreadable: {exc}")
        registry_loader = ""
    try:
        store = store_path.read_text(encoding="utf-8")
    except OSError as exc:
        issues.append(f"settings store is unreadable: {exc}")
        store = ""

    expected_registry_path = _expected_resource_path(
        str(contract.get("registry_path", ""))
    )
    actual_registry_path = _source_constant(registry_loader, "REGISTRY_PATH")
    if not expected_registry_path or actual_registry_path != expected_registry_path:
        issues.append(
            "settings registry loader path drift: "
            f"expected {expected_registry_path!r}, got {actual_registry_path!r}"
        )

    expected_user_path = contract.get("persistent_user_path")
    actual_user_path = _source_constant(store, "DEFAULT_PATH")
    if (
        not isinstance(expected_user_path, str)
        or not expected_user_path.startswith("user://")
        or not expected_user_path.endswith(".json")
    ):
        issues.append("policy persistent user path must be a user:// JSON file")
    elif actual_user_path != expected_user_path:
        issues.append(
            "settings user-data path drift: "
            f"expected {expected_user_path!r}, got {actual_user_path!r}"
        )

    registry_schema = registry.get("schema_version")
    store_schema = _source_integer_constant(store, "SCHEMA_VERSION")
    if not isinstance(registry_schema, int) or registry_schema != store_schema:
        issues.append(
            "settings registry/store schema drift: "
            f"registry={registry_schema!r}, store={store_schema!r}"
        )

    required_store_tokens = (
        "_registry.persistent_default_values()",
        '"settings": persistent_values()',
        "spec.is_persistent()",
    )
    for token in required_store_tokens:
        if token not in store:
            issues.append(
                f"settings store no longer derives persistence from registry: {token}"
            )


def _validate_runtime_sources(
    root: Path,
    settings_by_id: dict[str, Any],
    contract: dict[str, Any],
    issues: list[str],
) -> None:
    source_root = root / str(contract.get("runtime_source_root", ""))
    if not source_root.is_dir():
        issues.append(f"runtime settings source root is missing: {source_root}")
        return

    category_ids = {setting_id.split(".", 1)[0] for setting_id in settings_by_id}
    forbid_defaults = bool(contract.get("forbid_runtime_default_duplicates", False))
    for path in sorted(source_root.rglob("*.gd")):
        source = path.read_text(encoding="utf-8")
        relative_path = path.relative_to(root)
        for match in SETTING_TOKEN_RE.finditer(source):
            setting_id = match.group(1)
            if (
                setting_id.split(".", 1)[0] in category_ids
                and setting_id not in settings_by_id
            ):
                issues.append(
                    f"{relative_path} references unknown setting id {setting_id}"
                )

        if not forbid_defaults:
            continue
        for setting_id, spec in settings_by_id.items():
            quoted_id = rf"""["']{re.escape(setting_id)}["']"""
            fallback_call = re.compile(
                rf"(?<![A-Za-z0-9_])(?:value|get|setting_value|get_setting)\s*\(\s*"
                rf"{quoted_id}\s*,"
            )
            if fallback_call.search(source):
                issues.append(
                    f"{relative_path} supplies a runtime fallback for {setting_id}"
                )

            default_literal = re.escape(
                json.dumps(spec.get("default"), separators=(",", ":"))
            )
            duplicate_mapping = re.compile(
                rf"{quoted_id}\s*:\s*{default_literal}(?:\s*[,}}]|\s*$)",
                re.MULTILINE,
            )
            if duplicate_mapping.search(source):
                issues.append(
                    f"{relative_path} duplicates the registry default for {setting_id}"
                )


def validate_repository(root: Path) -> list[str]:
    issues: list[str] = []
    policy_pack = _load_json(root / POLICY_PACK_PATH, issues, "policy pack")
    governance = policy_pack.get("governance")
    if not isinstance(governance, dict):
        issues.append("policy pack governance section is missing")
        return issues
    contract = governance.get("godot_settings_externalization_contract")
    if not isinstance(contract, dict):
        issues.append("Godot settings externalization contract is missing")
        return issues

    registry_path = root / str(contract.get("registry_path", ""))
    registry = _load_json(registry_path, issues, "Godot settings registry")
    settings_by_id = _validate_registry(registry, contract, issues)
    _validate_paths_and_store(root, registry, contract, issues)
    _validate_runtime_sources(root, settings_by_id, contract, issues)
    return issues


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    issues = validate_repository(root)
    if issues:
        print("Godot settings externalization check failed:")
        for issue in issues:
            print(f"- {issue}")
        return 1
    print("Godot settings externalization: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
