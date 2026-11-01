# Settled helper idle repair — 2026-10-30

Base: `cf8a9517` (plan), with capture work in progress separately. Scope:
HelperFitState completion; accepted scale, policy and layout remain unchanged.

Real macOS capture readiness reproduced a permanently busy Live-4D cockpit.
The side fit had scale 0.6 and searching=false, yet every unchanged layout
observation reopened compact sample agreement. Snapshot measurements and
geometry stayed constant while coordinator work and pending samples persisted.

`_scale_step` now returns an already completed scaled fit before requesting new
agreement. Intrinsic edits still reset through the content key; width/room
changes retain their existing earlier invalidation. This corrects settled-state
lifetime rather than hiding pending state in the capture consumer.

The new repeated-observation regression fails on the preceding state owner and
passes on the repair. Focused helper-state, live-cockpit and coordinator scripts
passed before the expanded resize/capture run completed. The production macOS
3D and 4D A/B capture scenario then passed with different arm UI scales; both
arm PNGs and metadata were produced and the original arm restored. Previously
3D passed and 4D timed out before any PNG publication. Actual window rendering:
Godot 4.7.2, Metal Forward+, Apple M1 Pro, 1280×720 point application canvas
and 2560×1440 root image. Native extension was freshly built from the pinned
submodule. This is execution/inspection evidence, not owner visual sign-off.

The separate F4 record owns capture-operation acceptance and final broad-gate
results. This repair alone does not close integrated/manual R1/R2 acceptance.
