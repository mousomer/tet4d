import math
import os
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

out = Path(os.environ["SPHERE_OUTPUT"])
frames = out / "frames"
frames.mkdir(parents=True, exist_ok=True)
W, H = 1120, 760
font_file = os.environ["GLUING_FONT"]
fonts = {n: ImageFont.truetype(font_file, n) for n in (16, 18, 20, 23, 27, 39)}
colors = {"a": "#ffb45c", "b": "#64e2e9"}
N = 64
nodes, index, tris = [], {}, []
for i in range(N + 1):
    for j in range(N + 1 - i):
        index[i, j] = len(nodes)
        nodes.append((N - i - j, i, j))
for i in range(N):
    for j in range(N - i):
        tris.append([index[i, j], index[i + 1, j], index[i, j + 1]])
        if i + j + 1 < N:
            tris.append([index[i + 1, j], index[i + 1, j + 1], index[i, j + 1]])
nodes = np.array(nodes, dtype=float)
nodes /= np.linalg.norm(nodes, axis=1)[:, None]
# Flip each corner ear so the upper and lower patches each have
# their own interior edges all the way to the cone tips.
for corner in (index[0, 0], index[N, 0], index[0, N]):
    ear_id = next(i for i, tri in enumerate(tris) if corner in tri)
    ear = tris[ear_id]
    k = ear.index(corner)
    left, right = ear[(k + 1) % 3], ear[(k + 2) % 3]
    neighbor_id = next(
        i for i, tri in enumerate(tris) if i != ear_id and left in tri and right in tri
    )
    inward = next(i for i in tris[neighbor_id] if i not in (left, right))
    tris[ear_id] = [corner, left, inward]
    tris[neighbor_id] = [corner, inward, right]
