from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
POLICY_PATH = ROOT / "config/project/policy_pack.json"
WORKFLOW_PATH = ROOT / "docs/WORKFLOW_CODEX.md"
BACKLOG_PATH = ROOT / "docs/BACKLOG.md"

RESOLVER_PATH = ROOT / "tools/governance/resolve_codex_verification.py"
TEST_PATH = ROOT / "tests/unit/governance/test_resolve_codex_verification.py"
RESOLVER_REL = "tools/governance/resolve_codex_verification.py"

RESOLVER = r'''from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_POLICY_PATH = PROJECT_ROOT / "config/project/policy_pack.json"

LAYER_REQUIREMENTS: dict[str, tuple[str, ...]] = {
    "documentation": ("documentation",),
    "governance": ("governance_structure",),
    "python": ("python",),
    "godot": ("godot",),
    "native": ("native",),
    "deterministic_state": ("deterministic",),
    "topology": ("deterministic",),
    "parity_contract": ("parity_or_conformance",),
    "integration_boundary": ("integration",),
    "visible_product": ("human_visual",),
    "packaging": ("packaging",),
    "platform": ("platform",),
    "release": ("release_acceptance",),
}


class ResolutionError(ValueError):
    """Raised when a routing request violates the machine contract."""


@dataclass(frozen=True)
class Claim:
    description: str
    requirements: tuple[str, ...]


@dataclass(frozen=True)
class Resolution:
    task_type: str
    workflow_modifiers: tuple[str, ...]
    repository_changed: bool
    affected_layers: tuple[str, ...]
    claims: tuple[Claim, ...]
    typical_verification_requirements: tuple[str, ...]
    omitted_typical_requirements: tuple[tuple[str, str], ...]
    verification_requirements: tuple[str, ...]
    authorities: tuple[str, ...]
    requires_full_repository_gate: bool
    scope_matrix: tuple[tuple[str, tuple[str, ...]], ...]
    checks_run: tuple[str, ...]
    authority_outcome: str
    remaining_risks: tuple[str, ...]
    unverified_areas: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": 1,
            "task_type": self.task_type,
            "workflow_modifiers": list(self.workflow_modifiers),
            "repository_changed": self.repository_changed,
            "affected_layers": list(self.affected_layers),
            "claims": [
                {
                    "description": claim.description,
                    "requirements": list(claim.requirements),
                }
                for claim in self.claims
            ],
            "typical_verification_requirements": list(
                self.typical_verification_requirements
            ),
            "omitted_typical_requirements": {
                requirement: reason
                for requirement, reason in self.omitted_typical_requirements
            },
            "verification_requirements": list(self.verification_requirements),
            "authorities": list(self.authorities),
            "requires_full_repository_gate": self.requires_full_repository_gate,
            "scope_matrix": [
                {"layer": layer, "requirements": list(requirements)}
                for layer, requirements in self.scope_matrix
            ],
            "checks_run": list(self.checks_run),
            "authority_outcome": self.authority_outcome,
            "remaining_risks": list(self.remaining_risks),
            "unverified_areas": list(self.unverified_areas),
        }


def _load_policy(path: Path) -> dict[str, object]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ResolutionError(f"missing policy pack: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ResolutionError(f"invalid policy pack JSON: {exc}") from exc
    if not isinstance(payload, dict):
        raise ResolutionError("policy pack must be a JSON object")
    return payload


def _non_empty_string(value: object, *, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ResolutionError(f"{field} must be a non-empty string")
    return value.strip()


def _string_list(
    value: object,
    *,
    field: str,
    allow_empty: bool = True,
) -> tuple[str, ...]:
    if not isinstance(value, list):
        raise ResolutionError(f"{field} must be a list[str]")
    items = tuple(_non_empty_string(item, field=f"{field}[]") for item in value)
    if not allow_empty and not items:
        raise ResolutionError(f"{field} must not be empty")
    if len(items) != len(set(items)):
        raise ResolutionError(f"{field} must not contain duplicates")
    return items


def _optional_string_list(value: object, *, field: str) -> tuple[str, ...]:
    if value is None:
        return ()
    return _string_list(value, field=field)


def _bool(value: object, *, field: str, default: bool | None = None) -> bool:
    if value is None and default is not None:
        return default
    if not isinstance(value, bool):
        raise ResolutionError(f"{field} must be a boolean")
    return value


def _ordered_subset(values: set[str], order: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(item for item in order if item in values)


def _routing_payload(policy: dict[str, object]) -> dict[str, object]:
    routing = policy.get("codex_routing")
    if not isinstance(routing, dict):
        raise ResolutionError("policy pack missing codex_routing object")
    return routing


def _routing_identifiers(
    routing: dict[str, object], key: str
) -> tuple[str, ...]:
    return _string_list(routing.get(key), field=f"codex_routing.{key}", allow_empty=False)


def _task_spec(
    routing: dict[str, object], task_type: str
) -> dict[str, object]:
    task_types = routing.get("task_types")
    if not isinstance(task_types, dict):
        raise ResolutionError("codex_routing.task_types must be an object")
    task = task_types.get(task_type)
    if not isinstance(task, dict):
        known = ", ".join(sorted(task_types))
        raise ResolutionError(f"unknown task_type {task_type!r}; expected one of: {known}")
    return task


def _validate_known(
    values: tuple[str, ...],
    *,
    known: tuple[str, ...],
    field: str,
) -> None:
    unknown = sorted(set(values) - set(known))
    if unknown:
        raise ResolutionError(f"{field} contains unknown identifiers: {', '.join(unknown)}")


def _claims(
    raw: object,
    *,
    known_requirements: tuple[str, ...],
) -> tuple[Claim, ...]:
    if not isinstance(raw, list):
        raise ResolutionError("claims must be a list[object]")
    claims: list[Claim] = []
    for index, item in enumerate(raw):
        if not isinstance(item, dict):
            raise ResolutionError(f"claims[{index}] must be an object")
        description = _non_empty_string(
            item.get("description"), field=f"claims[{index}].description"
        )
        requirements = _optional_string_list(
            item.get("requirements"), field=f"claims[{index}].requirements"
        )
        _validate_known(
            requirements,
            known=known_requirements,
            field=f"claims[{index}].requirements",
        )
        claims.append(Claim(description=description, requirements=requirements))
    return tuple(claims)


def _omissions(
    raw: object,
    *,
    typical: tuple[str, ...],
) -> dict[str, str]:
    if raw is None:
        return {}
    if not isinstance(raw, dict):
        raise ResolutionError("omitted_typical_requirements must be an object")
    omissions: dict[str, str] = {}
    for requirement, reason in raw.items():
        key = _non_empty_string(requirement, field="omitted_typical_requirements key")
        if key not in typical:
            raise ResolutionError(
                f"omitted_typical_requirements references non-typical requirement: {key}"
            )
        omissions[key] = _non_empty_string(
            reason, field=f"omitted_typical_requirements.{key}"
        )
    return omissions


def _authorities(
    policy: dict[str, object], task: dict[str, object]
) -> tuple[str, ...]:
    authority_model = policy.get("authority_model")
    if not isinstance(authority_model, dict):
        raise ResolutionError("policy pack missing authority_model object")
    resolved: list[str] = []
    authority_keys = task.get("authority_keys", [])
    if not isinstance(authority_keys, list):
        raise ResolutionError("task authority_keys must be a list")
    for key in authority_keys:
        if not isinstance(key, str) or not isinstance(authority_model.get(key), str):
            raise ResolutionError(f"task references invalid authority key: {key!r}")
        resolved.append(str(authority_model[key]))
    dispatch_paths = task.get("dispatch_paths", [])
    if not isinstance(dispatch_paths, list) or not all(
        isinstance(path, str) for path in dispatch_paths
    ):
        raise ResolutionError("task dispatch_paths must be a list[str]")
    resolved.extend(dispatch_paths)
    return tuple(dict.fromkeys(resolved))


def _scope_matrix(
    affected_layers: tuple[str, ...],
    *,
    requirement_order: tuple[str, ...],
) -> tuple[tuple[str, tuple[str, ...]], ...]:
    return tuple(
        (
            layer,
            _ordered_subset(set(LAYER_REQUIREMENTS[layer]), requirement_order),
        )
        for layer in affected_layers
    )


def _review_only_resolution(
    *,
    task_type: str,
    modifiers: tuple[str, ...],
    affected_layers: tuple[str, ...],
    claims: tuple[Claim, ...],
    typical: tuple[str, ...],
    authorities: tuple[str, ...],
    request: dict[str, object],
) -> Resolution:
    if _bool(request.get("repository_changed"), field="repository_changed", default=False):
        raise ResolutionError("review_only is invalid when repository_changed is true")
    if "cross_layer" in modifiers or "verification_failure" in modifiers:
        raise ResolutionError(
            "review_only cannot be combined with cross_layer or verification_failure"
        )
    extra = _optional_string_list(
        request.get("additional_verification_requirements"),
        field="additional_verification_requirements",
    )
    if extra or any(claim.requirements for claim in claims):
        raise ResolutionError(
            "review_only cannot include executable verification requirements"
        )
    if _bool(
        request.get("requires_full_repository_gate"),
        field="requires_full_repository_gate",
        default=False,
    ):
        raise ResolutionError("review_only cannot require the full repository gate")
    omissions = tuple(
        (requirement, "review-only; tracked repository state is unchanged")
        for requirement in typical
    )
    return Resolution(
        task_type=task_type,
        workflow_modifiers=modifiers,
        repository_changed=False,
        affected_layers=affected_layers,
        claims=claims,
        typical_verification_requirements=typical,
        omitted_typical_requirements=omissions,
        verification_requirements=(),
        authorities=authorities,
        requires_full_repository_gate=False,
        scope_matrix=(),
        checks_run=_optional_string_list(request.get("checks_run"), field="checks_run"),
        authority_outcome=_non_empty_string(
            request.get("authority_outcome", "No authority change."),
            field="authority_outcome",
        ),
        remaining_risks=_optional_string_list(
            request.get("remaining_risks"), field="remaining_risks"
        ),
        unverified_areas=_optional_string_list(
            request.get("unverified_areas"), field="unverified_areas"
        ),
    )


def resolve_request(
    request: dict[str, object],
    *,
    policy: dict[str, object] | None = None,
) -> Resolution:
    if not isinstance(request, dict):
        raise ResolutionError("request must be a JSON object")
    policy_payload = policy if policy is not None else _load_policy(DEFAULT_POLICY_PATH)
    routing = _routing_payload(policy_payload)
    modifier_order = _routing_identifiers(routing, "workflow_modifiers")
    requirement_order = _routing_identifiers(routing, "verification_requirements")

    task_type = _non_empty_string(request.get("task_type"), field="task_type")
    task = _task_spec(routing, task_type)
    modifiers = _optional_string_list(
        request.get("workflow_modifiers"), field="workflow_modifiers"
    )
    _validate_known(modifiers, known=modifier_order, field="workflow_modifiers")
    modifiers = _ordered_subset(set(modifiers), modifier_order)

    affected_layers = _optional_string_list(
        request.get("affected_layers"), field="affected_layers"
    )
    unknown_layers = sorted(set(affected_layers) - set(LAYER_REQUIREMENTS))
    if unknown_layers:
        raise ResolutionError(
            f"affected_layers contains unknown identifiers: {', '.join(unknown_layers)}"
        )
    claims = _claims(
        request.get("claims", []), known_requirements=requirement_order
    )
    typical = _string_list(
        task.get("typical_verification_requirements"),
        field=f"codex_routing.task_types.{task_type}.typical_verification_requirements",
        allow_empty=False,
    )
    _validate_known(typical, known=requirement_order, field="typical requirements")
    authorities = _authorities(policy_payload, task)

    if "review_only" in modifiers:
        return _review_only_resolution(
            task_type=task_type,
            modifiers=modifiers,
            affected_layers=affected_layers,
            claims=claims,
            typical=typical,
            authorities=authorities,
            request=request,
        )

    repository_changed = _bool(
        request.get("repository_changed"), field="repository_changed", default=True
    )
    if not repository_changed:
        raise ResolutionError(
            "repository_changed=false requires the review_only workflow modifier"
        )
    if not affected_layers:
        raise ResolutionError("repository-changing work requires affected_layers")
    if not claims:
        raise ResolutionError("repository-changing work requires at least one claim")

    omissions = _omissions(
        request.get("omitted_typical_requirements"), typical=typical
    )
    requirements = set(typical) - set(omissions)
    for layer in affected_layers:
        requirements.update(LAYER_REQUIREMENTS[layer])
    for claim in claims:
        requirements.update(claim.requirements)
    additional = _optional_string_list(
        request.get("additional_verification_requirements"),
        field="additional_verification_requirements",
    )
    _validate_known(
        additional,
        known=requirement_order,
        field="additional_verification_requirements",
    )
    requirements.update(additional)

    if "cross_layer" in modifiers:
        if len(affected_layers) < 2:
            raise ResolutionError(
                "cross_layer requires at least two distinct affected_layers"
            )
        requirements.add("integration")

    reintroduced = sorted(set(omissions) & requirements)
    if reintroduced:
        raise ResolutionError(
            "omitted typical requirements are still required by the change: "
            + ", ".join(reintroduced)
        )
    if not requirements:
        raise ResolutionError(
            "repository-changing work cannot resolve to an empty verification set"
        )

    return Resolution(
        task_type=task_type,
        workflow_modifiers=modifiers,
        repository_changed=True,
        affected_layers=affected_layers,
        claims=claims,
        typical_verification_requirements=typical,
        omitted_typical_requirements=tuple(
            (requirement, omissions[requirement])
            for requirement in requirement_order
            if requirement in omissions
        ),
        verification_requirements=_ordered_subset(requirements, requirement_order),
        authorities=authorities,
        requires_full_repository_gate=_bool(
            request.get("requires_full_repository_gate"),
            field="requires_full_repository_gate",
            default=False,
        ),
        scope_matrix=(
            _scope_matrix(affected_layers, requirement_order=requirement_order)
            if "cross_layer" in modifiers
            else ()
        ),
        checks_run=_optional_string_list(request.get("checks_run"), field="checks_run"),
        authority_outcome=_non_empty_string(
            request.get("authority_outcome", "No authority change."),
            field="authority_outcome",
        ),
        remaining_risks=_optional_string_list(
            request.get("remaining_risks"), field="remaining_risks"
        ),
        unverified_areas=_optional_string_list(
            request.get("unverified_areas"), field="unverified_areas"
        ),
    )


def _bullet_lines(values: tuple[str, ...], *, empty: str) -> list[str]:
    return [f"- {value}" for value in values] if values else [f"- {empty}"]


def render_markdown(resolution: Resolution) -> str:
    modifiers = ", ".join(resolution.workflow_modifiers) or "none"
    layers = ", ".join(resolution.affected_layers) or "none"
    requirements = ", ".join(resolution.verification_requirements) or "none"
    lines = [
        f"Task type: `{resolution.task_type}`",
        f"Workflow modifiers: {modifiers}",
        f"Repository changed: {'yes' if resolution.repository_changed else 'no'}",
        f"Affected layers: {layers}",
        "",
        "Claims made:",
    ]
    lines.extend(
        _bullet_lines(
            tuple(
                f"{claim.description}"
                + (
                    " [requirements: " + ", ".join(claim.requirements) + "]"
                    if claim.requirements
                    else ""
                )
                for claim in resolution.claims
            ),
            empty="none",
        )
    )
    lines.extend(["", f"Verification requirements: {requirements}", "", "Authorities consulted:"])
    lines.extend(_bullet_lines(resolution.authorities, empty="none"))
    lines.extend(["", "Checks run:"])
    lines.extend(_bullet_lines(resolution.checks_run, empty="not yet recorded"))
    lines.extend(["", "Typical checks not run:"])
    lines.extend(
        _bullet_lines(
            tuple(
                f"{requirement}: {reason}"
                for requirement, reason in resolution.omitted_typical_requirements
            ),
            empty="none",
        )
    )
    lines.extend(
        [
            "",
            "Full repository gate required: "
            + ("yes" if resolution.requires_full_repository_gate else "no"),
            "",
            "Scope matrix:",
        ]
    )
    if resolution.scope_matrix:
        lines.extend(["", "| Layer | Required verification |", "| --- | --- |"])
        lines.extend(
            f"| `{layer}` | {', '.join(requirements) or 'none'} |"
            for layer, requirements in resolution.scope_matrix
        )
    else:
        lines.append("- not applicable")
    lines.extend(
        [
            "",
            "Authority reused, transferred, or established:",
            f"- {resolution.authority_outcome}",
            "",
            "Remaining risks:",
        ]
    )
    lines.extend(_bullet_lines(resolution.remaining_risks, empty="none recorded"))
    lines.extend(["", "Unverified areas:"])
    lines.extend(_bullet_lines(resolution.unverified_areas, empty="none recorded"))
    return "\n".join(lines).rstrip() + "\n"


def _load_request(path: str) -> dict[str, object]:
    if path == "-":
        raw = sys.stdin.read()
    else:
        raw = Path(path).read_text(encoding="utf-8")
    try:
        payload: Any = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ResolutionError(f"invalid request JSON: {exc}") from exc
    if not isinstance(payload, dict):
        raise ResolutionError("request must be a JSON object")
    return payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Resolve Tet4D Codex task routing and verification requirements."
    )
    parser.add_argument("request", help="request JSON file, or - for stdin")
    parser.add_argument(
        "--policy",
        type=Path,
        default=DEFAULT_POLICY_PATH,
        help="policy pack path",
    )
    parser.add_argument(
        "--format", choices=("json", "markdown"), default="json"
    )
    args = parser.parse_args(argv)
    try:
        resolution = resolve_request(
            _load_request(args.request), policy=_load_policy(args.policy)
        )
    except (OSError, ResolutionError) as exc:
        print(f"verification resolution failed: {exc}", file=sys.stderr)
        return 2
    if args.format == "markdown":
        sys.stdout.write(render_markdown(resolution))
    else:
        print(json.dumps(resolution.to_dict(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'''

