# Pull Request Checklist

## Summary

- [ ] Change purpose is described.
- [ ] Scope is limited to the stated task.
- [ ] Unrelated dirty files were not staged.

## Authority and architecture

- [ ] Python semantic authority is preserved unless a completed
      authority-transfer record exists.
- [ ] Godot/GDScript changes are presentation, routing, diagnostics, or
      adapter work only, unless explicitly covered by authority transfer.
- [ ] C++/GDExtension changes remain provisional unless covered by parity
      evidence and authority transfer.
- [ ] Authority-map and parity/transfer docs were updated if authority claims
      changed.

## Workspace governance

- [ ] Existing implementation/utilities were searched before adding helpers.
- [ ] No unnecessary rewrite or duplicate implementation was introduced.
- [ ] No secrets, local absolute paths, or machine-specific state were added.
- [ ] Nontrivial constants route through config/constants authority.
- [ ] Generated outputs were not hand-edited.

## Validation

- [ ] Relevant focused tests were run.
- [ ] `tools/governance/validate_governance.py` was run for governance changes.
- [ ] Native tooling changes checked local advisory mode and strict
      `TET4D_STRICT_NATIVE_TOOLS=1` behavior, or documented the blocker.
- [ ] `CODEX_MODE=1 ./scripts/verify.sh` was run, or skipped with reason.
- [ ] Failures/skips are documented below.

## Technical debt and drift

- [ ] New suppressions/advisories are removed, justified, or recorded as debt.
- [ ] Technical-debt delta is described.
- [ ] New governance files are reachable from a router/index/manifest/local
      `AGENTS.md`.
- [ ] New validators are wired into the governance runner.
- [ ] Drift protection impact is described.

## Generated files and staging

- [ ] Generated files were committed separately where practical.
- [ ] Mixed files were staged with `git add -p`.
- [ ] The staged diff was checked with `git diff --cached --check`.

## Notes

Validation commands run:

```text
<commands and results>
```

Remaining risks:

```text
<known risks>
```
