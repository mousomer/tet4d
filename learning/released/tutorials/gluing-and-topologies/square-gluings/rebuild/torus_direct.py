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


def patch(uvw, side, fold, puff, gap=0):
    _a, b, c = (uvw * uvw).T
    x = (b + c if side == 1 else c) - 0.5
    y = 0.5 - (c if side == 1 else b + c)
    k = 2 * np.pi * fold
    circum = 1 + 0.80 * fold
    height = circum * y * np.sinc(k * y / np.pi)
    offset = (
        np.zeros_like(x)
        if not fold
        else circum / k * (-2 * np.sin(k * y / 2) ** 2 + fold**2)
    )
    if not puff:
        return np.column_stack(((1 + 0.65 * fold) * x, height, offset))
    k = 2 * np.pi * puff
    radius = 1.65 * (1 - puff) / k + 0.93 * puff
    angle = k * x
    return np.column_stack(
        (
            (radius - offset) * np.sin(angle),
            height,
            radius * (2 * np.sin(angle / 2) ** 2 - puff**2) + offset * np.cos(angle),
        )
    )


def final(uvw, side):
    return patch(uvw, side, 1, 1)


def pigment(p):
    angle = np.arctan2(p[:, 2], p[:, 0]) + 0.4
    return np.array([147 + 105 * np.cos(angle - v) for v in (0, 2.1, 4.2)]).T


def camera(t):
    curl = ease((t - 1.55) / 2.7)
    bend = ease((t - 5.15) / 2.75)
    orbit = ease((t - 8.5) / 3.0)
    yaw = 0.49 * curl - 1.44 * orbit
    tilt = 0.14 * curl + 0.61 * bend + 0.04 * orbit
    c, s = np.cos(yaw), np.sin(yaw)
    h, j = np.cos(tilt), np.sin(tilt)
    return np.array([[1, 0, 0], [0, h, -j], [0, j, h]]) @ np.array(
        [[c, 0, s], [0, 1, 0], [-s, 0, c]]
    )


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
    ctypes.CDLL(os.environ["GLUING_RASTER"]).paint(
        ptr(arr), W, H, *map(ptr, buffers), len(depth)
    )
    im = Image.fromarray(arr)
    d = ImageDraw.Draw(im)
    return pts, im, d


def draw_edge_annotations(d, edge, glued_a, glued_b, lower, t, top, txt):
    if not glued_a:
        edge(lower, edge_b, "a", True)
    if not glued_b:
        edge(lower, edge_a, "b", True)
    edge(top, edge_a, "a", not glued_b)
    edge(top, edge_b, "b", not glued_b)
    if 4.25 <= t < 7.55:
        for fraction, symbol in ((0.32, "●"), (0.69, "◆")):
            mid = round(N * fraction)
            for q, idx in ((top, edge_b[mid]), (lower, edge_a[mid])):
                x, y = q[idx, :2]
                d.ellipse(
                    (x - 8, y - 8, x + 8, y + 8),
                    fill="#172335",
                    outline=colors["b"],
                    width=2,
                )
                txt(x, y, symbol, 16, colors["b"], "mm")


def draw_corner_labels(fold, glued_a, glued_b, lower, mark, t, top):
    if glued_b:
        mark(top, A, "A + B + C + D · 360°", (-86, 25))
    elif not glued_b:
        start = 1 - ease((t - 1.45) / 2.45)
        if not glued_a:
            mark(top, A, "A", (-34, -14 - 17 * start))
        if not glued_a:
            mark(top, C, "C", (34, 15 + 9 * start))
        if glued_a:
            mark(top, B, "B + C", (36, -29))
            mark(top, A, "A + D", (-39, 32))
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
        scale = 310 - 71 * ease((t - 5.15) / 2.75)
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
        else "Roll the square until the orange edges meet"
        if t < 4.25
        else "Cylinder · the two cyan rims are open"
        if t < 5.15
        else "Bend the cylinder and bring its rims together"
        if t < 7.9
        else "Four right angles meet at one smooth point"
        if t < 10
        else "Torus · the orange and cyan seams meet once"
    )
    txt(46, 35, "Opposite-edge torus", 39)
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
    draw_edge_annotations(d, edge, glued_a, glued_b, lower, t, top, txt)

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
    txt(91, 692, "a   A → B  /  D → C", 18, "#fae4cd", "lm")
    d.line((338, 692, 368, 692), fill=colors["b"], width=5)
    txt(380, 692, "b   B → C  /  A → D", 18, "#daf8fa", "lm")
    txt(
        1071,
        692,
        "Orange and cyan lines mark glued seams" if glued_b else "Square → torus",
        18,
        "#d6e3ef",
        "rm",
    )
    im.save(frames / f"{k + 1:04}.png", compress_level=2)


if __name__ == "__main__":
    import sys

    for k in map(int, sys.argv[1:]) if len(sys.argv) > 1 else range(576):
        render(k)
