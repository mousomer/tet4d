from __future__ import annotations

import configparser
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.release.release_metadata import ARTIFACT_SPECS, ArtifactSpec

POLICY_PATH = ROOT / "config/project/policy_pack.json"
WORKFLOW_PATH = ROOT / ".github/workflows/release-packaging.yml"
PRESETS_PATH = ROOT / "godot/Tet4D.Godot/export_presets.cfg"
CHANGE_GOVERNANCE_PATH = ROOT / "docs/governance/CHANGE_GOVERNANCE.md"
RDS_PATH = ROOT / "docs/rds/RDS_PACKAGING.md"
BACKLOG_PATH = ROOT / "docs/BACKLOG.md"

PRODUCT_IDS = ("python_tet4d", "godot_game", "godot_designer")
PLATFORM_LABELS = {
    "macos": "macOS",
    "windows": "Windows",
    "linux": "Linux",
    "android": "Android",
    "ipados": "iPadOS",
}
VALID_CONSUMER_STATUSES = {"implemented", "transitional_mismatch"}
GRANDFATHERED_TRANSITIONAL_CONSUMERS = {
    "legacy_designer_android": ("godot_designer", "android"),
    "legacy_designer_ipados": ("godot_designer", "ipados"),
}
RDS_MATRIX_SECTION = "## 1. Purpose"


@dataclass
class ConsumerEvidence:
    consumer_ids: set[str] = field(default_factory=set)
    workflow_jobs: set[str] = field(default_factory=set)
    export_presets: set[str] = field(default_factory=set)
    implemented: set[tuple[str, str]] = field(default_factory=set)
    consumers: dict[str, tuple[str, str, str]] = field(default_factory=dict)
    transitional_consumers: set[str] = field(default_factory=set)


def _string(value: object, label: str, issues: list[str]) -> str:
    if not isinstance(value, str) or not value.strip():
        issues.append(f"{label} must be a non-empty string")
        return ""
    return value


def _strings(value: object, label: str, issues: list[str]) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        issues.append(f"{label} must be a string list")
        return []
    if len(value) != len(set(value)):
        issues.append(f"{label} contains duplicates")
    return value


def _workflow_jobs(text: str) -> dict[str, str]:
    jobs: dict[str, str] = {}
    current = ""
    in_jobs = False
    for line in text.splitlines():
        if line == "jobs:":
            in_jobs = True
            continue
        if not in_jobs:
            continue
        match = re.fullmatch(r"  ([a-z0-9-]+):", line)
        if match:
            current = match.group(1)
            jobs[current] = ""
            continue
        if current and (match := re.fullmatch(r"    name: (.+)", line)):
            jobs[current] = match.group(1).strip('"')
    return jobs


def _export_presets(text: str) -> dict[str, dict[str, str]]:
    parser = configparser.ConfigParser(interpolation=None, strict=False)
    parser.read_string(text)
    presets: dict[str, dict[str, str]] = {}
    for section in parser.sections():
        match = re.fullmatch(r"preset\.(\d+)", section)
        if not match:
            continue
        name = parser[section].get("name", "").strip('"')
        options = dict(parser[f"preset.{match.group(1)}.options"])
        presets[name] = {key: value.strip('"') for key, value in options.items()}
    return presets


def _rds_matrix(text: str, issues: list[str]) -> dict[str, list[str]]:
    rows: dict[str, list[str]] = {}
    label_to_id = {
        label.casefold(): platform for platform, label in PLATFORM_LABELS.items()
    }
    pattern = re.compile(r"^\| `([^`]+)` \| [^|]+ \| ([^|]+) \|$")
    section_start = text.find(RDS_MATRIX_SECTION)
    if section_start < 0:
        issues.append(f"RDS is missing matrix section: {RDS_MATRIX_SECTION}")
        return rows
    section_text = text[section_start + len(RDS_MATRIX_SECTION) :]
    next_section = re.search(r"^## ", section_text, flags=re.MULTILINE)
    if next_section:
        section_text = section_text[: next_section.start()]
    for line in section_text.splitlines():
        match = pattern.fullmatch(line)
        if not match:
            continue
        platforms: list[str] = []
        for label in match.group(2).split(","):
            platform = label_to_id.get(label.strip().casefold())
            if platform is None:
                issues.append(
                    f"RDS matrix uses unknown platform label: {label.strip()}"
                )
            else:
                platforms.append(platform)
        rows[match.group(1)] = platforms
    return rows


