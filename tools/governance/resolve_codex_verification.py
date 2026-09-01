from __future__ import annotations

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
    routes: tuple[str, ...]
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
            "schema_version": 2,
            "routes": list(self.routes),
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


def _routing_identifiers(routing: dict[str, object], key: str) -> tuple[str, ...]:
    return _string_list(
        routing.get(key), field=f"codex_routing.{key}", allow_empty=False
    )


def _route_specs(
    routing: dict[str, object], routes: tuple[str, ...]
) -> tuple[dict[str, object], ...]:
    route_specs = routing.get("routes")
    if not isinstance(route_specs, dict):
        raise ResolutionError("codex_routing.routes must be an object")
    unknown = sorted(set(routes) - set(route_specs))
    if unknown:
        raise ResolutionError(
            f"routes contains unknown identifiers: {', '.join(unknown)}"
        )
    specs: list[dict[str, object]] = []
    for route in routes:
        spec = route_specs[route]
        if not isinstance(spec, dict):
            raise ResolutionError(f"codex_routing.routes.{route} must be an object")
        specs.append(spec)
    return tuple(specs)


def _validate_known(
    values: tuple[str, ...],
    *,
    known: tuple[str, ...],
    field: str,
) -> None:
    unknown = sorted(set(values) - set(known))
    if unknown:
        raise ResolutionError(
            f"{field} contains unknown identifiers: {', '.join(unknown)}"
        )


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
    policy: dict[str, object], route_specs: tuple[dict[str, object], ...]
) -> tuple[str, ...]:
    authority_model = policy.get("authority_model")
    if not isinstance(authority_model, dict):
        raise ResolutionError("policy pack missing authority_model object")
    resolved: list[str] = []
    for spec in route_specs:
        authority_keys = spec.get("authority_keys", [])
        if not isinstance(authority_keys, list):
            raise ResolutionError("route authority_keys must be a list")
        for key in authority_keys:
            if not isinstance(key, str) or not isinstance(
                authority_model.get(key), str
            ):
                raise ResolutionError(
                    f"route references invalid authority key: {key!r}"
                )
            resolved.append(str(authority_model[key]))
        dispatch_paths = spec.get("dispatch_paths", [])
        if not isinstance(dispatch_paths, list) or not all(
            isinstance(path, str) for path in dispatch_paths
        ):
            raise ResolutionError("route dispatch_paths must be a list[str]")
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
    routes: tuple[str, ...],
    modifiers: tuple[str, ...],
    affected_layers: tuple[str, ...],
    claims: tuple[Claim, ...],
    typical: tuple[str, ...],
    authorities: tuple[str, ...],
    request: dict[str, object],
) -> Resolution:
    if _bool(
        request.get("repository_changed"), field="repository_changed", default=False
    ):
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
        routes=routes,
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


@dataclass(frozen=True)
class _ResolutionContext:
    policy: dict[str, object]
    requirement_order: tuple[str, ...]
    routes: tuple[str, ...]
    modifiers: tuple[str, ...]
    affected_layers: tuple[str, ...]
    claims: tuple[Claim, ...]
    typical: tuple[str, ...]
    authorities: tuple[str, ...]


def _build_resolution_context(
    request: dict[str, object], policy_payload: dict[str, object]
) -> _ResolutionContext:
    routing = _routing_payload(policy_payload)
    route_specs_raw = routing.get("routes")
    if not isinstance(route_specs_raw, dict):
        raise ResolutionError("codex_routing.routes must be an object")
    route_order = tuple(route_specs_raw)
    modifier_order = _routing_identifiers(routing, "workflow_modifiers")
    requirement_order = _routing_identifiers(routing, "verification_requirements")
    routes = _optional_string_list(request.get("routes"), field="routes")
    _validate_known(routes, known=route_order, field="routes")
    routes = _ordered_subset(set(routes), route_order)
    route_specs = _route_specs(routing, routes)

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

    claims = _claims(request.get("claims", []), known_requirements=requirement_order)
    typical_set: set[str] = set()
    for route, spec in zip(routes, route_specs, strict=True):
        route_typical = _string_list(
            spec.get("typical_verification_requirements"),
            field=f"codex_routing.routes.{route}.typical_verification_requirements",
            allow_empty=False,
        )
        _validate_known(
            route_typical, known=requirement_order, field="typical requirements"
        )
        typical_set.update(route_typical)
    typical = _ordered_subset(typical_set, requirement_order)
    return _ResolutionContext(
        policy=policy_payload,
        requirement_order=requirement_order,
        routes=routes,
        modifiers=modifiers,
        affected_layers=affected_layers,
        claims=claims,
        typical=typical,
        authorities=_authorities(policy_payload, route_specs),
    )


