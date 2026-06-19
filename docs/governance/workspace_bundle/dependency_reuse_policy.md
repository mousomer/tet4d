# Dependency and Utility Reuse Policy

Prefer existing project utilities before adding new helpers.

Prefer existing stable libraries for nontrivial generic functionality such as
parsing, serialization, schema validation, cryptography, compression, testing,
formatting, and static analysis.

Do not add dependencies for trivial local logic.

Avoid duplicate utilities, local mini-frameworks, copy/pasted helpers, and
parallel implementations.

Projects should maintain a utility index or equivalent authority map for
reusable helpers.
