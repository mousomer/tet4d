# Graphical language P1: board skin captures

These are before and after captures of the same fixture boards, rendered by the
production `TraceSceneRenderer` through
`godot/Tet4D.Godot/tests/run_spatial_readability_capture.gd`:

```text
godot --path godot/Tet4D.Godot --script tests/run_spatial_readability_capture.gd -- <out> \
  scenes=2d_stack,3d_dense,4d_dense styles=<style> grids=full sizes=ref masks=0
```

| File | Style | Theme |
| --- | --- | --- |
| `*_before.png` | `tet4d_balanced` (shipped default) | `plain` |
| `*_after.png` | `tet4d_luminous` | `luminous` |

Each pair renders identical board content: the same cells and colour IDs, the
same camera and the same fit. Compare them with the concept images in
`docs/design/graphical_language/`. They are presentation evidence only; they
are not perceptual measurements.
