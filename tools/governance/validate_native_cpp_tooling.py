from __future__ import annotations

import os
from pathlib import Path
import shutil
import subprocess


ROOT = Path(__file__).resolve().parents[2]

NATIVE_DIRS = (
    "native",
    "gdextension",
    "godot_cpp",
    "cpp",
    "src/core",
    "src/godot_adapter",
)
CPP_EXTS = {".cpp", ".cc", ".cxx", ".hpp", ".hh", ".hxx", ".h"}
IMPLEMENTATION_EXTS = {".cpp", ".cc", ".cxx"}
EXCLUDED_PARTS = {
    "third_party",
    "vendor",
    "external",
    "build",
    ".godot",
}
EXCLUDED_PREFIXES = ("cmake-build-",)
COMPILE_DATABASE_RELS = (
    "compile_commands.json",
    "build/compile_commands.json",
    "native/compile_commands.json",
)
STRICT_ENV = "TET4D_STRICT_NATIVE_TOOLS"
CI_STRICT_ENV = "TET4D_NATIVE_TOOLS_CI_STRICT"
CI_ENVS = ("CI", "GITHUB_ACTIONS")


def _is_strict() -> bool:
    if os.environ.get(STRICT_ENV) == "1":
        return True
    return os.environ.get(CI_STRICT_ENV) == "1" and any(
        os.environ.get(name) for name in CI_ENVS
    )


def _mode_name(strict: bool) -> str:
    if not strict:
        return "local advisory"
    if any(os.environ.get(name) for name in CI_ENVS):
        return "CI strict"
    return "local strict"


def _is_excluded(path: Path) -> bool:
    return any(part in EXCLUDED_PARTS for part in path.parts) or any(
        part.startswith(EXCLUDED_PREFIXES) for part in path.parts
    )


def discover_native_cpp_files(root: Path = ROOT) -> list[Path]:
    files: list[Path] = []
    for rel in NATIVE_DIRS:
        directory = root / rel
        if not directory.exists():
            continue
        for path in directory.rglob("*"):
            relative = path.relative_to(root)
            if not path.is_file() or _is_excluded(relative):
                continue
            if path.suffix.lower() in CPP_EXTS:
                files.append(path)
    return sorted(files)


def _relative_paths(paths: list[Path], root: Path) -> list[str]:
    return [path.relative_to(root).as_posix() for path in paths]


def _find_compile_database(root: Path) -> Path | None:
    for rel in COMPILE_DATABASE_RELS:
        path = root / rel
        if path.is_file():
            return path
    return None


def _run_command(command: list[str], root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )


def _append_command_output(
    issues: list[str], result: subprocess.CompletedProcess[str]
) -> None:
    output = "\n".join(
        line.strip()
        for line in (result.stderr + "\n" + result.stdout).splitlines()
        if line.strip()
    )
    if output:
        issues.append(output)


def _clang_format_supports_dry_run(clang_format: str, root: Path) -> bool:
    result = _run_command([clang_format, "--dry-run", "--version"], root)
    combined = f"{result.stdout}\n{result.stderr}".lower()
    return (
        result.returncode == 0
        and "unknown" not in combined
        and "unsupported" not in combined
    )


def _run_clang_format_dry_run(
    clang_format: str, files: list[Path], root: Path
) -> list[str]:
    rels = _relative_paths(files, root)
    result = _run_command([clang_format, "--dry-run", "--Werror", *rels], root)
    if result.returncode == 0:
        return []
    issues = ["clang-format reported formatting violations."]
    _append_command_output(issues, result)
    return issues


def _run_clang_format_compare(
    clang_format: str, files: list[Path], root: Path
) -> list[str]:
    violations: list[str] = []
    for path in files:
        original = path.read_text(encoding="utf-8")
        result = _run_command([clang_format, path.relative_to(root).as_posix()], root)
        if result.returncode != 0:
            rel = path.relative_to(root).as_posix()
            issues = [f"clang-format failed on {rel}."]
            _append_command_output(issues, result)
            return issues
        if result.stdout != original:
            violations.append(path.relative_to(root).as_posix())
    if not violations:
        return []
    return [
        "clang-format reported formatting violations in: "
        + ", ".join(violations[:10])
        + (" ..." if len(violations) > 10 else "")
    ]


def _validate_clang_format(
    files: list[Path], root: Path, strict: bool
) -> tuple[list[str], str]:
    clang_format = shutil.which("clang-format")
    if clang_format is None:
        message = "clang-format not found; skipping format execution."
        if strict:
            return ["clang-format is required in strict native tooling mode."], message
        return [], message

    if _clang_format_supports_dry_run(clang_format, root):
        issues = _run_clang_format_dry_run(clang_format, files, root)
    else:
        issues = _run_clang_format_compare(clang_format, files, root)
    return issues, f"clang-format: checked {len(files)} files."


def _validate_clang_tidy(
    files: list[Path], root: Path, strict: bool
) -> tuple[list[str], str]:
    compile_database = _find_compile_database(root)
    if compile_database is None:
        message = "clang-tidy: skipped; compile_commands.json not found."
        if strict:
            return [
                "compile_commands.json is required in strict native tooling mode."
            ], message
        return [], message

    implementation_files = [
        path for path in files if path.suffix.lower() in IMPLEMENTATION_EXTS
    ]
    if not implementation_files:
        return [], "clang-tidy: skipped; no native implementation files found."

    clang_tidy = shutil.which("clang-tidy")
    if clang_tidy is None:
        message = "clang-tidy not found; skipping static-analysis execution."
        if strict:
            return ["clang-tidy is required in strict native tooling mode."], message
        return [], message

    build_dir = compile_database.parent
    rels = _relative_paths(implementation_files, root)
    result = _run_command([clang_tidy, f"-p={build_dir.as_posix()}", *rels], root)
    if result.returncode == 0:
        return [], f"clang-tidy: checked {len(implementation_files)} files."
    issues = ["clang-tidy reported diagnostics."]
    _append_command_output(issues, result)
    return issues, f"clang-tidy: checked {len(implementation_files)} files."


def validate(
    root: Path = ROOT, strict: bool | None = None
) -> tuple[list[str], list[str]]:
    if strict is None:
        strict = _is_strict()

    files = discover_native_cpp_files(root)
    if not files:
        return [], ["No native C++ files found; native tooling checks skipped."]

    messages: list[str] = [f"Native C++ tooling mode: {_mode_name(strict)}."]
    issues: list[str] = []
    for rel in (".clang-format", ".clang-tidy"):
        if not (root / rel).is_file():
            issues.append(f"{rel} is missing.")

    format_issues, format_message = _validate_clang_format(files, root, strict)
    issues.extend(format_issues)
    messages.append(format_message)

    tidy_issues, tidy_message = _validate_clang_tidy(files, root, strict)
    issues.extend(tidy_issues)
    messages.append(tidy_message)

    if issues:
        return issues, messages
    return [], ["Native C++ tooling validation passed.", *messages]


def main() -> int:
    issues, messages = validate()
    if issues:
        print("Native C++ tooling validation failed:")
        for issue in issues:
            print(f"- {issue}")
        for message in messages:
            print(message)
        return 1

    for message in messages:
        print(message)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
