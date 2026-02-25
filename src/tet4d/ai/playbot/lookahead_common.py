from __future__ import annotations

import time
from collections.abc import Callable, Sequence
from typing import TypeVar


CandidateT = TypeVar("CandidateT")


def choose_best_with_followup(
    *,
    candidates: Sequence[CandidateT],
    base_candidate: CandidateT,
    score_of: Callable[[CandidateT], float],
    cleared_of: Callable[[CandidateT], int],
    followup_score_of: Callable[[CandidateT], float],
    deadline_s: float,
    followup_weight: float,
) -> tuple[CandidateT, float]:
    ranked = sorted(
        candidates, key=lambda item: (score_of(item), cleared_of(item)), reverse=True
    )
    final_candidate = base_candidate
    best_combined = score_of(base_candidate)

    for candidate in ranked:
        if time.perf_counter() >= deadline_s:
            break
        followup_score = followup_score_of(candidate)
        combined = score_of(candidate) + followup_weight * followup_score
        if combined > best_combined or (
            combined == best_combined
            and cleared_of(candidate) > cleared_of(final_candidate)
        ):
            final_candidate = candidate
            best_combined = combined

    return final_candidate, best_combined
