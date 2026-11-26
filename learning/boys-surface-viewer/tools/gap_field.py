"""Gap Width field for the Boy's surface viewer.

Usage:  python gap_field.py [out.json]            write the packed map (default: gap_field.json)
        python gap_field.py --embed VIEWER.html   rewrite the viewer's embedded GAP constant

Requires numpy and scipy. Takes about eight minutes.

The narrow slits between the tubes and the central area are widened by a map of space, x -> x + g Delta(x),
g = the Gap Width slider. Being a map of space (checked to stay invertible for every g in [0, 1]), it can
create no new self-intersections on any shape, and the self-intersection curve stays on the same points
of the parameter disk, so the membrane and curve data stay exact.

Steps:
  1. the slimmed surface (slimming 1, the viewer's embedded field, read from the page);
  2. slit walls: pairs of points under 0.10 apart in space, far apart on the disk, with facing normals,
     away from the self-intersection curve (the page's curve data);
  3. stretchers: one per 0.025 cell of the slits' mid-surface, at the mean midpoint, oriented across
     the slit (dominant eigenvector of the pair directions' outer products);
  4. V(x) = A sum_k g_k(x) ((x - m_k).n_k) n_k / (sum_k g_k + 0.05) * min(1, sum_k g_k / 0.5), with
     anisotropic Gaussians g_k (0.10 across the slit, 0.07 along it): it stretches space across each slit
     and is quadratic in n_k, so the normals' signs do not matter;
  5. Delta = flow of V for time 1 (RK4, 12 steps) minus the identity, on a 96^3 grid around the surface,
     zero away from the stretchers; det(I + g grad Delta) > 0 checked for g = 0.05 .. 1;
  6. int8, zlib + base64.

With A = 1.4 the slits open from a median width of 0.074 to 0.26, about the tubes' diameter.
"""

import base64
import json
import re
import sys
import time
import zlib
from pathlib import Path

import numpy as np
from scipy.spatial import cKDTree

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fold_check as fc  # the page's surface and slimming flow, ported line for line

HERE = Path(__file__).resolve().parent
PAGE = HERE.parent / "boys-surface-viewer.html"
NR, NT = 96, 576  # analysis mesh on the disk
WALL = 0.10  # slit walls: facing points closer than this
A = 1.4  # stretch strength
SN, ST = 0.10, 0.07  # Gaussian widths across / along a slit
CELL = 0.025  # one stretcher per cell of this size
G = 96  # output grid


def bar(i, n, label):
    k = int(24 * i / n)
    print(f"\r{label} [{'#' * k}{'.' * (24 - k)}] {i}/{n}", end="", flush=True)
    if i == n:
        print()


def page_curve_far(page_html, w):
    """True where a disk point is clear of the self-intersection curve (the page's curve data)."""
    m = json.loads(re.search(r"const MEMBRANE = (\{.*?\});", page_html).group(1))
    S = m["S"]
    q = np.frombuffer(zlib.decompress(base64.b64decode(m["curve"])), np.uint8).reshape(
        S, S
    )
    ix = np.clip(((w.real + 1) / 2 * S).astype(int), 0, S - 1)
    iy = np.clip(((w.imag + 1) / 2 * S).astype(int), 0, S - 1)
    return q[iy, ix] / 255 >= 0.95


def slit_pairs(X, w, far_from_curve):
    P = X.reshape(NR + 1, NT + 1, 3)
    N = np.cross(np.gradient(P, axis=0), np.gradient(P, axis=1)).reshape(-1, 3)
    N /= np.linalg.norm(N, axis=1, keepdims=True) + 1e-12
    tree = cKDTree(X)
    I, J = [], []
    for ch in np.array_split(np.arange(len(X)), 40):
        for a, js in zip(ch, tree.query_ball_point(X[ch], WALL), strict=True):
            js = np.asarray(js, int)
            js = js[(js > a) & (np.abs(w[js] - w[a]) > 0.25)]
            if len(js):
                I.append(np.full(len(js), a))
                J.append(js)
    i, j = np.concatenate(I), np.concatenate(J)
    rim = (np.abs(w[i]) > 0.97) & (np.abs(w[j]) > 0.97) & (np.abs(w[i] + w[j]) < 0.06)
    u = X[j] - X[i]
    u /= np.linalg.norm(u, axis=1, keepdims=True) + 1e-12
    facing = (
        (np.abs((N[i] * N[j]).sum(1)) > 0.7)
        & (np.abs((N[i] * u).sum(1)) > 0.7)
        & (np.abs((N[j] * u).sum(1)) > 0.7)
    )
    k = ~rim & facing & far_from_curve[i] & far_from_curve[j]
    return i[k], j[k], u[k]


