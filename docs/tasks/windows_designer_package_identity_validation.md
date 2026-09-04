# Task Contract — Windows Designer Package Identity Validation

Status: active on `codex/fix-designer-package-identity-validation`.

## Objective

Repair the narrow Windows Designer packaging-validator defect that blocks the
0.9.0 release candidate. The repair proves the exported package identity from
the PCK resource table; it does not run, create, publish, or promote a release.

## Authority and scope

`config/project/policy_pack.json` remains the product/profile authority and
`docs/rds/RDS_PACKAGING.md` owns this package boundary. Routes are
`godot_product_shell`, `governance_and_tooling`, and `packaging_and_release`;
the workflow modifier is `cross_layer` (profile staging, Godot export, package
validation).

| Layer | Allowed change | Consumer evidence |
| --- | --- | --- |
| Profile staging | Generate and validate an identity resource from the selected canonical profile. | Staging tests reject an incorrect ID or scene. |
| Godot export | Include the staged, profile-bound identity resource in the PCK. | A real-format PCK table carries the selected marker. |
| Windows validator | Parse the PCK table and require the Designer marker. | Designer passes; absent, Game, and arbitrary-text cases fail. |
| Documentation | Record the exported-identity rule and release blocker. | Packaging and governance validation. |

## Acceptance criteria

1. The validator fails closed on malformed PCK data, a missing Designer marker,
   or a Game marker; a filename or arbitrary source-config text cannot pass it.
2. Staging proves exact Designer ID, display name, main scene, and the generated
   profile marker before the Windows export begins.
3. Existing PE product-name, payload, version, and sanitation checks remain.
4. Godot stays pinned to 4.7.2; the registry, matrix, `current_all`, explicit
   submatrix semantics, Android, and iPadOS classifications stay unchanged.
5. Focused tests, the repository canonical gate, exact-head PR CI, and exact
   merge-commit `master` CI pass before completion.

## Explicit non-goals and deferrals

No version, registry, release-scope, signing, runtime, or release-workflow
change is permitted. No tag, draft/public release, artifact reuse, or dispatch
is authorized. Clean-machine Windows runtime acceptance remains separately
deferred in `docs/BACKLOG.md`.