def _validate_product(
    product_id: str,
    product: object,
    targets_value: object,
    platform_ids: list[str],
    rds_matrix: dict[str, list[str]],
    issues: list[str],
) -> tuple[set[str], str]:
    label = f"product_platform_contract.products.{product_id}"
    if not isinstance(product, dict):
        issues.append(f"{label} must be an object")
        return set(), ""
    for attribute in (
        "display_name",
        "runtime_family",
        "purpose",
        "application_identity",
        "artifact_name_token",
        "backlog_label",
    ):
        _string(product.get(attribute), f"{label}.{attribute}", issues)
    if product_id in {"godot_game", "godot_designer"}:
        for attribute in ("main_scene", "icon", "permitted_package_role"):
            _string(product.get(attribute), f"{label}.{attribute}", issues)
    targets = _strings(
        targets_value,
        f"product_platform_contract.target_platforms.{product_id}",
        issues,
    )
    unknown = sorted(set(targets) - set(platform_ids))
    if unknown:
        issues.append(f"{label} has unknown target platforms: {unknown}")
    if rds_matrix.get(product_id) != targets:
        issues.append(
            f"RDS matrix for {product_id} {rds_matrix.get(product_id)} "
            f"does not match machine authority {targets}"
        )
    return set(targets), str(product.get("application_identity", ""))


def _validate_contract_header(
    contract: dict[str, object], issues: list[str]
) -> list[str]:
    if contract.get("schema_version") != 1:
        issues.append("product_platform_contract.schema_version must be 1")
    authority = contract.get("authority")
    if not isinstance(authority, dict):
        issues.append("product_platform_contract.authority must be an object")
    else:
        expected_authority = {
            "change_route": "product_planning",
            "human_owner": "docs/rds/RDS_PACKAGING.md",
            "change_governance": "docs/governance/CHANGE_GOVERNANCE.md",
            "implementation_gaps": "docs/BACKLOG.md",
        }
        if authority != expected_authority:
            issues.append("product_platform_contract authority routing changed")
    platform_ids = _strings(
        contract.get("platform_ids"), "product_platform_contract.platform_ids", issues
    )
    if set(platform_ids) != set(PLATFORM_LABELS):
        issues.append(f"platform_ids must be exactly {list(PLATFORM_LABELS)}")
    return platform_ids


def _validate_products(
    contract: dict[str, object],
    platform_ids: list[str],
    rds_text: str,
    issues: list[str],
) -> tuple[dict[str, object], dict[str, set[str]], dict[str, str]]:
    products = contract.get("products")
    if not isinstance(products, dict):
        issues.append("product_platform_contract.products must be an object")
        return {}, {}, {}
    if tuple(products) != PRODUCT_IDS:
        issues.append(f"product IDs must be exactly {list(PRODUCT_IDS)} in that order")
    target_platforms = contract.get("target_platforms")
    if not isinstance(target_platforms, dict) or tuple(target_platforms) != PRODUCT_IDS:
        issues.append("target_platforms must map the exact ordered product IDs")
        target_platforms = {}
    rds_matrix = _rds_matrix(rds_text, issues)
    target_sets: dict[str, set[str]] = {}
    identities: dict[str, str] = {}
    for product_id in PRODUCT_IDS:
        targets, identity = _validate_product(
            product_id,
            products.get(product_id),
            target_platforms.get(product_id),
            platform_ids,
            rds_matrix,
            issues,
        )
        target_sets[product_id] = targets
        identities[product_id] = identity
    godot_profiles = [
        products.get(product_id, {}) for product_id in ("godot_game", "godot_designer")
    ]
    for attribute in (
        "application_identity",
        "main_scene",
        "icon",
        "artifact_name_token",
    ):
        values = [
            str(profile.get(attribute, ""))
            for profile in godot_profiles
            if isinstance(profile, dict)
        ]
        if len(values) == 2 and values[0] == values[1]:
            issues.append(f"Godot product profiles must use distinct {attribute}")
    return products, target_sets, identities


