# Stage 55B: semantic export contract

Status: deterministic, non-authoritative inspection export.

`tools/ui_export/semantic_design.py` derives a compact semantic tree from
runtime probe records. It keeps visible viewports, declared semantic roles, and
meaningful textual/runtime structure while retaining source runtime IDs and
probe versions as provenance. Generated wrapper identity is discarded using
runtime provenance (with one normalized identifier fallback); meaningful
descendants survive. It does not claim that every runtime control has rich
semantic annotation, and it has no per-screen geometry, binding inventory, or
layout policy.

The normal output is `semantic/semantic_ui.json`; `runtime/runtime_ui.json` is
an optional uncompressed diagnostic form. Both are generated on demand under
the ignored `design/bootstrap/` tree. Neither is an authority, fixture, or
canonical design workflow.

The schemas remain intentionally separate: `tet4d.ui-bootstrap.v2` is the
runtime-observation schema; `tet4d.semantic-projection.v1` is the internal
compressed tree; and `tet4d.semantic-export.v1` is the portable envelope. The
envelope declares its source and projection schemas explicitly. Generic
projected grouping uses the neutral `container` kind, not `frame`.

Verification uses synthetic unit fixtures plus the deterministic projection
rules; it does not require checked-in runtime captures:

```bash
.venv/bin/python -m pytest -q tests/ui_export
```

Any later product-design decision must be established in its owning RDS and
implemented and accepted through the normal Godot workflow. This export can
inform investigation only.
