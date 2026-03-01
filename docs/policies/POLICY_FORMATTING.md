# Policy: Repository Formatting and Line Length

## Purpose
Keep the codebase readable and consistent by enforcing formatting across all tracked text files (including scripts and tools) and by avoiding excessively long lines.

## Rule
1. Format all tracked text files before commit.
   - Python (`src/`, `tests/`, `scripts/`, `tools/`): `ruff format` with the repo defaults.
   - Shell and other text assets (`.sh`, `.md`, `.json`, `.yaml`, `.yml`): keep conventional indentation, trailing newline, and apply available formatters when present.
2. Line length: keep lines at or below 120 characters for source, scripts, tests, tools, and docs.
   - Brief, documented exceptions are allowed for literals/URLs that cannot be wrapped cleanly.
   - Do not introduce new long lines in scripts; prefer wrapping over horizontal scrolling.
3. No new formatting tools or dependencies may be added without governance approval; use the existing toolchain.

## Exceptions
- Only allow over-120-character lines when wrapping would materially harm clarity (for example, unbreakable URLs or schema examples). Add an inline comment `# format-length-exception: <reason>` nearby.
- When a formatter cannot be applied (for example, generated files in `config/project/format_allowlist.txt`), document the reason in that allowlist.

## Enforcement
- CI executes `scripts/check_policy_compliance.sh`, which runs the repository text-formatting checks. Future lint rules may block long lines; treat this policy as immediately binding for all new/modified lines.
- Code reviews must reject changes that violate this policy or lack documented exceptions.
