# Godot Release Exports

Tet4D has three products governed by `product_platform_contract` in
`config/project/policy_pack.json`: Python Tet4D, the playable Godot Tet4D game,
and the desktop Tet4D Designer. Python packages are not fallback Godot
artifacts, and workflow coverage is implementation evidence rather than the
target-platform plan.
Earlier release records call the Python path legacy; that term is historical,
not its current product status.

The Godot source tree is shared, but it is exported through explicit product
profiles. `godot_game` stages `game_bootstrap.tscn` with the Tet4D game icon
and `io.github.mousomer.tet4d`; `godot_designer` stages
`designer_bootstrap.tscn` with the Designer icon and
`io.github.mousomer.tet4d.designer`. Staging changes only a disposable export
copy. The macOS builder selects the game profile, while the Windows and
transitional Android/iPadOS builders select the Designer profile. This does not
create additional platform packages or prepare a 0.9.0 release.

## Build the current release candidate

Requirements:

1. macOS 13 or newer;
2. the exact Godot 4.7.2 stable editor pinned by
   `config/project/policy_pack.json`;
3. the matching official Godot 4.7.2 export templates;
4. the pinned `native/third_party/godot-cpp` submodule; and
5. the repository development environment with SCons 4.10.1.

From the repository root:

```bash
git submodule update --init --recursive
GODOT_BIN=/path/to/Godot packaging/godot/build_macos.sh
```

The script performs these release-boundary checks:

- exact Godot build identifier;
- universal release GDExtension build for macOS 13+;
- Godot release export through the checked-in `macOS Universal` preset;
- disposable `godot_game` profile staging before export;
- required executable, `Info.plist`, and packaged release framework;
- bundle identifier and version consistency;
- packaged `x86_64` plus `arm64` native slices;
- deep strict code-signature validation; and
- ZIP creation that preserves the macOS app-bundle structure; and
- two isolated clean-user launches of a copied app outside the checkout via
  `packaging/godot/smoke_macos.sh`.

Outputs are ignored local artifacts:

```text
artifacts/godot/macos/Tet4D.app
artifacts/godot/macos/Tet4D-0.7.5-macos-universal.zip
```

The versioned filename follows `pyproject.toml`; do not edit the export-preset
version independently.

## Build the Windows Design Laboratory candidate

Requirements are the exact pinned Godot 4.7.2 editor and matching export
templates, the pinned godot-cpp submodule, SCons 4.10.1, and either a native
Windows C++ toolchain or MinGW-w64 on macOS/Linux. From the repository root:

```bash
GODOT_BIN=/path/to/Godot \
GODOT_TEMPLATE_ROOT=/path/to/Godot-4.7.2-templates \
packaging/godot/build_windows.sh
```

The script cross-builds the release GDExtension, stages `godot_designer` in a
disposable project copy, exports from that copy, and validates the exact
project copy, and validates the exact portable payload, PE binaries, version,
required laboratory resources, exclusions, and path sanitation. The production
MSVC invocation explicitly disables godot-cpp native debug records for
`template_release`; no PDB is part of the portable product. Existing
compiler/linker path maps remain active, and MSVC trims the repository root
from godot-cpp runtime `__FILE__` diagnostics using a Windows-form directory
prefix forwarded through the compiler's process-wide `CL` option channel before
strict package validation. Its generated output remains ignored:

```text
artifacts/godot/windows/Tet4D-Designer-0.7.5-windows-x86_64.zip
```

The exact validator-approved candidate nominated for clean-machine testing is
stored outside Git as an Actions artifact or release-candidate asset:

```text
Tet4D-Designer-0.7.5-windows-x86_64.zip
SHA-256 04941cb3f6d1070521f7a4d2d306fee5478908e3cf5e51d782c96a7e973913b9
```

See `release-candidates/windows/README.md` for retrieval and verification.
Publishing this candidate as an external build asset does not establish
clean-machine Windows runtime acceptance, and generated ZIPs must not enter
normal repository history.

Extract that ZIP to any user-writable directory and launch
`Tet4D Designer.exe`. This is an equivalent portable distributable, not an
MSI: extraction installs it, deleting that extracted directory uninstalls it,
and it creates no Start Menu entry, desktop shortcut, or registry uninstaller.
Profiles, evaluations, captures, and proposal exports are written to the
platform application-data directory through Godot `user://`, not the extracted
application directory. The package embeds no Python runtime or Godot editor.

Local cross-build and validation do not establish Windows runtime acceptance.
The Windows workflow builds natively, runs the focused laboratory suite,
validates the package, and performs a bounded headless start; a direct clean
Windows-machine review remains an explicit Stage 54F-5 acceptance item.

## Audit the transitional Android Design Laboratory artifact

This artifact carries Designer identity even though Designer/Android is not a
target. It remains transitional evidence until the required Godot game/Android
package has its own identity and entry contract. Requirements are the pinned
Godot 4.7.2 editor and Android export templates. A
full artifact additionally requires a working Java SDK, an Android SDK with
`platform-tools` and `build-tools`, and the NDK. Godot 4.7.2 requires all of
these unconditionally; `package/signed=false` does not bypass the check.

```bash
GODOT_BIN=/path/to/Godot \
GODOT_TEMPLATE_ROOT=/path/to/Godot-4.7.2-templates \
packaging/godot/build_android.sh --configuration-only
```

`--configuration-only` exports and validates the Android resource pack and
export configuration using only Godot, so it runs on any host. Dropping the flag
additionally cross-compiles the arm64 GDExtension and exports the signed APK:

