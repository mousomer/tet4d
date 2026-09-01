from __future__ import annotations

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
            "schema_version": 2,
            "routes": {
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
        "routes": ["native_deterministic_core"],
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
            "routes": ["product_planning"],
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
                "routes": ["product_planning"],
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
                "routes": ["product_planning"],
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


def test_native_and_packaging_routes_compose_by_union() -> None:
    result = resolve_request(
        _request(routes=["native_deterministic_core", "packaging_and_release"]),
        policy=_policy(),
    )
    assert result.routes == ("native_deterministic_core", "packaging_and_release")
    assert result.verification_requirements == (
        "native",
        "deterministic",
        "packaging",
        "platform",
    )
    assert result.authorities == (
        "docs/ARCHITECTURE_CONTRACT.md",
        "docs/architecture/authority_map.md",
        "native/AGENTS.md",
        "docs/rds/RDS_PACKAGING.md",
    )


def test_zero_routes_still_uses_diff_claim_and_verification_floor() -> None:
    result = resolve_request(
        _request(
            routes=[],
            affected_layers=["documentation"],
            claims=[{"description": "Clarify documentation."}],
        ),
        policy=_policy(),
    )
    assert result.routes == ()
    assert result.typical_verification_requirements == ()
    assert result.verification_requirements == ("documentation",)


def test_zero_routes_cannot_bypass_repository_change_floor() -> None:
    with pytest.raises(ResolutionError, match="affected_layers"):
        resolve_request(_request(routes=[], affected_layers=[]), policy=_policy())


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
        resolve_request(_request(workflow_modifiers=["cross_layer"]), policy=_policy())


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
            "routes": ["packaging_and_release"],
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
            "routes": ["packaging_and_release"],
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


def test_unknown_route_is_rejected() -> None:
    with pytest.raises(ResolutionError, match="routes contains unknown"):
        resolve_request(_request(routes=["other"]), policy=_policy())


def test_unknown_modifier_is_rejected() -> None:
    with pytest.raises(ResolutionError, match="unknown identifiers"):
        resolve_request(_request(workflow_modifiers=["other"]), policy=_policy())


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
    assert "Routes:" in rendered
    assert "Checks run:" in rendered
    assert "Typical checks not run:" in rendered
    assert "Authority reused, transferred, or established:" in rendered
    assert "Remaining risks:" in rendered
    assert "Unverified areas:" in rendered