def _validate_consumer_status(
    consumer_id: str,
    product_id: str,
    platform_id: str,
    status: str,
    workflow_job: str,
    target_sets: dict[str, set[str]],
    workflow_jobs: dict[str, str],
    evidence: ConsumerEvidence,
    issues: list[str],
) -> None:
    is_target = platform_id in target_sets[product_id]
    if status == "implemented":
        if not is_target:
            issues.append(
                f"forbidden implemented pairing: {product_id} / {platform_id}"
            )
        evidence.implemented.add((product_id, platform_id))
        return
    if status != "transitional_mismatch":
        issues.append(f"unknown consumer status: {status}")
        return
    expected = GRANDFATHERED_TRANSITIONAL_CONSUMERS.get(consumer_id)
    if expected != (product_id, platform_id):
        issues.append(
            f"transitional mismatch is not a grandfathered consumer: {consumer_id}"
        )
        return
    evidence.transitional_consumers.add(consumer_id)
    if is_target:
        issues.append(
            f"transitional consumer is already an allowed target: {consumer_id}"
        )
    job_name = workflow_jobs.get(workflow_job, "").casefold()
    if "transitional" not in job_name or "not a target" not in job_name:
        issues.append(
            f"{workflow_job} does not expose its transitional non-target status"
        )


def _validate_consumer_workflow(
    product_id: str,
    workflow_job: str,
    workflow_jobs: dict[str, str],
    issues: list[str],
) -> None:
    if workflow_job not in workflow_jobs:
        issues.append(f"registered workflow job is missing: {workflow_job}")
        return
    if (
        product_id == "godot_game"
        and "designer" in workflow_jobs[workflow_job].casefold()
    ):
        issues.append(f"Godot game job is misleadingly named Designer: {workflow_job}")


def _validate_consumer_preset(
    consumer: dict[str, object],
    label: str,
    product_id: str,
    identities: dict[str, str],
    presets: dict[str, dict[str, str]],
    evidence: ConsumerEvidence,
    issues: list[str],
) -> None:
    preset_name = consumer.get("export_preset")
    if preset_name is None:
        return
    if not isinstance(preset_name, str) or preset_name not in presets:
        issues.append(f"{label} references missing export preset {preset_name!r}")
        return
    evidence.export_presets.add(preset_name)
    identity_field = _string(
        consumer.get("identity_field"), f"{label}.identity_field", issues
    )
    expected_identity = str(consumer.get("identity_value", identities[product_id]))
    actual_identity = presets[preset_name].get(identity_field)
    if actual_identity != expected_identity:
        issues.append(
            f"{preset_name} identity {identity_field}={actual_identity!r} does not "
            f"match {product_id} identity {expected_identity!r}"
        )


