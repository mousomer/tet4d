# Pull Request Contract

## Objective

<!-- State one semantic objective. -->

## Scope

Allowed systems/paths:

- <!-- allowed path -->

Forbidden changes and explicit deferrals:

- <!-- deferral -->

<!-- Add this matrix only for deliberate cross-layer integration. -->

| Layer | Why it must change | Allowed paths | Verification |
| --- | --- | --- | --- |
|  |  |  |  |

## Authority and semantic impact

- Selected routes and workflow modifiers:
- Affected layers and claims:
- Current authority:
- Behavior/schema/identity impact:
- Authority change or transfer: None

## Verification

- [ ] Relevant focused checks passed.
- [ ] `git diff --check`
- [ ] `./scripts/check_git_sanitation_repo.sh`
- [ ] `CODEX_MODE=1 ./scripts/verify.sh`
- [ ] Governance changes ran the governance validators and generated-doc checks.
- [ ] Native tooling changes exercised `TET4D_STRICT_NATIVE_TOOLS=1`, or the
      blocker is recorded.
- [ ] Tests were not weakened to fit implementation.

Required evidence and justified omissions:

- <!-- evidence requirement, or omitted default plus rationale -->

Validation commands and results:

```text
<commands and results>
```

## Manual verification

<!-- Environment, checks, and result; write None when not applicable. -->

## Warnings and limitations

New warnings:

- None

Known advisories:

- None

Unresolved limitations:

- None

## Governance and repository hygiene

- [ ] One semantic objective; no silent continuation into deferred work.
- [ ] Python semantic authority is preserved unless a completed
      authority-transfer protocol record applies.
- [ ] Godot/GDScript remains presentation/adapter code where applicable.
- [ ] C++/GDExtension remains provisional where authority is not transferred.
- [ ] Existing utilities were searched and no unnecessary duplicate helper was
      introduced.
- [ ] Config/constants authority remains explicit.
- [ ] Open debt/deferrals and drift risk were reviewed in `docs/BACKLOG.md`.
- [ ] Generated outputs identify their source and were not hand-edited.
- [ ] Unrelated formatting/toolchain work is separated where practical.
- [ ] Staging is intentional; `git diff --cached --check` passed.
- [ ] No secrets, machine-local paths, or unrelated dirty files are included.
