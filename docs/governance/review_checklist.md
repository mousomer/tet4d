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
