# Save State Migration Ledger

Canonical schema: `/Users/omer/workspace/test-code/tet4d/config/schema/save_state.schema.json`
Planned runtime file: `/Users/omer/workspace/test-code/tet4d/state/save_state.json`

## Version 1 (planned)

- Defines canonical save payload sections:
  - `version`, `mode`, `timestamp_utc`, `seed`
  - `config`, `board`, `active_piece`, `metrics`, `status`

## Migration policy

1. Any incompatible structure change increments `version`.
2. Conversion scripts must document before/after examples in this file.
3. Recovery path for unreadable saves: reject payload, keep previous file, show non-fatal UI warning.

## Compatibility notes

1. Save files must stay JSON (RFC 8259 strict JSON in repository policy).
2. New fields should be additive where possible to reduce migration churn.
