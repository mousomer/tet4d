# Tet4D governance dispatcher

Tet4D uses the vendored `workspace-governance` pack to resolve bounded context without weakening existing authorities.

## Start here

- Workspace membership and pack lock: `.governance/workspace.json`
- Project facts, authority IDs, routes, environment, and task profiles: `config/governance/project.json`
- Optional ignored machine overlay: `.governance/workspace.local.json`
- Unmigrated machine-policy compatibility authority: `config/project/policy_pack.json`
- Product and architecture truth: the human authorities referenced by the project manifest

Run `./gov check`, then use `./gov resolve` or `./gov explain <key>` for sources and provenance.
`./gov explain --task "<description>"` shows representative-task resolution. Run
`./gov doctor` before environment-dependent work when identity is uncertain.

Resolved stable facts with provenance are sufficient. Reopen canonical sources only for omitted
semantics, ambiguity/conflict, boundary/escalation, provenance audit, or authority edits. See
`docs/architecture/workspace_governance_v0_1.md` for the full rule.

## Choose an execution mode

- `LOCAL_FIX`: reproduce, inspect the minimum owning path/direct tests, then expand from evidence.
- `FEATURE`: identify the owner, neighboring contracts, and a bounded architecture surface.
- `STRUCTURAL_CHANGE`: review authorities, routing, broad impact, migrations, and generated surfaces.

Mode controls exploration cost only. Required evidence always resolves from
the task, authority, actual diff, claims, and risk. Escalate a local fix when
ownership is unclear or crossed, implementations disagree, a generated
authority changes, or packaging/release behavior changes.

Follow `godot/AGENTS.md` or `native/AGENTS.md` when those trees are in scope.
Authority establishment or transfer follows
`docs/architecture/authority_transfer_protocol.md`.
Behaviour evidence and impact-driven authority, documentation, and
`docs/BACKLOG.md` duties are defined canonically in
`docs/governance/CHANGE_GOVERNANCE.md`.
The resolved full gate is `CODEX_MODE=1 ./scripts/verify.sh`; `--verbose` changes
logging only.
