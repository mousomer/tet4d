# Claude Guidance

Read and follow `AGENTS.md` first. This file is only a compatibility pointer;
it owns no governance.

Use the canonical governance, product, architecture, backlog, and conditional
handoff authorities routed by `AGENTS.md`.

For Python commands, use the workspace-managed environment when available:
prefer `${PYTHON_BIN}` if set, otherwise use `${WORKSPACE_VENV}/bin/python` if
`WORKSPACE_VENV` is set. Otherwise use the project's documented verification
scripts.
