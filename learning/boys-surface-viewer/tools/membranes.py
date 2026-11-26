"""Membrane field for the Boy's surface viewer.

Usage:  python membranes.py [out.json]            write the field (default: membrane_field.json)
        python membranes.py --embed VIEWER.html   rewrite the viewer's embedded MEMBRANE constant

Requires numpy and scipy.

The self-intersection curve of Boy's surface (Bryant-Kusner, c = 0.95) is three loops through the
triple point. On the parameter disk (antipodal rim points identified) its preimage cuts the disk into
exactly 4 regions: chi(RP^2) = 1 = V - E + F with V = 3 triple-point preimages and E = 6 arcs, so F = 4.
The three small regions are discs bounded entirely by self-intersection arcs: the membranes that a tube
passes through. The viewer removes them by default, as in the usual drawing of a Klein bottle.

Steps:
  1. sample the surface on a 900^2 grid over the disk;
  2. mark points that have a far-away (in the disk) partner at the same place in space: the curve;
  3. label the regions between the curves, gluing across the rim (w ~ -w);
  4. check the three small regions are discs bounded only by the curve;
  5. signed distance to their boundary (+ inside), smoothed, sampled to 512^2, uint8, zlib + base64.
"""

import base64
import json
import sys
import zlib

import numpy as np
from scipy import ndimage
from scipy.spatial import cKDTree

S5 = np.sqrt(5.0)
C = 0.95  # Bryant-Kusner family member used by the viewer
G = 900  # analysis grid over [-1, 1]^2
S = 512  # output texture size
CLAMP = 0.04  # signed distance range stored, in disk units


def bar(i, n, label):
    k = int(24 * i / n)
    print(f"\r{label} [{'#' * k}{'.' * (24 - k)}] {i}/{n}", end="", flush=True)
    if i == n:
        print()


def bk(w, c=C):
    """Bryant-Kusner surface, X = H |d|^2 / |H|^2 (finite at the zeros of d)."""
    w3 = w**3
    w6 = w3 * w3
    d = w6 + S5 * w3 - 1.0
    dd = np.abs(d) ** 2
    h1 = -1.5 * np.imag(w * (1 - w**4) * np.conj(d))
    h2 = -1.5 * np.real(w * (1 + w**4) * np.conj(d))
    h3 = np.imag((1 + w6) * np.conj(d)) - c * dd
    s = dd / np.maximum(h1**2 + h2**2 + h3**2, 1e-300)
    return np.stack([h1 * s, h2 * s, h3 * s], -1)


def curve_mask(U, V, inside):
    """Grid points whose surface point is also reached from a distant point of the disk."""
    w = (U + 1j * V)[inside]
    X = bk(w)
    idx = -np.ones(U.shape, int)
    idx[inside] = np.arange(inside.sum())

    def nb(dy, dx):
        j = np.roll(np.roll(idx, dy, 0), dx, 1)[inside]
        return np.where(j >= 0, np.linalg.norm(X - X[np.maximum(j, 0)], axis=1), 0)

    spacing = np.maximum.reduce([nb(1, 0), nb(-1, 0), nb(0, 1), nb(0, -1)])
    tree = cKDTree(X)
    near = np.zeros(len(X), bool)
    cell = 2.0 / G
    chunks = np.array_split(np.arange(len(X)), 30)
    for ci, ids in enumerate(chunks):
        for i, js in zip(
            ids, tree.query_ball_point(X[ids], r=1.2 * spacing[ids]), strict=True
        ):
            if len(js) < 2:
                continue
            js = np.asarray(js)
            far = np.abs(w[js] - w[i]) > 8 * cell
            same_rim_point = (np.abs(w[i]) > 1 - 4 * cell) & (
                np.abs(w[js] + w[i]) < 8 * cell
            )
            if (far & ~same_rim_point).any():
                near[i] = True
        bar(ci + 1, len(chunks), "self-intersection curve")
    band = np.zeros(U.shape, bool)
    band[inside] = near
    return ndimage.binary_dilation(band, iterations=1) & inside


def regions(U, V, inside, band):
    """Regions between the curves, glued across the rim (a rim pixel and its antipode)."""
    lab, n = ndimage.label(inside & ~band)
    parent = np.arange(n + 1)

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    rim = inside & (U**2 + V**2 > (1 - 6.0 / G) ** 2) & (lab > 0)
    for y, x in zip(*np.nonzero(rim), strict=True):
        ya, xa = G - 1 - y, G - 1 - x
        if lab[ya, xa] > 0:
            a, b = find(lab[y, x]), find(lab[ya, xa])
            if a != b:
                parent[a] = b
    roots = np.array([find(k) for k in range(n + 1)])
    return roots[lab]


def main():
    g = (np.arange(G) + 0.5) / G * 2 - 1
    U, V = np.meshgrid(g, g, indexing="xy")
    inside = U**2 + V**2 <= 1
    band = curve_mask(U, V, inside)
    lab = regions(U, V, inside, band)
    ids, cnt = np.unique(lab[lab > 0], return_counts=True)
    print(f"regions between the curves: {len(ids)} (expected 4)")
    big = ids[np.argmax(cnt)]
    nb_band = ndimage.binary_dilation(band, iterations=2)
    for i in ids[ids != big]:
        m = lab == i
        pieces = ndimage.label(m)[1]
        holes = ndimage.label(ndimage.binary_fill_holes(m) & ~m)[1]
        edge = m & ~ndimage.binary_erosion(m)
        on_curve = (edge & nb_band).sum() / edge.sum()
        print(
            f"  membrane {i}: {m.sum()} px, pieces {pieces}, holes {holes}, boundary on the curve {on_curve:.0%}"
        )
    # band pixels go to the nearest region, so the boundary between regions runs along the curve
    _, (jy, jx) = ndimage.distance_transform_edt(lab == 0, return_indices=True)
    patch = np.where(inside, lab[jy, jx], 0)
    M = inside & (patch > 0) & (patch != big)
    h = 2.0 / G
    sd = (ndimage.distance_transform_edt(M) - ndimage.distance_transform_edt(~M)) * h
    sd += 0.5 * h * np.sign(sd)
    sd = ndimage.gaussian_filter(sd, 4.0)  # smooth the pixel staircase of the zero line
    c = (np.arange(S) + 0.5) / S * G - 0.5
    YY, XX = np.meshgrid(c, c, indexing="ij")
    sds = ndimage.map_coordinates(sd, [YY, XX], order=1, mode="nearest")
    q = np.clip(
        np.round(128 + np.clip(sds, -CLAMP, CLAMP) / CLAMP * 127), 0, 255
    ).astype(np.uint8)
    return {
        "S": S,
        "clamp": CLAMP,
        "data": base64.b64encode(zlib.compress(q.tobytes(), 9)).decode(),
    }


if __name__ == "__main__":
    args = sys.argv[1:]
    field = main()
    if args[:1] == ["--embed"]:
        path = args[1]
        with open(path, encoding="utf-8") as fh:
            html = fh.read()
        a = html.index("const MEMBRANE = ")
        b = html.index(";\n", a)
        html = html[:a] + "const MEMBRANE = " + json.dumps(field) + html[b:]
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(html)
        print(f"embedded into {path}")
    else:
        out = args[0] if args else "membrane_field.json"
        with open(out, "w", encoding="utf-8") as fh:
            json.dump(field, fh)
        print(f"wrote {out} ({len(field['data']) / 1024:.1f} KB)")
