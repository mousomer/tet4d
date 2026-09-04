"""Apply one governed Godot product profile to a disposable project copy."""

from __future__ import annotations

import argparse
import configparser
import json
from pathlib import Path


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


def _validate_staging_target(repository_root: Path, staged_root: Path) -> tuple[Path, Path]:
    canonical_root = (repository_root / "godot/Tet4D.Godot").resolve()
    if staged_root == canonical_root:
        raise ProfileError("profile staging target is not an approved disposable project")
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
    marker = 'config/tet4d_product_id='
    if marker in project_text:
        project_text = _set_single(project_text, "config/tet4d_product_id", product_id)
    else:
        project_text = project_text.replace(
            "config/quit_on_go_back=false\n",
            f'config/quit_on_go_back=false\nconfig/tet4d_product_id="{product_id}"\n',
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


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository-root", type=Path, required=True)
    parser.add_argument("--staged-root", type=Path, required=True)
    parser.add_argument("--product", required=True)
    args = parser.parse_args()
    try:
        apply_profile(args.repository_root, args.staged_root, args.product)
    except (OSError, ProfileError, json.JSONDecodeError) as exc:
        raise SystemExit(f"product profile staging failed: {exc}") from exc
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