def _validate_consumer(
    consumer: dict[str, object],
    label: str,
    products: dict[str, object],
    platform_ids: list[str],
    target_sets: dict[str, set[str]],
    identities: dict[str, str],
    workflow_jobs: dict[str, str],
    presets: dict[str, dict[str, str]],
    evidence: ConsumerEvidence,
    issues: list[str],
) -> None:
    consumer_id = _string(consumer.get("consumer_id"), f"{label}.consumer_id", issues)
    product_id = _string(consumer.get("product_id"), f"{label}.product_id", issues)
    platform_id = _string(consumer.get("platform_id"), f"{label}.platform_id", issues)
    status = _string(consumer.get("status"), f"{label}.status", issues)
    workflow_job = _string(
        consumer.get("workflow_job"), f"{label}.workflow_job", issues
    )
    if consumer_id in evidence.consumer_ids:
        issues.append(f"duplicate consumer_id: {consumer_id}")
    evidence.consumer_ids.add(consumer_id)
    evidence.workflow_jobs.add(workflow_job)
    if product_id not in products or platform_id not in platform_ids:
        issues.append(f"{label} references unknown product or platform")
        return
    evidence.consumers[consumer_id] = (product_id, platform_id, status)
    _validate_consumer_status(
        consumer_id,
        product_id,
        platform_id,
        status,
        workflow_job,
        target_sets,
        workflow_jobs,
        evidence,
        issues,
    )
    _validate_consumer_workflow(product_id, workflow_job, workflow_jobs, issues)
    _validate_consumer_preset(
        consumer, label, product_id, identities, presets, evidence, issues
    )


def _validate_consumers(
    contract: dict[str, object],
    products: dict[str, object],
    platform_ids: list[str],
    target_sets: dict[str, set[str]],
    identities: dict[str, str],
    workflow_text: str,
    presets_text: str,
    issues: list[str],
) -> ConsumerEvidence:
    evidence = ConsumerEvidence()
    consumers = contract.get("packaging_consumers")
    if not isinstance(consumers, list):
        issues.append("product_platform_contract.packaging_consumers must be a list")
        return evidence
    workflow_jobs = _workflow_jobs(workflow_text)
    presets = _export_presets(presets_text)
    for index, consumer in enumerate(consumers):
        label = f"packaging_consumers[{index}]"
        if not isinstance(consumer, dict):
            issues.append(f"{label} must be an object")
            continue
        _validate_consumer(
            consumer,
            label,
            products,
            platform_ids,
            target_sets,
            identities,
            workflow_jobs,
            presets,
            evidence,
            issues,
        )
    if evidence.transitional_consumers != set(GRANDFATHERED_TRANSITIONAL_CONSUMERS):
        issues.append(
            "transitional consumers must be exactly the grandfathered set: "
            f"{sorted(GRANDFATHERED_TRANSITIONAL_CONSUMERS)}"
        )
    package_jobs = {job for job in workflow_jobs if job.startswith("package-")}
    if package_jobs != evidence.workflow_jobs:
        issues.append(
            "release workflow package jobs and registered consumers disagree: "
            f"unregistered={sorted(package_jobs - evidence.workflow_jobs)}, "
            f"missing={sorted(evidence.workflow_jobs - package_jobs)}"
        )
    if set(presets) != evidence.export_presets:
        issues.append(
            "Godot export presets and registered consumers disagree: "
            f"unregistered={sorted(set(presets) - evidence.export_presets)}, "
            f"missing={sorted(evidence.export_presets - set(presets))}"
        )
    return evidence


