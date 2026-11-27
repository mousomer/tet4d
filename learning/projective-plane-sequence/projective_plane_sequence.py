"""Usage:  python projective_plane_sequence.py keys [out_dir]   -> strip + per-stage PNGs
        python projective_plane_sequence.py anim [out_dir]   -> animated WebP
Requires numpy, matplotlib, pillow.

Square -> Boy's surface (Bryant–Kusner, c = 0.5) with the square's edges and vertices tracked throughout.

Domain: square [-1,1]^2, opposite edges glued with a flip (antipodal boundary) = RP^2.
Fong's elliptical map (odd) sends the square to the unit disk; the surface at stage s is the image of the
parameter disk of radius s, so every intermediate frame is a genuine piece of Boy's surface.
Edge pairs: y = +-1 (orange), x = +-1 (blue). Vertex classes: (1,1)~(-1,-1) white, (1,-1)~(-1,1) black."""

import colorsys
import io
import sys
from itertools import pairwise

import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection

N, LINE_EVERY = 160, 20
S5 = np.sqrt(5.0)
S0 = 0.22


def bk(w, c=0.5):
    w3 = w**3
    w6 = w3 * w3
    d = w6 + S5 * w3 - 1.0
    n1 = w * (1 - w**4)
    n2 = w * (1 + w**4)
    n3 = 1 + w6
    dd = np.abs(d) ** 2
    h1 = -1.5 * np.imag(n1 * np.conj(d))
    h2 = -1.5 * np.real(n2 * np.conj(d))
    h3 = np.imag(n3 * np.conj(d)) - c * dd
    s = dd / np.maximum(h1**2 + h2**2 + h3**2, 1e-300)
    return np.stack([h1 * s, h2 * s, h3 * s], -1)


smooth = lambda t: t * t * (3 - 2 * t)
g = np.linspace(-1, 1, N + 1)
SX, SY = np.meshgrid(g, g, indexing="ij")
U = SX * np.sqrt(1 - SY**2 / 2)
V = SY * np.sqrt(1 - SX**2 / 2)
POLE = bk(np.array([0j]))[0]


def piece(s):
    return bk(s * (U + 1j * V)) - POLE


CAP = piece(S0)
CAP = CAP / np.linalg.norm(CAP, axis=-1).max()
# lay the flat square in the cap's tangent plane, using the best linear fit of the map near the pole,
# so the blend square -> cap never passes through a degenerate (edge-on / mirrored) shape
_A, *_ = np.linalg.lstsq(np.c_[U.ravel(), V.ravel()], CAP.reshape(-1, 3), rcond=None)
SQUARE = (np.c_[SX.ravel(), SY.ravel()] @ _A).reshape(N + 1, N + 1, 3)


def normalise(X):
    X = X - (X.reshape(-1, 3).max(0) + X.reshape(-1, 3).min(0)) / 2
    return X / np.linalg.norm(X, axis=-1).max()


def s_of(t):
    return S0 + (1 - S0) * smooth(min(max(t - 1, 0), 1))


def shape(t):
    """t in [0,2]: 0 flat square, 1 small cap of Boy's surface, 2 whole surface."""
    if t <= 1:
        a = smooth(t)
        return normalise((1 - a) * SQUARE + a * CAP)
    return normalise(piece(s_of(t)))


def alpha_of(t):
    return 1.0 if t <= 1 else 1.0 - 0.52 * smooth(min(t - 1, 1))


# surface colours (fixed on the domain): hue = 2*angle (antipodally invariant), grid lines darkened
cu = 0.25 * (U[:-1, :-1] + U[1:, :-1] + U[1:, 1:] + U[:-1, 1:])
cv = 0.25 * (V[:-1, :-1] + V[1:, :-1] + V[1:, 1:] + V[:-1, 1:])
hue = (2 * np.arctan2(cv, cu) / (2 * np.pi)) % 1.0
sat = np.clip(np.hypot(cu, cv), 0, 1) ** 0.8 * 0.8
base = np.array(
    [colorsys.hsv_to_rgb(h, s, 0.95) for h, s in zip(hue.ravel(), sat.ravel())]
).reshape(N, N, 3)
ii, jj = np.meshgrid(np.arange(N), np.arange(N), indexing="ij")
base[
    (ii % LINE_EVERY == 0) | (jj % LINE_EVERY == 0) | (ii == N - 1) | (jj == N - 1)
] *= 0.4

EDGE_A = np.array([0.95, 0.45, 0.05])  # top & bottom (y = +-1)
EDGE_B = np.array([0.10, 0.35, 0.95])  # left & right (x = +-1)
# boundary polylines in grid indices: (i along x, j along y)
EDGES = [
    ([(i, N) for i in range(N + 1)], EDGE_A),
    ([(i, 0) for i in range(N + 1)], EDGE_A),
    ([(0, j) for j in range(N + 1)], EDGE_B),
    ([(N, j) for j in range(N + 1)], EDGE_B),
]
VERTS = [((N, N), "w"), ((0, 0), "w"), ((N, 0), "k"), ((0, N), "k")]
L = np.array([0.35, 0.55, 0.75])
L /= np.linalg.norm(L)


def view(elev, azim):
    ce, se, ca, sa = np.cos(elev), np.sin(elev), np.cos(azim), np.sin(azim)
    return np.array([[1, 0, 0], [0, ce, -se], [0, se, ce]]) @ np.array(
        [[ca, -sa, 0], [sa, ca, 0], [0, 0, 1]]
    )


def cam(t):
    a = smooth(min(t / 2, 1))
    return view(np.radians(-58 * a), np.radians(25 * a))


