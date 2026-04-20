from __future__ import annotations

import argparse
import ast
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Iterable

if __package__:
    from . import check_drift_protection as drift_guard
    from ._common import iter_python_files, load_maintenance_docs
else:
    sys.path.append(str(Path(__file__).resolve().parent))
    import check_drift_protection as drift_guard
    from _common import iter_python_files, load_maintenance_docs

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CURRENT_STATE_PATH = PROJECT_ROOT / "CURRENT_STATE.md"
PROJECT_STRUCTURE_PATH = PROJECT_ROOT / "docs" / "PROJECT_STRUCTURE.md"
DEFAULT_SYMBOL_SOURCE_ROOTS = ("src/tet4d", "cli")
DEFAULT_TEST_SOURCE_ROOTS = ("src/tet4d", "cli")
DEFAULT_TEST_ROOTS = ("tests",)
DEFAULT_SYMBOLS_PER_FILE = 12
DEFAULT_TEST_MATCHES_PER_FILE = 4
MAX_SYMBOLS_PER_FILE = 24
MAX_TEST_MATCHES_PER_FILE = 8
MAX_FALLBACK_TEST_MATCHES = 2
MAX_SIGNATURE_CHARS = 52
MAX_SIGNATURE_ITEMS = 6
GENERIC_FALLBACK_TOKENS = frozenset(
    {
        "api",
        "app",
        "audio",
        "cell",
        "common",
        "config",
        "controller",
        "copy",
        "helpers",
        "launcher",
        "menu",
        "model",
        "render",
        "scoring",
        "runtime",
        "schema",
        "state",
        "store",
        "topology",
        "types",
        "utils",
        "validate",
        "view",
    }
)
GENERIC_LIKELY_TEST_STEMS = frozenset(
    {
        "menu",
        "render",
        "scoring",
        "state",
        "topology",
    }
)
NON_AFFINITY_PATH_TOKENS = frozenset(
    {
        "src",
        "tet4d",
        "tests",
        "test",
        "unit",
        "integration",
        "ui",
        "pygame",
        "engine",
        "core",
        "runtime",
        "cli",
        "ai",
        "playbot",
    }
)
THIN_CLI_PREFIX_HINT_SUFFIX_TOKENS = frozenset(
    {
        "cli",
        "launch",
        "launcher",
        "route",
        "routes",
        "setup",
        "smoke",
    }
)
MAX_THIN_CLI_SHIM_REAL_LOC = 40


@dataclass(frozen=True)
class _SymbolIndexConfig:
    source_roots: tuple[str, ...]
    max_symbols_per_file: int


@dataclass(frozen=True)
class _LikelyTestFilesConfig:
    source_roots: tuple[str, ...]
    test_roots: tuple[str, ...]
    max_matches_per_file: int


@dataclass(frozen=True)
class _LikelyTestMatch:
    path: str
    tier: str


def _load_maintenance_doc_contract() -> dict[str, object]:
    payload = load_maintenance_docs(PROJECT_ROOT)
    if isinstance(payload, dict):
        return payload
    raise SystemExit("missing required file: config/project/policy_pack.json")


def _rows_from_entries(entries: object) -> tuple[tuple[str, str], ...]:
    if not isinstance(entries, list):
        return ()
    rows: list[tuple[str, str]] = []
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        path = entry.get("path")
        description = entry.get("description")
        if isinstance(path, str) and isinstance(description, str):
            rows.append((path, description))
    return tuple(rows)


def _owner_rows(
    contract: dict[str, object], section: str, heading: str
) -> tuple[tuple[str, str], ...]:
    owners = contract.get(section)
    if not isinstance(owners, dict):
        return ()
    return _rows_from_entries(owners.get(heading))


