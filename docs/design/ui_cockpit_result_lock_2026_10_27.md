# UI and cockpit result lock — 2026-10-27

## Status and identity

The owner requested that actual results be locked before UI/cockpit orchestration
is restructured. This locks accepted observable behavior, not the present file
structure, private APIs or known bugs. It introduces no product redesign.

The reproducible implementation base is master `e37441bb`, on the separate
`codex/ui-cockpit-orchestration` worktree. The original dirty release checkout
at `a0b00718` is preserved and superseded as the implementation base; its newer
CI/classification omissions are not carried forward. The source manifest now
records committed baseline hashes, not an unnamed working tree.

Historical observed output is retained under
`docs/design/baselines/cockpit_windowed_2026_10_26/`. Three supplied observation
files have identical SHA-256 `9687a9225c3b95d29affe4d748f658148c31c437c1cbbabebc450f8b7ded9ca9`:
410 observations each, with zero recorded failures. The repository copy adds
exactly one final LF for publication formatting; its separate hash and original
source hash are recorded in `manifest.json`. All three run identities and
358 PNG identities are recorded. The PNG bundle was externally retained at inspection; the manifest
uses a portable capture ID and does not establish durable retrieval. Obtain
the bundle before any screenshot comparison claim.
This is inspection of existing evidence, not a new run or new visual sign-off.

Sources of acceptance are the owner-accepted 2026-10-25 layout contract in
`docs/architecture/godot_shell_layout_stabilization.md`, its
`test_locked_shell_layouts.gd` cases, and the amendment in
`stage_58b_readability_evidence.md`. Earlier 58B viewport-share measurements
remain historical; they do not override the later drawn-content contract.

## Later owner decision: redesign exploration reopened (2026-11-23)

