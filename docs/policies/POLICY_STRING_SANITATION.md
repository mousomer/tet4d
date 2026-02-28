# Policy: String Sanitization

## Purpose

Prevent malformed, unsafe, or inconsistent string inputs from entering runtime,
configuration, persistence, or UI flows.

## Rule

All external or user-controlled string inputs must be normalized and validated
through approved sanitization helpers before use.

## Scope

This policy applies to:
1. CLI arguments and environment-variable values
2. menu and settings text input
3. file paths and file-name segments
4. config payloads loaded from JSON/YAML
5. persistence read/write payload fields
6. network/message payload strings (if introduced)

## Approved Decision Order

Use this order:
1. existing repository sanitization helpers
2. language standard-library normalization and parsing tools
3. small, reviewed shared helper additions in `engine/runtime`

## Minimum Requirements

1. Strip surrounding whitespace unless semantics require preserving it.
2. Enforce explicit allowlists/ranges for constrained values.
3. Reject invalid values with deterministic, testable errors.
4. Avoid silent coercions that hide malformed input.

## Exceptions

Custom handling is allowed only when documented:
1. strict domain semantics require non-standard parsing behavior
2. compatibility constraints require temporary transitional handling
3. performance constraints are demonstrated and reviewed

## Mandatory Documentation for Exceptions

When taking an exception, include:
1. header comment: `Sanitization Exception: ...`
2. alternatives considered
3. reason category
4. tests for valid, invalid, and edge-case inputs

## Review and Enforcement

1. PR review rejects unsanitized external string handling.
2. Validation and runtime config paths must use canonical sanitization helpers.
3. New string-entry points require targeted tests.
