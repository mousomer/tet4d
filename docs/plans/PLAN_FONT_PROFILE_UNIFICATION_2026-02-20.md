# Plan Report: Font Profile Unification (2026-02-20)

Status: Planned + Executed  
Related backlog item: `BKL-P2-019`  
Related RDS files: `docs/rds/RDS_TETRIS_GENERAL.md`

## 1. Objective

1. Remove duplicated font-model/factory code across 2D/3D/4D setup/render paths.
2. Keep visual behavior unchanged by preserving per-mode font profile values.
3. Keep launcher compatibility with both 2D and ND gameplay entry flows.

## 2. RDS Comparison

1. Existing RDS emphasizes shared helpers and avoiding frontend drift.
2. Existing implementation had duplicated `GfxFonts` + `init_fonts()` in:
3. `tetris_nd/gfx_game.py`,
4. `tetris_nd/frontend_nd.py`,
5. `tetris_nd/front3d_render.py`.

## 3. Design

1. Add one shared font module:
2. `tetris_nd/font_profiles.py`.
3. Keep one shared `GfxFonts` data model.
4. Keep profile-specific initialization values:
5. `2d` profile (`panel=18`),
6. `nd` profile (`panel=17`).
7. Preserve existing module APIs by keeping local `init_fonts()` wrappers in:
8. `tetris_nd/gfx_game.py` -> `init_fonts_for_profile("2d")`,
9. `tetris_nd/frontend_nd.py` -> `init_fonts_for_profile("nd")`,
10. `tetris_nd/front3d_render.py` -> `init_fonts_for_profile("nd")`.

## 4. Scope

1. In scope:
2. shared font model/factory extraction,
3. per-mode font profile mapping,
4. launcher call-site alignment.
5. Out of scope:
6. font family redesign,
7. style/size tuning changes.

## 5. Acceptance Criteria

1. No gameplay behavior changes.
2. Visual output remains profile-equivalent to previous values.
3. Lint/tests/CI gates stay green.
