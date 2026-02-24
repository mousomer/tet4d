from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LayoutRect:
    x: int
    y: int
    width: int
    height: int

    @property
    def right(self) -> int:
        return self.x + self.width

    @property
    def bottom(self) -> int:
        return self.y + self.height


@dataclass(frozen=True)
class MenuLayoutZones:
    frame: LayoutRect
    header: LayoutRect
    content: LayoutRect
    footer: LayoutRect


def _clamp_int(value: int, minimum: int, maximum: int) -> int:
    if minimum > maximum:
        minimum, maximum = maximum, minimum
    return max(minimum, min(maximum, int(value)))


def compute_menu_layout_zones(
    *,
    width: int,
    height: int,
    outer_pad: int,
    header_height: int,
    footer_height: int,
    gap: int,
    min_content_height: int,
) -> MenuLayoutZones:
    w = max(1, int(width))
    h = max(1, int(height))
    min_side = min(w, h)

    pad_cap = max(0, (min_side - 40) // 2)
    pad = _clamp_int(int(outer_pad), 0, pad_cap)

    frame_x = pad
    frame_y = pad
    frame_w = max(1, w - (pad * 2))
    frame_h = max(1, h - (pad * 2))
    frame = LayoutRect(frame_x, frame_y, frame_w, frame_h)

    effective_gap = _clamp_int(int(gap), 1, max(1, frame_h // 8))
    header_min = max(18, frame_h // 12)
    footer_min = max(16, frame_h // 14)

    header_h = _clamp_int(int(header_height), header_min, frame_h)
    footer_h = _clamp_int(int(footer_height), footer_min, frame_h)
    target_content = _clamp_int(int(min_content_height), 1, frame_h)

    total_target = header_h + footer_h + (effective_gap * 2) + target_content
    if total_target > frame_h:
        overflow = total_target - frame_h

        header_reducible = max(0, header_h - header_min)
        reduce_header = min(overflow, header_reducible)
        header_h -= reduce_header
        overflow -= reduce_header

        footer_reducible = max(0, footer_h - footer_min)
        reduce_footer = min(overflow, footer_reducible)
        footer_h -= reduce_footer
        overflow -= reduce_footer

        if overflow > 0 and effective_gap > 1:
            gap_reducible = (effective_gap - 1) * 2
            reduce_gap = min(overflow, gap_reducible)
            effective_gap -= (reduce_gap + 1) // 2

    content_h = max(1, frame_h - header_h - footer_h - (effective_gap * 2))
    header = LayoutRect(frame.x, frame.y, frame.width, header_h)
    content_y = header.bottom + effective_gap
    content = LayoutRect(frame.x, content_y, frame.width, content_h)
    footer_y = content.bottom + effective_gap
    footer_h_final = max(1, frame.bottom - footer_y)
    footer = LayoutRect(frame.x, footer_y, frame.width, footer_h_final)

    return MenuLayoutZones(frame=frame, header=header, content=content, footer=footer)
