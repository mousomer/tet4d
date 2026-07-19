from __future__ import annotations

import json
import shutil
from pathlib import Path

from tools.governance.check_godot_settings_externalization import (
    POLICY_PACK_PATH,
    validate_repository,
)


REPO_ROOT = Path(__file__).resolve().parents[3]


def _contract_root(tmp_path: Path) -> Path:
    policy = json.loads((REPO_ROOT / POLICY_PACK_PATH).read_text(encoding="utf-8"))
    contract = policy["governance"]["godot_settings_externalization_contract"]
    copied_paths = (
        POLICY_PACK_PATH,
        Path(contract["registry_path"]),
        Path(contract["registry_loader_path"]),
        Path(contract["store_path"]),
    )
    for relative_path in copied_paths:
        destination = tmp_path / relative_path
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(REPO_ROOT / relative_path, destination)
    return tmp_path


def _registry(root: Path) -> tuple[Path, dict]:
    policy = json.loads((root / POLICY_PACK_PATH).read_text(encoding="utf-8"))
    registry_path = (
        root
        / policy["governance"]["godot_settings_externalization_contract"][
            "registry_path"
        ]
    )
    return registry_path, json.loads(registry_path.read_text(encoding="utf-8"))


def _write_registry(path: Path, registry: dict) -> None:
    path.write_text(json.dumps(registry, indent=2) + "\n", encoding="utf-8")


def test_repository_satisfies_settings_externalization_contract() -> None:
    assert validate_repository(REPO_ROOT) == []


def test_gate_rejects_missing_external_default(tmp_path: Path) -> None:
    root = _contract_root(tmp_path)
    path, registry = _registry(root)
    del registry["settings"][0]["default"]
    _write_registry(path, registry)

    assert any(
        "missing required fields" in issue for issue in validate_repository(root)
    )


def test_gate_rejects_persistence_policy_drift(tmp_path: Path) -> None:
    root = _contract_root(tmp_path)
    path, registry = _registry(root)
    registry["settings"][0]["persist"] = False
    _write_registry(path, registry)

    assert any("persist is false" in issue for issue in validate_repository(root))


def test_gate_rejects_registry_store_schema_and_path_drift(tmp_path: Path) -> None:
    root = _contract_root(tmp_path)
    path, registry = _registry(root)
    registry["schema_version"] += 1
    _write_registry(path, registry)
    store_path = root / "godot/Tet4D.Godot/scripts/ui/settings/settings_store.gd"
    store_path.write_text(
        store_path.read_text(encoding="utf-8").replace(
            "user://shell_settings.json", "res://shell_settings.json"
        ),
        encoding="utf-8",
    )

    issues = validate_repository(root)
    assert any("schema drift" in issue for issue in issues)
    assert any("user-data path drift" in issue for issue in issues)


def test_gate_rejects_unknown_runtime_setting(tmp_path: Path) -> None:
    root = _contract_root(tmp_path)
    consumer = root / "godot/Tet4D.Godot/scripts/ui/settings/contract_test_consumer.gd"
    consumer.write_text(
        'func apply(store):\n\treturn store.value("display.code_only")\n',
        encoding="utf-8",
    )

    assert any(
        "unknown setting id display.code_only" in issue
        for issue in validate_repository(root)
    )


def test_gate_rejects_duplicate_runtime_default(tmp_path: Path) -> None:
    root = _contract_root(tmp_path)
    consumer = root / "godot/Tet4D.Godot/scripts/ui/settings/contract_test_consumer.gd"
    consumer.write_text(
        'const FALLBACKS := {"display.window_mode": "windowed"}\n',
        encoding="utf-8",
    )

    assert any(
        "duplicates the registry default for display.window_mode" in issue
        for issue in validate_repository(root)
    )
