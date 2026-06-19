# Drift Protection Policy

## Scope

This policy defines reusable governance drift-protection principles.

It does not define project-specific authority, concrete generated surfaces,
concrete validators, domain semantics, or project-specific migration plans.

## General drift risks

Projects should guard against:

- governance files that are not reachable from a router or index
- reusable bundle files that are missing from a manifest
- project overlays that fail to link to their general workspace policies
- generated outputs that do not identify their source authority or generator
- validators that are not wired into the main governance runner
- advisory findings or suppressions that are never classified
- authority claims that conflict across documents
- deprecated, replaced, or superseded policies that remain unmarked
- policy files that are not covered by tests or validation
- duplicated general policy prose that drifts between overlays

## General drift-protection rules

- Every governance file should be reachable from a router, index, manifest, or
  local agent instruction file.
- Every reusable bundle file should appear in the bundle manifest.
- Project-specific overlays should link to the general workspace policies they
  extend.
- Generated outputs should identify their generator, source configuration, or
  contract.
- Validators should be integrated into the project's main governance validation
  command.
- Suppressions and advisory findings should be classified, removed, or recorded
  as debt.
- Authority claims should be centralized or cross-checked.
- Deprecated or superseded governance should be marked clearly or removed.
- Drift validators should report actionable findings and avoid broad false
  positives.

## Project-specific drift maps

Each adopting project should define its own drift surfaces, such as:

- authority maps
- config/generated output relationships
- dependency and utility indexes
- parity or golden-fixture protocols
- local agent routing files
- project-specific validators
- generated documentation surfaces

The reusable bundle defines the model. The adopting project defines the
concrete drift map.
