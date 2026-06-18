# Config and Constants Policy

This file routes Godot/C++ migration-specific config ownership. The repo-wide
authorities remain:

- `docs/policies/POLICY_CONFIGURATION_DOCUMENTATION.md`
- `docs/policies/POLICY_NO_MAGIC_NUMBERS.md`

## Migration authority

Python configuration remains authoritative for current Python behavior unless
`docs/architecture/authority_map.md` records a narrower transfer.

Godot UI constants may live in Godot theme/config resources when they affect
presentation only. Gameplay and topology constants must not be redefined
independently in Godot.

## Required behavior

When adding a new nontrivial migration constant:

1. Follow the existing config authority and access pattern.
2. Add or update schema/validation if the repo uses schemas.
3. Add default and fixture values where needed.
4. Keep config lookup localized behind existing typed accessors or a new
   documented accessor.