tris = np.array(tris)
edge_a = [index[i, 0] for i in range(N + 1)]
edge_b = [index[N - i, i] for i in range(N + 1)]
A, B, C = index[0, 0], index[N, 0], index[0, N]
seam_mid_a, seam_mid_b = edge_a[N // 2], edge_b[N // 2]
light = np.array([-0.35, 0.65, 0.67])


def ease(x):
    x = min(1, max(0, x))
    return x * x * (3 - 2 * x)


def patch(uvw, side, fold, puff, gap):
    u, v, w = uvw.T
    bend = puff
    a, b, c = u * u, v * v, w * w
    x = c - a + bend * 0.42 * b * (c - a)
    y = b - 0.5 + bend * 0.18 * b * (a + c)
    z = side * 2.48 * puff * u * v * w
    if side < 0:
        angle = math.pi * (1 - fold)
        y = (y + 0.5) * math.cos(angle) - 0.5
        z -= (b + bend * 0.18 * b * (a + c)) * math.sin(angle)
        z -= gap * 4 * b * c
    return np.column_stack((x, y, z))


def camera(t):
    end = ease((t - 3.3) / 2.7)
    rotate = ease((t - 8.1) / 2.4)
    roll = math.pi / 4 * (1 - ease((t - 1.45) / 2.45)) - 0.065 * end
    az = 0.31 * end - 0.61 * rotate
    el = 0.73 * end - 0.16 * rotate
    cr, sr, ca, sa, ce, se = (
        math.cos(roll),
        math.sin(roll),
        math.cos(az),
        math.sin(az),
        math.cos(el),
        math.sin(el),
    )
    return (
        np.array([[cr, sr, 0], [-sr, cr, 0], [0, 0, 1]])
        @ np.array([[1, 0, 0], [0, ce, -se], [0, se, ce]])
        @ np.array([[ca, 0, sa], [0, 1, 0], [-sa, 0, ca]])
    )


def draw_surface(cam, fold, gap, im, project, puff, transparency, t, backdrop, d):
    pts = []
    depth = []
    face_xy = []
    face_colors = []
    for side in (1, -1):
        p = patch(nodes, side, fold, puff, gap)
        q = project(p)
        pts.append(q)
        face = p[tris]
        n = np.cross(face[:, 1] - face[:, 0], face[:, 2] - face[:, 0])
        n *= -side
        n /= np.maximum(np.linalg.norm(n, axis=1)[:, None], 1e-12)
        n = n @ cam.T
        if t < 2.7:
            n = np.where((n[:, 2] < 0)[:, None], -n, n)
        il = np.clip(n @ light, 0, 1)
        base = np.array([120, 161, 203])
        shade = (
            ((0.46 + 0.65 * il[:, None]) * base + 19 * il[:, None] ** 9)
            .clip(0, 255)
            .astype(np.uint8)
        )
        depth.extend(q[tris, 2].mean(axis=1))
        face_xy.extend(q[tris, :2].round().astype(int).tolist())
        face_colors.extend(map(tuple, shade.tolist()))
    for f in np.argsort(depth):
        d.polygon([tuple(p) for p in face_xy[f]], fill=face_colors[f])
    from PIL import ImageChops

    mask = ImageChops.difference(im, backdrop).getchannel("R").point([0] + [255] * 255)
    im.paste(
        im.filter(ImageFilter.GaussianBlur(2)),
        mask=mask.filter(ImageFilter.MinFilter(9)),
    )
    if transparency:
        im = Image.blend(im, backdrop, transparency)
        d = ImageDraw.Draw(im)
    return pts, im, d


def draw_edge_annotations(edge, glued_a, glued_b, lower, top):
    if not glued_a:
        edge(lower, edge_a, "a", True)
    if not glued_b:
        edge(lower, edge_b, "b", True)
    edge(top, edge_a, "a", not glued_b)
    edge(top, edge_b, "b", not glued_b)


def draw_corner_labels(fold, glued_a, glued_b, lower, mark, t, top):
    if glued_b:
        mark(top, A, "A · 90°", (-68, 27))
        mark(top, B, "B + D · 180°", (0, -37))
        mark(top, C, "C · 90°", (68, 27))
    else:
        start = 1 - ease((t - 1.45) / 2.45)
        mark(top, A, "A", (-34, -14 - 17 * start))
        mark(top, C, "C", (34, 15 + 9 * start))
        if glued_a:
            mark(top, B, "B + D", (7, -30))
        else:
            mark(top, B, "B", (25, -27))
            mark(lower, B, "D", (-25, 29) if fold < 0.77 else (-44, 18))


def draw_background_grid(d, transparency):
    if transparency > 0:
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
    t = k / 24
    fold = ease((t - 1.65) / 2.7)
    puff = ease((t - 1.6) / 3.2)
    gap = 0.62 * ease((t - 1.8) / 1.7) * (1 - ease((t - 5.25) / 1.65))
    cam = camera(t)

    def project(p):
        v = p @ cam.T
        scale = 244 + 92 * ease((t - 3.0) / 2.1)
        shift = 1 - ease((t - 1.45) / 2.65)
        return np.column_stack(
            (
                560 + 86 * shift + scale * v[:, 0],
                389 - 84 * shift - scale * v[:, 1],
                v[:, 2],
            )
        )

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
        if t < 1.65
        else "Bring the orange edges together"
        if t < 4.35
        else "Orange seam closed · cyan edges still open"
        if t < 5.25
        else "Bring the cyan edges together"
        if t < 6.9
        else "Both seams closed · three cone points"
    )
    txt(46, 35, "Adjacent-edge gluing", 39)
    txt(48, 87, state, 23, "#a9bfd5")
    d.line((48, 128, W - 48, 128), fill="#34465c")
    transparency = 0.5 * (1 - ease((t - 1.8) / 4.8))
    draw_background_grid(d, transparency)
    backdrop = im.copy()
    pts, im, d = draw_surface(
        cam, fold, gap, im, project, puff, transparency, t, backdrop, d
    )

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
    glued_a = t >= 4.35
    glued_b = t >= 6.9
    draw_edge_annotations(edge, glued_a, glued_b, lower, top)

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
    txt(380, 692, "b   B → C  /  D → C", 18, "#daf8fa", "lm")
    txt(1071, 692, "Sphere  S²" if glued_b else "Square → sphere", 20, "#d6e3ef", "rm")
    im.save(frames / f"{k + 1:04}.png", compress_level=2)


if __name__ == "__main__":
    import sys

    for k in map(int, sys.argv[1:]) if len(sys.argv) > 1 else range(264):
        render(k)
