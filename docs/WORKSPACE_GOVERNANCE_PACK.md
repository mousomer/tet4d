# Legacy Workspace Governance Template Pack

This document describes the legacy copy-based template bundle under
`tools/templates/governance/`; it is not the versioned runtime pack.

The canonical versioned pack consumed by Tet4D is
`tools/workspace_governance/`, pinned by
`config/governance/workspace.lock.json`, and specified by
`docs/architecture/workspace_governance_v0_1.md`. Project routes are canonical;
the legacy policy-pack routes are a validated compatibility facade. Other
Tet4D-specific facts remain with their existing authorities.

The pack is deliberately **not** Tet4D authority. Tet4D remains governed by its
root `AGENTS.md` and the canonical project-specific owners under
`docs/governance/`. The reusable pack provides general engineering rules that a
consumer project can adopt and then combine with its own authority, domain,
configuration, verification, and release rules.

## What the pack contains

The current manifest includes:

| File | Purpose | Typical customization |
| --- | --- | --- |
| `README.md` | Bundle overview and adoption notes | Usually |
| `MANIFEST.md` | Bundle inventory and copy contract | Usually |
| `programming_policy.md` | General programming discipline | Usually none |
| `codex_workflow_policy.md` | Agent/workflow rules | Usually |
| `testing_policy.md` | General testing expectations | Usually |
| `config_constants_policy.md` | Config and constants rules | Usually |
| `secrets_policy.md` | General secrets hygiene | Usually none |
| `dependency_reuse_policy.md` | Dependency and utility reuse rules | Usually |
| `technical_debt_policy.md` | Technical-debt accounting rules | Usually |
| `drift_protection_policy.md` | Drift-protection principles | Usually |
| `validator_design_policy.md` | Validator design rules | Usually none |
| `review_checklist_template.md` | Reusable review checklist | Yes |
| `AGENTS.template.md` | Root agent-instruction template | Yes |

The pack intentionally excludes Tet4D-specific product semantics, authority
paths, migration state, configuration locations, build commands, and framework
choices.

## Validate the source pack

Before exporting it, validate the reusable source in Tet4D:

```bash
./scripts/resolve_python_env.sh tools/governance/validate_workspace_bundle.py
```

The validator checks that required files exist, that `MANIFEST.md` describes the
bundle, that the templates remain explicitly non-authoritative, and that known
Tet4D-specific terms and authority references have not leaked into the shared
surface.

The workspace-bundle validator is also part of Tet4D's broader governance
validation path.

## Export the pack into another project

From the Tet4D repository root, first preview the export:

```bash
python tools/governance/export_workspace_governance_bundle.py \
  --target /path/to/other-project/governance/shared \
  --dry-run
```

Then perform the copy:

```bash
python tools/governance/export_workspace_governance_bundle.py \
  --target /path/to/other-project/governance/shared
```

The exporter refuses to overwrite an existing target by default. Use `--force`
only when deliberately replacing an existing exported copy:

```bash
python tools/governance/export_workspace_governance_bundle.py \
  --target /path/to/other-project/governance/shared \
  --force
```

A useful consumer layout is:

```text
other-project/
├── AGENTS.md
├── governance/
│   ├── shared/
│   │   ├── README.md
│   │   ├── MANIFEST.md
│   │   ├── programming_policy.md
│   │   └── ...
│   └── project/
│       ├── authority.md
│       ├── verification.md
│       └── ...
└── ...
```

The exact project-overlay paths are a consumer decision; the important rule is
to keep the reusable generic layer distinct from project-specific authority.

## Adopt the pack in the receiving project

Exporting files is only the bootstrap step. The receiving project should then:

1. Create a project-specific root `AGENTS.md` using `AGENTS.template.md` as a
   starting point.
2. Define the project's own authority map and routing.
3. Register the project's actual verification and build commands.
4. Define project-specific configuration and generated-data locations.
5. Add language-, framework-, platform-, and domain-specific constraints where
   needed.
6. Add or adapt local validators for those project-specific rules.
7. Review the combined governance surface before declaring it authoritative.

The shared pack should own generic engineering/process rules. The consuming
repository should own facts that are true only for that project.

### Shared layer

Examples of suitable shared concerns include:

- programming and review discipline;
- testing principles;
- dependency reuse before reinvention;
- secrets and repository hygiene;
- technical-debt accounting;
- drift protection;
- validator design.

### Project overlay

Examples that should remain local include:

- authority maps;
- product/domain semantics;
- exact verification commands;
- configuration and generated-file locations;
- language/framework/platform constraints;
- release/product matrices;
- current-state and backlog context.

A copied template must not become authoritative merely because it exists in the
repository. Authority should be established explicitly after project-specific
review and routing are in place.

## Updating an existing consumer

The current mechanism is copy-based rather than package/version based. To update
a consumer today:

1. validate the Tet4D source pack;
2. export to a temporary directory or use `--dry-run` to inspect the intended
   copy;
3. compare the new shared files with the consumer's current shared copy;
4. review upstream generic-policy changes separately from local overlay changes;
5. replace the shared copy deliberately;
6. rerun the consumer project's own governance and verification gates.

Avoid using `--force` as an unreviewed synchronization mechanism. Consumer-local
changes inside the shared directory are signs of drift and should normally be
moved into the project overlay instead of being silently overwritten.

## Current limitation and planned direction

At present, Tet4D is still the source repository for the reusable pack and the
exporter performs a filesystem copy. There is not yet a canonical external,
versioned governance package with deterministic consumer pinning.

The planned evolution is tracked in:

- [#103 — Establish canonical shared workspace-governance source](https://github.com/mousomer/tet4d/issues/103)
- [#104 — Make Tet4D consume versioned shared governance with drift protection](https://github.com/mousomer/tet4d/issues/104)
- [#105 — Validate shared governance on a second project and document adoption workflow](https://github.com/mousomer/tet4d/issues/105)

The intended end state is a canonical shared source, explicit version pinning,
drift detection, project-specific overlays, deterministic offline verification,
and validation in at least one independent second project.
