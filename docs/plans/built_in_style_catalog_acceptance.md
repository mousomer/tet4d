# Built-in Style Catalog — Stage 54F-4 Acceptance

Status: COMPLETE / LOCAL AGENT-DRIVEN ACCEPTANCE GREEN

Branch: `codex/built-in-style-catalog`

Starting SHA: `1cb6e8db474d57832c0b715fd9bc5d57716aa354`

Owning contract: `docs/architecture/built_in_style_catalog.md`

This record covers candidate style creation only. Ranking the candidates is
Stage 54F-5 and selecting the product default is Stage 54F-6. Nothing here
claims a winner.

## 1. What shipped

| Artifact | Path |
| --- | --- |
| Shipped catalog data | `godot/Tet4D.Godot/config/built_in_style_catalog.json` |
| Read-only catalog owner | `godot/Tet4D.Godot/scripts/presentation/built_in_style_catalog.gd` |
| Animated backdrop component | `godot/Tet4D.Godot/scripts/rendering/animated_background.gd` |
| Backdrop shader | `godot/Tet4D.Godot/assets/shaders/animated_background.gdshader` |
| Focused suite | `godot/Tet4D.Godot/tests/test_built_in_style_catalog.gd` |

Three registry parameters were added under the existing
`ENVIRONMENT_PRESENTATION` owner:
`environment.background_animation_mode` (`none`, `tron_grid_flow`; default
`none`), `environment.background_animation_intensity` (`0.00..1.00`, default
`0.55`), and `environment.background_animation_speed` (`0.00..2.00`, default
`1.00`). The registry therefore grows from 26 to 29 parameters and the
live-applicable Designer counts move from 16/18/20 to 19/21/23. Those documented
counts and their test assertions were updated to match additive growth; no
assertion was weakened or removed.

## 2. Agent-driven real-window review

Environment:

- Godot `4.7.2.stable.official.ed1daf0bf`, the pinned baseline;
- macOS DisplayServer, Metal 4.0 Forward+, Apple M1 Pro;
- production scene `res://scenes/trace_replay.tscn`, production native
  fixed-seed Live 2D, 3D, and 4D sessions;
- logical window 1600 x 960, standard UI scale, gravity paused per mode so every
  style is judged over the same visible board.

Each of the six shipped styles was applied in each of Live 2D, Live 3D, and
Live 4D through the actual Designer `Apply to B` path, giving 41 captures. The
committed subset is under
`docs/design/screenshots/built_in_style_catalog/`.

The capture driver also reported deterministic isolation directly:

```text
state_hash=daef26d673067f1cccf82085672ed1a0747e19bf0ba178ead3421bba2a0476c2
hash_stable=true
snapshot_stable=true
bounds_stable=true
layout_stable=true
background_running=true
next_visible=true hold_visible=true controls_visible=true basis_visible=true
phase_t1=0.0054  phase_t2=2.1748  phase_moved=true
```

## 3. Style x mode x criteria matrix

Criteria: **B** board readability, **P** active/locked/Ghost clarity, **N** NEXT,
**H** HOLD, **C** piece-control readability, **S** 4D slice/basis readability,
**K** background distraction acceptable.

| Style | Mode | B | P | N | H | C | S | K |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Tet4D Balanced | 2D | pass | pass | pass | pass | pass | n/a | pass |
| Tet4D Balanced | 3D | pass | pass | pass | pass | pass | n/a | pass |
| Tet4D Balanced | 4D | pass | pass | pass | pass | pass | pass | pass |
| Python Reference | 2D | pass | pass | pass | pass | pass | n/a | pass |
| Python Reference | 3D | pass | pass | pass | pass | pass | n/a | pass |
| Python Reference | 4D | pass | pass | pass | pass | pass | pass | pass |
| Arcade Neon | 2D | pass | pass | pass | pass | pass | n/a | pass |
| Arcade Neon | 3D | pass | pass | pass | pass | pass | n/a | pass |
| Arcade Neon | 4D | pass | pass | pass | pass | pass | pass | pass |
| Tron Grid Flow | 2D | pass | pass | pass | pass | pass | n/a | pass after tuning |
| Tron Grid Flow | 3D | pass | pass | pass | pass | pass | n/a | pass after tuning |
| Tron Grid Flow | 4D | pass | pass | pass | pass | pass | pass | pass after tuning |
| Blueprint Technical | 2D | pass | pass | pass | pass | pass | n/a | pass |
| Blueprint Technical | 3D | pass | pass | pass | pass | pass | n/a | pass |
| Blueprint Technical | 4D | pass | pass | pass | pass | pass | pass | pass |
| High Contrast | 2D | pass | pass | pass | pass | pass | n/a | pass |
| High Contrast | 3D | pass | pass | pass | pass | pass | n/a | pass |
| High Contrast | 4D | pass | pass | pass | pass | pass | pass | pass |

