"""Release identity, scope, manifest, and release-note contract utilities.

The candidate and publication workflows deliberately share this module. A
candidate records the exact selected package bytes in a v2 manifest; the
publication workflow validates those downloaded bytes before it changes a draft
release to published. Neither phase has a fallback to a branch, filename, or
an inferred job selection.
"""

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
CURRENT_ALL_SCOPE = "current_all"
MANIFEST_SCHEMA = "tet4d.release-manifest.v2"


@dataclass(frozen=True)
class ArtifactSpec:
    """One registered package consumer and its immutable release filename."""

    consumer_id: str
    product_id: str
    platform_id: str
    key: str
    filename_template: str
    evidence: dict[str, str]


# This order is the scope canonicalization order. Do not derive a release
# scope from filenames, job names, or policy-list order.
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


def _policy_contract() -> dict[str, Any]:
    policy = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
    contract = policy.get("product_platform_contract")
    if not isinstance(contract, dict):
        raise TypeError("policy pack is missing product_platform_contract")
    return contract


def product_contract() -> dict[str, dict[str, Any]]:
    products = _policy_contract().get("products")
    if not isinstance(products, dict):
        raise TypeError("product_platform_contract.products must be an object")
    return products


def packaging_consumers() -> dict[str, dict[str, Any]]:
    consumers = _policy_contract().get("packaging_consumers")
    if not isinstance(consumers, list):
        raise TypeError("product_platform_contract.packaging_consumers must be a list")
    indexed: dict[str, dict[str, Any]] = {}
    for consumer in consumers:
        if not isinstance(consumer, dict) or not isinstance(
            consumer.get("consumer_id"), str
        ):
            raise TypeError("every packaging consumer must have a consumer_id")
        consumer_id = consumer["consumer_id"]
        if consumer_id in indexed:
            raise ValueError(f"duplicate registered packaging consumer {consumer_id!r}")
        indexed[consumer_id] = consumer
    return indexed


def consumer_specs() -> dict[str, ArtifactSpec]:
    indexed: dict[str, ArtifactSpec] = {}
    for spec in ARTIFACT_SPECS:
        if spec.consumer_id in indexed:
            raise ValueError(
                f"duplicate artifact consumer identity {spec.consumer_id!r}"
            )
        indexed[spec.consumer_id] = spec
    return indexed


def registered_consumer_ids() -> tuple[str, ...]:
    return tuple(spec.consumer_id for spec in ARTIFACT_SPECS)


def parse_release_scope(release_scope: str) -> tuple[str, ...]:
    """Return a validated, registered-order release scope."""

    if not isinstance(release_scope, str):
        raise TypeError("release scope must be a string")
    if release_scope == CURRENT_ALL_SCOPE:
        return registered_consumer_ids()
    if release_scope.strip() == CURRENT_ALL_SCOPE:
        raise ValueError("current_all must be supplied exactly without whitespace")
    parts = release_scope.split(",")
    if not parts:
        raise ValueError("release scope must select at least one consumer")
    selected: set[str] = set()
    known = set(registered_consumer_ids())
    for raw_consumer_id in parts:
        consumer_id = raw_consumer_id.strip()
        if not consumer_id:
            raise ValueError("release scope contains an empty consumer identifier")
        if consumer_id == CURRENT_ALL_SCOPE:
            raise ValueError("current_all must be the sole release scope value")
        if consumer_id in selected:
            raise ValueError(
                f"release scope contains duplicate consumer {consumer_id!r}"
            )
        if consumer_id not in known:
            raise ValueError(f"release scope contains unknown consumer {consumer_id!r}")
        selected.add(consumer_id)
    return tuple(
        spec.consumer_id for spec in ARTIFACT_SPECS if spec.consumer_id in selected
    )


def scope_payload(release_scope: str) -> dict[str, Any]:
    selected_scope = parse_release_scope(release_scope)
    selected = set(selected_scope)
    return {
        "release_scope": list(selected_scope),
        "selected": {
            consumer_id: consumer_id in selected
            for consumer_id in registered_consumer_ids()
        },
    }


def validate_source_sha(source_sha: str) -> str:
    if not isinstance(source_sha, str) or not SOURCE_SHA_PATTERN.fullmatch(source_sha):
        raise ValueError(
            "source SHA must be exactly 40 lowercase hexadecimal characters"
        )
    return source_sha


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
            f"release tag version {normalized!r} does not match pyproject.toml version {version!r}"
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


def _filename_version(spec: ArtifactSpec, filename: str) -> str | None:
    expression = re.escape(spec.filename_template).replace(
        re.escape("{version}"), r"(?P<version>[^/]+)"
    )
    match = re.fullmatch(expression, filename)
    return match.group("version") if match else None


