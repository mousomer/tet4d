# Advisory sanitation reference review

The security policy owns sanitation requirements. This document defines the
Tet4D baseline integration's reviewed-reference mechanism; it changes no product
behavior, semantic ownership, strict sanitation or secret-scanning contract.

The advisory baseline retains its Git-visible scan scope, path warning classes,
filename-space check and advisory exit semantics. Its generic string matches
also find required scanner literals, negative-test inputs, relative build and
application resource paths, and links to canonical skills inside the repository.
These references are intentional rather than machine-local user paths or
unvalidated user-controlled traversal.

`config/project/policy/manifests/sanitation_references.json` records reviewed
warning class, repository-relative file, source-line SHA-256 and reason. Each
listed digest approves one occurrence. Moving that source line within the file
preserves review; changing it, copying it to another file or adding another
occurrence retains a warning. No file-wide or directory-wide grant is supported.
Malformed registers fail closed. Missing registers grant no exceptions.

`scripts/check_git_sanitation.sh` filters each advisory class through
`tools/governance/filter_sanitation_findings.py`. The stricter repository
sanitation check and secret scanner do not consume this register. The shared
policy-kit release and immutable baseline copy remain unchanged. The optional
local template-hash manifest is refreshed through its existing generator.

Regression evidence must exercise the actual shell baseline, clean reviewed
references, new real path findings in every class, changed/copied/duplicate
references and malformed register rejection. Run the focused sanitation tests
and the canonical full repository gate before completion.

The shared fleet planner and audit both refused with
`DISTRIBUTION_VALIDATION_FAILED` during this repair. This repository correction
does not resolve that separate distribution-validation boundary, change fleet
files or claim fresh fleet adoption. Further distribution work must use the
canonical kit's guarded migration and verification workflow.
