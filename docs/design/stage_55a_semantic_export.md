# Stage 55A: runtime semantic export

Status: reproducible inspection tooling. Runtime and product-layout authority
remain with the Python reference and Godot product shell.

The Stage 55 capture tools observe the plain initial 2D, 3D, and 4D shells and
emit neutral JSON records containing the runtime tree, bounds, visibility,
text, semantic roles, generated-node provenance, and capture provenance. They neither consume images nor
establish a design-tool, layout, or product authority.

Generated probe and export files are ignored. Capture them only when an
investigation or review needs fresh evidence:

```bash
capture_root="$(mktemp -d)"
.venv/bin/python tools/ui_export/python_runtime_probe.py --output "$capture_root/probes/python"
/Applications/Godot.app/Contents/MacOS/Godot --headless --path godot/Tet4D.Godot --script res://tools/ui_export_probe.gd -- "$capture_root/probes/godot"
.venv/bin/python tools/ui_export/exporter.py --probes "$capture_root/probes" --output "$capture_root/export"
.venv/bin/python tools/ui_export/exporter.py --probes "$capture_root/probes" --output "$capture_root/export" --projection runtime
```

The runtime-observation schema is `tet4d.ui-bootstrap.v2`. Its generated-node
marker is source provenance used only to discard wrapper identity during
projection; meaningful descendants remain observable.

The headless Godot route records structural output but cannot provide a
viewport PNG. Screenshots, when deliberately captured, remain local review
aids and are not test inputs.
