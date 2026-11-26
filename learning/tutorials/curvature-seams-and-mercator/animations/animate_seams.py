"""Render the three tutorial GIFs. Run: python animate_seams.py --out ."""

import argparse
from functools import lru_cache
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from seam_paths import LEFT, RIGHT, UP, bond_status, path

BG, INK, MUTED, GOLD = "#f6f4ee", "#183541", "#526871", "#bb7222"
COLORS = ["#007967", "#8248aa", "#355d9a", "#a0442e"]
STEP = 52
SIZE = 4 * STEP
DOMINO = [(0, 1), (1, 1)]
FOUR = [(0, 1), (1, 1), (2, 1), (2, 0)]
ROTATE = "Rotate 90° counterclockwise"
# Committed Cartesian CCW poses from the native tutorial_domino_sequences test.
ROTATED_DOMINO = [[(1, 0), (2, 0)], [(3, 2), (3, 3)]]
ACTIONS = {LEFT: "Left  ←", RIGHT: "Right  →", UP: "Up (+Y)  ↑"}
CLIPS = [
    (
        "01_reverse",
        "Cross the seam, then reverse",
        DOMINO,
        [LEFT, RIGHT],
        [[(2, 0), (1, 1)], DOMINO],
        ["bond broken", "bond intact"],
    ),
    (
        "02_up",
        "Left → Up → Right",
        DOMINO,
        [LEFT, UP, RIGHT],
        [[(2, 1), (1, 2)], [(0, 0), (1, 2)]],
        ["bond broken", "bond broken"],
    ),
    (
        "04_rotate",
        "Left → Rotate 90° CCW → Right",
        DOMINO,
        [LEFT, ROTATE, RIGHT],
        [[(2, 0), (3, 0)], [(0, 1), (0, 0)]],
        ["bond intact", "bond intact"],
    ),
    (
        "03_collision",
        "Two cells claim one destination",
        FOUR,
        [LEFT],
        [FOUR, [(3, 2), (0, 1), (1, 1), (1, 0)]],
        ["bonds intact", "bonds intact"],
    ),
]


