# Claude Guidance

Read and follow `AGENTS.md` first. This file is only a compatibility pointer;
it owns no governance.

Use the canonical governance, product, architecture, backlog, and conditional
handoff authorities routed by `AGENTS.md`.

For Python commands, never invoke a bare `python3`/`python` from `PATH`. Resolve
the interpreter with `./scripts/resolve_python_env.sh`, which prints the one the
governance certifies. Do not set `PYTHON_BIN` as an input; it now only carries a
resolved path to child processes.

The certified chain is `TET4D_PYTHON`, then the `interpreter` key in the ignored
`.governance/workspace.local.json` (where the workspace venv belongs; copy
`.governance/workspace.local.example.json`), then the repository `.venv`, else
`ENVIRONMENT_INVALID`. It never falls back, so a broken higher tier fails rather
than silently selecting another interpreter.

`config/governance/project.json#/environment` and
`docs/architecture/workspace_governance_v0_1.md` are the authority; this file is
only a pointer.
