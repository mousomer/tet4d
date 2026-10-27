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
410 observations each, with zero recorded failures. One exact observation file
is copied into the repository; all three identities and 358 PNG identities are
recorded. The PNG files remain in the supplied external capture directory.
This is inspection of existing evidence, not a new run or new visual sign-off.

Sources of acceptance are the owner-accepted 2026-10-25 layout contract in
`docs/architecture/godot_shell_layout_stabilization.md`, its
`test_locked_shell_layouts.gd` cases, and the amendment in
`stage_58b_readability_evidence.md`. Earlier 58B viewport-share measurements
remain historical; they do not override the later drawn-content contract.

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

## Evidence limits and current verification

This record adds no fresh execution, screenshot, device result or owner
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
and the observation file's original missing final newline are retained; the
latter preserves its recorded hash. No repository-wide scan or new functional
result is claimed.

The bounded migration and acceptance gates are in
`docs/plans/ui_cockpit_orchestration_repair.md`. Depth/contrast remains 58C,
W-label tracking remains Stage 59, and the existing stale A/B-preview issue
remains separate. This lock neither closes those items nor expands their scope.
