import math
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


def disk_parameters(uvw, side):
    _a, b, c = (uvw * uvw).T
    r = b + c
    s = np.divide(c, r, out=np.zeros_like(r), where=r > 0)
    theta = np.pi * s if side == 1 else np.pi * (2 - s)
    return r, theta


def immersion(q):
    x, y, z = q.T
    w = (x + 1j * y) / (1 + z + 1e-15)
    den = w**6 + np.sqrt(5) * w**3 - 1
    g = np.column_stack(
        (
            -1.5 * (w * (1 - w**4) / den).imag,
            -1.5 * (w * (1 + w**4) / den).real,
            ((1 + w**6) / den).imag - 0.5,
        )
    )
    return g / np.sum(g * g, axis=1)[:, None]


def param(r, theta):
    theta = theta + 0.64
    q = (
        np.column_stack((2 * r * np.cos(theta), 2 * r * np.sin(theta), 1 - r * r))
        / (1 + r * r)[:, None]
    )
    axis = np.array([np.cos(0.64), np.sin(0.64), 0])
    angle = 0.64
    return (
        q * np.cos(angle)
        + np.cross(axis, q) * np.sin(angle)
        + (q @ axis)[:, None] * axis * (1 - np.cos(angle))
    )


centers = param(np.array([0.0, 1.0]), np.array([0.0, 0.0]))


def boy(uvw, side):
    q = param(*disk_parameters(uvw, side))
    p = immersion(q)
    for center in centers:
        pos = immersion(center[None, :])[0]
        tangent = np.cross(center, [0.0, 0.0, 1.0])
        tangent /= np.linalg.norm(tangent)
        tangent2 = np.cross(center, tangent)
        samples = center + 1e-5 * np.array([tangent, tangent2])
        u, v = immersion(samples / np.linalg.norm(samples, axis=1)[:, None]) - pos
        normal = np.cross(u, v)
        normal /= np.linalg.norm(normal)
        if normal @ (pos - [0, 0, -0.55]) < 0:
            normal = -normal
        # Local support on the same quotient sheet; constant radial slope at apex.
        local = np.abs(q @ center) > 0.84
        dist = np.linalg.norm(p - pos, axis=1)
        h = np.maximum(0, 1 - dist / 0.54) ** 2
        p += local[:, None] * h[:, None] * 0.85 * normal
    return p


def pigment(p):
    angle = np.arctan2(p[:, 1], p[:, 0])
    return np.array([135 + 118 * np.cos(angle - v) for v in (0, 2.1, 4.2)]).T


def section_lines(vertices, faces, level=0.12):
    tri = vertices[faces]
    tri = tri[(tri[:, :, 2].min(1) < level) & (tri[:, :, 2].max(1) > level)]
    segments = []
    for face in tri:
        hits = [
            a + (b - a) * (level - a[2]) / (b[2] - a[2])
            for a, b in zip(face, np.roll(face, 1, axis=0))
            if (a[2] < level) != (b[2] < level)
        ]
        if len(hits) == 2:
            segments.append(hits)
    return np.array(segments)


sections = np.concatenate([section_lines(boy(nodes, i), tris) for i in (1, -1)])


def patch(uvw, side, fold, puff, gap):
    _a, b, c = (uvw * uvw).T
    x = np.where(side == 1, b + c, c)
    y = np.where(side == 1, c, b + c)
    length = np.hypot(x, y)
    theta = np.pi / 4 - np.arctan2(y, x)
    # A circular cone develops to a sector; increasing the azimuth preserves its arc lengths.
    beta = np.pi / 2 - fold * np.arccos(0.25)
    sine = np.sin(beta)
    phi = theta / sine
    along = length * sine * np.cos(phi)
    across = length * sine * np.sin(phi)
    z = length * np.cos(beta)
    px = (along + across) / np.sqrt(2)
    py = (-along + across) / np.sqrt(2)
    angle = 1.37 * fold
    apex = np.array([-0.50 - 0.15 * fold, 0.50 - 0.38 * fold, 0])
    cone = apex + np.column_stack(
        (
            np.cos(angle) * px + np.sin(angle) * z,
            py,
            -np.sin(angle) * px + np.cos(angle) * z,
        )
    )
    target = boy(uvw, side) * 0.86
    return (1 - puff) * cone + puff * target


def camera(t):
    end = ease((t - 4.9) / 2.6)
    rotate = ease((t - 9) / 2.8)
    az = -0.80 * end + 0.66 * rotate
    el = 0.44 * end - 0.34 * rotate
    ca, sa, ce, se = math.cos(az), math.sin(az), math.cos(el), math.sin(el)
    return np.array([[1, 0, 0], [0, ce, -se], [0, se, ce]]) @ np.array(
        [[ca, 0, sa], [0, 1, 0], [-sa, 0, ca]]
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
        base = pigment(boy(nodes, side)[tris].mean(axis=1))
        raw = (0.35 + 0.8 * il[:, None]) * base + 45 * il[:, None] ** 12
        vertex = np.zeros_like(p)
        for col in tris.T:
            np.add.at(vertex, col, raw)
        vertex /= np.maximum(1, np.bincount(tris.ravel(), minlength=len(p)))[:, None]
        shading = vertex[tris]
        for corner in (A, B, C):
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


def draw_edge_annotations(d, edge, glued_a, glued_b, lower, pill, project, t, top, txt):
    if not glued_a:
        edge(lower, edge_a, "a", True)
    if not glued_b:
        edge(lower, edge_b[::-1], "b", True)
    if t < 9:
        edge(top, edge_a, "a", not glued_b)
    if t < 9:
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
    if glued_b and t < 9:
        x, y = project(np.zeros((1, 3)))[0, :2]
        d.ellipse((x - 5, y - 5, x + 5, y + 5), outline="white", width=2)
        d.line((x + 5, y, x + 171, y - 92), fill="white")
        pill(x + 225, y - 92, "Triple crossing", n=16)


def draw_corner_labels(fold, glued_a, glued_b, lower, mark, t, top):
    if glued_b and t < 9:
        ease((t - 9) / 2.8)
        mark(top, A, "A · 90°", (-130, -36))
        mark(top, B, "B + C + D · 270°", (97, -29))
    elif not glued_b:
        start = 1 - ease((t - 1.45) / 2.45)
        mark(top, A, "A", (-34, -14 - 17 * start))
        mark(top, C, "C", (34, 15 + 9 * start))
        if glued_a:
            mark(top, B, "B + D", (7, -30))
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
        scale = 310 - 98 * ease((t - 5.15) / 2.75)
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
        else "Bring the orange edges together"
        if t < 4.25
        else "A is a cone · the cyan rim is open"
        if t < 5.15
        else "Match opposite points on the cyan rim"
        if t < 7.9
        else "Three lobes around the central hollow"
        if t < 10
        else "Three openings · two cone tips"
    )
    txt(46, 35, "Boy’s surface", 39)
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
    txt(91, 692, "a   A → B  /  A → D", 18, "#fae4cd", "lm")
    d.line((338, 692, 368, 692), fill=colors["b"], width=5)
    txt(380, 692, "b   B → C  /  C → D", 18, "#daf8fa", "lm")
    txt(
        1071,
        692,
        "Unlabelled surface"
        if t >= 9
        else "Orange and cyan lines mark glued seams"
        if glued_b
        else "Square → projective plane",
        18,
        "#d6e3ef",
        "rm",
    )
    im.save(frames / f"{k + 1:04}.png", compress_level=2)


if __name__ == "__main__":
    import sys

    for k in map(int, sys.argv[1:]) if len(sys.argv) > 1 else range(576):
        render(k)
