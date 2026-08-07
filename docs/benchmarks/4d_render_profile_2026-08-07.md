# 4D Render Profile Report (2026-08-07)

Context: Stage 54C changes the Godot live-4D presentation mapper and event-time
slice reconstruction. The repository's canonical profiler measures the
inherited Pygame 4D renderer, so this report is supplementary threshold
evidence rather than a direct Godot transition benchmark. Godot regression
coverage separately asserts that settle frames retain the same stable grid
geometry and rebuild only when the exact destination basis is rendered.

Command:

```bash
.venv/bin/python tools/benchmarks/profile_4d_render.py \
  --frames 60 \
  --warmup 10 \
  --output state/bench/4d_render_profile_latest.json \
  --assert-threshold
```

Scenario summary:

| Scenario | Avg ms/frame | FPS |
|---|---:|---:|
| default_sparse | 3.9821 | 251.12 |
| hyper_sparse | 4.2855 | 233.34 |
| default_dense | 24.9456 | 40.09 |
| hyper_dense | 29.7488 | 33.61 |

Threshold result:

- Sparse overhead: `+0.3034 ms` (`+7.62%`).
- Policy limits: `15%` or `2.0 ms/frame`.
- Threshold exceeded: `false`.

Decision: no threshold-driven mitigation is required. Stage 54C's Godot basis
settle modifies only the renderer-root presentation scale per transition frame;
stable grid geometry, slice-panel placement, and locked-cell presentation are
not reconstructed by the transition process loop.
