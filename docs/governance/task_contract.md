# Task Contract

Use this contract for work that changes repository state. It constrains the
outcome and boundaries; it does not prescribe routine implementation steps.

## Objective

State one semantic objective. If the work has multiple independent objectives,
split it into separate tasks and pull requests.

## Current Authority

List the product, architecture, migration, governance, and implementation
sources that decide the change. State whether Python semantic authority or any
recorded subsystem transfer applies.

## Allowed Systems and Paths

Name the systems and path families that may change. Cross-layer work must add a
scope matrix:

| Layer | Why it must change | Allowed paths | Verification |
| --- | --- | --- | --- |
| Example | Required integration seam | `path/**` | focused check |

## Required Changes

Describe the observable or contractual changes needed to satisfy the objective.

## Forbidden Changes

List adjacent behavior, authority, schemas, toolchains, formatting, or product
areas that must remain unchanged.

## Acceptance Criteria

Use objective, directly verifiable criteria. Partial satisfaction is not
completion.

## Automated Verification

List focused checks, deterministic/parity evidence, validators, sanitation, and
the applicable final gate.

## Manual Verification

List required real-window, device, packaging, accessibility, performance, or
subjective acceptance. Write `None` when no manual verification applies.

## Documentation Updates

Name the owning design/status/backlog documents that must change. Historical
records remain historical; do not turn a task contract into a stage diary.

## Explicit Deferrals

Name visible adjacent work that is deliberately outside this task. Completion
does not silently authorize continuation into a deferral.