TESTS = r'''from __future__ import annotations

import copy

import pytest

from tools.governance.resolve_codex_verification import (
    ResolutionError,
    render_markdown,
    resolve_request,
)


def _policy() -> dict[str, object]:
    return {
        "authority_model": {
            "machine_authority": "config/project/policy_pack.json",
            "architecture_contract": "docs/ARCHITECTURE_CONTRACT.md",
            "subsystem_authority_map": "docs/architecture/authority_map.md",
        },
        "codex_routing": {
            "schema_version": 1,
            "task_types": {
                "product_planning": {
                    "authority_keys": ["machine_authority"],
                    "typical_verification_requirements": ["documentation"],
                },
                "native_deterministic_core": {
                    "authority_keys": [
                        "architecture_contract",
                        "subsystem_authority_map",
                    ],
                    "dispatch_paths": ["native/AGENTS.md"],
                    "typical_verification_requirements": [
                        "native",
                        "deterministic",
                    ],
                },
                "packaging_and_release": {
                    "dispatch_paths": ["docs/rds/RDS_PACKAGING.md"],
                    "typical_verification_requirements": [
                        "packaging",
                        "platform",
                    ],
                },
            },
            "workflow_modifiers": [
                "review_only",
                "staged_handoff",
                "cross_layer",
                "verification_failure",
            ],
            "verification_requirements": [
                "documentation",
                "governance_structure",
                "python",
                "godot",
                "native",
                "deterministic",
                "parity_or_conformance",
                "integration",
                "human_visual",
                "packaging",
                "platform",
                "release_acceptance",
            ],
        },
    }


def _request(**overrides: object) -> dict[str, object]:
    request: dict[str, object] = {
        "task_type": "native_deterministic_core",
        "workflow_modifiers": [],
        "repository_changed": True,
        "affected_layers": ["native"],
        "claims": [
            {
                "description": "Change deterministic native behaviour.",
                "requirements": ["deterministic"],
            }
        ],
    }
    request.update(overrides)
    return request


def test_review_only_resolves_to_empty_requirements() -> None:
    result = resolve_request(
        {
            "task_type": "product_planning",
            "workflow_modifiers": ["review_only"],
            "repository_changed": False,
            "affected_layers": ["documentation"],
            "claims": [{"description": "Review programme routing."}],
        },
        policy=_policy(),
    )
    assert result.verification_requirements == ()
    assert dict(result.omitted_typical_requirements) == {
        "documentation": "review-only; tracked repository state is unchanged"
    }


def test_review_only_rejects_repository_change() -> None:
    with pytest.raises(ResolutionError, match="repository_changed"):
        resolve_request(
            {
                "task_type": "product_planning",
                "workflow_modifiers": ["review_only"],
                "repository_changed": True,
                "claims": [{"description": "Review."}],
            },
            policy=_policy(),
        )


def test_review_only_rejects_executable_requirements() -> None:
    with pytest.raises(ResolutionError, match="executable"):
        resolve_request(
            {
                "task_type": "product_planning",
                "workflow_modifiers": ["review_only"],
                "repository_changed": False,
                "claims": [
                    {
                        "description": "Review.",
                        "requirements": ["documentation"],
                    }
                ],
            },
            policy=_policy(),
        )


def test_repository_change_requires_affected_layers() -> None:
    with pytest.raises(ResolutionError, match="affected_layers"):
        resolve_request(_request(affected_layers=[]), policy=_policy())


def test_repository_change_requires_claim() -> None:
    with pytest.raises(ResolutionError, match="at least one claim"):
        resolve_request(_request(claims=[]), policy=_policy())


def test_typical_requirements_are_included() -> None:
    result = resolve_request(_request(), policy=_policy())
    assert result.verification_requirements == ("native", "deterministic")


def test_omitted_typical_requirement_requires_rationale() -> None:
    with pytest.raises(ResolutionError, match="non-empty string"):
        resolve_request(
            _request(omitted_typical_requirements={"native": ""}),
            policy=_policy(),
        )


def test_omitted_requirement_cannot_be_reintroduced_by_layer() -> None:
    with pytest.raises(ResolutionError, match="still required"):
        resolve_request(
            _request(omitted_typical_requirements={"native": "Not applicable."}),
            policy=_policy(),
        )


def test_changed_layers_add_requirements() -> None:
    result = resolve_request(
        _request(affected_layers=["native", "godot"]), policy=_policy()
    )
    assert result.verification_requirements == (
        "godot",
        "native",
        "deterministic",
    )


def test_claim_requirements_compose_by_union() -> None:
    result = resolve_request(
        _request(
            claims=[
                {
                    "description": "Expose a native contract.",
                    "requirements": ["parity_or_conformance"],
                }
            ]
        ),
        policy=_policy(),
    )
    assert result.verification_requirements == (
        "native",
        "deterministic",
        "parity_or_conformance",
    )


def test_cross_layer_requires_two_layers() -> None:
    with pytest.raises(ResolutionError, match="at least two"):
        resolve_request(
            _request(workflow_modifiers=["cross_layer"]), policy=_policy()
        )


def test_cross_layer_adds_integration_and_scope_matrix() -> None:
    result = resolve_request(
        _request(
            workflow_modifiers=["cross_layer"],
            affected_layers=["native", "godot"],
            claims=[
                {
                    "description": "Expose native behaviour to Godot.",
                    "requirements": ["parity_or_conformance"],
                }
            ],
        ),
        policy=_policy(),
    )
    assert result.verification_requirements == (
        "godot",
        "native",
        "deterministic",
        "parity_or_conformance",
        "integration",
    )
    assert result.scope_matrix == (
        ("native", ("native",)),
        ("godot", ("godot",)),
    )


def test_platform_and_release_requirements_are_independent() -> None:
    result = resolve_request(
        {
            "task_type": "packaging_and_release",
            "workflow_modifiers": [],
            "repository_changed": True,
            "affected_layers": ["platform", "release"],
            "claims": [
                {
                    "description": "Accept a release candidate.",
                    "requirements": ["release_acceptance"],
                }
            ],
        },
        policy=_policy(),
    )
    assert result.verification_requirements == (
        "packaging",
        "platform",
        "release_acceptance",
    )


def test_packaging_prose_can_resolve_to_documentation_only() -> None:
    result = resolve_request(
        {
            "task_type": "packaging_and_release",
            "workflow_modifiers": [],
            "repository_changed": True,
            "affected_layers": ["documentation"],
            "claims": [{"description": "Clarify packaging prose."}],
            "omitted_typical_requirements": {
                "packaging": "No executable packaging files changed.",
                "platform": "No platform behaviour is claimed.",
            },
        },
        policy=_policy(),
    )
    assert result.verification_requirements == ("documentation",)


def test_full_gate_override_is_preserved() -> None:
    result = resolve_request(
        _request(requires_full_repository_gate=True), policy=_policy()
    )
    assert result.requires_full_repository_gate is True


def test_unknown_task_type_is_rejected() -> None:
    with pytest.raises(ResolutionError, match="unknown task_type"):
        resolve_request(_request(task_type="other"), policy=_policy())


def test_unknown_modifier_is_rejected() -> None:
    with pytest.raises(ResolutionError, match="unknown identifiers"):
        resolve_request(
            _request(workflow_modifiers=["other"]), policy=_policy()
        )


def test_unknown_layer_is_rejected() -> None:
    with pytest.raises(ResolutionError, match="affected_layers"):
        resolve_request(_request(affected_layers=["other"]), policy=_policy())


def test_unknown_requirement_is_rejected() -> None:
    with pytest.raises(ResolutionError, match="unknown identifiers"):
        resolve_request(
            _request(additional_verification_requirements=["other"]),
            policy=_policy(),
        )


def test_resolution_order_is_stable() -> None:
    request = _request(
        workflow_modifiers=["cross_layer", "staged_handoff"],
        affected_layers=["godot", "native"],
        additional_verification_requirements=["documentation"],
    )
    first = resolve_request(copy.deepcopy(request), policy=_policy()).to_dict()
    second = resolve_request(copy.deepcopy(request), policy=_policy()).to_dict()
    assert first == second
    assert first["workflow_modifiers"] == ["staged_handoff", "cross_layer"]


def test_markdown_report_contains_completion_fields() -> None:
    result = resolve_request(
        _request(
            checks_run=["native tests passed"],
            authority_outcome="Reused existing native authority.",
            remaining_risks=["Visible consumer review remains."],
            unverified_areas=["Windows packaging."],
        ),
        policy=_policy(),
    )
    rendered = render_markdown(result)
    assert "Task type:" in rendered
    assert "Checks run:" in rendered
    assert "Typical checks not run:" in rendered
    assert "Authority reused, transferred, or established:" in rendered
    assert "Remaining risks:" in rendered
    assert "Unverified areas:" in rendered
'''

