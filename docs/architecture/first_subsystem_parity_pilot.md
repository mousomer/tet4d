# First Subsystem Parity Pilot

This pilot is an evidence-only process check for `stable_hash_text(text)`.

Scope:
- Python remains the semantic oracle.
- The pilot compares a narrow, deterministic text fixture set.
- The result is either candidate evidence or a blocked follow-up.
- It must not be recorded as an authority transfer.

Fixture set:
- `""`
- `tet4d`
- `oracle-check`
- `hash-bridge`

Primary commands:
- `PYTHONPATH=src .venv/bin/python tools/migration/first_subsystem_parity_pilot.py`
- `TET4D_STRICT_PARITY=1 PYTHONPATH=src .venv/bin/python tools/migration/first_subsystem_parity_pilot.py`
- `./scripts/test_godot_tet4d_core.sh --pilot-stable-hash`

Routing:
- `docs/architecture/parity_protocol.md`
- `docs/architecture/authority_transfer_protocol.md`
- `docs/architecture/parity_pilot_audit_and_promotion_gates.md`
- `docs/governance/README.md`
- `docs/governance/drift_protection_map.md`

Status rule:
- Evidence-only pilot results stay process documentation.
- No authority transfer entry may say `transferred`.

Mode rule:
- Default mode is advisory only when the native bridge/toolchain is unavailable.
- `TET4D_STRICT_PARITY=1` makes native unavailability blocking.
- Any real hash mismatch is blocking.
