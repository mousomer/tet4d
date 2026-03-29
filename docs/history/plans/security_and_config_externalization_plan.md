# Security And Config Externalization Plan

Status: historical reference
Last updated: 2026-03-29

This document preserves the older standalone policy-plan framing for secret
scanning and config externalization.

Current policy authority no longer lives here.
Use the live governance layer instead:

- `config/project/policy/governance.json`
- `config/project/policy/code_rules.json`
- `docs/policies/INDEX.md`
- `config/project/policy/manifests/secret_scan.json`
- `config/project/io_paths.json`
- `config/project/constants.json`

## Historical scope

The original plan defined:

1. repository-level secret scanning policy and CI enforcement
2. repository-level policy for moving runtime constants and path definitions
   into editable config files

## Historical implemented controls

### Secret scanning

- policy file: `config/project/policy/manifests/secret_scan.json`
- scanner: `tools/governance/scan_secrets.py`
- CI/local gate integration through the repo verification scripts

### Path/config externalization

- canonical path defaults in `config/project/io_paths.json`
- canonical runtime constants in `config/project/constants.json`
- generated references in `docs/CONFIGURATION_REFERENCE.md` and
  `docs/USER_SETTINGS_REFERENCE.md`
- config-reference generator/check in
  `tools/governance/generate_configuration_reference.py`
- safe loader/resolver in `src/tet4d/engine/runtime/project_config.py`

## Historical notes

- The old standalone plan is retained only as background.
- Ongoing policy updates should be made in the unified governance layer and
  synchronized through the current maintenance contracts.
