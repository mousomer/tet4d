# tet4d Review Checklist

This checklist extends
`docs/governance/workspace_bundle/review_checklist_template.md`.

Use it for Codex tasks, local commits, PRs, and governance reviews.

## Governance routing

- [ ] Existing governance was inspected.
- [ ] Existing governance was reused or extended.
- [ ] No duplicate policy was created unnecessarily.
- [ ] Root governance remains Python-centered.
- [ ] Godot/C++ governance is scoped as a migration overlay.

## Authority

- [ ] Python semantic authority is preserved.
- [ ] Godot ownership is limited to UI/product-shell/presentation unless
      explicitly documented.
- [ ] C++ authority requires parity evidence.
- [ ] C++/GDExtension remains provisional until parity evidence and a completed
      authority-transfer record exist.
- [ ] No GDScript semantic duplication was introduced.
- [ ] `docs/architecture/authority_map.md`,
      `docs/architecture/parity_protocol.md`, and
      `docs/architecture/authority_transfer_protocol.md` were updated when
      authority claims changed.

## Safety

- [ ] No secrets were introduced.
- [ ] No unsafe memory policy weakening was introduced.
- [ ] No no-rewrite/no-reinvention policy weakening was introduced.

## Dependency / utility reuse

- [ ] Existing helpers, utilities, and libraries were searched before adding a
      new helper.
- [ ] Reusable helpers are routed through `docs/architecture/utility_index.md`
      when they become shared project utilities.
- [ ] No duplicate config loader, trace reader, topology helper, projection
      helper, subprocess wrapper, or local mini-framework was introduced.
- [ ] Utility-reuse advisory findings were reviewed, and strict findings or
      invalid suppressions from `tools/governance/validate_utility_reuse.py`
      were resolved.

## Technical debt

- [ ] `docs/governance/technical_debt_register.md` was checked when debt,
      suppressions, or advisories changed.
- [ ] New suppressions are either removed or recorded as debt.
- [ ] Advisory validator findings introduced by this change are classified.
- [ ] Accepted/deferred cleanup has a debt record with remediation estimate.
- [ ] Technical-debt delta is reported in the final task summary.

## Drift protection

- [ ] `docs/governance/drift_protection_map.md` was checked when governance,
      generated, authority, or validator routing changed.
- [ ] New governance files are reachable from a router, index, manifest, or
      local `AGENTS.md`.
- [ ] New validators are wired into
      `tools/governance/validate_governance.py`.
- [ ] Authority claims remain consistent with
      `docs/architecture/authority_map.md`.
- [ ] Config/generated surfaces still identify source authority or generator.
- [ ] New project overlays link to the workspace policies they extend.
- [ ] Generated outputs were not hand-edited.
- [ ] Generated bundle updates under `migration/exported_bundle/` reflect
      committed source/config/docs.
- [ ] Generated bundle files and other generated outputs were committed
      separately where practical.
- [ ] `docs/BACKLOG.md` and generated bundle files were not staged wholesale
      when they contained mixed hunks.
- [ ] Accepted advisory findings or suppressions are classified or recorded as
      debt.

## Native C++ safety

- [ ] No raw owning pointers.
- [ ] No naked `new` or `delete`.
- [ ] Ownership/lifetime/nullability documented for public APIs and stored
      Godot pointers.
- [ ] GDExtension adapter remains thin.
- [ ] Native code does not become semantic authority without parity evidence.

## Native tooling CI readiness

- [ ] `docs/governance/native_tooling_ci_policy.md` was checked for native
      tooling, CI, clang-format, clang-tidy, or compile database changes.
- [ ] Local advisory mode still skips unavailable native tools without failing
      unrelated local validation.
- [ ] Strict mode with `TET4D_STRICT_NATIVE_TOOLS=1` was run or the blocker was
      recorded as accepted native-tooling debt.
- [ ] CI strict mode was not enabled unless clang-format, clang-tidy, and
      `compile_commands.json` are reproducible.
- [ ] Native tooling readiness was not treated as parity evidence or C++
      semantic authority.

## Parity / authority transfer

- [ ] Python oracle behavior identified.
- [ ] Golden traces or equivalent deterministic fixtures exist.
- [ ] C++ output compared against Python output.
- [ ] Disagreements resolved in favor of Python unless an explicit semantic
      change was approved.
- [ ] Godot visual correctness was not treated as semantic parity.
- [ ] First parity pilot evidence was documented as process-only and not
      authority transfer.
- [ ] The first-pilot audit and promotion gates were checked before approving a
      second parity slice.
- [ ] Review verified Python oracle, fixture set, comparison command, and
      strict/default parity behavior.
- [ ] Any claim of transferred authority has a completed
      `docs/architecture/authority_transfer_protocol.md` transfer record.
- [ ] Authority map updated if semantic ownership changed.
- [ ] Transfer review includes fallback path and known exclusions.

## Godot semantic boundary

- [ ] GDScript does not compute legal moves, topology transitions, collision,
      gravity, rotation validity, scoring, trace correctness, or replay
      correctness.
- [ ] Godot display/replay/probe code treats semantic state as input, not
      locally owned truth.
- [ ] Any semantic-boundary validator suppression has a narrow accepted reason.

## Config

- [ ] Nontrivial constants are routed through config policy.
- [ ] Magic-number policy is clear.
- [ ] Config authority between Python/Godot/C++ is clear.
- [ ] Generated config/reference/migration-bundle outputs identify their source
      authority or generator.
- [ ] Suspicious hardcoded constants from the config-authority validator are
      addressed, suppressed with a narrow reason, or documented as advisory
      debt.

## Tests

- [ ] Behavioral changes require tests.
- [ ] Migration work requires parity evidence.
- [ ] Testing policy covers Python, C++, and Godot layers.

## Validation commands

- [ ] Focused tests or validators relevant to the changed area were run.
- [ ] Governance changes ran `tools/governance/validate_governance.py`.
- [ ] Full verification ran with `CODEX_MODE=1 ./scripts/verify.sh`, or the
      skip/failure reason is recorded.
- [ ] Staged diff hygiene ran with `git diff --cached --check` before commit.

## Staging discipline

- [ ] Unrelated dirty files were not staged.
- [ ] Mixed files were staged with `git add -p`.
- [ ] Generated files were committed separately where practical.

## Final report expectations

- [ ] Files changed and files created are reported.
- [ ] Preserved areas are reported.
- [ ] Checks run and remaining risks are reported.
- [ ] Technical-debt delta and drift/authority implications are reported.

## Maintainability

- [ ] AGENTS.md files are short and operational.
- [ ] Detailed policy lives under governance/architecture docs.
- [ ] Folder-local rules add constraints without weakening root rules.
