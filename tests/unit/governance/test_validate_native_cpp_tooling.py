from __future__ import annotations

from pathlib import Path

import tools.governance.validate_native_cpp_tooling as native_tooling


def _write_text(path: Path, content: str = "") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_native_cpp_file_discovery_excludes_vendor_and_build_dirs(
    tmp_path: Path,
) -> None:
    included = tmp_path / "native" / "tet4d_core" / "src" / "core" / "sample.cpp"
    _write_text(included)
    _write_text(tmp_path / "native" / "third_party" / "lib" / "vendored.cpp")
    _write_text(tmp_path / "native" / "tet4d_core" / "build" / "generated.cpp")
    _write_text(tmp_path / "native" / "tet4d_core" / "cmake-build-debug" / "x.cpp")
    _write_text(tmp_path / "src" / "core" / "domain.hpp")

    files = native_tooling.discover_native_cpp_files(tmp_path)

    assert [path.relative_to(tmp_path).as_posix() for path in files] == [
        "native/tet4d_core/src/core/sample.cpp",
        "src/core/domain.hpp",
    ]


def test_native_cpp_tooling_skips_when_no_native_files(tmp_path: Path) -> None:
    issues, messages = native_tooling.validate(tmp_path)

    assert issues == []
    assert messages == ["No native C++ files found; native tooling checks skipped."]


def test_native_cpp_tooling_requires_configs_when_native_files_exist(
    tmp_path: Path, monkeypatch
) -> None:
    _write_text(tmp_path / "native" / "tet4d_core" / "src" / "core" / "sample.cpp")
    monkeypatch.setattr(native_tooling.shutil, "which", lambda name: None)

    issues, messages = native_tooling.validate(tmp_path)

    assert ".clang-format is missing." in issues
    assert ".clang-tidy is missing." in issues
    assert "Native C++ tooling mode: local advisory." in messages
    assert "clang-format not found; skipping format execution." in messages
    assert "clang-tidy: skipped; compile_commands.json not found." in messages


def test_native_cpp_tooling_strict_mode_fails_for_missing_tools(
    tmp_path: Path, monkeypatch
) -> None:
    _write_text(tmp_path / ".clang-format", "BasedOnStyle: LLVM\n")
    _write_text(tmp_path / ".clang-tidy", "Checks: clang-analyzer-*\n")
    _write_text(tmp_path / "native" / "tet4d_core" / "src" / "core" / "sample.cpp")
    monkeypatch.setattr(native_tooling.shutil, "which", lambda name: None)

    issues, messages = native_tooling.validate(tmp_path, strict=True)

    assert "clang-format is required in strict native tooling mode." in issues
    assert "compile_commands.json is required in strict native tooling mode." in issues
    assert "Native C++ tooling mode: local strict." in messages
    assert "clang-format not found; skipping format execution." in messages
    assert "clang-tidy: skipped; compile_commands.json not found." in messages


def test_native_cpp_tooling_strict_mode_fails_for_missing_clang_tidy(
    tmp_path: Path, monkeypatch
) -> None:
    _write_text(tmp_path / ".clang-format", "BasedOnStyle: LLVM\n")
    _write_text(tmp_path / ".clang-tidy", "Checks: clang-analyzer-*\n")
    _write_text(tmp_path / "compile_commands.json", "[]\n")
    _write_text(tmp_path / "native" / "tet4d_core" / "src" / "core" / "sample.cpp")

    def fake_which(name: str) -> str | None:
        if name == "clang-format":
            return "/usr/bin/clang-format"
        return None

    monkeypatch.setattr(native_tooling.shutil, "which", fake_which)
    monkeypatch.setattr(
        native_tooling,
        "_validate_clang_format",
        lambda files, root, strict: ([], "clang-format: checked 1 files."),
    )

    issues, messages = native_tooling.validate(tmp_path, strict=True)

    assert "clang-tidy is required in strict native tooling mode." in issues
    assert "Native C++ tooling mode: local strict." in messages
    assert "clang-tidy not found; skipping static-analysis execution." in messages


def test_native_cpp_tooling_ci_strict_env_uses_strict_mode(
    tmp_path: Path, monkeypatch
) -> None:
    _write_text(tmp_path / ".clang-format", "BasedOnStyle: LLVM\n")
    _write_text(tmp_path / ".clang-tidy", "Checks: clang-analyzer-*\n")
    _write_text(tmp_path / "native" / "tet4d_core" / "src" / "core" / "sample.cpp")
    monkeypatch.setattr(native_tooling.shutil, "which", lambda name: None)
    monkeypatch.setenv("CI", "true")
    monkeypatch.setenv("TET4D_NATIVE_TOOLS_CI_STRICT", "1")

    issues, messages = native_tooling.validate(tmp_path)

    assert "clang-format is required in strict native tooling mode." in issues
    assert "compile_commands.json is required in strict native tooling mode." in issues
    assert "Native C++ tooling mode: CI strict." in messages


def test_native_cpp_tooling_preserves_python_authority_in_policy() -> None:
    policy = Path("docs/governance/cpp_safety_policy.md").read_text(encoding="utf-8")

    assert "Python remains the semantic oracle" in policy