def render(ax, t, scale_px=1.0):
    P = shape(t)
    M = cam(t)
    Q = P @ M.T
    al = alpha_of(t)
    q = np.stack([Q[:-1, :-1], Q[1:, :-1], Q[1:, 1:], Q[:-1, 1:]], 2).reshape(-1, 4, 3)
    n = np.cross(q[:, 2] - q[:, 0], q[:, 3] - q[:, 1])
    n /= np.linalg.norm(n, axis=1, keepdims=True) + 1e-12
    n *= np.sign(n[:, 2:3] + 1e-12)
    lam = 0.5 + 0.5 * np.clip(n @ L, 0, 1)
    col = np.c_[np.clip(base.reshape(-1, 3) * lam[:, None], 0, 1), np.full(len(q), al)]
    polys = list(q[:, :, :2])
    depth = list(q[:, :, 2].mean(1))
    cols = list(col)
    w = 0.022 * scale_px
    for path, c in EDGES:
        pts = np.array([Q[i, j] for i, j in path])
        for a, b in pairwise(pts):
            d = b[:2] - a[:2]
            ln = np.linalg.norm(d)
            if ln < 1e-9:
                continue
            e = d / ln * 0.25 * w  # small overlap so segments join without gaps
            for width, colr, bias in (
                (1.55 * w, np.r_[0.04, 0.04, 0.04, 1.0], 0.02),
                (w, np.r_[c, 1.0], 0.021),
            ):
                nn = np.array([-d[1], d[0]]) / ln * width
                polys.append(
                    np.array(
                        [a[:2] - e + nn, b[:2] + e + nn, b[:2] + e - nn, a[:2] - e - nn]
                    )
                )
                depth.append(0.5 * (a[2] + b[2]) + bias)
                cols.append(colr)
    ang = np.linspace(0, 2 * np.pi, 13)[:-1]
    for (i, j), c in VERTS:
        p = Q[i, j]
        ring = np.c_[np.cos(ang), np.sin(ang)]
        polys.append(p[:2] + ring * 0.055 * scale_px)
        depth.append(p[2] + 0.03)
        cols.append(np.r_[0.05, 0.05, 0.05, 1.0])
        fill = [1, 1, 1] if c == "w" else [0.12, 0.12, 0.12]
        polys.append(p[:2] + ring * 0.04 * scale_px)
        depth.append(p[2] + 0.031)
        cols.append(np.r_[fill, 1.0])
    order = np.argsort(depth)
    ax.add_collection(
        PolyCollection(
            [polys[k] for k in order],
            facecolors=[cols[k] for k in order],
            edgecolors="none" if al < 1 else [cols[k] for k in order],
            linewidths=0.15,
        )
    )
    ax.set_xlim(-1.12, 1.12)
    ax.set_ylim(-1.12, 1.12)
    ax.set_aspect("equal")
    ax.axis("off")


if __name__ == "__main__":
    # usage: python projective_plane_sequence.py keys|anim [output_dir]
    import os

    out = sys.argv[2] if len(sys.argv) > 2 else "wrap_out"
    os.makedirs(out, exist_ok=True)
    if sys.argv[1] == "keys":
        stages = [
            0.0,
            0.4,
            0.75,
            1.0,
            1.25,
            1.45,
            1.6,
            1.66,
            1.72,
            1.78,
            1.84,
            1.9,
            1.95,
            2.0,
        ]
        fig, axs = plt.subplots(2, 7, figsize=(30, 10.2), facecolor="white")
        for k, t in enumerate(stages):
            ax = axs.flat[k]
            render(ax, t)
            if t == 0:
                title = "1  flat square"
            elif t <= 1:
                title = f"{k + 1}  bending"
            elif t < 2:
                title = f"{k + 1}  s = {s_of(t):.2f}"
            else:
                title = f"{k + 1}  s = 1: edges glued"
            ax.set_title(title, fontsize=14)
            f2, a2 = plt.subplots(figsize=(6, 6), facecolor="white")
            render(a2, t)
            f2.savefig(f"{out}/stage_{k + 1:02d}.png", dpi=120, bbox_inches="tight")
            plt.close(f2)
            print(
                f"\rstages [{'#' * (k + 1)}{'.' * (13 - k)}] {k + 1}/14",
                end="",
                flush=True,
            )
        print()
        fig.text(
            0.5,
            0.012,
            "the two orange edges are glued to each other with a flip, and so are the two blue edges;    "
            "the white corners meet each other, as do the black corners",
            ha="center",
            fontsize=15,
        )
        fig.subplots_adjust(
            left=0.01, right=0.99, top=0.95, bottom=0.06, wspace=0.04, hspace=0.12
        )
        fig.savefig(f"{out}/wrap-sequence.png", dpi=85)
        print("strip saved")
    else:
        from PIL import Image

        ts = (
            list(np.linspace(0, 2, 100))
            + [2.0] * 20
            + list(np.linspace(2, 0, 50))
            + [0.0] * 12
        )
        frames = []
        for k, t in enumerate(ts):
            f, a = plt.subplots(figsize=(4.8, 4.8), facecolor="white")
            render(a, t)
            buf = io.BytesIO()
            f.savefig(buf, dpi=100, bbox_inches="tight")
            plt.close(f)
            frames.append(Image.open(buf).convert("RGB"))
            j = int(24 * (k + 1) / len(ts))
            print(
                f"\ranimation [{'#' * j}{'.' * (24 - j)}] {k + 1}/{len(ts)}",
                end="",
                flush=True,
            )
        print()
        frames[0].save(
            f"{out}/wrap-animation.webp",
            save_all=True,
            append_images=frames[1:],
            duration=50,
            loop=0,
            quality=82,
        )
        print("animation saved")
