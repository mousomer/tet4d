# Adaptive File Fetch Library RDS (Small Python Library)

Status: Draft v0.1 (Design baseline, Verified 2026-02-20)  
Author: Omer + Codex  
Date: 2026-02-20  
Target Runtime: Python 3.11+

## 1. Purpose

Define a small Python library that manages file-fetch lifecycle operations with predictable memory behavior and runtime strategy adaptation:
1. load files,
2. keep selected files resident in memory,
3. save file updates safely,
4. clean memory on demand or under pressure.

The library must optimize fetch behavior on the go by learning from recent workload patterns without requiring heavyweight infrastructure.

## 2. Canonical Design Location

This file is the canonical requirements/design specification for this library concept.
1. API docs may summarize usage, but this RDS defines behavior contracts.
2. Implementation choices should not contradict lifecycle semantics in this RDS.

## 3. Design Goals

1. Small API surface for local and service use.
2. Deterministic core behavior under fixed configuration.
3. Bounded memory usage with explicit controls.
4. Runtime adaptation across different access patterns:
5. random reads,
6. sequential scans,
7. write-heavy bursts,
8. mixed workloads.
9. Safe failure semantics for load/save operations.
10. Minimal external dependencies.

## 4. Non-Goals

1. Distributed multi-node cache coherence.
2. Full data-lake ingestion framework behavior.
3. Mandatory ML model training pipeline.
4. Kernel-level or filesystem-driver features.

## 5. Terminology

1. `fetch`: any operation that materializes file content for caller use.
2. `residency`: cached in-memory presence of file content or decoded representation.
3. `hot file`: frequently accessed file with high recency/frequency score.
4. `dirty entry`: in-memory content modified but not durably flushed.
5. `policy profile`: named strategy bundle for caching/prefetch/write behavior.

## 6. File Action Model (Differences by Action Group)

### 6.1 Load actions

1. `load(path, ...)`:
2. reads full file and returns complete payload.
3. may populate memory cache.
4. `load_if_cached(path)`:
5. returns payload only if already resident; never hits disk/network.
6. `stream(path, chunk_size, ...)`:
7. yields chunks without requiring full in-memory materialization.
8. `prefetch(paths)`:
9. opportunistic background load for predicted near-future reads.

Key difference: load actions determine how bytes enter memory and whether the call blocks on full data availability.

### 6.2 Memory-residence actions

1. `pin(path)`:
2. marks an entry as non-evictable unless explicitly unpinned or emergency trim occurs.
3. `touch(path)`:
4. updates recency/frequency counters without re-reading file bytes.
5. `set_ttl(path, seconds)`:
6. sets freshness window for cache validity.
7. `unpin(path)`:
8. restores normal eviction eligibility.

Key difference: residence actions control in-memory lifecycle without changing persisted file state.

### 6.3 Save actions

1. `save(path, data, mode="write_through")`:
2. writes and persists immediately; returns after durable write success.
3. `save(path, data, mode="write_back")`:
4. updates cache first, marks entry dirty, flushes later.
5. `flush(path=None)`:
6. forces dirty entries (one or all) to durable storage.
7. `checkpoint()`:
8. flushes all dirty entries and emits consistency marker/summary event.

Key difference: save actions govern durability guarantees and dirty-state transitions.

### 6.4 Cleanup actions

1. `release(path)`:
2. evicts specific entry (or marks as evictable immediately).
3. `trim_to_budget(bytes_limit)`:
4. evicts until memory budget is satisfied.
5. `clear_cache(include_pinned=False)`:
6. bulk eviction operation with optional pinned override.
7. `clean_expired()`:
8. removes stale entries based on TTL/age policy.

Key difference: cleanup actions reclaim memory and remove stale state; they do not load or save new user data.

## 7. Core Components

1. `FetchManager` (facade):
2. user-facing API for all lifecycle operations.
3. `StorageAdapter`:
4. pluggable backend (`local_fs` baseline; optional remote backends later).
5. `MemoryStore`:
6. cache entries, recency/frequency stats, pin/dirty/ttl metadata.
7. `Optimizer`:
8. policy profile selection and dynamic parameter tuning.
9. `TelemetrySink`:
10. request/latency/hit-rate/eviction/flush metrics emission.

## 8. Optimization Toolbox

The optimizer may use one or more of the following tools:
1. Eviction policy:
2. `LRU` baseline,
3. optional `LFU-lite` for highly repetitive workloads.
4. Admission control:
5. skip caching for one-off large scans that reduce hit ratio.
6. Prefetch policy:
7. sequential detector (next-N files/chunks),
8. caller-hint prefetch queue.
9. Write policy switching:
10. choose `write_through` for durability-critical mode,
11. choose `write_back` for burst throughput mode.
12. Dynamic memory partitioning:
13. reserve pool for pinned/hot entries,
14. reserve pool for streaming buffers.
15. Hysteresis-based profile switching:
16. avoid rapid oscillation between policies.

## 9. On-The-Go Optimization Strategy

