# Stage 55A: runtime semantic export

Status: reproducible inspection tooling. Runtime and product-layout authority
remain with the Python reference and Godot product shell.

The Stage 55 capture tools observe the plain initial 2D, 3D, and 4D shells and
emit neutral JSON records containing the runtime tree, bounds, visibility,
text, semantic roles, and capture provenance. They neither consume images nor
establish a design-tool, layout, or product authority.

Generated probe and export files are ignored. Capture them only when an
investigation or review needs fresh evidence:

```bash
.venv/bin/python tools/ui_export/python_runtime_probe.py --output design/bootstrap/probes/python
/Applications/Godot.app/Contents/MacOS/Godot --headless --path godot/Tet4D.Godot --script res://tools/ui_export_probe.gd -- design/bootstrap/probes/godot
.venv/bin/python tools/ui_export/exporter.py
.venv/bin/python tools/ui_export/exporter.py --projection runtime
```

The headless Godot route records structural output but cannot provide a
viewport PNG. Screenshots, when deliberately captured, remain local review
aids and are not test inputs.
