# Stage 58C owner acceptance — 2026-11-02

The owner confirmed that the outstanding Stage 58C macOS/Metal review was
completed and accepted the documented visual and performance tradeoffs. The
confirmation was given in response to the explicit question about blue-piece
contrast, distant-slice readability and dense-board performance in PR #154.

This closes the recorded Stage 58C.7 owner checkpoint for the proposed renderer
hierarchy. The original implementation and historical measurements are at
`0e6822da`; integration retains its tuning values and renderer behavior while
bringing forward current master, correcting the evidence record and asserting
scaffold reuse. Automated integration checks remain separate evidence.

## Accepted tradeoffs and evidence limits

- 3D blue remains at 13.1–14.3 ΔL* in six of seven historical style
  configurations, below the proposed 15 margin. Acceptance does not change
  those measurements or claim the proposal is met.
- Far-slice colour identity and occupied-cell contrast recede, particularly in
  Arcade Neon and High Contrast. The documented qualifications remain valid.
- Historical dense rebuild overhead is approximately 13–15% headless CPU and
  6–8% for 4D Vulkan/lavapipe. Those measurements are not retagged as Metal
  timings or a new platform performance benchmark.
- Owner-reported interactive acceptance is distinct from agent inspection,
  automated material-state checks and current integration captures.
- Stage 58B scale/framing and locked shell layouts remain accepted. Stage 58D,
  Stage 59, Designer text sizing and replay-viewer issues retain separate scope.

The acceptance does not establish exact historical PNG parity, other-device
proof, a release, or new platform support. Remaining polish stays in
`docs/BACKLOG.md`; evidence details are in
`docs/design/stage_58c_spatial_readability_evidence.md`.
