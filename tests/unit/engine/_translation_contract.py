from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Any


def assert_repeated_translation_progress(
    testcase,
    *,
    step: Callable[[], Any],
    signature: Callable[[], Any],
    expected_signatures: Sequence[Any],
    label: str,
    result_assertion: Callable[[Any, Any, int], None] | None = None,
) -> None:
    previous = signature()
    for index, expected in enumerate(expected_signatures, start=1):
        result = step()
        if result_assertion is not None:
            result_assertion(testcase, result, index)
        current = signature()
        testcase.assertNotEqual(
            current,
            previous,
            f"{label} stalled at step {index}",
        )
        testcase.assertEqual(
            current,
            expected,
            f"{label} produced unexpected state at step {index}",
        )
        previous = current
