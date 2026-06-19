# Review Checklist

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
- [ ] Authority map updated if semantic ownership changed.

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

## Tests

- [ ] Behavioral changes require tests.
- [ ] Migration work requires parity evidence.
- [ ] Testing policy covers Python, C++, and Godot layers.

## Maintainability

- [ ] AGENTS.md files are short and operational.
- [ ] Detailed policy lives under governance/architecture docs.
- [ ] Folder-local rules add constraints without weakening root rules.
