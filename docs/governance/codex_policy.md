# Codex Policy

This project overlay extends
`docs/governance/workspace_bundle/programming_policy.md`. Detailed contributor
workflow and verification live in `docs/WORKFLOW_CODEX.md`.

## Before editing

Inspect the current files, tests, and owning authority. Search for existing
implementations, helpers, utilities, libraries, policies, and validators before
adding new ones. For governance work, extend an existing owner instead of
creating a duplicate authority. Check shared utilities against
`docs/architecture/utility_index.md`.

## Task routing

- Python behaviour: relevant RDS, architecture contract, current modules/tests.
- Godot product shell: `godot/AGENTS.md`, Godot/C++ policy, authority map, and
  relevant product/presentation authority.
- Native C++/GDExtension: `native/AGENTS.md`, safety/tooling policies,
  authority map, and applicable parity/transfer protocol.
- Parity implementation: selected subsystem document, Python oracle, fixtures,
  comparison command, strict/default behaviour, and tests.
- Parity evidence review: promotion gates and the applicable evidence package.
- Authority transfer: transfer protocol, fallback, evidence, transfer record,
  and authority-map update.
- Governance: policy pack, router, affected validators/generators/tests.

Use `docs/DOCUMENTATION_MAP.md` to locate current or historical documents.
Completed stage numbers are not universal task context.

## Change discipline

- Preserve Python semantic authority unless an explicit completed transfer
  record changes a named subsystem.
- Do not duplicate semantic rules in Godot, GDScript, or adapter glue.
- Do not rewrite existing functions or governance documents wholesale unless
  the task requests a rewrite or the owning document requires coherent
  restructuring.
- Preserve links and validator coverage when consolidating or splitting
  governance.
- Do not treat partial acceptance as completion.

## Review reporting

Use `docs/governance/review_checklist.md`. Report changed and deliberately
untouched files, authorities reused, routing/authority implications, checks,
and remaining risks.

Parity work additionally reports the Python oracle, fixture evidence,
comparison command, default/strict behaviour, exclusions, and authority
status. Authority-transfer work additionally reports the transfer record,
fallback path, map update, and validation.
