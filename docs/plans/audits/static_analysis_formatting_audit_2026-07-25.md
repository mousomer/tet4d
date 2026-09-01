# Static-analysis and formatting audit

Status: completed with explicitly recorded unavailable and partial lanes
Audit date: 2026-07-25
Audited branch: `codex/configurable-plain-boards`
Audited head: `ffb57675be13c2de3dd8525db24607ce331e5620`

## Purpose and authority boundary

This report records the non-modifying quality-tool audit requested for the
current Tet4D repository. It is evidence, not a new semantic or architecture
authority. Machine-readable findings are summarized in
`config/project/policy_pack.json`; durable quality-tool category policy remains
in `docs/governance/ENGINEERING.md` and
`docs/governance/VERIFICATION.md`.

The audit introduced no gameplay, topology, replay, native-authority,
state-hash, or RNG change. Python remains the semantic oracle, Godot remains the
product shell and adapter host, and native C++ remains within its existing
documented authority.

## Repository inventory

The authoritative counts below use tracked files so ignored worktrees, caches,
build outputs, and the `native/third_party/godot-cpp` submodule do not inflate
the project-owned inventory.

| Area | Tracked project-owned files | Build/configuration path | Classification |
| --- | ---: | --- | --- |
| Python | 458 `.py` | `pyproject.toml`, setuptools | Current primary implementation and tests |
| GDScript | 78 `.gd` | `godot/Tet4D.Godot/project.godot` | Godot shell, adapters, and tests |
| Godot scenes/resources | 1 `.tscn`, 3 `.tres`, 1 project file, 1 GDExtension descriptor | Godot 4.6.3 target | Project-owned runtime assets |
| Native C++ | 18 `.cpp`, 2 `.h`, 11 `.hpp` | SCons plus standalone compiler test script | Project-owned native core, adapter, and tests |
| C# | 24 `.cs`, 2 `.asmdef`; no `.csproj` or `.sln` | Unity 2022.3.20f1 project metadata | Legacy Unity replay spike, not Godot C# |
| Shell | 23 `.sh` | Bash scripts | Build, packaging, governance, and verification |
| Project configuration | 237 JSON, 3 YAML, 1 TOML, 1 INI, Godot/GDExtension resources | Repo governance and domain schemas | Project-owned and generated/copy inputs are already distinguished by repository policy |

Vendored/generated boundaries are:

- `native/third_party/godot-cpp`: exact Git submodule commit
  `a7770ef949fc664892e46b7e98a708672e8a44a8`, excluded from project-owned
  Ruff and native-tool discovery;
- `.godot`, `.venv`, build outputs, caches, and ignored worktrees: local or
  generated, not audit targets;
- `godot/Tet4D.Godot/assets/tet4d_bundle`,
  `unity/Tet4D.Unity/Assets/StreamingAssets/tet4d_bundle`, and
  `migration/exported_bundle`: copied/generated migration inputs, not primary
  semantic or formatting owners.

## Canonical tool table

`Autofix/risk` describes capability only. No autofix or broad formatter was
run during this audit.

