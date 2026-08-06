from __future__ import annotations

from pathlib import Path

PATH = Path("tools/governance/resolve_codex_verification.py")
START = "def resolve_request(\n"
END = "\ndef _bullet_lines("

REPLACEMENT = r'''@dataclass(frozen=True)
class _ResolutionContext:
    policy: dict[str, object]
    requirement_order: tuple[str, ...]
    task_type: str
    modifiers: tuple[str, ...]
    affected_layers: tuple[str, ...]
    claims: tuple[Claim, ...]
    typical: tuple[str, ...]
    authorities: tuple[str, ...]


def _build_resolution_context(
    request: dict[str, object], policy_payload: dict[str, object]
) -> _ResolutionContext:
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
    return _ResolutionContext(
        policy=policy_payload,
        requirement_order=requirement_order,
        task_type=task_type,
        modifiers=modifiers,
        affected_layers=affected_layers,
        claims=claims,
        typical=typical,
        authorities=_authorities(policy_payload, task),
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
        task_type=context.task_type,
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
            task_type=context.task_type,
            modifiers=context.modifiers,
            affected_layers=context.affected_layers,
            claims=context.claims,
            typical=context.typical,
            authorities=context.authorities,
            request=request,
        )
    return _resolve_changed_request(context, request)
'''


def main() -> None:
    text = PATH.read_text(encoding="utf-8")
    start = text.index(START)
    end = text.index(END, start)
    PATH.write_text(text[:start] + REPLACEMENT + text[end:], encoding="utf-8")


if __name__ == "__main__":
    main()
