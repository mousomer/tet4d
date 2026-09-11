# Tet4D governance dispatcher

Tet4D uses the vendored `workspace-governance` pack to resolve bounded context
without weakening its existing semantic or verification authorities.

## Start here

- Workspace membership and pack lock: `.governance/workspace.json`
- Project facts, stable authority IDs, routes, environment, and task profiles:
  `config/governance/project.json`
- Machine-local execution overlay (optional and ignored):
  `.governance/workspace.local.json`
- Unmigrated Tet4D machine policy compatibility authority:
  `config/project/policy_pack.json`
- Human product and architecture truth: the authority sources referenced by the
  project manifest

Run `./gov check`, then use `./gov resolve` or `./gov explain <key>` to discover
the applicable source and provenance. `./gov explain --task "<description>"`
shows a declared representative task resolution. Run `./gov doctor` before
environment-dependent work when environment identity is uncertain.

## Choose an execution mode

- `LOCAL_FIX`: reproduce, inspect the minimum owning path and direct tests, then
  expand only from evidence.
- `FEATURE`: identify the owner, neighboring contracts, and a bounded
  architecture surface.
- `STRUCTURAL_CHANGE`: review authorities, routing, broad impact, migrations,
  and generated surfaces as applicable.

Mode controls exploration cost only. Required evidence always resolves from
the task, authority, actual diff, claims, and risk. Escalate a local fix when
ownership is unclear or crossed, implementations disagree, a generated
authority changes, or packaging/release behavior changes.

Follow `godot/AGENTS.md` or `native/AGENTS.md` when those trees are in scope.
Authority establishment or transfer follows
`docs/architecture/authority_transfer_protocol.md`.
Update the owning design source and `docs/BACKLOG.md` for repository changes.
The resolved full gate is `CODEX_MODE=1 ./scripts/verify.sh`; `--verbose` changes
logging only.