WORKFLOW_INSERT = '''### Machine resolver

Use the policy-backed resolver to turn a task declaration into a stable
verification decision and completion-report skeleton:

```bash
python tools/governance/resolve_codex_verification.py request.json --format json
python tools/governance/resolve_codex_verification.py request.json --format markdown
```

The request records one primary task type, modifiers, repository-change status,
affected layers, claims with any explicit evidence obligations, additional
requirements, justified omissions of typical requirements, and the full-gate
override. The resolver loads `policy_pack.json`; callers must not copy the task
or requirement inventories into a second configuration.

The resolver enforces these invariants:

- `review_only` requires `repository_changed=false`, no executable evidence
  requirements, and no full gate;
- repository-changing work requires affected layers, at least one claim, and a
  non-empty verification set;
- `cross_layer` requires at least two affected layers, adds `integration`, and
  emits a scope matrix;
- omitted typical requirements need a non-empty rationale and may not be
  reintroduced by the actual layers or claims;
- deterministic, integration, platform, and release obligations remain
  independent members of the union.

Resolver output selects evidence obligations; it does not claim that checks
have passed. Completion reports must populate checks, authority effects,
remaining risks, and unverified areas with actual final evidence.

'''


def _write_sources() -> None:
    RESOLVER_PATH.parent.mkdir(parents=True, exist_ok=True)
    TEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESOLVER_PATH.write_text(RESOLVER, encoding="utf-8")
    TEST_PATH.write_text(TESTS, encoding="utf-8")