| Tool / language | Present and configured | Local installation and version | Reproducibility | Current result and diagnostics | Autofix / semantic risk | Local verification | GitHub CI | Recommendation |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Ruff / Python | Yes; `pyproject.toml`, default rule set plus C901, `native/third_party` excluded, no per-file ignores | `.venv`: 0.16.0; shell command: stale 0.14.1 | Exactly pinned as `ruff==0.16.0` in dev dependencies; CI prints version | **PASS**: lint 0 diagnostics; C901 0 diagnostics; full format check reports 638 files formatted | Safe and unsafe lint fixes exist; any fix can change behavior, while formatting is mechanical but broad | Lint full tree; canonical format gate currently checks only `scripts tools`; audit full-tree format check passed | **PARTIAL**: full lint and C901 run on Python 3.11–3.14; format checks only `scripts tools` | Retain; make the existing CI format command cover the full configured tree in a narrow follow-up |
| mypy / Python | Not configured or declared | Shell-level 2.2.0; absent from `.venv` | Unpinned and non-canonical | **NOT CONFIGURED**; not executed | No autofix; annotation changes can affect runtime compatibility | No | No | Optional later only after choosing a typed package boundary; annotations are substantial but the package is not marked `py.typed` |
| Pyright / Python | Not configured or declared | Not installed | Not applicable | **NOT INSTALLED**; not executed | No autofix; may require annotation/config migration | No | No | Do not adopt alongside mypy by default; choose one checker only if a dedicated typing stage is approved |
| Godot parser/static analyser / GDScript | Yes, through Godot project loading and the existing headless test runner | Godot 4.7 stable | Project records 4.6.3 stable but has no reproducible acquisition/toolchain pin; local version mismatches target | **PASS/PARTIAL**: all scripts parsed and tests passed under 4.7; no GDScript warnings emitted; no explicit warning-as-error or global warning suppression policy found | No broad autofix; warning-policy changes can be noisy or version-sensitive | Existing headless suite plus editor import | No | Mandatory target-version runner; retain Godot as primary GDScript authority and do not enable all warnings as errors blindly |
| gdlint / GDScript | Not configured | Not installed; `gdtoolkit` absent | Not applicable | **NOT INSTALLED** | May autofix selected issues; syntax/version false positives are possible | No | No | Optional later, only in a dedicated compatibility/churn trial against Godot 4.6.3 |
| gdformat / GDScript | Not configured | Not installed; `gdtoolkit` absent | Not applicable | **NOT INSTALLED** | Broad mechanical churn likely | No | No | Optional later; do not adopt without a separately reviewed formatting migration |
| Godot `ResourceLoader` and scene instantiation / scenes and resources | Existing `test_scene_integrity.gd` loads and instantiates the only project scene; editor import scans project resources | Godot 4.7 stable | Same target-version mismatch as above | **PASS/PARTIAL**: 1 scene loaded/instantiated, 3 theme resources imported, main scene started, GDExtension loaded; editor cache writes were sandbox-blocked | No autofix; import may generate local metadata | Existing suite, editor import, bounded startup | No | Add target-version CI and later generalize the existing integrity test if project-owned scene/resource count grows |
| Apple Clang compiler / C++ | Yes; standalone core tests use C++17, `-Wall -Wextra -Werror`; SCons builds the GDExtension | Apple Clang 21.0.0 | System-provided, unpinned; SCons 4.10.1 is also locally installed but undeclared | **PASS**: GDExtension build and four standalone native test binaries pass with no project warning; only macOS sandbox `confstr()` fallback warnings occurred | Compiler only; fixes can change semantics | Manual canonical build/test scripts | No native build in CI | Keep current flags; add a reproducible native CI lane before expanding warning policy |
| Additional compiler warnings / C++ core | Not configured in canonical scripts | Apple Clang 21.0.0 probes | System-provided | **PASS** for `-Wpedantic`, `-Wshadow`, `-Wnon-virtual-dtor`, `-Wold-style-cast`, `-Woverloaded-virtual`, `-Wnull-dereference`; **FAIL** for `-Wconversion` with 1 signedness diagnostic in `core_api.cpp` | No autofix; warning-driven edits can affect conversions and API behavior | Audit-only `-fsyntax-only` probes on project core | No | Safe flags are high-value next-stage candidates; handle `-Wconversion` in a dedicated cleanup and validate the Godot adapter with real compile commands |
| clang-format / C++ | `.clang-format` present; 31 project-owned C/C++ files discoverable | Not installed | Unpinned | **NOT INSTALLED**; validator skips execution in advisory mode | Formatting only, but broad churn and generated/vendor spill are risks | Advisory validator only | CI explicitly skips clang execution in advisory mode | High-value next stage: pin/install a compatible version, check project-owned files only, and avoid `native/third_party` |
| clang-tidy / C++ | `.clang-tidy` present with scoped categories; no supported compilation database | Not installed | Unpinned | **BLOCKED**: no `compile_commands.json`; a real analysis was not claimed | Some checks have fixes; Godot ownership/lifecycle false positives are a material risk | Advisory validator skips | CI explicitly skips clang execution in advisory mode | High-value after reproducible compile database generation; keep current exclusions for trailing-return, naming, magic-number, and lifecycle-sensitive rules |
| cppcheck / C++ | Not configured or invoked | 2.21.0 | System-provided, unpinned | **NOT CONFIGURED**; not executed | Fixes are manual; Godot macro false positives likely | No | No | Optional later only if it demonstrates marginal value beyond compiler and clang-tidy |
| ASan / C++ | Not configured | Compiler capability not adopted | Not applicable | **NOT CONFIGURED**; canonical build scripts expose no documented safe sanitizer configuration | Runtime instrumentation; low semantic risk, platform/runtime compatibility risk | No | No | High-value next stage for standalone native tests |
| UBSan / C++ | Not configured | Compiler capability not adopted | Not applicable | **NOT CONFIGURED** | Runtime instrumentation; may expose real undefined behavior | No | No | High-value next stage with ASan for standalone native tests |
| LSan / C++ | Not configured | Platform-dependent | Not applicable | **NOT CONFIGURED** | Runtime instrumentation; Godot/runtime leak noise likely | No | No | Optional after ASan/UBSan and platform feasibility evidence |
| TSan / C++ | Not configured | Platform-dependent | Not applicable | **NOT CONFIGURED** | Expensive and potentially noisy | No | No | Not necessary now; no selected native multithreading quality target |
| Unity compiler/Roslyn / C# | 24 C# files and Unity assembly definitions exist; no `.csproj`, `.sln`, analyzer config, or standalone .NET build | Unity Editor not found; .NET SDK not installed | Unity project exactly records 2022.3.20f1; no reproducible CI installation | **BLOCKED**: source is applicable, but no local or CI compiler path is available | IDE/compiler fixes can alter Unity serialization/lifecycle behavior | No | No | Treat as a legacy-spike gap; establish a dedicated Unity/C# baseline only if this spike is reactivated |
| `dotnet format` / C# | No SDK project exists | Not installed | Not applicable to the current assembly-definition-only path | **NOT APPLICABLE** to the current checked-in build path | Would rewrite whitespace/style/analyser fixes | No | No | Do not add a `.csproj` solely for this audit |
| Nullable reference types / C# | No project-level policy | Not available without a build path | Not applicable | **NOT CONFIGURED** | Enabling globally can create a large migration | No | No | Assess migration size only if Unity C# becomes active |
| StyleCop / C# | Not referenced | Not installed | Not applicable | **NOT CONFIGURED** | Potentially high documentation/order noise | No | No | Optional later only if strict file-layout/documentation policy is explicitly desired |
| SonarAnalyzer.CSharp / C# | Not referenced | Not installed | Not applicable | **NOT CONFIGURED** | Overlap and Godot/Unity lifecycle false positives are possible | No | No | Optional later after built-in Roslyn coverage exists |
| JetBrains InspectCode / C# | Not configured | Not installed | Not applicable | **NOT CONFIGURED** | IDE-specific diagnostics and licensing/maintenance cost | No | No | Reject as a mandatory primary gate; optional developer tooling only |
| `bash -n` / shell | All 23 tracked scripts declare Bash | Bash 3.2.57 | System-provided | **PASS**: 23/23 syntax checks | No autofix | Audit-only syntax check | Scripts execute in CI, but no dedicated syntax matrix | Retain as a low-cost local diagnostic; it does not replace ShellCheck |
| ShellCheck / shell | Not configured | Not installed | Unpinned | **NOT INSTALLED** | Some autofixes/suggestions; portability findings require review | No | No | High-value next stage, scoped to the declared Bash dialect |
| shfmt / shell | Not configured | Not installed | Unpinned | **NOT INSTALLED** | Broad mechanical churn possible | No | No | Optional after ShellCheck; adopt only with a reviewed style and no blind rewrite |
| Repository governance/config validators / JSON, YAML, TOML, Godot config | Existing policy, sanitation, schema, generation, secret, and text-format checks | Python 3.14.6 via `.venv` | Python CI pins minor versions only; repository rules are versioned in source | **PASS** | Some generators can update derived docs; validation commands are non-modifying | Canonical verification gate | Required in Python 3.11–3.14 matrix | Retain; these validators complement rather than replace language tools |

