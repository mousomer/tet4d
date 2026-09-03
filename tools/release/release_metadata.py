"""Validate release identity and generate checksum-bearing release metadata."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

SOURCE_SHA_PATTERN = re.compile(r"^[0-9a-f]{40}$")
POLICY_PATH = Path(__file__).resolve().parents[2] / "config/project/policy_pack.json"


@dataclass(frozen=True)
class ArtifactSpec:
    consumer_id: str
    product_id: str
    platform_id: str
    key: str
    filename_template: str
    evidence: dict[str, str]


ARTIFACT_SPECS = (
    ArtifactSpec(
        "python_windows",
        "python_tet4d",
        "windows",
        "windows_x86_64",
        "tet4d-python-{version}-windows-x86_64.msi",
        {
            "artifact_class": "MSI installer",
            "runtime": "installed outside-checkout smoke passed",
            "removal": "uninstall and registration removal passed",
        },
    ),
    ArtifactSpec(
        "python_macos",
        "python_tet4d",
        "macos",
        "macos_arm64",
        "tet4d-python-{version}-macos-arm64.dmg",
        {
            "artifact_class": "DMG containing an arm64 app",
            "runtime": "mounted outside-checkout smoke passed",
            "signing": "embedded PyInstaller executable ad-hoc signed; outer app unsigned",
            "notarization": "not notarized",
        },
    ),
    ArtifactSpec(
        "python_linux",
        "python_tet4d",
        "linux",
        "linux_x86_64",
        "tet4d-python-{version}-linux-x86_64.deb",
        {
            "artifact_class": "amd64 DEB installer",
            "runtime": "installed outside-checkout smoke passed",
            "removal": "package purge passed",
        },
    ),
    ArtifactSpec(
        "godot_designer_windows",
        "godot_designer",
        "windows",
        "windows_x86_64",
        "tet4d-designer-{version}-windows-x86_64.zip",
        {
            "artifact_class": "portable Godot Designer ZIP",
            "runtime": "bounded native Windows packaged start passed",
            "device_acceptance": "direct clean-machine human acceptance not claimed",
        },
    ),
    ArtifactSpec(
        "godot_game_macos",
        "godot_game",
        "macos",
        "macos_universal",
        "tet4d-godot-game-{version}-macos-universal.zip",
        {
            "artifact_class": "Universal 2 Godot Tet4D game app ZIP",
            "runtime": "two isolated outside-checkout smokes passed",
            "signing": "ad-hoc signed",
            "notarization": "not notarized",
        },
    ),
    ArtifactSpec(
        "legacy_designer_android",
        "godot_designer",
        "android",
        "android_arm64",
        "tet4d-designer-{version}-android-arm64.apk",
        {
            "artifact_class": "arm64 Android tablet APK",
            "signing": "ephemeral CI test release key",
            "device_acceptance": "emulator and physical-device acceptance not claimed",
            "target_status": "transitional mismatch; not a supported Designer target",
        },
    ),
    ArtifactSpec(
        "legacy_designer_ipados",
        "godot_designer",
        "ipados",
        "ipados_xcodeproject",
        "tet4d-designer-{version}-ipados-xcodeproject.zip",
        {
            "artifact_class": "release Xcode project",
            "build_status": "exported and compiled unsigned for the simulator",
            "signing": "unsigned",
            "device_acceptance": "not installed or tested on a physical iPad",
            "target_status": "transitional mismatch; not a supported Designer target",
        },
    ),
)


def product_contract() -> dict[str, dict[str, Any]]:
    policy = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
    contract = policy.get("product_platform_contract")
    if not isinstance(contract, dict):
        raise TypeError("policy pack is missing product_platform_contract")
    products = contract.get("products")
    if not isinstance(products, dict):
        raise TypeError("product_platform_contract.products must be an object")
    return products


def project_version(pyproject_path: Path) -> str:
    payload = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))
    version = str(payload["project"]["version"]).strip()
    if not version:
        raise ValueError("pyproject.toml project version is empty")
    return version


def normalize_tag(tag: str) -> str:
    normalized = tag.strip().removeprefix("refs/tags/").removeprefix("v")
    if not normalized:
        raise ValueError("release tag is empty after normalization")
    return normalized


def validate_tag(tag: str, version: str) -> str:
    normalized = normalize_tag(tag)
    if normalized != version:
        raise ValueError(
            f"release tag version {normalized!r} does not match "
            f"pyproject.toml version {version!r}"
        )
    return normalized


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as artifact:
        for chunk in iter(lambda: artifact.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _find_exact_artifact(artifact_dir: Path, filename: str) -> Path:
    matches = sorted(path for path in artifact_dir.rglob(filename) if path.is_file())
    if len(matches) != 1:
        raise ValueError(
            f"expected exactly one {filename!r} below {artifact_dir}, found {len(matches)}"
        )
    return matches[0]


def generate_manifest(artifact_dir: Path, version: str, source_sha: str) -> dict:
    normalized_sha = source_sha.strip().lower()
    if not SOURCE_SHA_PATTERN.fullmatch(normalized_sha):
        raise ValueError(
            "source SHA must be exactly 40 lowercase hexadecimal characters"
        )

    products = product_contract()
    families: dict[str, dict] = {}
    for product_id in {spec.product_id for spec in ARTIFACT_SPECS}:
        product = products.get(product_id)
        if not isinstance(product, dict) or not isinstance(
            product.get("display_name"), str
        ):
            raise TypeError(
                f"release artifact references unknown product {product_id!r}"
            )
        families[product_id] = {
            "display_name": product["display_name"],
            "artifacts": {},
        }
    for spec in ARTIFACT_SPECS:
        filename = spec.filename_template.format(version=version)
        artifact = _find_exact_artifact(artifact_dir, filename)
        families[spec.product_id]["artifacts"][spec.key] = {
            "filename": filename,
            "sha256": sha256(artifact),
            "bytes": artifact.stat().st_size,
            "evidence": spec.evidence,
        }

    return {
        "schema": "tet4d.release-manifest.v1",
        "version": version,
        "source_sha": normalized_sha,
        "product_families": families,
    }


def write_manifest(
    artifact_dir: Path, version: str, source_sha: str, output_path: Path
) -> None:
    manifest = generate_manifest(artifact_dir, version, source_sha)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--pyproject", type=Path, default=Path("pyproject.toml"), help="version source"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("project-version")

    validate = subparsers.add_parser("validate-tag")
    validate.add_argument("--tag", required=True)

    manifest = subparsers.add_parser("manifest")
    manifest.add_argument("--artifact-dir", type=Path, required=True)
    manifest.add_argument("--source-sha", required=True)
    manifest.add_argument("--output", type=Path, required=True)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    version = project_version(args.pyproject)
    try:
        if args.command == "project-version":
            print(version)
        elif args.command == "validate-tag":
            print(validate_tag(args.tag, version))
        elif args.command == "manifest":
            write_manifest(args.artifact_dir, version, args.source_sha, args.output)
            print(args.output)
        else:  # pragma: no cover - argparse owns this boundary.
            raise AssertionError(f"unsupported command: {args.command}")
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
