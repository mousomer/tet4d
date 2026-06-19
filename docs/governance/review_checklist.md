# Review Checklist

This checklist extends the reusable workspace governance in
`docs/governance/workspace_bundle/`.

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
- [ ] No GDScript semantic duplication was introduced.

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

- [ ] New suppressions are either removed or recorded as debt.
- [ ] Advisory validator findings introduced by this change are classified.
- [ ] Accepted/deferred cleanup has a debt record with remediation estimate.
- [ ] Technical-debt delta is reported in the final task summary.

## Drift protection

- [ ] New governance files are reachable from a router, index, manifest, or
      local `AGENTS.md`.
- [ ] New validators are wired into
      `tools/governance/validate_governance.py`.
- [ ] Authority claims remain consistent with
      `docs/architecture/authority_map.md`.
- [ ] Config/generated surfaces still identify source authority or generator.
- [ ] New project overlays link to the workspace policies they extend.
- [ ] Generated outputs were not hand-edited.
- [ ] Accepted advisory findings or suppressions are classified or recorded as
      debt.

## Native C++ safety

- [ ] No raw owning pointers.
- [ ] No naked `new` or `delete`.
- [ ] Ownership/lifetime/nullability documented for public APIs and stored
      Godot pointers.
- [ ] GDExtension adapter remains thin.
- [ ] Native code does not become semantic authority without parity evidence.

## Parity / authority transfer

- [ ] Python oracle behavior identified.
- [ ] Golden traces or equivalent deterministic fixtures exist.
- [ ] C++ output compared against Python output.
- [ ] Disagreements resolved in favor of Python unless an explicit semantic
      change was approved.
- [ ] Godot visual correctness was not treated as semantic parity.
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
- [ ] Suspicious hardcoded constants from the config-authority validator are
      addressed, suppressed with a narrow reason, or documented as advisory
      debt.

## Tests

- [ ] Behavioral changes require tests.
- [ ] Migration work requires parity evidence.
- [ ] Testing policy covers Python, C++, and Godot layers.

## Maintainability

- [ ] AGENTS.md files are short and operational.
- [ ] Detailed policy lives under governance/architecture docs.
- [ ] Folder-local rules add constraints without weakening root rules.