def _update_policy() -> None:
    payload = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
    routing = payload["codex_routing"]
    routing["resolver_path"] = RESOLVER_REL
    required = payload["maintenance_contract"]["required_paths"]
    inserted = False
    for paths in required.values():
        if not isinstance(paths, list):
            continue
        if "tools/governance/validate_project_contracts.py" in paths:
            if RESOLVER_REL not in paths:
                index = paths.index("tools/governance/validate_project_contracts.py") + 1
                paths.insert(index, RESOLVER_REL)
            inserted = True
            break
    if not inserted:
        raise RuntimeError("could not locate governance required-path group")
    POLICY_PATH.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _update_workflow() -> None:
    text = WORKFLOW_PATH.read_text(encoding="utf-8")
    marker = "\n\n## Stable change classes\n"
    if marker not in text:
        raise RuntimeError("workflow insertion marker missing")
    if "### Machine resolver" not in text:
        text = text.replace(marker, "\n\n" + WORKFLOW_INSERT + "## Stable change classes\n", 1)
    WORKFLOW_PATH.write_text(text, encoding="utf-8")


def _update_backlog() -> None:
    text = BACKLOG_PATH.read_text(encoding="utf-8")
    old = '''Accepted follow-ups:

- **Slice B — verification resolver and completion reporting:** consume the
  routing model, enforce read-only exclusivity and non-empty verification for
  repository changes, compose requirements by union, and produce stable reports.
- **Slice C — path-sensitive CI lanes:** map resolved requirements to explicit
'''
    new = '''Slice B is implemented: the policy-backed resolver consumes the routing model,
enforces read-only and repository-change invariants, composes requirements by
union, emits scope matrices, and renders stable JSON or Markdown reports.

Accepted follow-up:

- **Slice C — path-sensitive CI lanes:** map resolved requirements to explicit
'''
    if old not in text:
        raise RuntimeError("backlog Slice B marker missing")
    BACKLOG_PATH.write_text(text.replace(old, new, 1), encoding="utf-8")


def main() -> None:
    _write_sources()
    _update_policy()
    _update_workflow()
    _update_backlog()


if __name__ == "__main__":
    main()
