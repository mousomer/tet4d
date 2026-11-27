import os
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

out = Path(os.environ["SPHERE_OUTPUT"])
frames = out / "frames"
frames.mkdir(parents=True, exist_ok=True)
W, H = 1120, 760
font_file = os.environ["GLUING_FONT"]
fonts = {n: ImageFont.truetype(font_file, n) for n in (16, 18, 20, 23, 27, 39)}
colors = {"a": "#ffb45c", "b": "#64e2e9"}
N = 72
nodes = [[1.0, 0.0, 0.0]]
tris = []


def idx(i, j):
    return 0 if i == 0 else 1 + (i - 1) * (N + 1) + j


for i in range(1, N + 1):
    r = i / N
    for j in range(N + 1):
        s = j / N
        nodes.append([1 - r, r * (1 - s), r * s])
        if j < N:
            tris.append([idx(i - 1, j), idx(i, j), idx(i, j + 1)])
            if i > 1:
                tris.append([idx(i - 1, j), idx(i, j + 1), idx(i - 1, j + 1)])
nodes = np.sqrt(nodes)
tris = np.array(tris)
edge_a = [idx(i, 0) for i in range(N + 1)]
edge_b = [idx(N, j) for j in range(N + 1)]
A, B, C = 0, edge_b[0], edge_b[-1]
light = np.array([-0.35, 0.65, 0.67])


def ease(x):
    x = min(1, max(0, x))
    return x * x * (3 - 2 * x)


def coords(uvw, side):
    _a, b, c = (uvw * uvw).T
    x = b + c if side == 1 else c
    y = c if side == 1 else b + c
    return x - y, x + y - 0.5


def patch(uvw, side, fold, puff, gap=0):
    l, m = coords(uvw, side)
    v = np.pi * m
    if fold == 0:
        return np.column_stack(((l + m - 0.5) / 2, (l - m + 0.5) / 2, np.zeros_like(l)))
    k = 2 * np.pi * fold
    u = k * l
    radius = (1 - fold) / (np.sqrt(2) * k) + 0.93 * fold
    transverse = (1 - puff) * m * (0.7071 - 0.29 * fold) + puff * 0.41 * np.sin(v)
    height = puff * 0.29 * np.sin(2 * v)
    radial = transverse * np.cos(u / 2) - height * np.sin(u / 2)
    z = transverse * np.sin(u / 2) + height * np.cos(u / 2)
    d = (radius + radial) * np.sin(u)
    e = (
        radius * (-2 * np.sin(u / 2) ** 2 + fold**2)
        + radial * np.cos(u)
        - (1 - fold) * 0.5 / np.sqrt(2)
    )
    return np.column_stack(((d + e) / np.sqrt(2), (d - e) / np.sqrt(2), z))


def final(uvw, side):
    return patch(uvw, side, 1, 1)


def pigment(p):
    angle = np.arctan2(p[:, 1], p[:, 0]) + 0.4
    return np.array([147 + 105 * np.cos(angle - v) for v in (0, 2.1, 4.2)]).T


def camera(t):
    tilt = 0.79 * ease((t - 1.55) / 2.7) + 0.22 * ease((t - 9) / 2.8)
    az = 0.57 * ease((t - 9) / 2.8)
    c, s = np.cos(az), np.sin(az)
    h, j = np.cos(tilt), np.sin(tilt)
    return np.array([[1, 0, 0], [0, h, -j], [0, j, h]]) @ np.array(
        [[c, -s, 0], [s, c, 0], [0, 0, 1]]
    )


def crossing():
    angle = -1.65
    d, e = 0.93 * np.sin(angle), 0.93 * np.cos(angle)
    return np.array([[(d + e) / np.sqrt(2), (d - e) / np.sqrt(2), 0]])