def _validate_registered_specs() -> None:
    products = product_contract()
    contract = _policy_contract()
    platform_ids = contract.get("platform_ids")
    if not isinstance(platform_ids, list):
        raise TypeError("product_platform_contract.platform_ids must be a list")
    registered = packaging_consumers()
    artifact_consumers = consumer_specs()
    if set(artifact_consumers) != set(registered):
        missing = sorted(set(registered) - set(artifact_consumers))
        extra = sorted(set(artifact_consumers) - set(registered))
        raise ValueError(
            f"artifact consumers must exactly match policy consumers; missing={missing}, extra={extra}"
        )
    for spec in ARTIFACT_SPECS:
        product = products.get(spec.product_id)
        if not isinstance(product, dict) or not isinstance(
            product.get("display_name"), str
        ):
            raise TypeError(
                f"release artifact references unknown product {spec.product_id!r}"
            )
        if spec.platform_id not in platform_ids:
            raise ValueError(
                f"release artifact references unknown platform {spec.platform_id!r}"
            )
        consumer = registered[spec.consumer_id]
        if (
            consumer.get("product_id") != spec.product_id
            or consumer.get("platform_id") != spec.platform_id
        ):
            raise ValueError(
                f"consumer {spec.consumer_id!r} product/platform identity disagrees with policy"
            )
        if (
            spec.consumer_id.startswith("legacy_designer_")
            and consumer.get("status") != "transitional_mismatch"
        ):
            raise ValueError(
                f"transitional consumer {spec.consumer_id!r} must retain transitional status"
            )


def _selected_specs(release_scope: str) -> tuple[ArtifactSpec, ...]:
    _validate_registered_specs()
    selected = set(parse_release_scope(release_scope))
    return tuple(spec for spec in ARTIFACT_SPECS if spec.consumer_id in selected)


def _validate_directory_scope(
    artifact_dir: Path, version: str, selected_specs: tuple[ArtifactSpec, ...]
) -> None:
    selected_ids = {spec.consumer_id for spec in selected_specs}
    expected_filenames = [
        spec.filename_template.format(version=version) for spec in selected_specs
    ]
    if len(expected_filenames) != len(set(expected_filenames)):
        raise ValueError("selected consumers produce duplicate artifact filenames")
    for path in artifact_dir.rglob("*"):
        if not path.is_file():
            continue
        for spec in ARTIFACT_SPECS:
            artifact_version = _filename_version(spec, path.name)
            if artifact_version is None:
                continue
            if artifact_version != version:
                raise ValueError(
                    f"artifact {path.name!r} has version {artifact_version!r}, expected {version!r}"
                )
            if spec.consumer_id not in selected_ids:
                raise ValueError(
                    f"artifact {path.name!r} belongs to unselected consumer {spec.consumer_id!r}"
                )


def generate_manifest(
    artifact_dir: Path,
    version: str,
    source_sha: str,
    release_scope: str = CURRENT_ALL_SCOPE,
) -> dict[str, Any]:
    """Generate a scope-exact manifest from the selected package bytes."""

    normalized_sha = validate_source_sha(source_sha)
    selected_specs = _selected_specs(release_scope)
    selected_scope = tuple(spec.consumer_id for spec in selected_specs)
    _validate_directory_scope(artifact_dir, version, selected_specs)
    products = product_contract()
    families: dict[str, dict[str, Any]] = {}
    for spec in selected_specs:
        filename = spec.filename_template.format(version=version)
        artifact = _find_exact_artifact(artifact_dir, filename)
        family = families.setdefault(
            spec.product_id,
            {
                "display_name": products[spec.product_id]["display_name"],
                "artifacts": {},
            },
        )
        family["artifacts"][spec.consumer_id] = {
            "consumer_id": spec.consumer_id,
            "product_id": spec.product_id,
            "platform_id": spec.platform_id,
            "key": spec.key,
            "filename": filename,
            "sha256": sha256(artifact),
            "bytes": artifact.stat().st_size,
            "evidence": spec.evidence,
        }
    return {
        "schema": MANIFEST_SCHEMA,
        "version": version,
        "source_sha": normalized_sha,
        "release_scope": list(selected_scope),
        "product_families": families,
    }


