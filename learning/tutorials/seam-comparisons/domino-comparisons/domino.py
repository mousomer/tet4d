"""Reproduce the domino comparisons. Python 3.10+, Pillow, DejaVu Sans."""

import argparse
from functools import lru_cache
from itertools import product
from math import cos, pi, sin
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

N = 5
D = {"L": (-1, 0), "R": (1, 0), "U": (0, 1), "D": (0, -1)}
# Seam entries give paired edge and tangent sign.
GLUES = [("LD+", "RU+"), ("LR-", "DU-"), ("LD-", "RU+")]
TITLES = ["Sphere  S²", "Projective  RP²", "Projective  RP²"]
SUB = ["Adjacent · LB+  RT+", "Opposite · LR−  BT−", "Adjacent · LB−  RT+"]
START = ((0, 1), (1, 1))


def add(p, v, t=1):
    return tuple(x + t * y for x, y in zip(p, v))


def seam(g, d):
    s = next(s for s in GLUES[g] if d in s[:2])
    return next(k for k in s[:2] if k != d), (1 if s[2] == "+" else -1)


def project(g, p, d):
    f, sign = seam(g, d)
    x, y = p
    t = y if d in "LR" else x
    if sign < 0:
        t = N - 1 - t
    h = {"L": -1 - x, "R": x - N, "D": -1 - y, "U": y - N}[d]
    return {"L": (h, t), "R": (N - 1 - h, t), "D": (t, h), "U": (t, N - 1 - h)}[f]


def step(g, p, d):
    q = add(p, D[d])
    return q if all(0 <= x < N for x in q) else project(g, q, d)


def joined(g, p):
    return p[1] in [step(g, p[0], d) for d in D]


def move(g, p, d):
    q = tuple(step(g, v, d) for v in p)
    return (p, True) if q[0] == q[1] else (q, False)


def find_moves():
    found = {}
    for n in range(1, 7):
        for tail in product("LRUD", repeat=n - 1):
            seq = "L" + "".join(tail)
            poses = [START] * 3
            for d in seq:
                results = [move(g, p, d) for g, p in enumerate(poses)]
                if any(b for _, b in results):
                    break
                poses = [q for q, _ in results]
            else:
                key = tuple(joined(g, p) for g, p in enumerate(poses))
                found.setdefault(key, seq)
    return found


FILES = {
    "LUR": "01_left_up_right",
    "LTR": "02_left_rotate_right",
    "LR": "03_opposite_only",
    "LUL": "04_adjacent_projective_only",
    "LDLRL": "05_sphere_only",
}
WORDS = {"L": "Left", "R": "Right", "U": "Up", "D": "Down", "T": "Rotate clockwise"}
S = 48


@lru_cache
def font(n, b=False):
    return ImageFont.truetype("DejaVuSans" + ("-Bold" if b else "") + ".ttf", n)


def xy(v):
    return ((v[0] + 0.5) * S, (N - 0.5 - v[1]) * S)


def draw_tile(draw, c, label, color):
    x, y = xy(c)
    draw.rounded_rectangle((x - 17, y - 17, x + 17, y + 17), radius=7, fill=color)
    draw.text((x, y), label, font=font(16, True), fill="white", anchor="mm")


def rotate_offsets(g):
    # A just crossed left. Its material +x points opposite the incoming normal.
    f, _ = seam(g, "L")
    return D[f], f


def draw_bond(dr, g, at_rest):
    if joined(g, at_rest):
        for a, b in (at_rest, at_rest[::-1]):
            for d, delta in D.items():
                if step(g, a, d) == b:
                    dr.line((xy(a), xy(add(a, delta, 0.5))), fill="#294a55", width=8)