## Python detail

- Canonical executable: `.venv/bin/python` 3.14.6.
- Canonical Ruff: `.venv/bin/python -m ruff`, version 0.16.0.
- Shell-level `ruff` is 0.14.1 and is not acceptance evidence.
- `ruff check . --output-format=full`: **PASS**, 0 diagnostics.
- `ruff check --select C901 . --output-format=full`: **PASS**, 0 diagnostics.
- `ruff format --check .`: **PASS**, 638 files already formatted.
- Ruff uses its default excluded paths, respects Git ignore rules, and extends
  exclusions only for `native/third_party`.
- No `per-file-ignores` or file-wide suppressions are configured.
- There are 148 rule-specific inline annotations: 98 TRY004, 36 F401, 6 C901,
  5 BLE001, 2 SIM117, and 1 PLE0605. Their intentional groups are already
  recorded in the Ruff migration manifest.
- Static typing is plausible as a future bounded stage: 3,982 of 6,463 detected
  Python function definitions have return annotations. It is not ready to
  become a mandatory whole-repository gate without choosing a package boundary,
  checker, dependency pin, and dynamic UI/test policy.

## Godot and GDScript detail

The project declares `4.6.3-stable`; the available executable is
`4.7.stable.official.5b4e0cb0f`. Results therefore establish forward-version
compatibility evidence, not exact target-version reproducibility.