Designer coverage, captured in Live 4D under the animated style:

| Designer state | Result |
| --- | --- |
| Full, built-in section expanded | Board, active slice, W labels, NEXT, HOLD, piece controls, and basis/slice all remain readable beside the bounded panel. |
| Full, profile library expanded | Same, with the built-in section auto-collapsed by the mutual-exclusion rule. |
| Compact | Small A/B strip only; the cockpit is otherwise the ordinary Live 4D cockpit. |

## 4. The Tron readability correction

The first capture pass shipped `background_animation_intensity = 0.55` with a
brighter lattice. Review of the actual frames rejected it: in Live 2D the
background lanes cut through the play field at nearly the same hue and
brightness as the board's own grid, and the dense convergence band sat directly
behind the board. That is the exact failure the stage brief warns about, so the
surface was corrected rather than accepted.

The correction was:

- the dense convergence band is now removed by an explicit horizon-clear ramp
  instead of relying on derivative fade alone;
- centre damping deepened from `0.50` to `0.72` over a wider well, so the region
  where the board sits is the quietest part of the field;
- the horizon seam dropped from `0.45` to `0.18` with a much tighter falloff;
- fewer, larger lattice cells;
- the shipped Tron intensity lowered from `0.55` to `0.40`.

The second capture pass shows the board wireframes, active slice, and active
piece clearly dominant in all three modes while the flow remains legible as a
Tron field. Both passes are recorded here so the judgement is auditable.

## 5. Motion evidence

`live_4d__tron_grid_flow__phase_t1.png` and
`live_4d__tron_grid_flow__phase_t2.png` are the same paused deterministic 4D
game at flow phases `0.0054` and `2.1748`. The receding lattice has visibly
flowed toward the viewer between the two frames, while the slice matrix, active
piece, W labels, NEXT, HOLD, piece controls, and every HUD element are
unchanged. `live_4d_state_hash` is identical across both frames.

## 6. Structural evidence

Focused `tests/test_built_in_style_catalog.gd` covers: registry declaration,
ownership, applicability, bounds rejection, and defaults for the three animation
parameters; profile snapshot round-trip; catalog structure, read-only records,
completeness, pairwise distinctness, and deterministic snapshots; absence of any
mutation method; per-call detachment and source immutability under Designer
editing; malformed, unsupported-schema, and per-entry rejection isolation;
`none`-mode equivalence including zero phase and zero per-frame work; animated
activation, parameter propagation, phase advancement, reset, reduced-motion
freeze, zero-speed still frame, and zero-strength fallback; palette-derived line
colour with no hard-coded role colours; shader `depth_draw_never` with depth
testing retained and no engine-clock use; Designer listing distinguishability,
detached apply with unchanged A, disabled overwrite, unchanged catalog, Save As,
Copy to User Library, no silent user-profile write, and disclosure mutual
exclusion; every style applying in 2D, 3D, and 4D with registry-only exposure;
backdrop parentage, depth placement, and exclusion from the gameplay subtree;
and animation-only isolation of cockpit rects, board bounds, state hash, and
snapshot.

`tests/test_cockpit_density_control_hierarchy.gd` gained a regression proving
that expanding and collapsing the new Built-in Styles section leaves the Live 4D
gameplay viewport rect and the Designer rect unchanged while NEXT, HOLD, piece
controls, and basis/slice state stay visible.

## 7. Gates

| Check | Result |
| --- | --- |
| Isolated canonical Godot suite (4.7.2) | PASS — `Godot replay tests passed.`, no `SCRIPT ERROR` |
| Pinned Godot 4.7.2 gate | PASS |
| `check_godot_settings_externalization.py` | PASS |
| `validate_project_contracts.py` | PASS — 117 required paths |
| `generate_maintenance_docs.py --check` | PASS |
| `generate_configuration_reference.py --check` | PASS after regeneration |
| `validate_godot_semantic_boundary.py` | PASS — 123 scripts |
| `check_git_sanitation_repo.sh` | PASS |
| `git diff --check` | PASS |
| `CODEX_MODE=1 ./scripts/verify.sh` | PASS |

## 8. Known non-regressions and deferrals

The clipped `DOWN ENTRY` label at the left edge of Live 2D is present in every
style and is the pre-existing defect already recorded in the Godot 4.7.2 upgrade
audit. It is unchanged by this stage.

Intentional negative-path persistence diagnostics and the known non-failing Godot
teardown advisories remain visible in suite output.

This is agent-driven acceptance, not independent human sign-off. Comparative
ranking (54F-5), default selection and polish (54F-6), additional animation
modes, background animation scale, style thumbnails, palette-role editing, and
procedural style authoring remain deferred.
