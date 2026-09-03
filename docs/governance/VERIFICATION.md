# Verification

Canonical owner: test strategy, evidence composition, focused checks, full-gate
triggers, and verification reporting.

## Evidence model

Verification is a set, not a ladder. Start from every selected route's default
evidence, then union requirements from the actual diff, behavioural claims,
affected layers, compatibility contracts, authority boundaries, and workflow
modifiers. Remove a route default only when it is demonstrably inapplicable and
record the reason. A repository-changing task must never resolve to an empty
set.

The stable evidence vocabulary is:

`documentation`, `governance_structure`, `python`, `godot`, `native`,
`deterministic`, `parity_or_conformance`, `integration`, `human_visual`,
`packaging`, `platform`, `platform_macos`, `platform_windows`,
`platform_linux`, `platform_android`, `platform_ipados`, and
`release_acceptance`.

`review_only` is valid only when tracked repository state is unchanged and no
executable evidence or full gate is required. `cross_layer` requires at least
two affected layers, a scope matrix, provider and consumer checks, and
`integration` evidence. Deterministic, integration, platform, and release
evidence remain independent members of the union.

Hard triggers remain independent of route labels:

- deterministic behaviour changes require deterministic evidence;
- replay, trace, schema, or identity changes require compatibility and replay
  evidence;
- a real-platform claim requires evidence from that real platform;
- a release claim requires packaging, platform, and release evidence;
- a visual or usability claim requiring human judgment needs human evidence,
  reported separately from automated checks;
- an authority change requires the authority-transfer or establishment
  protocol and its conformance evidence.

Use the policy-backed resolver for a stable decision and report skeleton:

```bash
python tools/governance/resolve_codex_verification.py request.json --format json
python tools/governance/resolve_codex_verification.py request.json --format markdown
```

## Platform evidence identity

`platform` is a family label, not a platform. Machine evidence must name the
platform it proves, and `platform` never resolves to a default one. A
resolution naming `platform` without at least one explicit `platform_<id>`
member is rejected by `tools/governance/select_codex_ci_lanes.py`, so a macOS
package can never stand in for iPadOS, Windows, Android, or Linux evidence.

`config/project/codex_ci_lanes.json` owns the routing. `path_classification`
maps a changed path to the platforms it actually affects;
`platform_evidence.hosted_lanes` binds each hosted platform requirement to the
CI job, packaging consumer, and canonical toolchain command that exercise it;
`platform_evidence.unhosted_platform_requirements` names the platforms with no
hosted lane. Unhosted platform evidence is declared manual and reported as
outstanding, never satisfied by another platform's job. Platform identifiers
come from the `product_platform_contract`: CI selects evidence and never adds,
removes, or promotes a product/platform target, and a hosted lane claims only
the boundary it runs. Hosted final link is not physical-device acceptance.

Selection stays proportional: a changed path selects its own layers and its own
platform, and nothing more. Only an unmatched path forces the full repository
gate. That fail-safe is deliberate — repair a missing classification rule, never
the fallback.

## Test obligations

- Tests assert behaviour, invariants, regressions, errors, or parity—not merely
  line execution. Never weaken or delete tests to fit an implementation.
- Inherited native ports identify the Python/reference oracle, deterministic
  inputs, expected output, comparison mode, fixtures, edge cases, exclusions,
  and fallback. Visual Godot success is not semantic parity.
- New deterministic behaviour uses conformance tests against its normative
  contract; it does not require an artificial Python predecessor.
- Native core logic needs normal, boundary, invalid-input, regression, and
  applicable parity/conformance tests. Godot changes need adapter/product tests
  and manual visual evidence when visible quality is claimed.
- Golden evidence identifies the oracle, input, configuration, expected output,
  comparison mode, tolerance where applicable, and reason for inclusion.
- Validators cover success, failure, advisory/default mode, strict mode where
  applicable, suppression validity, and excluded paths.
- Every governance validator or meaningful policy-check family invoked by the
  canonical governance/full-verification graph names exactly one of the six
  canonical human owners in the machine provenance registry. Coverage is
  derived from the actual Python check registry and explicitly marked shell
  invocations, never from a parallel expected-name list. A real check without
  an owner, a registered family without real enforcement, or a non-canonical
  owner is invalid policy.
- After a non-patch source rewrite, check encoding and literal escape artifacts,
  then run focused lint before broader tests.

## Commands and escalation

Run focused checks first. Use the repository-managed environment when
available and quiet output by default. Never run the full verification and CI
wrappers in parallel.

```bash
./scripts/verify_focus.sh [--docs] [ruff-targets...] [--pytest pytest-targets...]
python tools/governance/validate_project_contracts.py
python tools/governance/validate_governance_surface.py
python tools/governance/generate_maintenance_docs.py --check
python tools/governance/generate_configuration_reference.py --check
git diff --check
./scripts/check_git_sanitation_repo.sh
CODEX_MODE=1 ./scripts/verify.sh
./scripts/ci_preflight.sh
```

Run `CODEX_MODE=1 ./scripts/verify.sh` for authority changes, governance,
broad shared infrastructure, material uncertainty, reviewer requests, release
claims, or when the route union requires it. Toolchain-specific commands remain
with the relevant manifest, script, or domain contract.

Report exact commands and results, typical checks omitted with rationale,
manual evidence separately from automated evidence, warnings, remaining risks,
and unverified areas. Never claim a check passed unless it ran successfully on
the reported tree.
