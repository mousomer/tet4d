"""Fold check for the Boy's surface viewer's shape controls.

Usage:  python fold_check.py [--page VIEWER.html] [--steps N]

Requires numpy and scipy.

The viewer's shape chain is (1) the flow of the embedded slimming field, (2) the gap map
x -> x + g Delta(x), then (3) one map of space for lobe width, length, thickness and twist. The flow is a
diffeomorphism by construction. For (2) this tool checks det(I + g grad Delta) > 0 on its whole grid for
g in [0.05, 1]. The map in (3)
keeps the surface an immersion wherever its Jacobian determinant stays positive, because composing an
immersion with a local diffeomorphism gives an immersion. This tool evaluates det J of the map (2) at
every vertex of the viewer's mesh, after the flow and the gap map, for a grid of slider values covering each slider's
full range. It reports the smallest determinant per slider and overall, and exits non-zero if the
determinant reaches zero (a fold) anywhere.

The flow, the mesh and the map are ported line for line from the page. The flow field is read from
the page itself, so the check always matches the shipped viewer.
"""

import argparse
import base64
import itertools
import json
import re
import sys
import zlib
from pathlib import Path

import numpy as np
from scipy import ndimage

HERE = Path(__file__).resolve().parent
S5 = np.sqrt(5.0)
BK_C = 0.95
NR, NT = 128, 720
COLOR_WINDOW0 = np.radians(-10.0)
RANGES = {  # slider ranges, as in the page's panel
    "len": (0.5, 2.0),
    "wid": (0.4, 1.6),
    "thk": (0.2, 2.0),
    "twist": (-4.0, 4.0),
    "slim": (0.0, 1.3),
}
GAP_VALUES = (0.0, 1.0)


def bar(i, n, label):
    k = int(24 * i / n)
    print(f"\r{label} [{'#' * k}{'.' * (24 - k)}] {i}/{n}", end="", flush=True)
    if i == n:
        print()


def bk(w, c=BK_C):
    w3 = w**3
    w6 = w3 * w3
    d = w6 + S5 * w3 - 1.0
    dd = np.abs(d) ** 2
    h1 = -1.5 * np.imag(w * (1 - w**4) * np.conj(d))
    h2 = -1.5 * np.real(w * (1 + w**4) * np.conj(d))
    h3 = np.imag((1 + w6) * np.conj(d)) - c * dd
    s = dd / np.maximum(h1**2 + h2**2 + h3**2, 1e-300)
    return np.stack([h1 * s, h2 * s, h3 * s], -1)


def read_flow(page):
    html = page.read_text(encoding="utf-8")
    meta = json.loads(re.search(r"const FLOW = (\{.*?\});", html).group(1))
    data = re.search(r'FLOW\.data = "([^"]+)"', html).group(1)
    q = np.frombuffer(zlib.decompress(base64.b64decode(data)), np.int8).astype(
        np.float64
    )
    G = meta["G"]
    return q.reshape(G, G, G, 3) * meta["scale"], np.array(meta["lo"]), meta["h"]


def read_gap(page):
    html = page.read_text(encoding="utf-8")
    meta = json.loads(re.search(r"const GAP = (\{.*?\});", html).group(1))
    G = meta["G"]
    q = np.frombuffer(zlib.decompress(base64.b64decode(meta["data"])), np.int8).astype(
        np.float64
    )
    return q.reshape(G, G, G, 3) * meta["scale"], np.array(meta["lo"]), meta["h"]


def gap_map(P, gap, g):
    """x + g Delta(x), trilinear, zero outside the grid (as in the page)."""
    D, lo, h = gap
    G = D.shape[0]
    f = ((P - lo) / h).T
    inside = np.all((f >= 0) & (f <= G - 1), axis=0)
    d = np.stack(
        [
            ndimage.map_coordinates(D[..., a], f, order=1, mode="nearest")
            for a in range(3)
        ],
        -1,
    )
    return P + g * d * inside[:, None]


def gap_det_min(gap):
    D, _, h = gap
    J = np.stack([np.stack(np.gradient(D[..., c], h), -1) for c in range(3)], -2)
    return min(np.linalg.det(np.eye(3) + g * J).min() for g in np.linspace(0.05, 1, 20))


def flow(P, field, t, steps=10):
    """RK4 through the trilinear velocity field; zero outside the grid (as in the page)."""
    V, lo, h = field
    G = V.shape[0]

    def sample(X):
        f = ((X - lo) / h).T
        inside = np.all((f >= 0) & (f <= G - 1), axis=0)
        out = np.stack(
            [
                ndimage.map_coordinates(V[..., a], f, order=1, mode="nearest")
                for a in range(3)
            ],
            -1,
        )
        return out * inside[:, None]

    X = P.copy()
    if t <= 0:
        return X
    dt = t / steps
    for _ in range(steps):
        k1 = sample(X)
        k2 = sample(X + 0.5 * dt * k1)
        k3 = sample(X + 0.5 * dt * k2)
        k4 = sample(X + dt * k3)
        X += dt / 6 * (k1 + 2 * k2 + 2 * k3 + k4)
    return X


