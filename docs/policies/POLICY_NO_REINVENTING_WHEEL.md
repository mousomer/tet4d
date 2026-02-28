# Policy: No Reinventing the Wheel

## Purpose

Prevent unnecessary custom implementations when reliable existing solutions
already satisfy correctness, performance, licensing, and maintenance needs.

## Rule

Do not implement custom functionality if an existing solution already covers
the need with acceptable correctness, performance, licensing, and maintenance.

## Scope

This policy applies to:
1. parsing, validation, formatting, serialization
2. data structures and algorithms
3. configuration loading and access
4. CLI and utility plumbing
5. UI widgets and interaction helpers
6. math and geometry helpers
7. logging, metrics, and persistence utilities

## Default Decision Order

Evaluate options in this order:
1. language built-ins and standard library
2. dependencies already present in this repository
3. widely used and maintained third-party packages
4. small code copied from authoritative sources with compatible license
   (last resort)

## Exceptions

Custom code is allowed only when documented and one of these applies:
1. correctness mismatch with required semantics
2. performance or memory constraints (with profiling evidence)
3. dependency constraints (size/platform/web/WASM/build/security)
4. licensing incompatibility
5. stability or maintenance risk (unmaintained, low adoption, brittle)
6. integration complexity exceeds minimal verified implementation

## Mandatory Documentation for Exceptions

When taking an exception, include all of the following:
1. a short header comment: `Wheel Exception: ...`
2. alternatives considered
3. chosen exception reason category
4. minimal tests for expected behavior and edge cases

## Review and Enforcement

1. PR review rejects reinventions without the required exception block.
2. CI may add a lint note that flags common reinventions, for example:
   ad-hoc JSON parsing, ad-hoc CLI parsing, and ad-hoc bool parsing.

## Examples

1. Not allowed: implementing custom boolean parsing when standard options exist.
2. Allowed with exception: strict accept/reject boolean semantics that standard
   options cannot express, with tests and exception note.
