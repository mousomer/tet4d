from __future__ import annotations

import tools.governance.check_wheel_reuse_rules as wheel


def test_ast_detector_flags_custom_bool_parser() -> None:
    text = """
def parse_bool(value: str) -> bool:
    normalized = value.strip().lower()
    return normalized in ("true", "1", "yes")
"""
    matched = wheel._match_ast_detectors(text, ["custom_bool_parser"])
    assert "ast:custom_bool_parser" in matched


def test_exception_marker_suppresses_violation() -> None:
    text = """
# Wheel Exception: strict semantic compatibility
def parse_bool(value: str) -> bool:
    normalized = value.strip().lower()
    return normalized in ("true", "1", "yes")
"""
    matched = wheel._violates_rule(
        text=text,
        forbidden_regex=[r"\.strip\(\)\.lower\(\)\s+in\s+\([^)]+\)"],
        ast_detectors=["custom_bool_parser"],
        prefer_symbols=[],
        exception_marker="Wheel Exception:",
    )
    assert matched == []