def _changed_requirements(
    context: _ResolutionContext,
    request: dict[str, object],
    omissions: dict[str, str],
) -> set[str]:
    requirements = set(context.typical) - set(omissions)
    for layer in context.affected_layers:
        requirements.update(LAYER_REQUIREMENTS[layer])
    for claim in context.claims:
        requirements.update(claim.requirements)

    additional = _optional_string_list(
        request.get("additional_verification_requirements"),
        field="additional_verification_requirements",
    )
    _validate_known(
        additional,
        known=context.requirement_order,
        field="additional_verification_requirements",
    )
    requirements.update(additional)

    if "cross_layer" in context.modifiers:
        if len(context.affected_layers) < 2:
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
    return requirements


def _resolve_changed_request(
    context: _ResolutionContext, request: dict[str, object]
) -> Resolution:
    repository_changed = _bool(
        request.get("repository_changed"), field="repository_changed", default=True
    )
    if not repository_changed:
        raise ResolutionError(
            "repository_changed=false requires the review_only workflow modifier"
        )
    if not context.affected_layers:
        raise ResolutionError("repository-changing work requires affected_layers")
    if not context.claims:
        raise ResolutionError("repository-changing work requires at least one claim")

    omissions = _omissions(
        request.get("omitted_typical_requirements"), typical=context.typical
    )
    requirements = _changed_requirements(context, request, omissions)
    return Resolution(
        routes=context.routes,
        workflow_modifiers=context.modifiers,
        repository_changed=True,
        affected_layers=context.affected_layers,
        claims=context.claims,
        typical_verification_requirements=context.typical,
        omitted_typical_requirements=tuple(
            (requirement, omissions[requirement])
            for requirement in context.requirement_order
            if requirement in omissions
        ),
        verification_requirements=_ordered_subset(
            requirements, context.requirement_order
        ),
        authorities=context.authorities,
        requires_full_repository_gate=_bool(
            request.get("requires_full_repository_gate"),
            field="requires_full_repository_gate",
            default=False,
        ),
        scope_matrix=(
            _scope_matrix(
                context.affected_layers,
                requirement_order=context.requirement_order,
            )
            if "cross_layer" in context.modifiers
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


def resolve_request(
    request: dict[str, object],
    *,
    policy: dict[str, object] | None = None,
) -> Resolution:
    if not isinstance(request, dict):
        raise ResolutionError("request must be a JSON object")
    policy_payload = policy if policy is not None else _load_policy(DEFAULT_POLICY_PATH)
    context = _build_resolution_context(request, policy_payload)
    if "review_only" in context.modifiers:
        return _review_only_resolution(
            routes=context.routes,
            modifiers=context.modifiers,
            affected_layers=context.affected_layers,
            claims=context.claims,
            typical=context.typical,
            authorities=context.authorities,
            request=request,
        )
    return _resolve_changed_request(context, request)


def _bullet_lines(values: tuple[str, ...], *, empty: str) -> list[str]:
    return [f"- {value}" for value in values] if values else [f"- {empty}"]


def render_markdown(resolution: Resolution) -> str:
    modifiers = ", ".join(resolution.workflow_modifiers) or "none"
    layers = ", ".join(resolution.affected_layers) or "none"
    requirements = ", ".join(resolution.verification_requirements) or "none"
    routes = ", ".join(resolution.routes) or "none"
    lines = [
        f"Routes: {routes}",
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
    lines.extend(
        ["", f"Verification requirements: {requirements}", "", "Authorities consulted:"]
    )
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
    parser.add_argument("--format", choices=("json", "markdown"), default="json")
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