- Existing headless suite: **PASS**, `Godot replay tests passed`.
- Expected negative-path error output: three settings-store replacement failure
  injections and three invalid native setup payloads. Classification:
  **D — intentional engine/test pattern**.
- Exit-time CanvasItem/ObjectDB/resource/RID leak messages from the test runner:
  **E — engine/test-harness cleanup output**; they do not change the successful
  exit status but should remain visible in a future target-version CI lane.
- Editor import: exit 0, all 78 scripts registered. Cache/settings writes outside
  the workspace were blocked by the sandbox. Classification:
  **E — environment-specific editor cache output**.
- The editor import generated 79 untracked `.uid` sidecars. The audit removed
  only those command-created sidecars and confirmed a clean tree before
  continuing.
- Main-scene startup: **PASS**, bounded to five frames with no immediate fatal
  error or missing asset.
- Scene/resource validation: the only scene loads and instantiates through
  `test_scene_integrity.gd`; all three theme resources pass editor import.
- GDExtension: loads in tests and startup.
- No project setting promotes GDScript warnings to errors, globally disables
  warnings, or records per-warning suppressions.

## Native C++ detail

- Compiler: Apple Clang 21.0.0, arm64 macOS.
- Standard: C++17.
- Standalone project-core policy: `-Wall -Wextra -Werror`.
- Build systems: SCons 4.10.1 locally; exact `godot-cpp` submodule commit with a
  Godot 4.6.0-stable extension API.
- GDExtension SCons build: **PASS** for debug arm64 macOS.
- Standalone native tests: **PASS** for plain 2D, plain ND, geometry, and query.
- The compiler and SCons versions are system/local environment inputs rather
  than repository pins.
- A supported `compile_commands.json` does not exist. Consequently clang-tidy is
  **BLOCKED**, not verified.
- `clang-format` and `clang-tidy` are absent. The advisory validator passes
  configuration/discovery and explicitly reports both execution skips.
- `cppcheck` is installed but has no repository configuration or invocation;
  running it without a scoped policy would not be acceptance evidence.
- Sanitizers were not run because current canonical scripts do not expose a
  documented safe sanitizer configuration.

Warning flag classification:

- already enabled: `-Wall`, `-Wextra`, with warnings treated as errors in
  standalone project-core tests;
- safe to enable for the standalone core based on zero-diagnostic probes:
  `-Wpedantic`, `-Wshadow`, `-Wnon-virtual-dtor`, `-Wold-style-cast`,
  `-Woverloaded-virtual`, `-Wnull-dereference`;
- needs dedicated cleanup: `-Wconversion`, which reports one signedness
  conversion in `native/tet4d_core/src/core/core_api.cpp`;
- needs a valid Godot adapter compilation database before classification:
  all additional flags against `src/godot`;
- platform-specific: final flag behavior across Linux, Windows, macOS, iOS, and
  the vendored Godot headers.

## C# and Unity detail

C# is present, but it is the retained Unity replay spike rather than a Godot C#
implementation. The scope rule therefore does not permit calling C# absent or
adding a new .NET project.

- 24 tracked `.cs` files and 2 Unity assembly definitions exist.
- No `.csproj`, `.sln`, `global.json`, `Directory.Build.props`, or
  `Directory.Build.targets` exists.
- The Unity project records editor 2022.3.20f1 exactly.
- Neither Unity Editor nor the .NET SDK is available locally.
- No Roslyn analyser, nullable, warnings-as-errors, code-style, StyleCop,
  SonarAnalyzer, or InspectCode configuration exists.
- No C# or Unity CI lane exists.

`dotnet format` is not applicable to the current assembly-definition-only build
path. C# compiler/analyser coverage is a real gap only if the legacy Unity spike
remains supported or becomes active again. No C# tooling or project was added.

## CI coverage matrix

The current PR is draft PR 37. Push run `30144884534` and pull-request run
`30144885222` both passed at audited head `ffb57675` on Python 3.11, 3.12, 3.13,
and 3.14.

