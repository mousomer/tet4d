# Menu Settings Migration Ledger

Canonical schema: `config/schema/menu_settings.schema.json`  
Runtime file: `state/menu_settings.json`

## Version 1

- Introduced unified payload envelope:
  - `version`,`active_profile`,`last_mode`
- `audio`,`display`,`settings`
- `settings` split by mode (`2d`,`3d`,`4d`) with bot fields per mode.
- Mode payload includes gameplay setup fields such as:
  - board sizes,
  - piece-set index,
  - `exploration_mode`,
  - `topology_mode` (`0=bounded`,`1=wrap_all`,`2=invert_all`),
  - `topology_advanced` (`0=off`,`1=on`),
  - `topology_profile_index` (profile row index in `config/topology/designer_presets.json`).

## Migration policy

1. Increment `version` for any incompatible field rename/type change.
2. Preserve backward compatibility for additive optional fields in the same major version.
3. If a payload cannot be migrated safely, reset to `config/menu/defaults.json` and log a warning.

## Next planned migration points

1. Persist keybinding profile metadata checksum.
2. Persist explicit menu-layout/profile preference version coupling.