**Status of this historical lock:** the 2026-10-25 accepted menu and cockpit
layout is still the current **implemented/tested baseline**, but is no longer
an immutable target for the P2 professional redesign. The owner explicitly
stated in the Tet4D project conversation on **2026-11-23** that the design lock
is being reopened, and subsequently required a **single cockpit infrastructure
for Play/Explorer and 2D/3D/4D**, with dimension differences represented by
capability/configuration rather than copied UI code. The decision is also
recorded in [draft PR #199](https://github.com/mousomer/tet4d/pull/199).

This authorizes **design and review of alternatives**, including Main Menu
order/grouping, Live 2D/3D rail placement, Live 4D control split and responsive
placement. It **does not approve any replacement** or change the current
behavioral contract. The original observations, numeric baselines, accepted
fit behavior and test evidence below remain historical facts. The existing
`godot/Tet4D.Godot/tests/test_locked_shell_layouts.gd` remains enforced through
behavior-preserving infrastructure work. An owner-accepted replacement layout
must update/re-lock its expectations **in the same implementation PR**, with
equivalent reachability, input, focus, fit, resize and board-preservation
coverage. Never silently rewrite the October evidence or disable its test.

This reopening is **only about application/cockpit layout and visual styling**.
Gameboard semantics, 4D internal slice layout, native commands, projection,
camera mapping, topology and replay identity remain governed elsewhere.

Redesign plan: `docs/plans/dual_mode_godot_ui_redesign.md` (new proposed
`unified_cockpit_visual_redesign.md` path once renamed). Original
`docs/plans/ui_cockpit_orchestration_repair.md` and
`docs/architecture/godot_shell_layout_stabilization.md` remain valid
historical accounts of the accepted 2026-10-25/27 results.

## Frozen results

| Surface | Result that must remain |
| --- | --- |
| Main Menu | One list with the same order/grouping and Play 2D/3D/4D reachable. Preserve logical font sizes and whole-menu fit down to 0.5 before scrolling; do not replace it with columns. Preserve the game/Designer product distinction. |
| Live 2D/3D | At 1440×900 and 1280×720, retain the rail beside the board, every helper without scrolling, whole NEXT/HOLD names, and the 3D MOVE compass beside drop keys. Rail growth uses width the board leaves spare. |
| Live 4D | Preserve the split and unscrolled helpers at those standard windows. At 700×480 the below-board deck leads with NEXT/HOLD and keeps that row on screen. |
| Helper fitting | Preserve measured room → compact gaps → uniform content scaling → scroll at floor 0.6. Keep text, keycaps, glyphs and previews in proportion. Reaching the same context must give the same final layout regardless of resize history. |
| Drawn content | Retain the recorded 1280×720 fitted-content shares: 3D approximately 0.194, 4D approximately 0.340; existing regression floors remain 0.18/0.32. Keep the 3D fit height-limited where the accepted standard layout is height-limited. |
| Style and geometry | Preserve the six-style comparison: same drawn content size, camera fit and slice anchors within each view. A different rail/viewport rectangle alone is not board-size drift. Keep canonical slice spacing and the existing scale-based tiling rule. |
| Render quality | Retain displayed-pixel viewport resolution and 4× MSAA. Do not compensate with line width, grid topology or material changes. |
| Settings/setup | Preserve responsive fields, focus-following content and reachable setup Start/Reset/Back footer actions. Keep preference and frozen-setup behavior. |
| Designer/Laboratory | Preserve bounded overlays, reachable close actions, detached session geometry, comparison/profile behavior and ordinary cockpit restoration on exit. No implicit profile save or camera reset. |
| Guidance/safe area | Preserve Hide Guide access, body-scroll fallback, current safe-area conversion, enlarged UI behavior and window/fullscreen transitions. |
| Input/native boundary | Preserve bindings, Relative/Absolute mapping, native commands and hashes, held input, restart, view controls, and the game/Designer capability boundary. |

Existing structural acceptance spans 1512×982, 1440×900, 1280×720, 1024×640 and
800×500, standard and enlarged UI, guide open/closed and height-only resizes.
Those cases remain required; standard-window no-scroll requirements must not
be incorrectly extended to every small/enlarged combination.

## Allowed review repairs

- **R1 / P2:** fit size, horizontal anchor, drawn span and rail demand must use
  one settled requested pose when Fit is requested during orbit interpolation.
  Owner-approved behavior: finish the pending orbit, then fit and notify relative-
  control consumers. Do not reset to a canonical pose or change margins.
- **R2 / P3:** abandoning/restarting a helper scale search clears its search and
  pending-measurement state. An idle relaxed layout must report settled, even
  after a resize or content rebuild interrupts fitting.

These exceptions correct the two recorded findings. They do not authorize
scale/framing retuning or changes to the settled accepted layouts. Unexpected
visual differences remain discrepancies for owner review, not new baselines.

## Evidence limits and recorded verification

The original 2026-10-27 lock added no fresh execution, screenshot, device result or owner
acceptance; it now preserves supplied pre-repair recordings. Earlier numerical/rendered evidence remains attributed to its
original record. The prior review turn ran selected checks before the owner
prohibited tests; those results do not verify the new R1/R2 edits.

R1/R2 source changes and regression cases are prepared, not functionally
verified. No tests, application launch, rendering or CI execution is authorized
in this pass; only secrets and string-sanitation checks may run. Planned checks
remain pending until the owner changes that instruction. No screenshot golden
is claimed to exist merely because source hashes were recorded. The supplied
observation baseline is available, but its screenshots have not been newly
reviewed or promoted to a pixel-equivalence oracle in this pass.

The prior changed-file sanitation result belongs to the superseded release-tree
revision. This master-based revision passed a scoped secret scan of all 16
changed/new files, with no findings. String sanitation and diff whitespace
checks found no newly introduced issues. Existing RDS Markdown line breaks/BOM
are retained. The original observation hash remains provenance; the repository
copy now appends exactly one LF and records its own hash. No repository-wide
scan or new functional result is claimed.

Subsequent evidence (2026-10-30): the owner authorized relevant tests. Focused
camera/cockpit/Designer/profile suites pass; see
`docs/history/ui_cockpit_focused_verification_2026_10_30.md`. This supersedes
the earlier execution restriction for relevant tests only, without changing the
locked source identity or observation data. The declared final-LF normalization
changes only the repository representation. Full gate, remote CI and manual
acceptance remain pending.

The bounded migration and acceptance gates are in
`docs/plans/ui_cockpit_orchestration_repair.md`. Depth/contrast remains 58C,
W-label tracking remains Stage 59, and the existing stale A/B-preview issue
remains separate. This lock neither closes those items nor expands their scope.
