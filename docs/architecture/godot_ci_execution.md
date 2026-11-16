# Godot CI execution

Owner: CI execution under `docs/governance/VERIFICATION.md`.
Scope: scheduling and caching only; product authorities are unchanged.

## Parallel Godot acceptance

The canonical Godot gate runs focused Explorer scripts before the complete
registered replay suite. CI partitions the complete registration list across
four zero-based shards by index modulo shard count; every script belongs to
exactly one shard. Each shard retains registration checks, script-error and
leak rejection, pinned engine/API validation, topology parity and startup.
All matrix jobs are required; matrix fail-fast is disabled so evidence remains
available for every partition. Local runs default to the complete suite.

Native dependency caching uses godot-cpp’s existing SCONS_CACHE store, keyed
by runner, compiler, binding pin and build configuration. Cache misses rebuild;
the extension is always built and tested from current source. Cached files
never substitute for test results. Each shard emits its own evidence artifact.
