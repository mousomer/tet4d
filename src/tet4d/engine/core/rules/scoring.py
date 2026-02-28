def score_for_clear(cleared_count: int) -> int:
    if cleared_count <= 0:
        return 0
    table = {
        1: 40,
        2: 100,
        3: 300,
        4: 1200,
    }
    if cleared_count in table:
        return table[cleared_count]
    return table[4] + (cleared_count - 4) * 400


__all__ = ["score_for_clear"]