def _manifest_entries(manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    families = manifest.get("product_families")
    if not isinstance(families, dict):
        raise TypeError("manifest product_families must be an object")
    entries: dict[str, dict[str, Any]] = {}
    for family_product_id, family in families.items():
        if not isinstance(family, dict) or not isinstance(
            family.get("artifacts"), dict
        ):
            raise TypeError(
                f"manifest product family {family_product_id!r} is malformed"
            )
        for map_consumer_id, entry in family["artifacts"].items():
            if not isinstance(entry, dict):
                raise TypeError(f"manifest artifact {map_consumer_id!r} is malformed")
            consumer_id = entry.get("consumer_id")
            if consumer_id != map_consumer_id:
                raise ValueError(
                    "manifest artifact consumer identity does not match its map key"
                )
            if consumer_id in entries:
                raise ValueError(
                    f"manifest contains duplicate consumer {consumer_id!r}"
                )
            if entry.get("product_id") != family_product_id:
                raise ValueError(
                    f"manifest consumer {consumer_id!r} is in the wrong product family"
                )
            entries[consumer_id] = entry
    return entries


def _validate_manifest_identity(
    manifest: dict[str, Any], source_sha: str | None
) -> tuple[str, tuple[str, ...], dict[str, dict[str, Any]], dict[str, ArtifactSpec]]:
    if manifest.get("schema") != MANIFEST_SCHEMA:
        raise ValueError(f"manifest schema must be {MANIFEST_SCHEMA!r}")
    version = manifest.get("version")
    if not isinstance(version, str) or not version:
        raise ValueError("manifest version must be a non-empty string")
    manifest_sha = validate_source_sha(manifest.get("source_sha"))
    if source_sha is not None and manifest_sha != validate_source_sha(source_sha):
        raise ValueError("manifest source SHA does not match the requested source SHA")
    scope = manifest.get("release_scope")
    if not isinstance(scope, list) or not all(isinstance(item, str) for item in scope):
        raise ValueError(
            "manifest release_scope must be a list of consumer identifiers"
        )
    canonical_scope = parse_release_scope(",".join(scope))
    if tuple(scope) != canonical_scope:
        raise ValueError("manifest release_scope is not in canonical registered order")
    _validate_registered_specs()
    entries = _manifest_entries(manifest)
    expected_specs = {
        spec.consumer_id: spec for spec in _selected_specs(",".join(scope))
    }
    if set(entries) != set(expected_specs):
        raise ValueError(
            "manifest consumers do not exactly match manifest release_scope"
        )
    return version, canonical_scope, entries, expected_specs


def _validate_manifest_entry(
    consumer_id: str,
    spec: ArtifactSpec,
    entry: dict[str, Any],
    version: str,
    artifact_dir: Path | None,
    filenames: set[str],
) -> None:
    expected_filename = spec.filename_template.format(version=version)
    if (
        entry.get("product_id") != spec.product_id
        or entry.get("platform_id") != spec.platform_id
        or entry.get("key") != spec.key
        or entry.get("filename") != expected_filename
    ):
        raise ValueError(
            f"manifest consumer {consumer_id!r} identity or filename is inconsistent"
        )
    if expected_filename in filenames:
        raise ValueError(f"manifest contains duplicate filename {expected_filename!r}")
    filenames.add(expected_filename)
    artifact_hash = entry.get("sha256")
    artifact_bytes = entry.get("bytes")
    if not isinstance(artifact_hash, str) or not re.fullmatch(
        r"[0-9a-f]{64}", artifact_hash
    ):
        raise ValueError(f"manifest consumer {consumer_id!r} has malformed SHA-256")
    if not isinstance(artifact_bytes, int) or artifact_bytes < 1:
        raise ValueError(f"manifest consumer {consumer_id!r} has invalid byte count")
    if entry.get("evidence") != spec.evidence:
        raise ValueError(f"manifest consumer {consumer_id!r} evidence is inconsistent")
    if artifact_dir is not None:
        artifact = _find_exact_artifact(artifact_dir, expected_filename)
        if (
            artifact.stat().st_size != artifact_bytes
            or sha256(artifact) != artifact_hash
        ):
            raise ValueError(
                f"manifest checksum or byte count differs for {expected_filename!r}"
            )


def validate_manifest(
    manifest: dict[str, Any],
    artifact_dir: Path | None = None,
    source_sha: str | None = None,
) -> tuple[str, ...]:
    """Validate v2 identity and, when supplied, every recorded artifact byte."""

    version, canonical_scope, entries, expected_specs = _validate_manifest_identity(
        manifest, source_sha
    )
    filenames: set[str] = set()
    for consumer_id, spec in expected_specs.items():
        _validate_manifest_entry(
            consumer_id, spec, entries[consumer_id], version, artifact_dir, filenames
        )
    if artifact_dir is not None:
        _validate_directory_scope(artifact_dir, version, tuple(expected_specs.values()))
    return canonical_scope


def read_manifest(manifest_path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"manifest is not valid JSON: {manifest_path}") from exc
    if not isinstance(payload, dict):
        raise TypeError("manifest root must be an object")
    return payload


def release_note_text(manifest: dict[str, Any]) -> str:
    """Describe only the package families actually listed in a valid manifest."""

    selected_scope = validate_manifest(manifest)
    entries = _manifest_entries(manifest)
    labels = {
        "python_macos": "Python Tet4D — macOS arm64",
        "python_windows": "Python Tet4D — Windows x86-64",
        "python_linux": "Python Tet4D — Linux x86-64",
        "godot_game_macos": "Tet4D game — macOS Universal",
        "godot_designer_windows": "Tet4D Designer — Windows x86-64",
        "legacy_designer_android": "Transitional Designer Android artifact — arm64 tablet APK",
        "legacy_designer_ipados": "Transitional Designer iPadOS artifact — Xcode project",
    }
    display_lines = [
        f"- {labels[consumer_id]}: `{entries[consumer_id]['filename']}`"
        for consumer_id in selected_scope
    ]
    transitional_notice = ""
    if (
        "legacy_designer_android" in selected_scope
        or "legacy_designer_ipados" in selected_scope
    ):
        transitional_notice = "\n\nThe transitional Designer Android artifact and transitional Designer iPadOS artifact are technical evidence only; neither claims a supported Designer platform or a Tet4D game package."
    return (
        f"# Tet4D {manifest['version']} candidate\n\nSource commit `{manifest['source_sha']}`\n\nSelected package artifacts\n"
        + "\n".join(display_lines)
        + transitional_notice
        + "\n"
    )


def manifest_asset_names(manifest: dict[str, Any], manifest_filename: str) -> list[str]:
    validate_manifest(manifest)
    if not manifest_filename:
        raise ValueError("manifest filename must not be empty")
    entries = _manifest_entries(manifest)
    return sorted(
        [manifest_filename, *(entry["filename"] for entry in entries.values())]
    )


def write_manifest(
    artifact_dir: Path,
    version: str,
    source_sha: str,
    release_scope: str,
    output_path: Path,
) -> None:
    manifest = generate_manifest(artifact_dir, version, source_sha, release_scope)
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
    validate_sha = subparsers.add_parser("validate-source-sha")
    validate_sha.add_argument("--source-sha", required=True)
    scope = subparsers.add_parser("scope")
    scope.add_argument("--release-scope", required=True)
    manifest = subparsers.add_parser("manifest")
    manifest.add_argument("--artifact-dir", type=Path, required=True)
    manifest.add_argument("--source-sha", required=True)
    manifest.add_argument("--release-scope", required=True)
    manifest.add_argument("--output", type=Path, required=True)
    notes = subparsers.add_parser("release-notes")
    notes.add_argument("--manifest", type=Path, required=True)
    notes.add_argument("--output", type=Path, required=True)
    validate_manifest_parser = subparsers.add_parser("validate-manifest")
    validate_manifest_parser.add_argument("--manifest", type=Path, required=True)
    validate_manifest_parser.add_argument("--artifact-dir", type=Path, required=True)
    validate_manifest_parser.add_argument("--source-sha", required=True)
    assets = subparsers.add_parser("asset-names")
    assets.add_argument("--manifest", type=Path, required=True)
    assets.add_argument("--manifest-filename", required=True)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        if args.command == "project-version":
            print(project_version(args.pyproject))
        elif args.command == "validate-tag":
            print(validate_tag(args.tag, project_version(args.pyproject)))
        elif args.command == "validate-source-sha":
            print(validate_source_sha(args.source_sha))
        elif args.command == "scope":
            print(json.dumps(scope_payload(args.release_scope), sort_keys=True))
        elif args.command == "manifest":
            write_manifest(
                args.artifact_dir,
                project_version(args.pyproject),
                args.source_sha,
                args.release_scope,
                args.output,
            )
            print(args.output)
        elif args.command == "release-notes":
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(
                release_note_text(read_manifest(args.manifest)), encoding="utf-8"
            )
            print(args.output)
        elif args.command == "validate-manifest":
            print(
                json.dumps(
                    {
                        "release_scope": list(
                            validate_manifest(
                                read_manifest(args.manifest),
                                args.artifact_dir,
                                args.source_sha,
                            )
                        )
                    },
                    sort_keys=True,
                )
            )
        elif args.command == "asset-names":
            print(
                json.dumps(
                    manifest_asset_names(
                        read_manifest(args.manifest), args.manifest_filename
                    )
                )
            )
        else:  # pragma: no cover - argparse owns this boundary.
            raise AssertionError(f"unsupported command: {args.command}")
    except (TypeError, ValueError) as exc:
        raise SystemExit(str(exc)) from exc
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
