# Claude Guidance

Read and follow `AGENTS.md` first; this compatibility pointer owns no governance.
For Python use `./scripts/resolve_python_env.sh`, never a bare Python from `PATH`.
`PYTHON_BIN` is output only; interpreter priority and source binding are owned by
`config/governance/project.json#/environment` and `docs/architecture/workspace_governance_v0_1.md`.

<!-- BEGIN workspace-governance managed dispatch -->
Use `./gov check` before work and `./gov resolve` for governed context.
The adopted pack is pinned in `.governance/fleet.json`. Existing local
instructions and stronger verification duties continue to apply.
Run the declared project verifier; its managed hook checks the pack first.
<!-- END workspace-governance managed dispatch -->
