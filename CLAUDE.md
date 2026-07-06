# Claude Guidance

Read and follow `AGENTS.md` first. This file is only a pointer for Claude; it
does not replace Codex governance.

Codex governance remains authoritative. In particular, use the routing and
workflow documents named by `AGENTS.md`, including `docs/WORKFLOW_CODEX.md`,
`docs/ARCHITECTURE_CONTRACT.md`, `CURRENT_STATE.md`, and `docs/BACKLOG.md`.

For Python commands, use the workspace-managed environment when available:
prefer `${PYTHON_BIN}` if set, otherwise use `${WORKSPACE_VENV}/bin/python` if
`WORKSPACE_VENV` is set. Otherwise use the project's documented verification
scripts.