def _validate_artifact_specs(
    products: dict[str, object],
    evidence: ConsumerEvidence,
    artifact_specs: tuple[ArtifactSpec, ...],
    issues: list[str],
) -> None:
    registered = set(evidence.consumers)
    registered_specs: set[str] = set()
    for spec in artifact_specs:
        if spec.consumer_id in registered_specs:
            issues.append(f"duplicate release artifact consumer: {spec.consumer_id}")
        registered_specs.add(spec.consumer_id)
        consumer = evidence.consumers.get(spec.consumer_id)
        if consumer is None:
            issues.append(
                f"release artifact references unregistered consumer: {spec.consumer_id}"
            )
            continue
        product_id, platform_id, _status = consumer
        if spec.product_id not in products:
            issues.append(
                f"release artifact references unknown product: {spec.product_id}"
            )
            continue
        if (spec.product_id, spec.platform_id) != (product_id, platform_id):
            issues.append(
                f"release artifact {spec.consumer_id} product/platform does not match "
                "its registered consumer"
            )
        product = products[spec.product_id]
        if not isinstance(product, dict):
            continue
        artifact_name_token = product.get("artifact_name_token")
        if not isinstance(artifact_name_token, str) or not artifact_name_token:
            continue
        expected_prefix = f"{artifact_name_token}-{{version}}-"
        if not spec.filename_template.startswith(expected_prefix):
            issues.append(
                f"release artifact consumer {spec.consumer_id!r} declares product "
                f"{spec.product_id!r} but filename template "
                f"{spec.filename_template!r} does not use expected product naming "
                f"identity {artifact_name_token!r}"
            )
    if registered_specs != registered:
        issues.append(
            "release artifacts and registered consumers disagree: "
            f"unregistered={sorted(registered_specs - registered)}, "
            f"missing={sorted(registered - registered_specs)}"
        )


def _validate_backlog(
    target_sets: dict[str, set[str]],
    implemented: set[tuple[str, str]],
    products: dict[str, object],
    backlog_text: str,
    issues: list[str],
) -> None:
    for product_id, targets in target_sets.items():
        for platform_id in targets:
            if (product_id, platform_id) in implemented:
                continue
            product = products.get(product_id)
            product_label = (
                product.get("backlog_label") if isinstance(product, dict) else None
            )
            if not isinstance(product_label, str) or not product_label.strip():
                issues.append(f"{product_id} has no canonical backlog_label")
                continue
            gap = f"{product_label} / {PLATFORM_LABELS[platform_id]}"
            if gap not in backlog_text:
                issues.append(
                    f"required unimplemented target is absent from backlog: {gap}"
                )


def _validate_change_governance(text: str, issues: list[str]) -> None:
    normalized = re.sub(r"\s+", " ", text)
    governance_tokens = (
        "product-family/platform support matrix",
        "controlled product-plan contract",
        "product_planning",
        "Missing or broken implementations do not remove a target",
        "workflow jobs, artifacts, and export presets do not add one",
    )
    for token in governance_tokens:
        if token not in normalized:
            issues.append(f"change governance is missing matrix rule: {token}")


def validate_contract(
    policy: dict[str, object],
    workflow_text: str,
    presets_text: str,
    change_governance_text: str,
    rds_text: str,
    backlog_text: str,
    artifact_specs: tuple[ArtifactSpec, ...] = ARTIFACT_SPECS,
) -> list[str]:
    issues: list[str] = []
    contract = policy.get("product_platform_contract")
    if not isinstance(contract, dict):
        return ["policy pack is missing product_platform_contract"]
    platform_ids = _validate_contract_header(contract, issues)
    products, target_sets, identities = _validate_products(
        contract, platform_ids, rds_text, issues
    )
    evidence = _validate_consumers(
        contract,
        products,
        platform_ids,
        target_sets,
        identities,
        workflow_text,
        presets_text,
        issues,
    )
    _validate_artifact_specs(products, evidence, artifact_specs, issues)
    _validate_backlog(target_sets, evidence.implemented, products, backlog_text, issues)
    _validate_change_governance(change_governance_text, issues)
    return issues


def main() -> int:
    policy = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
    issues = validate_contract(
        policy,
        WORKFLOW_PATH.read_text(encoding="utf-8"),
        PRESETS_PATH.read_text(encoding="utf-8"),
        CHANGE_GOVERNANCE_PATH.read_text(encoding="utf-8"),
        RDS_PATH.read_text(encoding="utf-8"),
        BACKLOG_PATH.read_text(encoding="utf-8"),
    )
    if issues:
        print("Product/platform matrix validation failed:")
        for issue in issues:
            print(f"- {issue}")
        return 1
    print("Product/platform matrix validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