| Area | Local command | CI command | Version visible | Required | Result |
| --- | --- | --- | --- | --- | --- |
| Python lint | `.venv/bin/python -m ruff check .` | `verify.sh`: Ruff full lint | Yes, 0.16.0 | Yes | **PASS** |
| Python format | `.venv/bin/python -m ruff format --check .` | `verify.sh`: `ruff format --check scripts tools` | Yes | Yes, partial scope | **PARTIAL** |
| Python tests | `CODEX_MODE=1 ./scripts/verify.sh` | Same through `ci_check.sh` | Python minor and Ruff visible | Yes | **PASS** at audited head |
| GDScript parse | Godot editor import/test suite | None | No | No | **NOT CONFIGURED** |
| Godot scene load | Existing scene-integrity test | None | No | No | **NOT CONFIGURED** |
| Godot headless tests | Godot test runner | None | No | No | **NOT CONFIGURED** |
| C++ format | Advisory validator | CI advisory validator skips execution | No | No | **NOT INSTALLED** |
| C++ compile warnings | Standalone test build | None | No | No | **NOT CONFIGURED** |
| C++ tests | `scripts/test_godot_tet4d_core.sh` | None; Python tests may skip if binaries are absent | No | No | **NOT CONFIGURED** |
| clang-tidy | Blocked without compile database | CI advisory validator skips execution | No | No | **BLOCKED** |
| Sanitizers | None | None | No | No | **NOT CONFIGURED** |
| C# build | Blocked without Unity/.NET build path | None | Unity version only in repo | No | **BLOCKED** |
| dotnet format | Not applicable to current path | None | No | No | **NOT APPLICABLE** |
| ShellCheck | Not installed | None | No | No | **NOT INSTALLED** |
| shfmt | Not installed | None | No | No | **NOT INSTALLED** |
| Governance/config validation | `verify.sh` | Same through `ci_check.sh` | Python minor visible | Yes | **PASS** |

## Gaps

| Gap | Consequence | Severity | Recurrence risk | Recommended owner | Recommended stage |
| --- | --- | --- | --- | --- | --- |
| CI Ruff format scope is narrower than repository policy | Python outside `scripts tools` can drift while CI remains green | Medium | High | Python/governance | Mandatory now, narrow follow-up |
| No reproducible Godot 4.6.3 runner and no Godot CI | Parser, scene, GDExtension, and headless regressions are locally dependent | High | Medium | Godot shell | Mandatory now |
| Local Godot is 4.7, not project target | Audit cannot prove exact target-version behavior | Medium | Medium | Godot shell/toolchain | Mandatory now |
| No native build/test CI | Compiler and parity binaries can regress without a blocking build | High | Medium | Native C++ | Mandatory now |
| clang-format absent/unpinned | Config exists but formatting is not executable or reproducible | Medium | Medium | Native tooling | High-value next stage |
| clang-tidy lacks tool and compilation database | Configured static analysis is not executable | Medium | Medium | Native tooling | High-value next stage |
| No ShellCheck | Script defects beyond syntax are not statically checked | Medium | Medium | Build/governance | High-value next stage |
| Unity C# has no executable build/analyser path | Retained legacy spike correctness cannot be reproduced | Low while inactive | Low | Migration/product owner | Optional reactivation stage |
| Compiler/SCons versions are unpinned | Native results may differ by workstation | Medium | Medium | Native tooling | High-value next stage |
| No sanitizer configuration | Native runtime memory/UB defects rely on tests and normal execution | Medium | Low-to-medium | Native C++ | High-value next stage |

## Staged recommendations

### Mandatory now

- Expand the existing CI Ruff format check from `scripts tools` to the full
  configured tree. Benefit: closes a policy/enforcement mismatch. Overlap:
  none beyond the already passing audit command. Expected noise: zero on this
  head. Maintenance and CI cost: low. Adoption risk: low.
- Add a Godot 4.6.3 headless lane for import, the existing test runner, and
  bounded startup. Benefit: covers GDScript, resources, scenes, and GDExtension.
  Overlap: complements, not replaces, gameplay tests. Expected noise: known
  negative-path and exit cleanup messages. Maintenance: medium. CI cost:
  medium. Adoption risk: medium until engine acquisition and native artifact
  setup are reproducible.
