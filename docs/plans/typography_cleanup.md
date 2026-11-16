# Typography cleanup (behaviour-locked)

Role: spec
Status: active
Source of truth: this file for typography cleanup sequencing and its behaviour lock
Supersedes: none
Authority: typography rules in `docs/architecture/godot_visual_style_authority.md`
and `docs/design/godot_visual_system.md`; the locked shell layouts
(`test_locked_shell_layouts.gd`) are unchanged by this plan.

## Invariant

Phases 0–3 are pure refactors. The **effective** typography a player sees —
face, weight and rendered size of every visible text control — must stay
identical, frame for frame, at every supported window size. Any visible change
(Phases 4–5) is a separate owner decision, landed with an approved baseline
update, never folded into a refactor.

Effective means measured from the running shell, not read from code: several
coded sizes are overwritten by `ShellControlStyleApplier` before they render.

## Measured baseline (2026-11-03)

Headless game bootstrap at 1280×800, isolated HOME, onboarding off.

- One face everywhere: Godot's embedded fallback, Open Sans SemiBold (600).
  No font files, no theme font, no `FontVariation`, no monospace.
- Rendered UI sizes: 16, 18, 22, 24, 32. 3D board labels: 36, 48, 54.

| Screen | Rendered sizes (count) |
| --- | --- |
| Main Menu | 22 ×4, 24 ×11, 32 ×1 |
| Settings | 16 ×73, 18 ×16, 24 ×2 |
| How to Play | 22 ×124, 24 ×11 |
| About | 24 ×8 |
| Advanced | 22, 24 ×3, 32 |
| Game Setup | 22 ×5, 24 ×11, 32 |
| Live 3D | 16 ×3, 18 ×7, 22 ×37; gizmo 36 ×3 |
| Live 4D | 16 ×3, 18 ×7, 22 ×61; gizmo 36 ×3; slice 48/54 |
| Explorer 4D | 16 ×3, 18 ×6, 22 ×47, 24 ×38 |

Coded values that do not render:

| Control | Coded | Rendered | Why |
| --- | --- | --- | --- |
| `MainMenuTitle` | `FONT_DISPLAY` 40 | 32 | name contains `Title` → `FONT_SCREEN_TITLE` |
| `AdvancedMenuTitle` | 30 | 32 | same rule |
| `MainMenuSubtitle` | `FONT_BODY` 24 | 22 | `SecondaryLabel` → `FONT_SUPPORTING` |
| `NextPieceTitle` / `HoldPieceTitle` | 13 | 22 | listed section title → `FONT_SECTION` |
| `NextPieceStatus` / `HoldPieceStatus` | 11 | 22 | plain label floor `max(size, 22)` |
| Theme `default_font_size` | 15 (`.tres`) | 24 | `build_theme()` replaces it |

| `OnboardingTitle` | 18 | 32 | name contains `Title` |
| `OnboardingBody` | 16 | 22 | plain label floor |

The full per-screen record, including the Designer panels, lives in the
Phase 0 baseline; camera guidance (coded 11), inspector section headers (13)
and control-hint group titles (12/13) are covered there where visible.

Glyphs: 9 of 17 non-ASCII characters in UI strings are absent from the
embedded face and render through OS system fallback:
`← ↑ → ↓ ↔ ↘ ⇧ ▸ ▾`. Covered: `· − — ° × … • –`.

## Phase 0 — Lock (gate for all later phases) — implemented 2026-11-03

Baseline taken on the 0.9.2 release code (`02babe3f`), including its compact
Settings and Designer menus.

```sh
"$GODOT_BIN" --headless --path godot/Tet4D.Godot --script tests/run_typography_lock.gd
# owner-approved regeneration only; a write run always reports a failure:
TET4D_WRITE_TYPOGRAPHY_BASELINE=1 "$GODOT_BIN" --headless --path godot/Tet4D.Godot --script tests/run_typography_lock.gd
```

1. `tests/test_typography_lock.gd`, registered in `tests/run_tests.gd`, with
   the checked-in `tests/fixtures/typography_baseline.json`.
2. Visits Main Menu, Settings, How to Play, About, Advanced, Game Setup
   (2D/3D/4D), Live 2D/3D/4D, Live 4D with onboarding and with the full
   Designer, and Explorer 3D/4D, at 1280×800 and 1280×720, from the Designer
   bootstrap with factory setups and temporary settings storage.
3. Fingerprint every visible text control (`Label`, `Button`, `OptionButton`
   items, `LineEdit`, `RichTextLabel`, `ItemList`, `Label3D`): screen, role
   name (node name without generated suffix), class, type variation, rendered
   size, font name and weight, and whether it sits under `shell_chrome` or
   `readable_guidance`. Compare as a sorted multiset; print a readable diff.
4. Lock `build_theme()` default size per display mode and the glyph set: the
   UI's non-ASCII characters and which ones the embedded face lacks. The test
   fails when that set changes in either direction.