def draw_surface(cam, fold, gap, im, project, puff, transparency):
    pts = []
    depth = []
    face_xy = []
    face_colors = []
    opacity = []
    for side in (1, -1):
        p = patch(nodes, side, fold, puff, gap)
        q = project(p)
        pts.append(q)
        face = p[tris]
        n = np.cross(face[:, 1] - face[:, 0], face[:, 2] - face[:, 0])
        n *= -side
        n /= np.maximum(np.linalg.norm(n, axis=1)[:, None], 1e-12)
        n = n @ cam.T
        n = np.where((n[:, 2] < 0)[:, None], -n, n)
        il = np.clip(n @ light, 0, 1)
        ((p[tris, 0].mean(axis=1) + 0.7) / 1.7).clip(0, 1)[:, None]
        base = pigment(final(nodes, side)[tris].mean(axis=1))
        raw = (0.35 + 0.8 * il[:, None]) * base + 45 * il[:, None] ** 12
        vertex = np.zeros_like(p)
        for col in tris.T:
            np.add.at(vertex, col, raw)
        vertex /= np.maximum(1, np.bincount(tris.ravel(), minlength=len(p)))[:, None]
        shading = vertex[tris]
        for corner in ():
            rr, cc = np.where(tris == corner)
            shading[rr, cc] = raw[rr]
        face_colors.append(np.clip(shading, 0, 255))
        fade = 0
        z = face[:, :, 2].mean(1)
        front = np.clip((z - 0.035) / 0.13, 0, 1)
        opacity.extend((1 - transparency) * (1 - 0.85 * fade * front))
        depth.extend(q[tris, 2].mean(1))
        face_xy.append(q[tris])
    import ctypes

    arr = np.array(im)
    buffers = [
        np.ascontiguousarray(np.concatenate(face_xy)),
        np.ascontiguousarray(np.concatenate(face_colors)),
        np.array(opacity),
        np.argsort(depth).astype(np.int32),
    ]
    ptr = lambda a: ctypes.c_void_p(a.ctypes.data)
    status = ctypes.CDLL(os.environ["GLUING_RASTER"]).paint(
        ptr(arr), W, H, *map(ptr, buffers), len(depth)
    )
    if status:
        raise RuntimeError(
            f"raster.c paint failed (status {status}: 1 invalid arguments, 2 out of memory)"
        )
    im = Image.fromarray(arr)
    d = ImageDraw.Draw(im)
    return pts, im, d


def draw_edge_annotations(d, edge, glued_a, glued_b, lower, pill, project, t, top, txt):
    if not glued_a:
        edge(lower, edge_a[::-1], "a", True)
    if not glued_b:
        edge(lower, edge_b[::-1], "b", True)
    if True:
        edge(top, edge_a, "a", not glued_b)
    if True:
        edge(top, edge_b, "b", not glued_b)
    if 4.25 <= t < 7.55:
        for fraction, symbol in ((0.32, "●"), (0.69, "◆")):
            mid = round(N * fraction)
            for q, idx in ((top, edge_b[mid]), (lower, edge_b[N - mid])):
                x, y = q[idx, :2]
                d.ellipse(
                    (x - 8, y - 8, x + 8, y + 8),
                    fill="#172335",
                    outline=colors["b"],
                    width=2,
                )
                txt(x, y, symbol, 16, colors["b"], "mm")
    if glued_b:
        x, y = project(crossing())[0, :2]
        d.ellipse((x - 5, y - 5, x + 5, y + 5), outline="white", width=2)
        d.line((x + 5, y, x - 135, y - 72), fill="white")
        pill(x - 190, y - 72, "Sheet crossing", n=16)


def draw_corner_labels(fold, glued_a, glued_b, lower, mark, t, top):
    if glued_b:
        mark(top, A, "A + B + C + D · 360°", (93, 48))
    elif not glued_b:
        start = 1 - ease((t - 1.45) / 2.45)
        if not glued_a:
            mark(top, A, "A", (-34, -14 - 17 * start))
        mark(top, C, "C", (34, 15 + 9 * start))
        if glued_a:
            mark(top, B, "A + B + D", (12, -32))
        else:
            mark(top, B, "B", (25, -27))
            mark(lower, B, "D", (-25, 29) if fold < 0.77 else (-44, 18))


def draw_background_grid(d, transparency, t):
    if t < 7.9:
        for x in range(178, 970, 35):
            for y in range(166, 637, 35):
                d.ellipse(
                    (x - 1, y - 1, x + 1, y + 1),
                    fill=tuple(
                        round(a + (b - a) * transparency * 2)
                        for a, b in zip((17, 27, 42), (117, 144, 172))
                    ),
                )


