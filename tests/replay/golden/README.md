# Replay Golden Fixtures

Golden fixtures capture Python-oracle behavior used to validate
C++/GDExtension parity.

Do not add large generated traces casually.

Every fixture should identify:

- subsystem
- scenario
- Python oracle source
- configuration source
- expected output
- comparison mode
- tolerance, if any
- reason for inclusion

See `docs/architecture/parity_protocol.md`.