5. Proven to bite: `FONT_CHROME_SUPPORTING` 16→15 produced 132 differences,
   and the camera gizmo's literal 36→35 produced 48; both were reverted. The
   runner requires completion, not just "passed".
6. Baseline regeneration is owner-approved only, as with locked shell layouts.

## Phase 1 — Make code state what renders (no visual change)

Replace every coded size that does not render with the value that renders, or
delete it where the applier already decides: the table above, then the
Phase 0 discoveries. Align the `.tres` `default_font_size` with the runtime 24
(or delete it and let `build_theme()` own it). Remove the no-op chrome
`add_theme_font_override("font", ThemeDB.fallback_font)`. Delete
`FONT_DISPLAY` if nothing renders at 40. Lock unchanged.

## Phase 2 — Explicit type roles (no visual change)

Introduce one role table (e.g. `ShellTypeRoles`) mapping display, screen
title, section, body, supporting, control hint and the three chrome roles to
tokens. Controls opt in with `set_meta("type_role", …)`; the applier reads the
role first and falls back to today's node-name matching. Migrate creators one
file at a time, then delete name matching. Renaming a node must no longer
change its size. Lock unchanged at every step.

## Phase 3 — Board label tokens (no visual change)

Move the 3D label sizes (slice 48/54, board/chart labels 30, gizmo 36 with outline 8)
into named board-typography tokens beside the shell tokens. Lock unchanged.

## Phase 4 — Glyph coverage (owner decision, visible change)

The 9 fallback glyphs look different per OS and may render as boxes on minimal
Linux/Android installs. Options:
(a) replace them with ASCII or drawn key-cap/disclosure icons;
(b) bundle an approved fallback face, which needs the authority's
"Do not bundle font files" rule amended;
(c) keep system fallback, verified on Windows, Linux and Android.
Land with an approved baseline update.

## Phase 5 — Reconcile the rules (owner decision)

The style authority (title 20–24, body 13–15), the design system (display 30,
body 15) and the code (screen title 32, body 24) give three scales. Record the
code's scale as the authority, if accepted, noting it is the documented scale at roughly 2×.
Decide the monospace rule for hashes, seeds and frame indexes (implement with a
platform `SystemFont`, or drop the rule) and the "use weight for hierarchy"
rule with a single 600 weight (add a `FontVariation`, or drop the rule).

## Non-goals

No new typeface, no size or layout change in Phases 0–3, no fit-policy or
renderer tuning, and no change to the locked live cockpit or Main Menu
layouts.

## Verification per phase

```sh
"$GODOT_BIN" --headless --path godot/Tet4D.Godot --script tests/run_tests.gd
GODOT_BIN=... ./scripts/verify_godot_4_7.sh
CODEX_MODE=1 ./scripts/verify.sh
git diff --check origin/master...HEAD
```

The typography lock and `test_locked_shell_layouts.gd` must pass unchanged in
Phases 0–3.


## Approved chrome-removal baseline integration (2026-11-15)

The owner authorized integration of Claude `235921d9` and a measured baseline
update: remove only the 2D `SPAWN ENTRY` Label3D and the gizmo's unlabelled
centre ball. Keep the active-piece origin cube. Generic `BOARD_LABEL_*` tokens
retain their existing values for chart/seam labels. The centre ball has no
text fingerprint. Review the regenerated baseline against its saved predecessor;
expected typography delta is only `SpawnEntryLabel` removal in Live 2D at the
two locked sizes. A write run is not acceptance; rerun normally and run the
combined focused and full gates. No blanket typography re-baseline is authorized.

Measured baseline review: exactly two removed fingerprints, `SpawnEntryLabel`
in Live 2D at 1280×800 and 1280×720; no added/changed text fingerprints.
Normal isolated-HOME typography lock passed after regeneration.


Combined-tree verification: isolated-HOME typography lock and renderer, Live
shell, Explorer input/practice/surface and cockpit-lock regressions passed.
`CODEX_MODE=1 ./scripts/verify.sh` passed before the concurrent governance
migration. The pinned `GODOT_BIN="$(command -v godot)"
./scripts/verify_godot_4_7.sh` passed all 101 scripts and 59 topology parity
cases. Product files and the two-fingerprint baseline remain unchanged across
that migration; fresh full-verifier evidence for the migrated tree is retained
separately from the earlier result. Human T2S acceptance and authority transfer
remain open. Integration sources: RDS `49220832`, cleanup `235921d9`.


Fresh post-migration `CODEX_MODE=1 ./scripts/verify.sh` passed. The checked
snapshot contained 1,786 source files with digest
`5a86abd73e872f726cda0ecf6946e928c46b34d39f3d6c55114bd27882b95e87`;
comparison after exit found no source changes during verification. Final
handoff/evidence wording is checked separately as documentation-only bookkeeping.
