# Security and Sanitation

Canonical owner: secrets, untrusted strings, dependency safety, repository
hygiene, and safe publication.

## Secrets and private data

Never commit or expose API keys, tokens, passwords, private keys, signing or
production credentials, private URLs, `.env` contents, private identity data,
or machine-local user paths. This applies to source, config, docs, prompts,
logs, traces, fixtures, screenshots, generated output, exported bundles, PRs,
issues, and release metadata.

Placeholders, documented variable names, `.env.example` with fake values, and
redacted logs are allowed. If a secret is found, stop and report it without
copying it elsewhere. Use
`config/project/policy/manifests/secret_scan.json` and the scanner:

```bash
python tools/governance/scan_secrets.py
```

## String and path sanitation

All external or user-controlled strings must use an approved shared sanitation
path before use. This includes CLI and environment values, text entry, file
paths and names, config/persistence payload fields, and future network or
message inputs.

Use this order:

1. existing repository sanitation helpers;
2. standard-library normalization and parsing;
3. a small reviewed shared helper in the existing runtime utility owner.

Strip surrounding whitespace unless the contract preserves it, enforce
explicit allowlists and ranges, reject invalid input with deterministic errors,
and avoid silent coercion. A non-standard exception must state the semantic,
compatibility, or measured-performance reason and test valid, invalid, and edge
cases.

## Dependencies and utilities

Search repository utilities and `docs/architecture/utility_index.md` before
adding helpers. Prefer built-ins, existing dependencies, and maintained
packages. Evaluate correctness, maintenance, license compatibility,
platform/build impact, size, and security. Do not add blocked dependencies from
the policy pack or a dependency for trivial logic. Custom replacements require
a documented reason and focused tests.

## Repository and publication hygiene

- Preserve unrelated user changes. Stage only intentional paths and review the
  staged diff before commit.
- Do not commit generated machine state, credentials, local worktree metadata,
  or unrelated formatting.
- Avoid destructive commands and production-impacting changes unless the task
  explicitly authorizes them and their target is verified.
- All GitHub writes target canonical `origin` under its repository owner. Check
  remote and active transport/CLI identity before writing; if ambiguous, stop.
  Do not publish the identity-check details.
- Run sanitation and whitespace checks required by `VERIFICATION.md` before
  completion.