def make_board(g, p, cmd, t, at_rest):
    im = Image.new("RGB", (N * S, N * S), "#ffffff")
    dr = ImageDraw.Draw(im)
    for i in range(N + 1):
        dr.line((0, i * S, N * S, i * S), fill="#c7d5dc")
        dr.line((i * S, 0, i * S, N * S), fill="#c7d5dc")
    if cmd == "T":
        v, edge = rotate_offsets(g)
        angle = -pi * t / 2
        endpoint = add(
            p[0],
            (
                cos(angle) * v[0] - sin(angle) * v[1],
                sin(angle) * v[0] + cos(angle) * v[1],
            ),
        )
        points = [[p[0]], [endpoint, project(g, endpoint, edge)]]
        # The second copy is visible only on the other side of the seam;
        # projection into the neighboring chart is clipped to its board.
    else:
        points = []
        for cell in p:
            pt = add(cell, D[cmd], t)
            copies = [pt]
            if step(g, cell, cmd) != add(cell, D[cmd]):
                copies.append(project(g, pt, cmd))
            points.append(copies)
    if at_rest:
        draw_bond(dr, g, at_rest)
    for i, copies in enumerate(points):
        for pt in copies:
            draw_tile(dr, pt, "AB"[i], ["#007c70", "#7854a4"][i])
    return im


def render(seq, traces, out):
    frames = []
    durations = []
    poses = [START] * 3

    def frame(k, d, t, rest, ms):
        im = Image.new("RGB", (888, 421), "#f3f5f1")
        draw = ImageDraw.Draw(im)

        def label(x, y, s, size, b=False, color="#173943"):
            draw.text((x, y), s, font=font(size, b), fill=color)

        label(19, 10, "   →   ".join(WORDS[c] for c in seq), 25, True)
        phase = (
            "Starting domino"
            if k == 0 and t == 0
            else f"{k + 1}/{len(seq)}   {WORDS[d]}"
        )
        label(20, 48, phase, 17, True, "#875312")
        for g in range(3):
            x = 20 + g * 292
            label(x, 83, TITLES[g], 19, True)
            label(x, 110, SUB[g], 14)
            im.paste(make_board(g, poses[g], d, t, rest[g] if rest else None), (x, 138))
            if rest:
                yes = joined(g, rest[g])
                label(
                    x,
                    385,
                    "A—B   Bond intact" if yes else "A  |  B   Bond lost",
                    16,
                    True,
                    "#12645c" if yes else "#ac3737",
                )
        frames.append(im)
        durations.append(ms)

    for k, d in enumerate(seq):
        targets = []
        for g, p in enumerate(poses):
            if d == "T":
                v, _ = rotate_offsets(g)
                turned = (v[1], -v[0])
                key = next(c for c in D if D[c] == turned)
                q = (p[0], step(g, p[0], key))
            else:
                q, blocked = move(g, p, d)
                assert not blocked
            expected, edge = traces[seq, g, k + 1]
            assert q == expected and joined(g, q) == edge
            targets.append(q)
        if k == 0:
            frame(k, d, 0, poses, 1100)
        for j in range(1, 25):
            u = j / 24
            frame(
                k,
                d,
                u * u * (3 - 2 * u),
                targets if j == 24 else None,
                (2700 if k == len(seq) - 1 else 1150) if j == 24 else 50,
            )
        poses = targets
    gif = out / (FILES[seq] + ".gif")
    frames[0].save(
        gif, save_all=True, append_images=frames[1:], duration=durations, loop=0
    )
    with Image.open(gif) as f:
        assert f.n_frames >= len(seq) * 18 and f.info["loop"] == 0


def main():
    root = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=root)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    traces = {}
    for row in (root / "native_traces.txt").read_text().splitlines():
        seq, g, k, x, y, u, v, b = row.split()
        traces[seq, int(g), int(k)] = (
            ((int(x), int(y)), (int(u), int(v))),
            bool(int(b)),
        )
    found = find_moves()
    assert [
        found[k]
        for k in [(False, True, False), (False, False, True), (True, False, False)]
    ] == list(FILES)[2:]
    for seq in FILES:
        render(seq, traces, args.out)


if __name__ == "__main__":
    main()