Recommended default approach:
1. Collect rolling-window telemetry:
2. cache hit rate,
3. p50/p95 load latency,
4. dirty backlog size,
5. eviction churn,
6. memory pressure events.
7. Score candidate policy profiles on weighted utility:
8. `utility = w_hit*hit_rate - w_lat*p95_latency - w_churn*eviction_churn - w_dirty*dirty_backlog`.
9. Switch profiles only if improvement crosses threshold and cooldown interval is met.
10. Expose manual override to lock profile during debugging/benchmarking.

## 10. RL vs Alternatives (Recommended Decision)

For a small library, full reinforcement learning should not be the default strategy.

Preferred path:
1. Start with rule-based adaptive heuristics + profile scoring (Section 9).
2. Add optional contextual bandit selection (for profile choice only) if workloads vary significantly.
3. Use full RL only if all are true:
4. large and diverse telemetry volume,
5. stable reward definition,
6. safe offline simulation/replay environment,
7. clear measured benefit over simpler methods.

Rationale:
1. simpler methods are easier to debug and safer for data durability paths,
2. they converge faster with smaller data,
3. operational behavior remains more predictable.

## 11. Public API Contract (Proposed)

```python
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Iterator, Literal, Optional

SaveMode = Literal["write_through", "write_back"]

@dataclass(frozen=True)
class FetchConfig:
    max_memory_bytes: int = 256 * 1024 * 1024
    default_ttl_seconds: int = 300
    policy_profile: str = "balanced"
    enable_prefetch: bool = True
    enable_adaptive_optimizer: bool = True

@dataclass(frozen=True)
class FetchStats:
    cache_entries: int
    cache_bytes: int
    hit_rate: float
    p95_load_ms: float
    dirty_entries: int
    evictions: int
    profile: str

class FetchManager:
    def __init__(self, config: FetchConfig) -> None: ...
    def load(self, path: Path, *, use_cache: bool = True) -> bytes: ...
    def load_if_cached(self, path: Path) -> Optional[bytes]: ...
    def stream(self, path: Path, *, chunk_size: int = 65536) -> Iterator[bytes]: ...
    def prefetch(self, paths: Iterable[Path]) -> None: ...

    def pin(self, path: Path) -> None: ...
    def unpin(self, path: Path) -> None: ...
    def set_ttl(self, path: Path, seconds: int) -> None: ...
    def touch(self, path: Path) -> None: ...

    def save(self, path: Path, data: bytes, *, mode: SaveMode = "write_through") -> None: ...
    def flush(self, path: Optional[Path] = None) -> int: ...
    def checkpoint(self) -> int: ...

    def release(self, path: Path) -> bool: ...
    def trim_to_budget(self, bytes_limit: int) -> int: ...
    def clear_cache(self, *, include_pinned: bool = False) -> int: ...
    def clean_expired(self) -> int: ...

    def stats(self) -> FetchStats: ...
    def set_profile(self, profile: str) -> None: ...
    def optimize_now(self) -> str: ...
```

## 12. Error and Consistency Model

1. `load` should raise typed read errors (`FileNotFoundError`, `PermissionError`, backend-specific errors wrapped in library exception).
2. `save(write_through)` returns only after durable backend success.
3. `save(write_back)` must mark entry dirty and expose backlog in stats.
4. `flush` returns number of entries successfully persisted; partial failures are reported.
5. corrupted cache entries are invalidated and reloaded from source on next access.

## 13. Concurrency Model

1. Baseline thread-safe manager using internal lock for metadata maps.
2. Optional async wrapper can be added later; core semantics stay identical.
3. Pin/unpin/save/flush operations must be atomic per file key.

## 14. Telemetry Contract

Required metrics:
1. request counts by action (`load`, `stream`, `save`, `flush`, `release`),
2. cache hits/misses,
3. latency histograms (`load_ms`, `save_ms`, `flush_ms`),
4. bytes read/written,
5. eviction counts and causes (`ttl`, `budget`, `manual`),
6. optimizer profile switches and reason codes.

Telemetry output should support in-memory callback and optional JSONL sink.

## 15. Testing Requirements

Minimum required coverage:
1. lifecycle correctness per action group.
2. dirty-state transitions and flush durability semantics.
3. pinned-entry behavior under trim pressure.
4. TTL expiration and stale-entry cleanup.
5. optimizer profile-switch hysteresis behavior.
6. deterministic stats under scripted workloads.
7. failure-injection tests for backend read/write errors.

## 16. Security and Safety

1. Resolve and validate canonical paths before backend access.
2. Support allowlisted root directories for local filesystem adapter.
3. Never silently drop dirty data on cleanup; require explicit override for destructive clear.
4. Keep telemetry payloads free of raw secrets by default.

## 17. Performance Targets (Small Library Baseline)

1. `load_if_cached` p95 under 1 ms for entries < 1 MB on local process.
2. memory overhead metadata < 10% of cached payload bytes.
3. no unbounded growth in dirty queue or prefetch queue.
4. profile-switch rate bounded by cooldown/hysteresis.

## 18. Implementation Roadmap

1. Milestone 1:
2. core manager + local filesystem adapter + LRU + write-through.
3. Milestone 2:
4. pin/unpin/ttl + cleanup actions + stats API.
5. Milestone 3:
6. adaptive profile scoring + prefetch + write-back mode.
7. Milestone 4:
8. optional contextual bandit profile selector + extended telemetry sinks.