def render(k):
    t = float(
        np.interp(
            k / 24,
            [0, 2, 4, 6, 8, 10, 12, 14, 16, 18, 21, 24],
            [0, 1.55, 2.4, 3.3, 4.25, 5.15, 6, 6.8, 7.9, 9, 11.8, 13],
        )
    )
    fold = ease((t - 1.55) / 2.7)
    puff = ease((t - 5.15) / 2.75)
    gap = 0
    cam = camera(t)

    def project(p):
        v = p @ cam.T
        scale = 310 - 98 * ease((t - 1.55) / 2.7)
        return np.column_stack((560 + scale * v[:, 0], 395 - scale * v[:, 1], v[:, 2]))

    im = Image.new("RGB", (W, H), "#111b2a")
    d = ImageDraw.Draw(im)

    def txt(x, y, s, n=20, fill="#f6f4ed", anchor=None):
        d.text((x, y), s, font=fonts[n], fill=fill, anchor=anchor)

    def pill(x, y, s, fill="#fff3df", n=20):
        bb = d.textbbox((x, y), s, font=fonts[n], anchor="mm")
        d.rounded_rectangle(
            (bb[0] - 10, bb[1] - 6, bb[2] + 10, bb[3] + 6),
            radius=8,
            fill="#172335",
            outline="#52657a",
            width=1,
        )
        txt(x, y, s, n, fill, "mm")

    state = (
        "Match the arrows on the square"
        if t < 1.55
        else "Twist and join the orange edges"
        if t < 4.25
        else "Orange seam closed · A, B and D meet"
        if t < 5.15
        else "Bring C to the shared corner along the cyan seam"
        if t < 7.9
        else "Four right angles meet at one smooth point"
        if t < 10
        else "Figure-eight immersion · two sheets cross"
    )
    txt(46, 35, "Adjacent-edge Klein bottle", 39)
    txt(48, 87, state, 23, "#a9bfd5")
    d.line((48, 128, W - 48, 128), fill="#34465c")
    transparency = 0.65 - 0.05 * ease((t - 1.8) / 4.8)
    draw_background_grid(d, transparency, t)
    im.copy()
    pts, im, d = draw_surface(cam, fold, gap, im, project, puff, transparency)

    def edge(q, ids, key, arrow):
        xy = [tuple(p) for p in q[ids, :2]]
        d.line(xy, fill="#25334a", width=9, joint="curve")
        d.line(xy, fill=colors[key], width=5, joint="curve")
        if arrow:
            mid = len(ids) // 2
            p0 = np.array(xy[mid - 4])
            p1 = np.array(xy[mid + 4])
            v = p1 - p0
            norm = np.linalg.norm(v)
            if norm > 3:
                v /= norm
                cross = np.array([-v[1], v[0]])
                tip = np.array(xy[mid]) + v * 10
                d.polygon(
                    [
                        tuple(tip),
                        tuple(tip - v * 21 + cross * 8),
                        tuple(tip - v * 21 - cross * 8),
                    ],
                    fill="#172335",
                )
                d.polygon(
                    [
                        tuple(tip - v * 3),
                        tuple(tip - v * 18 + cross * 6),
                        tuple(tip - v * 18 - cross * 6),
                    ],
                    fill=colors[key],
                )

    top, lower = pts
    glued_a = t >= 4.25
    glued_b = t >= 7.9
    draw_edge_annotations(d, edge, glued_a, glued_b, lower, pill, project, t, top, txt)

    def mark(q, i, s, offset):
        x, y = q[i, :2]
        dx, dy = offset
        d.ellipse(
            (x - 5, y - 5, x + 5, y + 5), fill="#fff4db", outline="#172335", width=2
        )
        d.line((x, y, x + dx * 0.82, y + dy * 0.82), fill="#c1d2e3", width=1)
        pill(x + dx, y + dy, s, n=18)

    draw_corner_labels(fold, glued_a, glued_b, lower, mark, t, top)
    d.line((48, 661, W - 48, 661), fill="#34465c")
    d.line((49, 692, 79, 692), fill=colors["a"], width=5)
    txt(91, 692, "a   A → B  /  D → A", 18, "#fae4cd", "lm")
    d.line((338, 692, 368, 692), fill=colors["b"], width=5)
    txt(380, 692, "b   B → C  /  C → D", 18, "#daf8fa", "lm")
    txt(
        1071,
        692,
        "Orange and cyan lines mark glued seams"
        if glued_b
        else "Square → Klein bottle",
        18,
        "#d6e3ef",
        "rm",
    )
    im.save(frames / f"{k + 1:04}.png", compress_level=2)


if __name__ == "__main__":
    import sys

    for k in map(int, sys.argv[1:]) if len(sys.argv) > 1 else range(576):
        render(k)
