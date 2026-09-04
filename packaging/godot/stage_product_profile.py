"""Apply one governed Godot product profile to a disposable project copy."""

from __future__ import annotations

import argparse
import configparser
import json
from pathlib import Path

IDENTITY_MARKER_DIRECTORY = "config/tet4d_product_identity"


class ProfileError(ValueError):
    """A requested product profile cannot safely be staged."""


def _inside(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
    except ValueError:
        return False
    return True


def load_profile(policy_path: Path, product_id: str) -> dict[str, str]:
    policy = json.loads(policy_path.read_text(encoding="utf-8"))
    products = policy.get("product_platform_contract", {}).get("products", {})
    profile = products.get(product_id)
    if not isinstance(profile, dict):
        raise ProfileError("unknown product profile")
    required = (
        "display_name",
        "application_identity",
        "main_scene",
        "icon",
        "artifact_name_token",
        "permitted_package_role",
    )
    result = {key: str(profile.get(key, "")) for key in required}
    if any(not value for value in result.values()):
        raise ProfileError("product profile is missing a governed field")
    return result


def _set_single(text: str, key: str, value: str) -> str:
    lines = text.splitlines(keepends=True)
    matches = [index for index, line in enumerate(lines) if line.startswith(f"{key}=")]
    if len(matches) != 1:
        raise ProfileError("staged configuration has ambiguous governed keys")
    lines[matches[0]] = f'{key}="{value}"\n'
    return "".join(lines)


def identity_marker_resource(product_id: str) -> str:
    if not product_id or "/" in product_id or "\\" in product_id:
        raise ProfileError("product profile has an unsafe identity marker name")
    return f"res://{IDENTITY_MARKER_DIRECTORY}/{product_id}.tres"


def _write_identity_marker(staged_root: Path, product_id: str, profile: dict[str, str]) -> str:
    resource = identity_marker_resource(product_id)
    marker_path = staged_root / resource.removeprefix("res://")
    marker_path.parent.mkdir(parents=True, exist_ok=True)
    marker_path.write_text(
        "[gd_resource type=\"Resource\" format=3]\n\n[resource]\n"
        + "metadata = "
        + json.dumps(
            {
                "product_id": product_id,
                "application_identity": profile["application_identity"],
                "display_name": profile["display_name"],
                "main_scene": profile["main_scene"],
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    return resource


def _bind_identity_marker(staged_root: Path, main_scene: str, marker_resource: str) -> None:
    scene_path = staged_root / main_scene.removeprefix("res://")
    scene_text = scene_path.read_text(encoding="utf-8")
    marker_declaration = f'[ext_resource type="Resource" path="{marker_resource}" id="2_identity"]\n'
    if marker_declaration in scene_text:
        raise ProfileError("staged product scene has an ambiguous identity marker")
    first_node = "[node "
    if first_node not in scene_text:
        raise ProfileError("staged product scene has no root node")
    scene_text = scene_text.replace(first_node, marker_declaration + "\n" + first_node, 1)
    node_end = scene_text.find("\n", scene_text.index(first_node)) + 1
    scene_text = (
        scene_text[:node_end]
        + 'metadata/tet4d_product_identity_marker = ExtResource("2_identity")\n'
        + scene_text[node_end:]
    )
    scene_path.write_text(scene_text, encoding="utf-8")


def _validate_staging_target(repository_root: Path, staged_root: Path) -> tuple[Path, Path]:
    canonical_root = (repository_root / "godot/Tet4D.Godot").resolve()
    if _inside(staged_root, canonical_root):
        raise ProfileError("profile staging target must be outside the canonical Godot project")
    project_path = staged_root / "project.godot"
    presets_path = staged_root / "export_presets.cfg"
    if not project_path.is_file() or not presets_path.is_file():
        raise ProfileError("staged project is incomplete")
    return project_path, presets_path


def _apply_project_profile(project_path: Path, staged_root: Path, product_id: str, profile: dict[str, str]) -> None:
    for resource in (profile["main_scene"], profile["icon"]):
        relative = resource.removeprefix("res://")
        if resource == relative or not _inside(staged_root / relative, staged_root) or not (staged_root / relative).is_file():
            raise ProfileError("product profile references a missing staged resource")
    project_text = project_path.read_text(encoding="utf-8")
    for key, value in (
        ("config/name", profile["display_name"]),
        ("run/main_scene", profile["main_scene"]),
        ("config/icon", profile["icon"]),
    ):
        project_text = _set_single(project_text, key, value)
    product_marker = 'config/tet4d_product_id='
    if product_marker in project_text:
        project_text = _set_single(project_text, "config/tet4d_product_id", product_id)
    else:
        project_text = project_text.replace(
            "config/quit_on_go_back=false\n",
            f'config/quit_on_go_back=false\nconfig/tet4d_product_id="{product_id}"\n',
            1,
        )
    identity_marker = _write_identity_marker(staged_root, product_id, profile)
    _bind_identity_marker(staged_root, profile["main_scene"], identity_marker)
    marker_key = "config/tet4d_product_identity_marker"
    if f"{marker_key}=" in project_text:
        project_text = _set_single(project_text, marker_key, identity_marker)
    else:
        project_text = project_text.replace(
            f'config/tet4d_product_id="{product_id}"\n',
            f'config/tet4d_product_id="{product_id}"\n{marker_key}="{identity_marker}"\n',
            1,
        )
    project_path.write_text(project_text, encoding="utf-8")


def _apply_preset_profile(presets_path: Path, profile: dict[str, str]) -> None:
    parser = configparser.ConfigParser(interpolation=None)
    parser.optionxform = str
    parser.read(presets_path, encoding="utf-8")
    for section in parser.sections():
        if not section.endswith(".options"):
            continue
        options = parser[section]
        platform = parser[section.removesuffix(".options")].get("platform", "").strip('"')
        if platform in {"macOS", "iOS"} and "application/bundle_identifier" in options:
            options["application/bundle_identifier"] = f'"{profile["application_identity"]}"'
        elif platform == "Windows Desktop" and "application/product_name" in options:
            options["application/product_name"] = f'"{profile["display_name"]}"'
        elif platform == "Android" and "package/unique_name" in options:
            options["package/unique_name"] = f'"{profile["application_identity"]}"'
            options["package/name"] = f'"{profile["display_name"]}"'
    with presets_path.open("w", encoding="utf-8", newline="\n") as output:
        parser.write(output, space_around_delimiters=False)


def apply_profile(repository_root: Path, staged_root: Path, product_id: str) -> None:
    repository_root = repository_root.resolve()
    staged_root = staged_root.resolve()
    project_path, presets_path = _validate_staging_target(repository_root, staged_root)
    profile = load_profile(repository_root / "config/project/policy_pack.json", product_id)
    _apply_project_profile(project_path, staged_root, product_id, profile)
    _apply_preset_profile(presets_path, profile)
    validate_staged_profile(repository_root, staged_root, product_id)


def validate_staged_profile(repository_root: Path, staged_root: Path, product_id: str) -> None:
    repository_root = repository_root.resolve()
    staged_root = staged_root.resolve()
    project_path, _ = _validate_staging_target(repository_root, staged_root)
    profile = load_profile(repository_root / "config/project/policy_pack.json", product_id)
    project_text = project_path.read_text(encoding="utf-8")
    expected = (
        ("config/tet4d_product_id", product_id),
        ("config/name", profile["display_name"]),
        ("run/main_scene", profile["main_scene"]),
        ("config/tet4d_product_identity_marker", identity_marker_resource(product_id)),
    )
    for key, value in expected:
        if f'{key}="{value}"' not in project_text:
            raise ProfileError("staged project identity does not match the selected profile")
    marker_path = staged_root / identity_marker_resource(product_id).removeprefix("res://")
    try:
        marker_text = marker_path.read_text(encoding="utf-8")
        marker = json.loads(marker_text.split("metadata = ", 1)[1])
    except (OSError, IndexError, json.JSONDecodeError) as exc:
        raise ProfileError("staged project identity marker is missing or invalid") from exc
    if marker != {
        "product_id": product_id,
        "application_identity": profile["application_identity"],
        "display_name": profile["display_name"],
        "main_scene": profile["main_scene"],
    }:
        raise ProfileError("staged project identity marker does not match the selected profile")
    scene_text = (staged_root / profile["main_scene"].removeprefix("res://")).read_text(encoding="utf-8")
    if (
        f'path="{identity_marker_resource(product_id)}"' not in scene_text
        or 'metadata/tet4d_product_identity_marker = ExtResource("2_identity")' not in scene_text
    ):
        raise ProfileError("staged product scene does not bind its identity marker")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository-root", type=Path, required=True)
    parser.add_argument("--staged-root", type=Path, required=True)
    parser.add_argument("--product", required=True)
    parser.add_argument("--validate", action="store_true")
    args = parser.parse_args()
    try:
        if args.validate:
            validate_staged_profile(args.repository_root, args.staged_root, args.product)
        else:
            apply_profile(args.repository_root, args.staged_root, args.product)
    except (OSError, ProfileError, json.JSONDecodeError) as exc:
        raise SystemExit(f"product profile staging failed: {exc}") from exc
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