- Add the standalone native compiler/test build to CI using the current C++17,
  `-Wall -Wextra -Werror` contract. Benefit: makes existing native correctness
  evidence blocking. Overlap: Python parity tests currently skip when native
  binaries are absent. Expected noise: low. Maintenance: medium. CI cost:
  medium. Adoption risk: low-to-medium.

### High-value next stage

- Pin and run clang-format on the 31 project-owned native files only. Benefit:
  deterministic layout. Overlap: none with compiler correctness. Expected
  noise: an initial diagnostic-only inventory. Maintenance/CI cost: low.
  Adoption risk: medium if converted into a broad rewrite.
- Generate a real compilation database and run the existing scoped clang-tidy
  policy. Benefit: bug, performance, and lifetime diagnostics. Overlap:
  compiler warnings partly overlap. Expected noise: medium around Godot
  ownership/macros. Maintenance and CI cost: medium-to-high. Adoption risk:
  medium.
- Add ShellCheck for the 23 Bash scripts. Benefit: quoting, globbing, error
  handling, and portability diagnostics. Overlap: deeper than `bash -n`.
  Expected noise: medium on packaging/platform scripts. Maintenance/CI cost:
  low. Adoption risk: low if diagnostic-first.
- Add an ASan/UBSan standalone native-test configuration. Benefit: runtime
  memory and undefined-behavior detection. Overlap: complementary to compiler
  and clang-tidy. Expected noise: low-to-medium. Maintenance/CI cost: medium.
  Adoption risk: platform-dependent.
- Consider enabling the six clean additional warning flags in a dedicated
  native stage, and clean the single `-Wconversion` diagnostic separately.
  Benefit: earlier compiler feedback. Overlap: partial clang-tidy overlap.
  Expected noise: low for core, unknown for adapter. Maintenance/CI cost: low.
  Adoption risk: medium without adapter compile commands.

### Optional later

- Trial gdtoolkit against the pinned Godot target before any adoption. Benefit:
  optional style diagnostics. Overlap: substantial with Godot. Expected noise
  and churn: medium-to-high. Maintenance/CI cost: medium. Adoption risk: medium.
- Choose one Python type checker for a bounded typed package, not the whole
  repository at once. Benefit: interface consistency. Overlap: some Ruff
  annotation rules. Expected noise: high initially. Maintenance/CI cost:
  medium. Adoption risk: medium.
- Evaluate cppcheck only after clang-tidy is operational. Benefit: possible
  marginal defect detection. Overlap: high. Expected noise: medium.
  Maintenance/CI cost: medium. Adoption risk: low if kept optional.
- Use LSan or TSan only after a demonstrated platform or concurrency need.

### Rejected or not applicable now

- Do not add a Godot C# project; existing C# belongs to the Unity spike.
- Do not add `.csproj` or `.sln` solely to make `dotnet format` runnable.
- Do not make StyleCop, SonarAnalyzer, or InspectCode mandatory before a
  supported Unity/C# build path exists.
- Do not add gdformat, shfmt, or clang-format as a broad autofix migration in
  this audit.
- Do not use cppcheck as a substitute for compiler warnings or clang-tidy.
- Do not enable TSan without a selected native multithreading target.

## Verification record

- Ruff full lint: **PASS**.
- Ruff C901: **PASS**.
- Ruff full-tree format check: **PASS**.
- Godot headless tests: **PASS** under available 4.7, with classified expected
  diagnostics.
- Godot editor import: **PASS/PARTIAL** under 4.7, with sandbox cache errors and
  generated sidecars removed.
- Godot bounded main-scene startup: **PASS**.
- Scene load/instantiation and GDExtension load: **PASS**.
- Native GDExtension build: **PASS**.
- Native standalone tests: **PASS**.
- Additional native warning probes: six clean, one `-Wconversion` diagnostic.
- Bash syntax: **PASS**, 23 files.
- clang-format, clang-tidy, gdtoolkit, ShellCheck, shfmt, Unity, and .NET:
  unavailable or blocked exactly as recorded above.
- `git diff --check`, sanitation, documentation/governance validation, and
  `CODEX_MODE=1 ./scripts/verify.sh`: **PASS**.

## Explicit confirmations

- No gameplay semantics changed.
- No topology semantics changed.
- No native authority changed.
- No replay semantics changed.
- No state hashing changed.
- No RNG changed.
- No broad formatter or autofix was run.
- No lint rule was weakened.
- No warning was suppressed merely to obtain a pass.
- No C# tooling or project was added.
- No generated or third-party code was reformatted.
- No merge, force-push, or push was performed.