def stretchers(X, i, j, u):
    m = 0.5 * (X[i] + X[j])
    _, inv = np.unique(np.floor(m / CELL).astype(int), axis=0, return_inverse=True)
    inv = inv.ravel()
    K = inv.max() + 1
    mk = np.zeros((K, 3))
    np.add.at(mk, inv, m)
    mk /= np.bincount(inv, minlength=K)[:, None]
    T = np.zeros((K, 3, 3))
    np.add.at(T, inv, u[:, :, None] * u[:, None, :])
    return mk, np.linalg.eigh(T)[1][:, :, -1]


def velocity(x, mk, nk):
    out = np.zeros_like(x)
    for ch in np.array_split(np.arange(len(x)), max(1, len(x) // 4000)):
        r = x[ch, None, :] - mk[None]
        a = (r * nk[None]).sum(-1)
        g = np.exp(-a * a / SN**2 - ((r * r).sum(-1) - a * a) / ST**2)
        s = g.sum(1, keepdims=True)
        out[ch] = (
            A
            * ((g * a)[..., None] * nk[None]).sum(1)
            / (s + 0.05)
            * np.minimum(1, s / 0.5)
        )
    return out


def flow(x, mk, nk, steps=12):
    x = x.copy()
    dt = 1.0 / steps
    for _ in range(steps):
        k1 = velocity(x, mk, nk)
        k2 = velocity(x + 0.5 * dt * k1, mk, nk)
        k3 = velocity(x + 0.5 * dt * k2, mk, nk)
        k4 = velocity(x + dt * k3, mk, nk)
        x += dt / 6 * (k1 + 2 * k2 + 2 * k3 + k4)
    return x


def build(page):
    html = page.read_text(encoding="utf-8")
    r = np.repeat(np.arange(NR + 1) / NR, NT + 1)
    t = np.tile(2 * np.pi * np.arange(NT + 1) / NT, NR + 1)
    w = r * np.exp(1j * t)
    X = fc.flow(fc.bk(w), fc.read_flow(page), 1.0)
    i, j, u = slit_pairs(X, w, page_curve_far(html, w))
    mk, nk = stretchers(X, i, j, u)
    print(f"slit-wall pairs {len(i)}, stretchers {len(mk)}")
    lo = X.min(0) - 0.3
    h = float((X.max(0) + 0.3 - lo).max() / (G - 1))
    grid = np.stack(
        np.meshgrid(*[lo[a] + h * np.arange(G) for a in range(3)], indexing="ij"), -1
    ).reshape(-1, 3)
    dd, _ = cKDTree(mk).query(grid)
    idx = np.nonzero(dd < 4 * max(SN, ST) + 0.2)[
        0
    ]  # beyond this the field is below e^-36
    Delta = np.zeros_like(grid)
    t0 = time.time()
    chunks = np.array_split(idx, 20)
    for k, ch in enumerate(chunks):
        Delta[ch] = flow(grid[ch], mk, nk) - grid[ch]
        bar(
            k + 1,
            len(chunks),
            f"flowing {len(idx)} grid points ({time.time() - t0:.0f}s)",
        )
    Dg = Delta.reshape(G, G, G, 3)
    J = np.stack([np.stack(np.gradient(Dg[..., c], h), -1) for c in range(3)], -2)
    det_min = min(
        np.linalg.det(np.eye(3) + g * J).min() for g in np.linspace(0.05, 1, 20)
    )
    print(f"det(I + g grad Delta) min over g in [0.05, 1]: {det_min:.3f}")
    if det_min <= 0:
        sys.exit("the gap map folds space: lower A")
    d_before = np.linalg.norm(X[j] - X[i], axis=1)
    Xg = flow(X[np.r_[i, j]], mk, nk)
    d_after = np.linalg.norm(Xg[len(i) :] - Xg[: len(i)], axis=1)
    print(f"slit width median {np.median(d_before):.3f} -> {np.median(d_after):.3f}")
    scale = float(np.abs(Dg).max() / 127)
    q = np.clip(np.round(Dg / scale), -127, 127).astype(np.int8)
    data = base64.b64encode(zlib.compress(q.tobytes(), 9)).decode()
    return {"G": G, "lo": [float(x) for x in lo], "h": h, "scale": scale, "data": data}


if __name__ == "__main__":
    args = sys.argv[1:]
    target = Path(args[1]) if args[:1] == ["--embed"] else PAGE
    field = build(target if args[:1] == ["--embed"] else PAGE)
    if args[:1] == ["--embed"]:
        html = target.read_text(encoding="utf-8")
        html = re.sub(
            r"const GAP = \{.*?\};",
            lambda _: "const GAP = " + json.dumps(field) + ";",
            html,
            count=1,
        )
        target.write_text(html, encoding="utf-8")
        print(f"embedded into {target} ({len(field['data']) / 1024:.0f} KB)")
    else:
        out = args[0] if args else "gap_field.json"
        with open(out, "w", encoding="utf-8") as fh:
            json.dump(field, fh)
        print(f"wrote {out} ({len(field['data']) / 1024:.0f} KB)")