@lru_cache(None)
def font(size, bold=False):
    for name in (
        (
            "DejaVuSans-Bold.ttf",
            "arialbd.ttf",
            "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        )
        if bold
        else (
            "DejaVuSans.ttf",
            "arial.ttf",
            "/System/Library/Fonts/Supplemental/Arial.ttf",
        )
    ):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    raise RuntimeError("Install DejaVu Sans or Arial (regular and bold).")


def pixel(p):
    return (round((p[0] + 0.5) * STEP), round((3.5 - p[1]) * STEP))


def tile(draw, p, name, color):
    x, y = pixel(p)
    draw.rounded_rectangle((x - 20, y - 20, x + 20, y + 20), 8, fill=color)
    draw.text((x, y), name, font=font(20, True), fill="white", anchor="mm")


def board(paths, t):
    image = Image.new("RGB", (SIZE, SIZE), "white")
    g = ImageDraw.Draw(image)
    for i in range(5):
        g.line((0, i * STEP, SIZE, i * STEP), fill="#b8c8c8")
        g.line((i * STEP, 0, i * STEP, SIZE), fill="#b8c8c8")
    for index, segment in enumerate(paths):
        if segment.seam:
            for p, d, sign in (
                (segment.source, segment.command, 1),
                (segment.target, segment.arrival, -1),
            ):
                cx, cy = pixel((p[0] + sign * d[0] / 2, p[1] + sign * d[1] / 2))
                vx, vy = 20 * d[1], 20 * d[0]
                g.line(
                    (cx - vx, cy - vy, cx + vx, cy + vy), fill=COLORS[index], width=7
                )
    # Drawing onto the board layer clips each copy at its own boundary.
    for i, segment in enumerate(paths):
        for centre in segment.centres(t):
            tile(g, centre, "ABCD"[i], COLORS[i])
    if t == 1:
        ends = [p.target for p in paths]
        for p in set(ends):
            ids = "".join("ABCD"[i] for i, end in enumerate(ends) if p == end)
            if len(ids) > 1:
                tile(g, p, ids, "#b4253a")
    return image


def render_frame(title, phase, action, paths, times, notes, caption, sample):
    im = Image.new("RGB", (820, 484), BG)
    g = ImageDraw.Draw(im)

    def label(x, y, text, size, bold=False, color=INK):
        g.text((x, y), text, fill=color, font=font(size, bold))

    label(24, 15, title, 28, True)
    label(24, 58, phase, 18, True, GOLD)
    if sample:
        g.rectangle((24, 86, 24 + 5 * sample, 89), fill=GOLD)
    for i, x in enumerate((26, 430)):
        label(
            x, 102, ("S²   /   adjacent edges", "RP²   /   opposite edges")[i], 21, True
        )
        label(x, 129, f"Command  {action}", 14)
        bx, by = x + 68, 154
        im.paste(board(paths[i], times[i]), (bx, by))
        g.rectangle((bx - 1, by - 1, bx + SIZE, by + SIZE), outline=MUTED)
        for k in range(4):
            label(bx + k * STEP + 20, by + SIZE + 3, str(k), 13)
            label(bx - 37, by + (3 - k) * STEP + 17, "y=0" if k == 0 else str(k), 13)
        label(x, 387, notes[i], 17, True)
    label(24, 427, caption, 15)
    label(
        24,
        455,
        (
            "Native-verified poses · Cartesian +Y upward · Matched edge marks indicate crossings."
            if "Rotate" in title
            else "Educational calculation under RDS §2.5 · Cartesian +Y upward · Matched edge marks indicate crossings."
        ),
        13,
        color=MUTED,
    )
    return im


def render(clip, out):
    name, title, source, commands, expected, expected_bonds = clip
    poses = [source, source]
    frames, durations = [], []

    def add(phase, action, paths, t, notes, caption, ms, sample=0):
        frames.append(
            render_frame(title, phase, action, paths, t, notes, caption, sample)
        )
        durations.append(ms)

    def rotation_pose(pose, phase, notes, caption, ms):
        stationary = [
            [path(cell, (0, 0), sphere) for cell in cells]
            for cells, sphere in zip(pose, (True, False))
        ]
        add(phase, ROTATE, stationary, [0, 0], notes, caption, ms)

    for index, cmd in enumerate(commands):
        if cmd == ROTATE:
            rotation_pose(
                poses,
                "Before rotation",
                ["A is the pivot"] * 2,
                "The native solver rebuilds the domino in A’s transported frame.",
                1300,
            )
            poses = ROTATED_DOMINO
            notes = [
                f"Accepted · {bond_status(cells, sphere)}"
                for cells, sphere in zip(poses, (True, False))
            ]
            rotation_pose(
                poses,
                "Rotation committed",
                notes,
                "A stays at the pivot. B is placed at the native solver’s destination.",
                2200,
            )
            continue
        paths = [
            [path(p, cmd, sphere) for p in pose]
            for pose, sphere in zip(poses, (True, False))
        ]
        action = ACTIONS[cmd]
        if index == 0:
            add(
                "Start   /   next move: Left",
                action,
                paths,
                [0, 0],
                ["Start position"] * 2,
                "Track A in teal through the first seam crossing.",
                1500,
            )
        targets = [[p.target for p in row] for row in paths]
        results = [bond_status(c, s) for c, s in zip(targets, (True, False))]
        for k in range(1, 41):
            u = k / 40
            t = u * u * (3 - 2 * u)
            add(
                action + "   /   proposed motion",
                action,
                paths,
                [t] * 2,
                ["Moving"] * 2,
                "Each cell receives the same board command.",
                40,
                sample=k,
            )
        if "collision" in results:
            assert targets[0] == [(1, 0), (0, 1), (1, 1), (1, 0)]
            add(
                "Decision   /   Left",
                action,
                paths,
                [1, 1],
                ["A + D overlap", "Accepted · bonds intact"],
                "Red marks a proposed overlap. The sphere keeps the entire source pose.",
                1800,
            )
            # Remove the proposal as a whole. Rewinding would imply a physical reverse move.
            add(
                "Outcome   /   Left",
                action,
                paths,
                [0, 1],
                ["Rejected · original pose kept", "Accepted · bonds intact"],
                "Only the projective board commits the move.",
                2400,
            )
        else:
            cap = {
                LEFT: "A and B still share an edge through the seam on both boards.",
                RIGHT: "Right restores the original domino on RP². On S² the original quotient bond breaks.",
                UP: "The +Y step breaks the bond on both boards.",
            }[cmd]
            if cmd == RIGHT and len(commands) == 3:
                cap = (
                    "Right moves both cells along the board X axis. The bond stays broken."
                    if UP in commands
                    else "Right preserves the bond. On RP² both cells cross the reversed seam."
                )
            add(
                "Outcome   /   " + action,
                action,
                paths,
                [1, 1],
                ["Accepted · " + r for r in results],
                cap,
                2200,
            )
        poses = [
            src if r == "collision" else dst
            for src, dst, r in zip(poses, targets, results)
        ]
    assert poses == expected
    assert [bond_status(c, s) for c, s in zip(poses, (True, False))] == expected_bonds
    file = out / (name + ".gif")
    frames[0].save(
        file, save_all=True, append_images=frames[1:], duration=durations, loop=0
    )
    with Image.open(file) as gif:
        assert gif.n_frames == len(durations) and gif.info["loop"] == 0
        for frame, duration in enumerate(durations):
            gif.seek(frame)
            assert gif.info["duration"] == duration
        print(file.name, gif.n_frames, "encoded frames")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=Path("."))
    out = parser.parse_args().out
    out.mkdir(parents=True, exist_ok=True)
    for clip in CLIPS:
        render(clip, out)
