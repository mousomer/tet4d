# Workspace governance v0.1 donor freeze

Recorded before substantive extraction on 2026-09-10.

- Donor branch: `codex/live-4d-cockpit-convergence-rebuilt`
- Donor HEAD: `ce5e57b8af3cdf18c11363fd1e547d182cfec498`
- Worktree: dirty with an unrelated live-cockpit documentation, Godot, test,
  design-evidence, and UI-export change; those paths were preserved and excluded
  from governance commits.

## Extraction-sensitive hashes at donor HEAD

| Path | SHA-256 |
| --- | --- |
| `AGENTS.md` | `ae90dacc8a854403c66755cb4343ec76452c5b41b60922b18b697a53baa3b527` |
| `config/project/policy_pack.json` | `da6e2dd66e723d224a65aac5c1e70150ff4e982f744304bb76918fe6399058fd` |
| `scripts/verify.sh` | `c9ff740644b202a1ec3acceabdc5e48b6cd341d25877cc680e677e60c2c18c29` |
| `scripts/bootstrap_env.sh` | `6bd41a97860485d05790989a79e74ca5fbd0a27a657309ff60019971cb7b93c6` |
| `scripts/check_editable_install.sh` | `5830fd6671b83abac8224ea5f1cc010dd83af5d2c4edeeac7dd0c6e0b1e153f6` |
| `tools/governance/validate_governance.py` | `b6bcd03909ec9be4eec3507263ad2bbb1365bc736073fd44e87268702508844f` |
| `tools/governance/resolve_codex_verification.py` | `aa079816a74bef0cd32a56f1ea02995a1aee4e98f8d5981e665774be352bf473` |
| `tools/governance/validate_workspace_bundle.py` | `53fcaf35f80a515f44041c96b9deb1385604d3540f9f3a1c929e9fa825233576` |
| `tools/governance/scan_secrets.py` | `81b2e35ac543bbf2692f15a9cf9a7747cd378e226b61a9b493f30565a76c237f` |
| `docs/ARCHITECTURE_CONTRACT.md` | `89de7bef57ed06a8bbb853e3436b585edd9a68799307d2d0f225fd12568a6915` |
| `docs/architecture/authority_map.md` | `2cb0e38565b46827c7ccc8b9bf24b87721bf8d906be22dcdbba5778450e03b89` |
| `docs/governance/VERIFICATION.md` | `9a76d3b39ca5964fdc5abdbd9333d69b73f16c6c7c60868bfa41d7729acb7ccc` |

## Donor coupling

Root dispatch selected route and authority keys from the monolithic policy
pack. The legacy verification resolver consumed that routing directly.
`verify.sh`, `check_editable_install.sh`, and policy checks independently chose
Python and permitted system fallback. `verify_local.sh` repaired `.venv` and
editable-install identity, while the canonical entrypoint did not. Governance
validation aggregated specialized validators; generated maintenance/config
surfaces and the workspace template bundle were policy-pack driven. Secret and
path sanitation already existed and was retained rather than duplicated.
