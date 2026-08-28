# Godot 4.7.2 Baseline Upgrade Audit

Date: 2026-08-28
Branch: `codex/canonical-local-board-geometry`
Stage: 54F-3R.2
Scope: engine/toolchain baseline only — pinned engine manifest, project target
declaration, operator documentation, and local verification

## Decision and boundaries

Tet4D now targets Godot `4.7.2-stable`, the newest officially published stable
4.7 patch on the upgrade date and the newest published Godot 4.x stable release
overall; no 4.8 line exists. The exact engine build is
`4.7.2.stable.official.ed1daf0bf`, from engine commit
`ed1daf0bf001b61586d9930840f2f1394092c079`, published 2026-08-18.

Upstream classifies 4.7.2 as a maintenance release: *"compatible with previous
releases and are recommended for adoption."*

This upgrade satisfies the existing policy-pack `selection_rule`, "newest
officially published stable Godot 4.7 patch release". The rule was **not**
amended, and no governance decision was reopened.

The `godot-cpp` submodule is **retained unchanged** at
`5ffd70e34d0ab87009a9f0ffa3361bc8f4b09731`. See "GDExtension and native build
review" for the evidence that no binding advance was required.

This upgrade changes compatibility and build infrastructure only. Python remains
the semantic oracle. It introduces no gameplay, topology, replay, state-hash,
RNG, scoring, persistence-schema, presentation, profile-library, or
native-authority change.

## Reproducible release inputs

| Platform | Official asset | SHA-256 |
| --- | --- | --- |
| Linux x86_64 | `Godot_v4.7.2-stable_linux.x86_64.zip` | `cadd3204e728a35d3f13adb7fd0d7902636b79f6b95c40c265eb73b6c35329e4` |
| macOS universal | `Godot_v4.7.2-stable_macos.universal.zip` | `c58a24e31d720be9d62f60cb5627c4e695fb72f21b0cfe1bc9ccaa9a3b3ba63e` |

Export templates `Godot_v4.7.2-stable_export_templates.tpz`, SHA-512
`ca4d71c4d7b81dfc15d1a98baa07534aa95b03fdda78a0075b06672e1648d2e5f40980c9adc28d23e1b92e732ee7bf3461997aa804af74ec2fcd7a93ccb84079`.

Hash provenance, which differs by field and is easy to get wrong: upstream
publishes only `SHA512-SUMS.txt` for the release archives (plus a `.sha256` for
the *source tarball*, which Tet4D does not consume). The two editor-archive
SHA-256 values above were therefore computed locally from the downloaded
archives, after each archive was first verified against the upstream
`SHA512-SUMS.txt` entry. The export-template SHA-512 is taken directly from
`SHA512-SUMS.txt`.

The canonical URLs and executable paths live in
`config/project/policy_pack.json`. CI reads those values rather than tracking a
mutable `latest` download.

## Repository version inventory

| Category | Locations | Disposition |
| --- | --- | --- |
| Engine manifest | `config/project/policy_pack.json` | Version, commit, URLs, hashes, template directory, and evidence refreshed |
| Project declarations | `project.godot` | `config/tet4d_target_godot_version` raised to `4.7.2-stable`; `config/features` stays `4.7` |
| Native compatibility | `.gdextension`, build script | Unchanged; `compatibility_minimum` and `api_version` are minor-scoped at `4.7` |
| Binding source | `native/third_party/godot-cpp` | Retained; no advance required |
| Verification/packaging strings | `scripts/verify_godot_4_7.sh`, `packaging/godot/build_macos.sh`, `.github/workflows/ci.yml` | Version literals updated in place; no refactoring to manifest lookups |
| Governance contract literal | `policy_pack.json` required-content rule for `docs/RELEASE_INSTALLERS.md` | Updated in lockstep with that document |
| Generated docs | `docs/CONFIGURATION_REFERENCE.md`, `docs/USER_SETTINGS_REFERENCE.md` | Regenerated from the policy pack |
| Current operator docs | root and Godot/native READMEs, release installers, packaging/keybinding/4D RDS | Updated to the new supported baseline |
| Historical stage records | `CURRENT_STATE.md` history, backlog archives, the 4.7 migration audit | Preserved unchanged; they are evidence of what was proven under 4.7.1 |

