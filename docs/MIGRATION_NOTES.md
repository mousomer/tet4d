# Migration Notes (Shims and Structure)

This repository was restructured in stages to reduce top-level clutter and prepare for a `src/` layout.

## What Changed (Stages 1-4)

- Entry scripts moved to `cli/` (`cli/front*.py`).
- Root `front*.py` files remain as compatibility wrappers.
- Runtime package moved from `tetris_nd/` to `src/tet4d/engine/`.
- Tooling was split into:
  - `tools/governance/`
  - `tools/stability/`
  - `tools/benchmarks/`

## Why the Shims Exist

- `tet4d/` (repo-root shim):
  - Lets `python -c "import tet4d.engine"` work from a fresh clone without requiring `PYTHONPATH=src`.
  - Keeps local developer workflows simple before install/editable-install standardization.

- `tetris_nd/` (legacy import shim):
  - Preserves existing imports while the repo migrates to the canonical package path.
  - Avoids a risky mass import rewrite during structure-only stages.

## Canonical Import Path (Going Forward)

Prefer:

```python
from tet4d.engine import ...
```

Do not introduce new imports from `tetris_nd` in new or modified code.

## Shim Removal Milestones

- Remove `tetris_nd/` shim after:
  - repo contains zero non-shim imports of `tetris_nd`, and
  - CI/verify passes after the import migration.

- Remove repo-root `tet4d/` shim after:
  - tests/tools run through an install/editable-install path (or an equivalent standardized import setup), and
  - `python -c "import tet4d.engine"` is no longer expected to work from repo root without install.