def _verification_contract(
    contract: dict[str, object],
) -> tuple[str, str, tuple[str, ...]]:
    verification = contract.get("verification")
    if not isinstance(verification, dict):
        return (
            "CODEX_MODE=1 ./scripts/verify.sh",
            "./scripts/ci_check.sh",
            (),
        )
    local_gate = verification.get("local_gate")
    if not isinstance(local_gate, str) or not local_gate.strip():
        local_gate = "CODEX_MODE=1 ./scripts/verify.sh"
    ci_entrypoint = verification.get("ci_entrypoint")
    if not isinstance(ci_entrypoint, str) or not ci_entrypoint.strip():
        ci_entrypoint = "./scripts/ci_check.sh"
    enforcers = verification.get("enforcers")
    if not isinstance(enforcers, list):
        return local_gate, ci_entrypoint, ()
    return (
        local_gate,
        ci_entrypoint,
        tuple(path for path in enforcers if isinstance(path, str)),
    )


def _arch_metrics_payload() -> dict[str, object]:
    result = subprocess.run(
        [sys.executable, "scripts/arch_metrics.py"],
        cwd=PROJECT_ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    return json.loads(result.stdout)


def _replace_generated_section(text: str, marker_id: str, body: str) -> str:
    begin = f"<!-- BEGIN GENERATED:{marker_id} -->"
    end = f"<!-- END GENERATED:{marker_id} -->"
    start_idx = text.find(begin)
    end_idx = text.find(end)
    if start_idx == -1 or end_idx == -1 or end_idx < start_idx:
        raise RuntimeError(f"missing generated marker block: {marker_id}")
    before = text[: start_idx + len(begin)]
    after = text[end_idx:]
    rendered = "\n" + body.rstrip() + "\n"
    return before + rendered + after


def _render_numbered_rows(rows: Iterable[tuple[str, str]]) -> str:
    return "\n".join(
        f"{index}. `{path}`: {description}"
        for index, (path, description) in enumerate(rows, start=1)
    )


def _render_bullet_rows(rows: Iterable[str]) -> str:
    return "\n".join(f"- `{row}`" for row in rows)


def _string_tuple(value: object, *, default: tuple[str, ...]) -> tuple[str, ...]:
    if not isinstance(value, list):
        return default
    cleaned: list[str] = []
    for item in value:
        if not isinstance(item, str):
            return default
        stripped = item.strip()
        if not stripped:
            return default
        cleaned.append(stripped)
    return tuple(cleaned) if cleaned else default


def _bounded_positive_int(
    value: object,
    *,
    default: int,
    maximum: int,
) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        return default
    return min(value, maximum)


def _symbol_index_config(contract: dict[str, object]) -> _SymbolIndexConfig:
    raw = contract.get("symbol_index")
    if not isinstance(raw, dict):
        raw = {}
    return _SymbolIndexConfig(
        source_roots=_string_tuple(
            raw.get("source_roots"), default=DEFAULT_SYMBOL_SOURCE_ROOTS
        ),
        max_symbols_per_file=_bounded_positive_int(
            raw.get("max_symbols_per_file"),
            default=DEFAULT_SYMBOLS_PER_FILE,
            maximum=MAX_SYMBOLS_PER_FILE,
        ),
    )


def _likely_test_files_config(
    contract: dict[str, object],
) -> _LikelyTestFilesConfig:
    raw = contract.get("likely_test_files")
    if not isinstance(raw, dict):
        raw = {}
    return _LikelyTestFilesConfig(
        source_roots=_string_tuple(
            raw.get("source_roots"), default=DEFAULT_TEST_SOURCE_ROOTS
        ),
        test_roots=_string_tuple(raw.get("test_roots"), default=DEFAULT_TEST_ROOTS),
        max_matches_per_file=_bounded_positive_int(
            raw.get("max_matches_per_file"),
            default=DEFAULT_TEST_MATCHES_PER_FILE,
            maximum=MAX_TEST_MATCHES_PER_FILE,
        ),
    )


def _iter_rel_python_files(*, roots: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(iter_python_files(PROJECT_ROOT, roots=roots))


def _parse_python_module(path: Path) -> ast.Module | None:
    try:
        return ast.parse(path.read_text(encoding="utf-8"))
    except (
        FileNotFoundError,
        IsADirectoryError,
        OSError,
        SyntaxError,
        UnicodeDecodeError,
    ):
        return None


def _is_public_top_level_symbol(node: ast.stmt) -> bool:
    return isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and (
        not node.name.startswith("_")
    )


def _tokenize(text: str) -> tuple[str, ...]:
    return tuple(token for token in re.findall(r"[a-z0-9]+", text.lower()) if token)


def _test_name_tokens(path: str) -> tuple[str, ...]:
    name = Path(path).stem
    prefix = "test_"
    if name.startswith(prefix):
        name = name[len(prefix) :]
    return _tokenize(name)


def _substantive_stem_tokens(stem: str) -> tuple[str, ...]:
    return tuple(
        token
        for token in _tokenize(stem)
        if len(token) >= 2 and token not in GENERIC_FALLBACK_TOKENS
    )


def _path_affinity_tokens(path: str) -> frozenset[str]:
    tokens = {
        token
        for part in Path(path).parent.parts
        for token in _tokenize(part)
        if len(token) >= 2 and token not in NON_AFFINITY_PATH_TOKENS
    }
    return frozenset(tokens)


@lru_cache(maxsize=None)
def _read_text_cached(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except (FileNotFoundError, IsADirectoryError, OSError, UnicodeDecodeError):
        return ""


def _source_module_path(source_path: str) -> str | None:
    parts = Path(source_path).with_suffix("").parts
    if not parts:
        return None
    if parts[0] == "src" and len(parts) >= 2:
        return ".".join(parts[1:])
    if parts[0] == "cli":
        return ".".join(parts)
    return None


def _test_mentions_source_module(test_path: str, source_path: str) -> bool:
    module_path = _source_module_path(source_path)
    if not module_path:
        return False
    text = _read_text_cached(PROJECT_ROOT / test_path)
    if not text:
        return False
    if module_path in text:
        return True
    parent, _, name = module_path.rpartition(".")
    if not parent or not name:
        return False
    pattern = rf"\bfrom\s+{re.escape(parent)}\s+import\s+.*\b{re.escape(name)}\b"
    return re.search(pattern, text) is not None


def _stem_is_generic(stem: str) -> bool:
    tokens = frozenset(_tokenize(stem))
    return bool(tokens) and tokens.issubset(GENERIC_LIKELY_TEST_STEMS)


def _is_thin_cli_shim(source_path: str) -> bool:
    path = PROJECT_ROOT / source_path
    if Path(source_path).parent.as_posix() != "cli" or not path.is_file():
        return False
    try:
        return drift_guard.count_real_loc(path) <= MAX_THIN_CLI_SHIM_REAL_LOC
    except OSError:
        return False


def _prefix_suffix_tokens(source_path: str, test_path: str) -> frozenset[str]:
    stem = Path(source_path).stem
    candidate = Path(test_path).stem
    prefix = f"test_{stem}_"
    if not candidate.startswith(prefix):
        return frozenset()
    return frozenset(_tokenize(candidate[len(prefix) :]))


def _match_support(source_path: str, test_path: str) -> tuple[bool, int]:
    return (
        _test_mentions_source_module(test_path, source_path),
        len(_path_affinity_tokens(source_path) & _path_affinity_tokens(test_path)),
    )


def _trim_compact_items(items: list[str]) -> str:
    text = ", ".join(items)
    if len(text) <= MAX_SIGNATURE_CHARS and len(items) <= MAX_SIGNATURE_ITEMS:
        return text
    trimmed: list[str] = []
    for item in items:
        candidate = ", ".join(trimmed + [item])
        if (
            len(candidate) > MAX_SIGNATURE_CHARS
            or len(trimmed) >= MAX_SIGNATURE_ITEMS - 1
        ):
            break
        trimmed.append(item)
    while trimmed and trimmed[-1] in {"/", "*"}:
        trimmed.pop()
    if not trimmed:
        return "..."
    return ", ".join([*trimmed, "..."])


def _positional_signature_items(
    args: ast.arguments, *, skip_first: bool = False
) -> list[str]:
    positional = [*args.posonlyargs, *args.args]
    posonly_count = len(args.posonlyargs)
    if skip_first and positional:
        positional = positional[1:]
        if posonly_count:
            posonly_count -= 1
    default_offset = len(positional) - len(args.defaults)
    items: list[str] = []
    for index, arg in enumerate(positional):
        entry = arg.arg
        if index >= default_offset:
            entry += "=..."
        items.append(entry)
        if posonly_count and index + 1 == posonly_count:
            items.append("/")
    return items


def _keyword_signature_items(args: ast.arguments) -> list[str]:
    items: list[str] = []
    if args.vararg is not None:
        items.append(f"*{args.vararg.arg}")
    elif args.kwonlyargs:
        items.append("*")
    for arg, default in zip(args.kwonlyargs, args.kw_defaults):
        entry = arg.arg
        if default is not None:
            entry += "=..."
        items.append(entry)
    if args.kwarg is not None:
        items.append(f"**{args.kwarg.arg}")
    return items


def _compact_signature(args: ast.arguments, *, skip_first: bool = False) -> str:
    items = _positional_signature_items(args, skip_first=skip_first)
    items.extend(_keyword_signature_items(args))
    return f"({_trim_compact_items(items)})"


def _class_constructor_signature(node: ast.ClassDef) -> str:
    for child in node.body:
        if (
            isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef))
            and child.name == "__init__"
        ):
            return _compact_signature(child.args, skip_first=True)
    return ""


def _format_public_symbol(node: ast.stmt) -> str:
    if isinstance(node, ast.ClassDef):
        signature = _class_constructor_signature(node)
        return f"{node.name}{signature}"
    if isinstance(node, ast.AsyncFunctionDef):
        return f"async {node.name}{_compact_signature(node.args)}"
    if isinstance(node, ast.FunctionDef):
        return f"{node.name}{_compact_signature(node.args)}"
    raise TypeError(f"unsupported symbol node: {type(node)!r}")


def _public_symbol_skim(
    rel_path: str,
    *,
    max_symbols: int,
) -> tuple[tuple[str, ...], bool]:
    tree = _parse_python_module(PROJECT_ROOT / rel_path)
    if tree is None:
        return (), False
    symbols: list[str] = []
    truncated = False
    for node in tree.body:
        if not _is_public_top_level_symbol(node):
            continue
        if len(symbols) >= max_symbols:
            truncated = True
            break
        symbols.append(_format_public_symbol(node))
    return tuple(symbols), truncated


def _fallback_test_matches(
    source_path: str,
    test_paths: tuple[str, ...],
    *,
    max_matches: int,
) -> tuple[_LikelyTestMatch, ...]:
    stem_tokens = frozenset(_substantive_stem_tokens(Path(source_path).stem))
    if not stem_tokens:
        return ()
    ranked: list[tuple[int, int, int, int, str]] = []
    for test_path in test_paths:
        candidate_tokens = frozenset(_test_name_tokens(test_path))
        shared_tokens = stem_tokens & candidate_tokens
        shared_count = len(shared_tokens)
        if shared_count == 0:
            continue
        mentions_source, affinity_hits = _match_support(source_path, test_path)
        if shared_count < 2 and not (
            shared_count == 1 and affinity_hits >= 1 and len(stem_tokens) >= 2
        ):
            continue
        extra_tokens = len(candidate_tokens - stem_tokens)
        score = shared_count * 100 + affinity_hits * 15 + int(mentions_source) * 25
        score -= extra_tokens
        ranked.append(
            (-score, -int(mentions_source), -affinity_hits, extra_tokens, test_path)
        )
    ranked.sort()
    limited = ranked[: min(max_matches, MAX_FALLBACK_TEST_MATCHES)]
    return tuple(_LikelyTestMatch(path=path, tier="fallback") for *_, path in limited)


def _likely_test_files_for_source(
    source_path: str,
    test_paths: tuple[str, ...],
    *,
    max_matches: int,
) -> tuple[_LikelyTestMatch, ...]:
    stem = Path(source_path).stem
    exact_name = f"test_{stem}.py"
    exact_matches = tuple(
        path
        for path in test_paths
        if Path(path).name == exact_name
        and (not _stem_is_generic(stem) or any(_match_support(source_path, path)))
    )
    if exact_matches:
        ranked_exact = sorted(
            exact_matches,
            key=lambda path: (
                -int(_match_support(source_path, path)[0]),
                -_match_support(source_path, path)[1],
                len(path),
                path,
            ),
        )
        return tuple(
            _LikelyTestMatch(path=path, tier="exact")
            for path in ranked_exact[:max_matches]
        )
    prefix = f"test_{stem}_"
    prefix_matches: list[tuple[int, int, int, str]] = []
    for path in test_paths:
        if not Path(path).name.startswith(prefix):
            continue
        suffix_tokens = _prefix_suffix_tokens(source_path, path)
        mentions_source, affinity_hits = _match_support(source_path, path)
        if _is_thin_cli_shim(source_path) and (
            not suffix_tokens
            or not suffix_tokens.issubset(THIN_CLI_PREFIX_HINT_SUFFIX_TOKENS)
        ):
            continue
        if _stem_is_generic(stem) and not (mentions_source or affinity_hits >= 1):
            continue
        prefix_matches.append((-int(mentions_source), -affinity_hits, len(path), path))
    if prefix_matches and _substantive_stem_tokens(stem):
        prefix_matches.sort()
        return tuple(
            _LikelyTestMatch(path=path, tier="prefix")
            for _, _, _, path in prefix_matches[:max_matches]
        )
    return _fallback_test_matches(source_path, test_paths, max_matches=max_matches)


def _render_public_symbol_skim(contract: dict[str, object]) -> str:
    config = _symbol_index_config(contract)
    rows: list[str] = []
    for rel_path in _iter_rel_python_files(roots=config.source_roots):
        symbols, truncated = _public_symbol_skim(
            rel_path, max_symbols=config.max_symbols_per_file
        )
        if not symbols:
            continue
        symbol_text = ", ".join(f"`{symbol}`" for symbol in symbols)
        if truncated:
            symbol_text += ", ..."
        rows.append(f"- `{rel_path}`: {symbol_text}")
    lines = [
        "## Public Symbol Skim",
        "",
        "This routing aid lists compact top-level public symbols from configured source files.",
        "It is a public symbol skim for navigation, not full API documentation, and it does not try to list every symbol.",
    ]
    if rows:
        lines.extend(["", *rows])
    else:
        lines.extend(["", "No configured source files produced symbol-routing hints."])
    return "\n".join(lines)


def _render_likely_test_files(contract: dict[str, object]) -> str:
    config = _likely_test_files_config(contract)
    test_paths = tuple(
        path
        for path in _iter_rel_python_files(roots=config.test_roots)
        if Path(path).name.startswith("test_")
    )
    rows: list[str] = []
    for rel_path in _iter_rel_python_files(roots=config.source_roots):
        matches = _likely_test_files_for_source(
            rel_path,
            test_paths,
            max_matches=config.max_matches_per_file,
        )
        if not matches:
            continue
        rows.append(
            f"- `{rel_path}`: "
            + ", ".join(f"`{match.path}` ({match.tier})" for match in matches)
        )
    lines = [
        "## Likely Test Files",
        "",
        "These heuristic links are likely test files for configured sources.",
        "They are routing hints only, using tiered exact, prefix, then controlled fallback matching.",
        "Match labels are shown inline as `(exact)`, `(prefix)`, or `(fallback)`.",
    ]
    if rows:
        lines.extend(["", *rows])
    else:
        lines.extend(
            ["", "No likely test-file hints were produced from the configured roots."]
        )
    return "\n".join(lines)


def _top_pressure_lines(metrics: dict[str, object]) -> list[str]:
    weighted = metrics["tech_debt"]["weighted_component_contributions"]
    if not isinstance(weighted, dict):
        return []
    ranked = sorted(
        (
            (name, float(value))
            for name, value in weighted.items()
            if float(value) > 0.0
        ),
        key=lambda item: item[1],
        reverse=True,
    )
    return [
        f"{index}. `{name} = {value:.2f}`"
        for index, (name, value) in enumerate(ranked[:2], start=1)
    ]


def render_current_state_sections(
    metrics: dict[str, object] | None = None,
) -> dict[str, str]:
    payload = metrics if metrics is not None else _arch_metrics_payload()
    drift_manifest = drift_guard._load_manifest()
    deep = payload["deep_imports"]
    purity = payload["engine_core_purity"]
    debt = payload["tech_debt"]
    sections: dict[str, str] = {}

    metric_lines = [
        "## Current Metric Snapshot",
        "",
        "From `python scripts/arch_metrics.py`:",
        "",
        f"- `deep_imports.engine_to_ui_non_api.count = {deep['engine_to_ui_non_api']['count']}`",
        f"- `deep_imports.engine_to_ai_non_api.count = {deep['engine_to_ai_non_api']['count']}`",
        f"- `deep_imports.ui_to_engine_non_api.count = {deep['ui_to_engine_non_api']['count']}` (allowed under current rule)",
        f"- `deep_imports.ai_to_engine_non_api.count = {deep['ai_to_engine_non_api']['count']}` (allowed under current rule)",
        f"- `engine_core_purity.violation_count = {purity['violation_count']}`",
        f"- `migration_debt_signals.pygame_imports_non_test.count = {payload['migration_debt_signals']['pygame_imports_non_test']['count']}`",
        f"- `tech_debt.score = {float(debt['score']):.2f}` (`{debt['status']}`)",
        "",
        "Dominant remaining pressure:",
        "",
    ]
    metric_lines.extend(_top_pressure_lines(payload))
    sections["current_state_metric_snapshot"] = "\n".join(metric_lines)
    sections["current_state_drift_watch"] = _render_current_state_drift_watch(
        drift_manifest=drift_manifest
    )
    return sections


def _render_current_state_drift_watch(*, drift_manifest: dict[str, object]) -> str:
    hotspot_scan = drift_manifest.get("hotspot_scan", {})
    if isinstance(hotspot_scan, dict):
        top_n = int(hotspot_scan.get("top_n", 8))
        roots = drift_guard._validate_hotspot_scan(hotspot_scan, [])
    else:
        top_n = 8
        roots = ("src", "cli", "tests", "tools", "scripts")
    hotspots = drift_guard.collect_top_hotspots(roots=roots, top_n=top_n)

    budget_rows: list[str] = []
    budget_entries = drift_manifest.get("thin_wrapper_budgets", [])
    if isinstance(budget_entries, list):
        for entry in budget_entries:
            if not isinstance(entry, dict):
                continue
            raw_path = entry.get("path")
            max_real_loc = entry.get("max_real_loc")
            role = entry.get("role")
            if not isinstance(raw_path, str) or not isinstance(max_real_loc, int):
                continue
            if not isinstance(role, str):
                role = "wrapper budget"
            current = drift_guard.count_real_loc(PROJECT_ROOT / raw_path)
            budget_rows.append(
                f"{raw_path}: {current}/{max_real_loc} real LOC ({role})"
            )

    lines = [
        "## Live Drift Watch",
        "",
        "Generated from `tools/governance/check_drift_protection.py` and `config/project/policy_pack.json`.",
        "",
        f"Top {top_n} live Python hotspots by real LOC:",
        "",
    ]
    lines.extend(
        f"{index}. `{path}`: `{loc}` real LOC"
        for index, (loc, path) in enumerate(hotspots, start=1)
    )
    lines.extend(
        [
            "",
            "Thin-wrapper budgets:",
            "",
        ]
    )
    lines.extend(f"{index}. `{row}`" for index, row in enumerate(budget_rows, start=1))
    lines.extend(
        [
            "",
            "Tutorial wording drift guard:",
            "",
            "1. Lesson copy must not start with `Goal:` or `Action:`.",
            "2. Tutorial overlay must keep `Do this:`, `Tip:`, and `USE:` tokens.",
        ]
    )
    return "\n".join(lines)


def render_project_structure_sections() -> dict[str, str]:
    maintenance_contract = _load_maintenance_doc_contract()
    local_gate, _, enforcers = _verification_contract(maintenance_contract)
    sections: dict[str, str] = {}
    sections["project_structure_entry_points"] = "\n".join(
        [
            "## Canonical Entry Points",
            "",
            _render_numbered_rows(
                _rows_from_entries(maintenance_contract.get("entry_points"))
            ),
        ]
    )

    owner_lines = ["## Canonical Runtime Owners", ""]
    for heading in ("Engine", "UI", "AI"):
        owner_lines.append(f"### {heading}")
        owner_lines.append("")
        owner_lines.append(
            _render_numbered_rows(
                _owner_rows(maintenance_contract, "runtime_owners", heading)
            )
        )
        owner_lines.append("")
    sections["project_structure_runtime_owners"] = "\n".join(owner_lines).rstrip()

    sections["project_structure_sources_of_truth"] = "\n".join(
        [
            "## Config And Docs Sources Of Truth",
            "",
            _render_numbered_rows(
                _rows_from_entries(maintenance_contract.get("sources_of_truth"))
            ),
        ]
    )

    sections["project_structure_verification_contract"] = "\n".join(
        [
            "## Verification Contract",
            "",
            "Run:",
            "",
            "```bash",
            local_gate,
            "```",
            "",
            "Authoritative enforcement is backed by:",
            "",
            *[f"{index}. `{path}`" for index, path in enumerate(enforcers, start=1)],
        ]
    )
    sections["project_structure_symbol_index"] = _render_public_symbol_skim(
        maintenance_contract
    )
    sections["project_structure_likely_test_files"] = _render_likely_test_files(
        maintenance_contract
    )
    return sections


def render_current_state_doc() -> str:
    text = CURRENT_STATE_PATH.read_text(encoding="utf-8")
    for marker_id, body in render_current_state_sections().items():
        text = _replace_generated_section(text, marker_id, body)
    return text.rstrip() + "\n"


def render_project_structure_doc() -> str:
    text = PROJECT_STRUCTURE_PATH.read_text(encoding="utf-8")
    for marker_id, body in render_project_structure_sections().items():
        text = _replace_generated_section(text, marker_id, body)
    return text.rstrip() + "\n"


def _check_doc(path: Path, expected: str) -> int:
    actual = path.read_text(encoding="utf-8")
    if actual != expected:
        rel = path.relative_to(PROJECT_ROOT).as_posix()
        print(
            f"Generated maintenance documentation is out of date: {rel}. Run tools/governance/generate_maintenance_docs.py.",
            file=sys.stderr,
        )
        return 1
    return 0


def check_generated_docs() -> int:
    failures = 0
    failures |= _check_doc(CURRENT_STATE_PATH, render_current_state_doc())
    failures |= _check_doc(PROJECT_STRUCTURE_PATH, render_project_structure_doc())
    return 1 if failures else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--check",
        action="store_true",
        help="fail if generated maintenance docs are stale",
    )
    args = parser.parse_args(argv)
    if args.check:
        return check_generated_docs()
    CURRENT_STATE_PATH.write_text(render_current_state_doc(), encoding="utf-8")
    PROJECT_STRUCTURE_PATH.write_text(render_project_structure_doc(), encoding="utf-8")
    print(f"Wrote {CURRENT_STATE_PATH.relative_to(PROJECT_ROOT).as_posix()}")
    print(f"Wrote {PROJECT_STRUCTURE_PATH.relative_to(PROJECT_ROOT).as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
