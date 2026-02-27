# 4D Render Profile Report (2026-02-27)

Command:

```bash
.venv/bin/python tools/benchmarks/profile_4d_render.py \
  --frames 60 \
  --warmup 10 \
  --output state/bench/4d_render_profile_latest.json
```

Result source:
- `state/bench/4d_render_profile_latest.json`
- `generated_at_utc`: `2026-02-27T18:39:01.067984+00:00`

Scenario summary:

| Scenario | Avg ms/frame | FPS |
|---|---:|---:|
| default_sparse | 2.9505 | 338.93 |
| hyper_sparse | 3.1772 | 314.74 |
| default_dense | 22.8388 | 43.79 |
| hyper_dense | 27.0044 | 37.03 |

Overhead summary:
- sparse: `+0.2267 ms` (`+7.68%`)
- dense: `+4.1656 ms` (`+18.24%`)

Threshold policy check (sparse only, per RDS):
- pct limit: `15.0%`
- ms limit: `2.0 ms`
- threshold exceeded: `false`

Decision:
- Do not add new projection/cache complexity in this batch.
- Keep current rendering path; no threshold-driven optimization action required.
