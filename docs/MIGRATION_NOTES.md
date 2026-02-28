# Migration Notes (Shims and Structure)

This repository was restructured in stages to reduce top-level clutter and prepare for a `src/` layout.

## What Changed (Stages 1-7)

- Entry scripts moved to `cli/` (`cli/front*.py`).
- Root `front*.py` files remain as compatibility wrappers.
- Runtime package moved from `tetris_nd/` to `src/tet4d/engine/`.
- Tooling was split into:
  - `tools/governance/`
  - `tools/stability/`
  - `tools/benchmarks/`
- Imports were migrated from `tetris_nd.*` to `tet4d.engine.*`.
- The root `tetris_nd/` legacy shim was removed after the import migration passed CI.
- The root `tet4d/` shim was removed; local development now relies on editable install (`pip install -e .[dev]`).

## Why the Shims Exist

- `tet4d/` (repo-root shim, removed in Stage 7):
  - Existed temporarily so repo-root imports worked before editable-install setup was standardized.
  - Removed after CI/scripts/docs were updated to rely on editable install.

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

- Repo-root `tet4d/` shim removal completed in Stage 7.
- Standard dev/CI import path now requires editable install (`pip install -e .[dev]` locally; CI installs `-e .[dev]`).
