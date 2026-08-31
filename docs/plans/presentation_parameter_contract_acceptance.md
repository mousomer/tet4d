# Presentation Parameter Contract Acceptance

Status: COMPLETE / LOCAL AGENT-DRIVEN ACCEPTANCE GREEN

Date: 2026-08-26

Branch: `codex/presentation-parameter-contract`

Local baseline: `codex/54g-release-hardening` at
`7d9d3872180905e67874329f8046f336744a348e`

## Outcome

The post-Stage-54 presentation-parameter follow-on is complete on the local
stack. The schema-3 shell-settings registry now declares all 26 presentation
parameters with one typed identity, default, persistence policy, semantic
owner, accessibility classification, and runtime applicability. Twenty-four
preferences are eligible for the existing shell settings file; the quick grid
toggle and layout diagnostics remain session-only.

A detached schema-1 `PresentationProfile` supplies canonical defaults,
validated copies, owner/applicability queries, snapshots, and copy-on-override
variants. `TraceReplayApp.apply_presentation_profile()` is the single bounded
product entry point. It applies HUD, accessibility, palette, renderer,
material, slice-layout, Ghost, replay playback, camera-preference, and
environment consumers without writing the profile to disk or reconstructing
gameplay.

Presentation configuration is non-gameplay state and cannot contribute to
deterministic session identity.

## Acceptance Matrix

| Criterion | Result and evidence |
| --- | --- |
| Inventory and unique ownership | PASS — 26 unique registry IDs; scalar validated `semantic_owner`; full inventory in `docs/architecture/presentation_parameter_contract.md`. |
| Typed contract | PASS — registry/spec validation owns types, defaults, numeric bounds or enum options, persistence, accessibility classification, and non-empty runtime applicability. |
| Default parity | PASS — canonical material, palette, layout, HUD, and camera-preference assertions retain accepted defaults; the default visible capture remains coherent. |
| Live representative updates | PASS — active/locked/Ghost opacity, grid/boundary opacity, theme, 4D slice spacing, background intensity, UI scale, HUD density, and accessibility compose through one app entry. |
| Frozen-state A/B isolation | PASS — canonical setup, exported snapshot/hash, current document, exact basis slots, shared local orientation, and all camera-pose fields compare unchanged across profile application. |
| Persistence isolation | PASS — schema-1/2/3 settings recovery and round trip accept new registry keys; only 24 `local_shell` entries persist; gameplay setup and forbidden deterministic keys remain excluded. |
| Renderer consumption | PASS — migrated render/material/layout paths consume profile values and derive their defaults/ranges from the registry. |
| Mode coverage | PASS — structural Godot coverage includes 2D, 3D, standard 4D, custom 4D, and W=1 responsive layout/application. |
| 3D/4D divergence | PASS — shared local geometry plus deliberate shape, slice-set composition, fit/mount, and active-material differences are documented; no mode-specific profile compensation was added. |
| Later A/B readiness | PASS — variants are detached copy-on-override values; no mutable process-global profile is required. Assignment, telemetry, and experiment UI remain deferred. |

## Agent-Driven Real-Window Review

Environment:

- Godot `4.7.1.stable.official.a13da4feb`;
- macOS 26.6.2 (build 25G83), arm64, Apple M1 Pro;
- macOS DisplayServer with Metal Forward+;
- entry scene `res://scenes/trace_replay.tscn`;
- production native fixed-seed Live-4D setup, standard `5 x 10 x 4 x 4`;
- application seam `TraceReplayApp.apply_presentation_profile()`.

The run froze one native Live-4D game and captured canonical profile A, then
applied profile B with Vector Arcade palette, grid opacity `0.75`, boundary
opacity `0.50`, active-piece opacity `0.60`, Ghost opacity multiplier `0.35`,
slice spacing `1.45`, and background intensity `0.45`. The active piece,
Ghost, grid/boundary hierarchy, palette, slice anchors, and environment changed
visibly. The four-slice presentation remained coherent. The native snapshot
and state hash, canonical setup, exact basis, shared local orientation, and
camera pose remained equal, and the run reported `isolation_ok: true`.

The Settings surface was then inspected with large UI scale and High Contrast.
Generated controls remained readable and reachable in the scroll-safe surface.
The screenshots are recorded under
`docs/design/screenshots/presentation_parameter_contract/`.

This was agent-driven verification, not independent human sign-off. The run
used the current local shell preference store, then explicitly applied the
canonical profile before capturing the default game. The visible A/B pair is
standard Live 4D; automated structural checks cover the other required modes.

## Verification

Passed on the final tracked tree before commit:

```text
python3 -m json.tool config/project/policy_pack.json
python3 -m json.tool godot/Tet4D.Godot/config/shell_settings_registry.json
python3 tools/governance/check_godot_settings_externalization.py
pytest -q tests/unit/governance/test_check_godot_settings_externalization.py
python3 tools/governance/validate_project_contracts.py
python3 tools/governance/generate_maintenance_docs.py --check
python3 tools/governance/generate_configuration_reference.py --check
python3 tools/governance/validate_godot_semantic_boundary.py
./scripts/check_git_sanitation_repo.sh
git diff --check
godot --headless --path godot/Tet4D.Godot --script res://tests/run_tests.gd
GODOT_BIN=/path/to/Godot ./scripts/verify_godot_4_7.sh
CODEX_MODE=1 ./scripts/verify.sh
```

Results: governance unit tests `7 passed`; project contracts `117 required
paths checked`; focused Godot `Godot replay tests passed`; pinned Godot
`Godot 4.7.1 verification passed` with 59 shared topology transport cases; and
the full repository result was `verify: OK`.

One immediate focused Godot retry encountered a Godot engine crash in the
log-copy/Zstd path before tests began. The next clean invocation and both
required Godot/full gates passed. Expected negative-path settings/native-input
messages and existing headless resource-teardown advisories remain non-failing.

## Authority and Deferrals

Authority effect: none. Godot retains presentation authority; native C++
retains deterministic live-game authority. No transfer or new-authority record
is required.

Deferred: named profile-library persistence and management UI, Designer Lab,
A/B assignment/telemetry/statistics, arbitrary palette-role editing, animated
or procedural environments, complete theme packs, and canonical projected
3D/4D board-geometry reconciliation.
