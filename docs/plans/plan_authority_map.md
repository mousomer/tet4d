# Plan Authority Map

Role: authority
Status: active
Source of truth: this file for planning-document ownership and precedence
Supersedes: ad hoc ownership notes spread across active planning docs
Last updated: 2026-03-22

## Purpose

Define which planning document owns which kind of rule.

This file exists so domain-specific files do not have to double as general
planning redirection notes.

## Ownership matrix

| Topic | Owning document |
| --- | --- |
| Planning-layer taxonomy, file roles, retirement rules | `README.md` |
| Planning-document ownership and precedence | `plan_authority_map.md` |
| Repo-wide structural cleanup sequencing | `cleanup_master_plan.md` |
| Topology-playground architecture, invariants, non-goals | `topology_playground_current_authority.md` |
| Topology-playground visible shell contract | `topology_playground_shell_redesign_spec.md` |
| Topology-playground transitional debt | `topology_playground_debt_register.md` |
| Domain reference material retained in active plans | reference files only |
| Completed one-off pass notes | history only |

## Conflict rule

When documents disagree, precedence is:

1. newer task instruction
2. this ownership map for determining document owner
3. owning active `authority` document
4. owning active or frozen `spec` document
5. active `ledger` documents
6. `reference` documents
7. historical documents

If a lower-precedence file conflicts with a higher-precedence file, fix the
lower-precedence file in the same batch.

## Scope rule

A filename should match the authority scope of the document.

- General planning infrastructure gets general names.
- Topology-playground-specific authority/spec/debt files keep topology-
  playground-specific names.
- A topology-playground file must not become the general routing document for
  the whole planning layer.

## Non-goals

This file does not define:
- topology-playground architecture,
- topology-playground shell behavior,
- cleanup-stage details,
- domain reference content.
