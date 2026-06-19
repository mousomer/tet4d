# General Testing Policy

Behavioural changes require tests. Bug fixes require regression tests.

Tests should verify meaningful behaviour, not just execute lines.

Golden fixtures should identify:

- oracle
- input
- configuration
- expected output
- comparison mode
- tolerance, if any
- reason for inclusion

Validator tests should cover:

- success path
- failure path
- advisory/default mode
- strict mode where applicable
- suppression validity
- excluded paths
