# Migration Notes (Shims and Structure)

This repository was restructured in stages to reduce top-level clutter and prepare for a `src/` layout.

## What Changed (Stages 1-6)

- Entry scripts moved to `cli/` (`cli/front*.py`).
- Root `front*.py` files remain as compatibility wrappers.
- Runtime package moved from `tetris_nd/` to `src/tet4d/engine/`.
- Tooling was split into:
  - `tools/governance/`
  - `tools/stability/`
  - `tools/benchmarks/`
- Imports were migrated from `tetris_nd.*` to `tet4d.engine.*`.
- The root `tetris_nd/` legacy shim was removed after the import migration passed CI.

## Why the Shims Exist

- `tet4d/` (repo-root shim):
  - Lets `python -c "import tet4d.engine"` work from a fresh clone without requiring `PYTHONPATH=src`.
  - Keeps local developer workflows simple before install/editable-install standardization.

- `tetris_nd/` (legacy import shim, removed in Stage 6):
  - Existed temporarily to preserve imports during the `src/` layout transition.
  - Removed after repo imports were migrated to `tet4d.engine.*` and validation passed.

## Canonical Import Path (Going Forward)

Prefer:

```python
from tet4d.engine import ...
```

Do not introduce imports from `tetris_nd`.

## Shim Removal Milestones

- `tetris_nd/` shim removal completed in Stage 6 after repo imports were migrated and CI/verify passed.

- Remove repo-root `tet4d/` shim after:
  - tests/tools run through an install/editable-install path (or an equivalent standardized import setup), and
  - `python -c "import tet4d.engine"` is no longer expected to work from repo root without install.
