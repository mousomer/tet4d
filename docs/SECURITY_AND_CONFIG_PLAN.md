# Security And Config Externalization Plan

## 1. Scope

This plan defines:
1. repository-level secret scanning policy and CI enforcement,
2. repository-level policy for moving runtime constants and path definitions into editable config files.

## 2. Secret scanning policy

Implemented controls:
1. policy file: `config/project/secret_scan.json`,
2. scanner: `tools/scan_secrets.py`,
3. CI/local gate: `scripts/ci_check.sh` (runs the scanner before lint/tests).

Rules:
1. no credentials, API keys, private keys, or long-lived tokens are committed,
2. scanner patterns are managed centrally in `config/project/secret_scan.json`,
3. allowlist exceptions must be explicit and narrow (`path_glob` + optional `pattern_ids` + optional `contains`),
4. scanner failures block CI until resolved.

Remediation flow:
1. remove/rewrite the leaked secret in source,
2. rotate/revoke the credential in the provider system,
3. add a targeted regression test or scanner rule update if the leak shape was missed,
4. document the change in `docs/CHANGELOG.md` when policy or scanner behavior changes.

## 3. Path/config externalization policy

Implemented controls:
1. canonical path defaults in `config/project/io_paths.json`,
2. canonical runtime constants in `config/project/constants.json`,
3. safe loader/resolver in `tetris_nd/project_config.py`,
4. path consumers updated to use safe `Path` resolution:
5. `tetris_nd/keybindings.py`,
6. `tetris_nd/menu_settings_state.py`,
7. `tetris_nd/runtime_config.py`,
8. `tetris_nd/score_analyzer.py`.

Rules:
1. I/O paths must be repo-relative and sanitized (`..`, drive prefixes, absolute paths rejected),
2. state outputs must remain under configured state root,
3. modules should use `pathlib.Path` joins/resolution, not ad-hoc string path composition.

## 4. Constants externalization roadmap

Current externalized constants:
1. cache limits (`gradient_surface_max`, `text_surface_max`, `projection_lattice_max`),
2. rendering layout constants for `2d`, `3d`, `4d` panel/margin and 4D layer gap.

Next batches:
1. move additional UI timing constants (animation durations) into `config/project/constants.json`,
2. move color/theme palettes into a dedicated config section if visual customization is required,
3. keep defaults in code only as strict fallback values for invalid/missing config fields.

## 5. Governance

1. update `docs/BACKLOG.md` and relevant `docs/rds/*.md` for each policy/contract change,
2. keep `config/project/canonical_maintenance.json` aligned with these artifacts,
3. run `scripts/ci_check.sh` before push and release.
