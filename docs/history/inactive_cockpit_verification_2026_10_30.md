# Inactive cockpit cancellation — 2026-10-30

Base: `cc9aeed1`; F4 consumer work remains a separate change.

A real-window paused replay capture timed out although no live helpers were
visible. The cockpit kept measuring/fitting the hidden live deck; its agreement
and scale state cycled and the coordinator never became idle. This is an
owning lifecycle defect, not evidence that the capture consumer should ignore
pending work.

The cockpit still resolves requested placement, but cancels helper state when
the deck is disabled. Inactive metric signals cannot restart fitting. Enabling
the deck applies policy and obtains fresh measurements normally. Visible layout
parameters, compaction/scaling policy and grid/camera semantics are unchanged.

The new hide/reactivate regression fails on the preceding owner and passes on
the repair. The complete live-cockpit script passes. Two existing isolated
packing/visibility fixtures now explicitly enable the deck, matching the active
viewer behavior they assert; no packing or reparenting assertion was removed.
Focused production resize-history and locked-layout scripts also passed.

Real macOS replay, live 3D and live 4D A/B captures then passed with differing
arm UI scales, exact frozen hash metadata and original-arm restoration. Evidence
ID: `tet4d-window-capture-pp_xdorx`. Agent inspected the replay board image and
found the board contained; this is not broad replay UI or owner acceptance.
The F4 history owns final full-gate/publication evidence and remaining limits.