def params(B, r, s):
    """The page's per-shape constants D, computed from the flowed surface B."""
    z = B[:, 2]
    rho = np.hypot(B[:, 0], B[:, 1])
    band = (r > 0.55) & (r < 0.9)
    tip = np.argmax(np.where(band, rho, -1))
    third = 2 * np.pi / 3
    tip_az = COLOR_WINDOW0 + (
        (np.arctan2(B[tip, 1], B[tip, 0]) - COLOR_WINDOW0) % third
    )
    cc = 0.42 * rho.max()
    return {
        "z0": 0.5 * (z.min() + z.max()),
        "cc2": cc * cc,
        "len": s["len"],
        "thk": s["thk"],
        "k": np.clip((1 - s["wid"]) * 1.4, -0.85, 0.85),
        "ca": np.cos(3 * tip_az),
        "sa": np.sin(3 * tip_az),
        "tw": s["twist"] / (z.max() - z.min()),
    }


def deform(X, D):
    x, y, z = X[..., 0], X[..., 1], X[..., 2] - D["z0"]
    r2 = x * x + y * y
    q = r2 + D["cc2"]
    u = r2 / q
    im3 = (y * (3 * x * x - y * y)) * D["ca"] - (x * (x * x - 3 * y * y)) * D["sa"]
    ang = (-D["k"] / 3) * im3 / (q * np.sqrt(q)) + D["tw"] * z
    sr = 1 + (D["len"] - 1) * u
    cs, sn = np.cos(ang) * sr, np.sin(ang) * sr
    return np.stack(
        [x * cs - y * sn, x * sn + y * cs, z * (1 + (D["thk"] - 1) * u)], -1
    )


def jac_det(X, D, eps=1e-5):
    cols = []
    for a in range(3):
        e = np.zeros(3)
        e[a] = eps
        cols.append((deform(X + e, D) - deform(X - e, D)) / (2 * eps))
    return np.linalg.det(np.stack(cols, -1))


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--page", default=str(HERE.parent / "boys-surface-viewer.html"))
    ap.add_argument(
        "--steps", type=int, default=5, help="values per slider (default 5)"
    )
    a = ap.parse_args()
    field = read_flow(Path(a.page))
    gap = read_gap(Path(a.page))
    gdet = gap_det_min(gap)
    print(f"gap map: det(I + g grad Delta) min over g in [0.05, 1] = {gdet:.4f}")
    r = np.repeat(np.arange(NR + 1) / NR, NT + 1)
    t = np.tile(2 * np.pi * np.arange(NT + 1) / NT, NR + 1)
    base = bk(r * np.exp(1j * t))
    vals = {k: np.linspace(lo, hi, a.steps) for k, (lo, hi) in RANGES.items()}
    flowed = {}
    for i, sl in enumerate(vals["slim"]):
        f = flow(base, field, sl)
        for g in GAP_VALUES:
            flowed[(sl, g)] = gap_map(f, gap, g)
        bar(i + 1, len(vals["slim"]), "slimming flow + gap map")
    vals["gap"] = np.array(GAP_VALUES)
    keys = ["len", "wid", "thk", "twist"]
    combos = list(
        itertools.product(*[vals[k] for k in keys], vals["slim"], vals["gap"])
    )
    worst = {k: {v: np.inf for v in vals[k]} for k in [*keys, "slim", "gap"]}
    overall = (np.inf, None)
    for n, (ln, wd, th, tw, sl, gp) in enumerate(combos):
        s = {"len": ln, "wid": wd, "thk": th, "twist": tw}
        B = flowed[(sl, gp)]
        det = jac_det(B, params(B, r, s)).min()
        for k, v in (
            *zip(keys, (ln, wd, th, tw), strict=True),
            ("slim", sl),
            ("gap", gp),
        ):
            worst[k][v] = min(worst[k][v], det)
        if det < overall[0]:
            overall = (det, {**s, "slim": sl, "gap": gp})
        if (n + 1) % 125 == 0 or n + 1 == len(combos):
            bar(n + 1, len(combos), "slider combinations")
    print(
        "smallest det J of the shape map over the surface, worst case across the other sliders:"
    )
    for k in [*keys, "slim", "gap"]:
        row = "  ".join(f"{v:+.2f}:{d:.3f}" for v, d in worst[k].items())
        print(f"  {k:>5}  {row}")
    det, at = overall
    at_s = ", ".join(f"{k}={v:.2f}" for k, v in at.items())
    print(f"overall minimum det J = {det:.4f} at {at_s}")
    if det <= 0 or gdet <= 0:
        print(
            "FOLD: the shape map is not a local diffeomorphism somewhere on the surface"
        )
        sys.exit(1)
    print("no fold: every slider combination keeps the surface an immersion")


if __name__ == "__main__":
    main()
