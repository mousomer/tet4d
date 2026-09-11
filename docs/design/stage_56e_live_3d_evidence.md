# Stage 56E Live-3D Cockpit Evidence

Status: focused-green on 2026-09-07.

At the `1600×960` reference shell, the legacy right-inspector allocation gave
the 3D game area `910×836` pixels (`760,760 px²`). The shared cockpit gives the
game area `1576×642` pixels (`1,011,792 px²`), a 33.0% increase in board area,
and places PIECE, VIEW, NEXT, and HOLD in the same lower-deck family as Live 4D.

- [Legacy inspector](screenshots/stage_56e_live_3d/before_legacy_inspector.png)
- [Shared cockpit](screenshots/stage_56e_live_3d/after_shared_cockpit.png)

The 3D VIEW module contains Fit, Reset, left-drag Orient, right-drag Translate,
and wheel Zoom only. The 3D PIECE module contains X/Z movement, Ctrl/Space
drop, and XY/XZ/YZ rotation only. No W translation, 4D rotation plane, or
exact-basis/re-slice operation is rendered.
