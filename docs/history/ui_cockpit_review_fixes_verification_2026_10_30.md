# Cockpit review fixes verification — 2026-10-30

Base: `b6bf9716`. Scope: three review findings on the cockpit orchestration
batch, inside the existing Godot shell authority. No manifest, native, grid,
style, profile or accepted visual parameter changes.

## Why

Remote run `41067387705` on `b6bf9716` was the batch's first completed Godot
lane, and it failed. Earlier batch runs were skipped or cancelled, and the
branch's focused verification records did not include
`test_stage_56g_responsive_cockpit.gd`.

## Findings and fixes

1. Resize round-trip regression, first failing at `aa0b11d7` (bisected:
   `91987bb1` and `966c0e2b` pass). After large→narrow→short→narrow+short→large
   the Live 4D deck box was 193 px but its rows stayed 355 px, 24 failures
   across styles. A frame trace showed `FitScaleContainer` sorting while its
   content's minimum was transiently 355 (legend text still wrapped at the
   previous 786 px width). The minimum settled back to 193 before Godot's
   deferred report, so no `minimum_size_changed` fired and no re-sort was
   queued. The pre-coordinator same-frame metrics check had masked this by
   re-applying. Fix: the fit box re-checks an oversized placement on the next
   frame and re-sorts if it no longer matches. The coordinator is unchanged;
   keeping its cancelled settle passes alone did not fix the round trip.
2. `test_cockpit_density_control_hierarchy.gd` read the removed
   `_designer_host` field (three script errors the runner reported as passing).
   It now uses `designer_surface_rect()`.
3. The content key includes label text, so each new piece's NEXT/HOLD text
   restarted a settled deck fit on the next layout pass: measured at 1100×600,
   scale 0.64 → 1.00 relaxed → 0.60 → 0.80 → 0.70 → 0.65 → 0.63 → 0.64 over
   about 14 frames, for the same result. A settled group whose new sample
   matches its last one (height, width, gap savings) now keeps its fit. The key
   still includes text, so height-changing edits refit as before.

## Evidence

Regressions: `test_fit_scale_container.gd` (fails on `b6bf9716` with the child
held at 80 px, passes with the fix) and a height-neutral edit case in
`test_helper_fit_state.gd`. Existing label/font refit cases still pass.

Full Godot lane (`scripts/verify_godot_4_7.sh`, pinned 4.7.2, isolated user
data, native extension freshly built from this tree's source and godot-cpp
pin): 92 scripts passed, no script errors, topology parity 59 cases. CI's
planner on the change selects baseline, documentation_governance and godot;
the documentation lane commands and `git diff --check` pass locally. Remote
CI and manual acceptance are not claimed here.
