# Stage 55B: semantic export contract

Status: deterministic, non-authoritative inspection export.

`tools/ui_export/semantic_design.py` derives a compact semantic tree from
runtime probe records. It keeps visible viewports, declared semantic roles, and
meaningful text while retaining source runtime IDs and probe versions as
provenance. It has no per-screen geometry, binding inventory, or layout policy.

The normal output is `semantic/semantic_ui.json`; `runtime/runtime_ui.json` is
an optional uncompressed diagnostic form. Both are generated on demand under
the ignored `design/bootstrap/` tree. Neither is an authority, fixture, or
canonical design workflow.

Verification uses synthetic unit fixtures plus the deterministic projection
rules; it does not require checked-in runtime captures:

```bash
.venv/bin/python -m pytest -q tests/ui_export
```

Any later product-design decision must be established in its owning RDS and
implemented and accepted through the normal Godot workflow. This export can
inform investigation only.