```text
artifacts/godot/android/Tet4D-Designer-0.7.5-android-arm64.apk
```

The APK is a landscape arm64 tablet build for use with a physical keyboard.
Handset screen support is deliberately refused. The build generates an
ephemeral test keystore, copies the canonical credential-free preset into the
disposable project, and injects the key's release path, alias, and password into
that staged copy before keeping `--export-release`. No keystore, password, or
credential is committed. Profiles, evaluations, captures, and proposal exports
are written through Godot `user://`, which is application private on Android, so
nomination also writes a portable archive and offers it to the system document
picker. Godot 4.7.2's prebuilt Android exporter stores project resources as
individual `assets/` members plus `assets/assets.sparsepck` directory metadata;
the artifact validator checks that exact layout, the required laboratory
resources, and path hygiene without requiring a nonexistent embedded `.pck`.

## Audit the transitional iPadOS Design Laboratory artifact

This artifact carries Designer identity even though Designer/iPadOS is not a
target. Its required successor is Godot game/iPadOS and must not be inferred
from this export. Requirements are macOS, the pinned Godot 4.7.2 editor, and the iOS export
template. A compiled application additionally requires full Xcode; Command Line
Tools alone do not provide the iPhoneOS SDK.

```bash
GODOT_BIN=/path/to/Godot \
GODOT_TEMPLATE_ROOT=/path/to/Godot-4.7.2-templates \
packaging/godot/build_ipados.sh --configuration-only
```

`--configuration-only` exports and validates a configuration-class Xcode
project on a host without the iPhoneOS SDK. Its reduced GDExtension descriptor
deliberately omits the unavailable iOS libraries, so its checksums are
configuration evidence only. Dropping the flag produces the distinct release
class, cross-compiles the iOS GDExtension, retains the complete descriptor, and
combines each Tet4D archive with the matching godot-cpp implementation before
staging the complete XCFramework directory for Godot to copy to
`Tet4DDesigner/dylibs/addons/tet4d_core/bin/`. It then compiles the exported
project unsigned for the `x86_64` simulator, which matches the actual binary in
the pinned Godot 4.7.2 simulator engine slice and proves the final link without
any signing credential. The physical-device slice remains `arm64`. Their
project outputs are:

```text
artifacts/godot/ipad/configuration-export/Tet4DDesigner.xcodeproj
artifacts/godot/ipad/release-export/Tet4DDesigner.xcodeproj
```

Both generated `export_options.plist` files must resolve to
`method = development`, sourced from integer
`application/export_method_release=1` in the canonical preset.

Open that project in Xcode to build, sign, and install. Set `TET4D_IOS_TEAM_ID`
to your own Apple Developer team identifier before exporting; the committed
value is a placeholder. No certificate, provisioning profile, or credential is
committed. The exported application exposes its Documents directory to the Files
app, so a nominated bundle can be retrieved from the device without the
development repository.

## Smoke and manual acceptance

The build already runs the two-user headless outside-tree smoke. For manual
acceptance, copy or extract the app outside the repository, use an isolated
application data directory, and launch the actual executable under
`Tet4D.app/Contents/MacOS/Tet4D`. Verify startup, native extension load, setup,
2D/3D/4D play, Hold, NEXT, Ghost, quit, and relaunch. The final Stage 54G
verdict requires independent human acceptance of the exported app.

The app is ad-hoc signed for local distribution testing. It is not notarized;
macOS may block a downloaded archive from an unknown source. Developer-ID
signing and notarization are post-gate distribution work unless separately
authorized and provisioned.

## Platform support boundary

- Current Godot game implementation: macOS 13+, Universal 2, Godot app/ZIP.
- Current packaged design candidates, all three from one Design Laboratory:
  - Windows x86-64 portable Godot ZIP; clean-machine runtime acceptance pending.
  - Android arm64 and iPadOS Designer-identity artifacts are transitional
    mismatches, not target support for either Designer or the Godot game.
- Development-configured only: Linux Godot GDExtension artifact names.
- Active Python product family: PyInstaller `.dmg`, `.deb`, and `.msi`
  builders under `packaging/scripts/` and `packaging/pyinstaller/`; macOS arm64,
  Linux amd64, and Windows x64 are proven from exact integrated master
  `d542d682`, including outside-checkout launch and removal/uninstall.

Do not report Python installer CI or static GDExtension declarations as Godot
runtime release evidence; keep all three products explicit.

## Current release workflow

`.github/workflows/release-packaging.yml` currently builds seven artifacts from
the exact triggering SHA: three Python installers, the Godot game macOS
package, the Designer Windows package, and two explicitly transitional
Designer-identity tablet artifacts. The Android job runs on `ubuntu-latest` and the iPadOS job
on `macos-latest`, because those runners carry the Android and Xcode toolchains
that a given development host may not. Every package job depends on a release
identity contract. On tag runs, `v0.7.5` and `0.7.5` both normalize to the
`pyproject.toml` version; a mismatch such as the historical `v0.8.0` release
label against project version `0.7.5` fails before package construction or
publication.

After all seven package jobs pass, the workflow creates
`tet4d-release-<version>-manifest.json`. It binds every exact filename and
SHA-256 to the full 40-character source commit and records evidence boundaries,
including that the iPadOS output is an unsigned Xcode project compiled for the
simulator rather than a signed or device-accepted application. A matching tag
publishes all seven artifacts plus this manifest to one GitHub release. Manual
workflow dispatch exercises the same build and manifest gates without creating
a release.