The script filename `scripts/verify_godot_4_7.sh` remains accurate; this is still
the 4.7 line.

## Official migration-guide audit

The upstream range `4.7.1-stable...4.7.2-stable` contains 62 commits, dominated
by editor and documentation translation updates. The remainder are bug fixes.
No API addition, removal, or signature change appears in the range, which the
extension-API comparison below proves independently rather than by inspection
alone.

Two changes were candidates for affecting Tet4D and were reviewed explicitly:

- **`Fix Color hash component order`** — inapplicable. Tet4D performs no
  GDScript-level `.hash()` call anywhere in `scripts/` or `tests/`, uses no
  `Color` as a dictionary key, and stores palette colors as configuration
  strings in `config/shell_theme_palettes.json`. Deterministic gameplay hashes
  come from the native C++ core (`live_2d/3d/4d_state_hash`), not from engine
  value hashing.
- **`Fix simultaneous shift release`** — inapplicable as a contract change. It is
  an input-handling bug fix; no keybinding contract, action set, or binding label
  changes.

No compatibility-preserving project setting had to be added for this upgrade,
unlike the 4.7 migration.

## GDExtension and native build review

The pinned gate requires the engine's dumped `extension_api.json` to be
structurally identical to the binding's, excluding only the `header` key — the
exclusion that permits a patch-level engine to run against a minor-level binding
baseline.

Dumping the API from `4.7.2.stable.official.ed1daf0bf` and comparing it to the
retained binding produced:

```text
engine header : version_major 4, version_minor 7, version_patch 2
binding header: version_major 4, version_minor 7, version_patch 0
EXTENSION API IDENTICAL (header excluded): True
```

Upstream corroborates this: godot-cpp's `gdextension/extension_api.json` has not
been re-synced since `5ffd70e` itself (`gdextension: Sync with upstream commit
5b4e0cb0fd279832bbdd69fed5354d4e5ad26f88 (4.7-stable)`, 2026-06-18). The only
later commit touching that file, `9d050a9` (2026-07-29), is a build-option change
rather than an API sync, and godot-cpp maintains no `4.7` branch — the 4.7 line
lives on `master`.

The binding pin was therefore retained, consistent with the task rule "no
`godot-cpp` bump unless compatibility evidence requires it". `previous_commit`
and `selected_commit` are deliberately equal in the manifest to record that this
upgrade's starting and ending binding state are the same, with the reason stated
in `selection_basis`.

The extension rebuilt against the unchanged binding and all native test lanes
passed. A clean rebuild was not required, because no binding regeneration
occurred.

## Verification evidence

All checks run against the final tree, with an isolated `HOME` for every Godot
invocation so leaked `user://` state cannot fake a result.

| Check | Result |
| --- | --- |
| `verify_godot_4_7.sh` under 4.7.2 | PASS — `Godot 4.7.2 verification passed.`, 59 topology transport parity cases, engine banner `v4.7.2.stable.official.ed1daf0bf`, zero `SCRIPT ERROR` |
| `build_godot_tet4d_core.sh` | PASS |
| `test_godot_tet4d_core.sh` | PASS — plain 2D, plain ND, geometry, query, topology contract, topology transport, board extent contract |
| `validate_project_contracts.py` | PASS — 117 required paths |
| `validate_godot_semantic_boundary.py` | PASS — 120 scripts |
| `check_godot_settings_externalization.py` | PASS |
| `generate_configuration_reference.py --check` | PASS after regeneration |
| `generate_maintenance_docs.py --check` | PASS |
| `check_git_sanitation_repo.sh` | PASS |
| `CODEX_MODE=1 ./scripts/verify.sh` | PASS — `verify: OK` |

