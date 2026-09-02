from __future__ import annotations

import importlib.util
import plistlib
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
NATIVE_PATH = ROOT / "packaging/godot/ipados_native.py"
GODOT_SYMBOL = "__ZN5godot10DictionaryC1Ev"


def _module():
    spec = importlib.util.spec_from_file_location("ipados_native", NATIVE_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class FakeNativeTools:
    def __init__(self) -> None:
        self.archs: dict[Path, str] = {}
        self.members: dict[Path, list[str]] = {}
        self.undefined: dict[Path, set[str]] = {}
        self.defined: dict[Path, set[str]] = {}
        self.drop_member = False
        self.drop_required_symbol = False

    def __call__(self, command: list[str]) -> str:
        path = Path(command[-1])
        if command[0] == "lipo":
            if path not in self.archs:
                if "ios-arm64" in path.parts:
                    return "arm64\n"
                if any("simulator" in part for part in path.parts):
                    return "x86_64\n"
            return self.archs[path] + "\n"
        if command[:2] == ["ar", "-t"]:
            return "\n".join(self.members[path]) + "\n"
        if command[0] == "nm":
            values = self.undefined[path] if "-u" in command else self.defined[path]
            return "\n".join(sorted(values)) + "\n"
        if command[:3] == ["xcrun", "libtool", "-static"]:
            tet4d = Path(command[3])
            godot_cpp = Path(command[4])
            output = Path(command[command.index("-o") + 1])
            output.touch()
            self.archs[output] = self.archs[tet4d]
            members = self.members[tet4d] + self.members[godot_cpp]
            self.members[output] = members[:-1] if self.drop_member else members
            self.undefined[output] = self.undefined[tet4d] | self.undefined[godot_cpp]
            self.defined[output] = self.defined[tet4d] | self.defined[godot_cpp]
            if self.drop_required_symbol:
                self.defined[output].discard(GODOT_SYMBOL)
            return ""
        raise AssertionError(f"unexpected command: {command}")


def _xcframework(
    root: Path,
    *,
    simulator_metadata: list[str] | None = None,
) -> tuple[Path, Path, Path]:
    framework = root / "native.xcframework"
    device = framework / "ios-arm64/libnative.a"
    simulator = framework / "ios-x86_64-simulator/libnative.a"
    device.parent.mkdir(parents=True)
    simulator.parent.mkdir(parents=True)
    device.touch()
    simulator.touch()
    payload = {
        "AvailableLibraries": [
            {
                "LibraryIdentifier": "ios-arm64",
                "LibraryPath": "libnative.a",
                "SupportedArchitectures": ["arm64"],
                "SupportedPlatform": "ios",
            },
            {
                "LibraryIdentifier": "ios-x86_64-simulator",
                "LibraryPath": "libnative.a",
                "SupportedArchitectures": simulator_metadata or ["x86_64"],
                "SupportedPlatform": "ios",
                "SupportedPlatformVariant": "simulator",
            },
        ],
        "CFBundlePackageType": "XFWK",
        "XCFrameworkFormatVersion": "1.0",
    }
    with (framework / "Info.plist").open("wb") as handle:
        plistlib.dump(payload, handle)
    return framework, device, simulator


def test_combined_archive_preserves_duplicate_members_and_required_symbols(
    tmp_path: Path,
) -> None:
    module = _module()
    tools = FakeNativeTools()
    tet4d = tmp_path / "tet4d.a"
    godot_cpp = tmp_path / "godot-cpp.a"
    output = tmp_path / "combined.a"
    tet4d.touch()
    godot_cpp.touch()
    tools.archs = {tet4d: "arm64", godot_cpp: "arm64"}
    tools.members = {
        tet4d: ["tet4d.o"],
        godot_cpp: ["object.o", "object.o", "dictionary.o"],
    }
    tools.undefined = {tet4d: {GODOT_SYMBOL}, godot_cpp: set()}
    tools.defined = {tet4d: set(), godot_cpp: {GODOT_SYMBOL}}

    result = module.combine_archives(tet4d, godot_cpp, output, "arm64", tools)

    assert result["combined_members"] == 4
    assert result["required_godot_cpp_symbols"] == 1
    assert output.is_file()


@pytest.mark.parametrize(
    ("failure", "message"),
    [("drop_member", "member mismatch"), ("drop_required_symbol", "lost required")],
)
def test_combined_archive_rejects_silent_composition_loss(
    tmp_path: Path, failure: str, message: str
) -> None:
    module = _module()
    tools = FakeNativeTools()
    tet4d = tmp_path / "tet4d.a"
    godot_cpp = tmp_path / "godot-cpp.a"
    tet4d.touch()
    godot_cpp.touch()
    tools.archs = {tet4d: "x86_64", godot_cpp: "x86_64"}
    tools.members = {tet4d: ["tet4d.o"], godot_cpp: ["godot.o"]}
    tools.undefined = {tet4d: {GODOT_SYMBOL}, godot_cpp: set()}
    tools.defined = {tet4d: set(), godot_cpp: {GODOT_SYMBOL}}
    setattr(tools, failure, True)

    with pytest.raises(module.IpadOsNativeError, match=message):
        module.combine_archives(
            tet4d, godot_cpp, tmp_path / "combined.a", "x86_64", tools
        )


def test_xcframework_rejects_metadata_that_disagrees_with_binary(
    tmp_path: Path,
) -> None:
    module = _module()
    framework, device, simulator = _xcframework(
        tmp_path, simulator_metadata=["arm64", "x86_64"]
    )
    tools = FakeNativeTools()
    tools.archs = {device: "arm64", simulator: "x86_64"}

    with pytest.raises(module.IpadOsNativeError, match="does not match binary"):
        module.validate_xcframework(framework, runner=tools)


def test_release_xcframework_requires_godot_cpp_definitions(tmp_path: Path) -> None:
    module = _module()
    framework, device, simulator = _xcframework(tmp_path)
    tools = FakeNativeTools()
    tools.archs = {device: "arm64", simulator: "x86_64"}
    tools.undefined = {device: set(), simulator: set()}
    tools.defined = {device: set(), simulator: set()}

    with pytest.raises(module.IpadOsNativeError, match="no godot-cpp definitions"):
        module.validate_xcframework(
            framework,
            exact_device=module.DEVICE_ARCHITECTURES,
            exact_simulator=module.SIMULATOR_ARCHITECTURES,
            require_godot_cpp=True,
            runner=tools,
        )


def test_pinned_engine_metadata_is_normalized_to_actual_x86_64(
    tmp_path: Path,
) -> None:
    module = _module()
    framework = tmp_path / "engine.xcframework"
    device = framework / "ios-arm64/libgodot.a"
    simulator = framework / "ios-arm64_x86_64-simulator/libgodot.a"
    device.parent.mkdir(parents=True)
    simulator.parent.mkdir(parents=True)
    device.touch()
    simulator.touch()
    with (framework / "Info.plist").open("wb") as handle:
        plistlib.dump(
            {
                "AvailableLibraries": [
                    {
                        "LibraryIdentifier": "ios-arm64",
                        "LibraryPath": "libgodot.a",
                        "SupportedArchitectures": ["arm64"],
                        "SupportedPlatform": "ios",
                    },
                    {
                        "LibraryIdentifier": "ios-arm64_x86_64-simulator",
                        "LibraryPath": "libgodot.a",
                        "SupportedArchitectures": ["arm64", "x86_64"],
                        "SupportedPlatform": "ios",
                        "SupportedPlatformVariant": "simulator",
                    },
                ]
            },
            handle,
        )
    tools = FakeNativeTools()
    tools.archs = {device: "arm64", simulator: "x86_64"}

    result = module.normalize_pinned_godot_engine(framework, tools)

    assert result == {"device": ["arm64"], "simulator": ["x86_64"]}
    assert (framework / "ios-x86_64-simulator/libgodot.a").is_file()
    with (framework / "Info.plist").open("rb") as handle:
        libraries = plistlib.load(handle)["AvailableLibraries"]
    simulator_entry = next(
        item
        for item in libraries
        if item.get("SupportedPlatformVariant") == "simulator"
    )
    assert simulator_entry["LibraryIdentifier"] == "ios-x86_64-simulator"
    assert simulator_entry["SupportedArchitectures"] == ["x86_64"]