The pinned-gate log retains the repository's intentional negative-path
persistence and setup diagnostics, and its known non-failing teardown RID and
ObjectDB advisories. No failure was bypassed. Exit status alone was not treated
as proof: the log was searched for `SCRIPT ERROR`, because the Godot test runner
prints a success line even when a test function aborts mid-way.

## Deterministic and presentation isolation

Beyond the required gates, the same working tree was exercised under both engines
and compared directly.

Layout contract rects, cockpit surface visibility, basis/slice text, and the
authoritative `live_4d_state_hash` are **identical** under 4.7.1 and 4.7.2:

```text
live_4d_state_hash=daef26d673067f1cccf82085672ed1a0747e19bf0ba178ead3421bba2a0476c2
diff(4.7.1, 4.7.2) = no differences
```

## Visual review

Real windowed macOS runs under `4.7.2.stable.official.ed1daf0bf` on Metal 4.0
Forward+ (Apple M1 Pro), with zero errors logged. Four frames were rendered and
saved from the live viewport: live 2D, live 3D, live 4D W slices, and the full
Presentation Designer with the Profile Library expanded.

Each frame is **byte-identical** to the same capture produced under 4.7.1:

| Frame | 4.7.1 | 4.7.2 |
| --- | --- | --- |
| `live_2d` | `65ead887baeea9f8` | `65ead887baeea9f8` |
| `live_3d` | `86416d673d75d82d` | `86416d673d75d82d` |
| `live_4d` | `de9fdb3765d18220` | `de9fdb3765d18220` |
| `live_4d_designer_library` | `32c1d75a2c4ea7e9` | `32c1d75a2c4ea7e9` |

The Designer capture also re-confirms the Stage 54F-3R cockpit invariant under
the new engine: with the Profile Library expanded, the W-slice boards, NEXT,
HOLD, piece controls, and 4D view actions remain in exactly the positions they
occupy without it.

One cosmetic clipped label (`DOWN ENTRY` truncated at the left board edge in live
2D) appears in both engines' captures. It is pre-existing and is **not** a 4.7.2
regression; it is out of scope for this baseline upgrade.

This review is agent-driven. No independent human sign-off is claimed.

## Performance comparison

Same project copy, isolated `HOME` per engine, one warm run discarded before each
timed run.

| Measure | 4.7.1 | 4.7.2 |
| --- | --- | --- |
| Headless suite | 70.88 s | 70.89 s |
| Bounded startup | 2.52 s | 2.31 s |
| Native tests | — | 39.36 s (engine-independent) |

No material regression. These figures are **not** comparable to the 4.7 migration
audit's numbers: the test suite has grown substantially since 2026-07-25, so both
columns here were measured on the current tree specifically to be comparable to
each other.

## Warning and limitation classification

- macOS is the local development evidence platform.
- Linux acceptance for this upgrade is deferred to CI on publication rather than
  re-proved locally. The CI lane acquires the engine from this manifest, so the
  refreshed Linux asset URL and SHA-256 are exercised on the first push.
- Windows native packaging remains declared but unverified.
- The visual review is agent-driven, with no independent human sign-off.

## CI acceptance

Not run. This upgrade is a local unpublished commit with no push and no pull
request, per the task rules. The CI Godot lane reads
`governance.godot_toolchain` for engine acquisition, so it exercises the new
pinned asset automatically once this branch is published.

## Explicit acceptance statements

- Supported Godot baseline: `4.7.2-stable` (`4.7.2.stable.official.ed1daf0bf`).
- Supported binding baseline: `5ffd70e34d0ab87009a9f0ffa3361bc8f4b09731`, API
  version `4.7`, retained unchanged on compatibility evidence.
- Godot is still the product shell and input/rendering adapter.
- Python remains the semantic authority.
- Native C++ remains provisional and parity-backed.
- No new authority or product-routing decision is introduced.
- No gameplay, presentation, or profile-library behavior changed; both are
  evidenced by identical state hashes and byte-identical rendered frames.
