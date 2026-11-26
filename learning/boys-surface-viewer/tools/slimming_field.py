"""Slimming field for the Boy's surface viewer.

Usage:  python slimming_field.py [out.json]            write the packed field (default: slimming_field.json)
        python slimming_field.py --embed VIEWER.html   rewrite the viewer's embedded FLOW constant

Requires numpy and scipy. Takes about two minutes.

The Slimming slider flows space along a smooth velocity field V for time t = slider value. The flow of
a smooth field is a diffeomorphism of R^3, so the surface stays an immersion of RP^2. V is built from a
voxel analysis of Boy's surface (Bryant-Kusner, c = 0.95):
  1. distance field to the surface on a 140^3 grid;
  2. air classified into the exterior (reached from the box boundary) and the central chamber (the
     largest enclosed region); exterior depth measured from the boundary;
  3. local thickness: radius of the largest inscribed ball containing each voxel;
  4. (a) thinning: in the chamber, where local thickness exceeds r_t (a third of the chamber's widest
     radius), move the walls inward along the distance gradient by the excess;
     (b) opening: push walls away from thin, deep exterior passages (the slits). The slits are about
     one voxel wide, so (b) has little effect: see DESIGN.md;
  5. blur, scale, downsample to 40^3, quantize to int8, zlib + base64.

Settings: blur 4.0 voxels, interior gain 1.08, gap speed 0.135. They reproduce the field the viewer
first shipped with to within 0.019 in vertex position at slimming 1 (object about 2.6 wide). That
field's final smoothing pass was not kept, so this script defines the field from v17 on.
"""

import base64
import json
import re
import sys
import zlib

import numpy as np
from scipy import ndimage
from scipy.spatial import cKDTree

S5 = np.sqrt(5.0)
C = 0.95
G = 140  # analysis grid
G_OUT = 40  # embedded grid
R_FRAC = 0.33  # target radius r_t as a fraction of the chamber's widest radius
DEEP_FRAC = 0.35  # exterior voxels deeper than this fraction of the maximum depth count as "deep"
BLUR = 4.0  # final blur of the thinning field, in voxels
GAIN = 1.08  # interior thinning strength
GAP_SPEED = 0.135  # slit opening strength


def bar(i, n, label):
    k = int(24 * i / n)
    print(f"\r{label} [{'#' * k}{'.' * (24 - k)}] {i}/{n}", end="", flush=True)
    if i == n:
        print()


def bk(w, c=C):
    w3 = w**3
    w6 = w3 * w3
    d = w6 + S5 * w3 - 1.0
    dd = np.abs(d) ** 2
    h1 = -1.5 * np.imag(w * (1 - w**4) * np.conj(d))
    h2 = -1.5 * np.real(w * (1 + w**4) * np.conj(d))
    h3 = np.imag((1 + w6) * np.conj(d)) - c * dd
    s = dd / np.maximum(h1**2 + h2**2 + h3**2, 1e-300)
    return np.stack([h1 * s, h2 * s, h3 * s], -1)


def surface(nr=384, nt=2160):
    r = np.linspace(0, 1, nr + 1)
    t = np.linspace(0, 2 * np.pi, nt + 1)
    R, T = np.meshgrid(r, t, indexing="ij")
    return bk(R * np.exp(1j * T)).reshape(-1, 3)


def distance_field(pts, lo, h):
    axes = [lo[i] + h * np.arange(G) for i in range(3)]
    grid = np.stack(np.meshgrid(*axes, indexing="ij"), -1).reshape(-1, 3)
    tree = cKDTree(pts)
    d = np.empty(len(grid))
    chunks = np.array_split(np.arange(len(grid)), 16)
    for i, sl in enumerate(chunks):
        d[sl] = tree.query(grid[sl])[0]
        bar(i + 1, len(chunks), "distance field")
    return d.reshape(G, G, G)


def regions(dist, h):
    free = dist > 1.1 * h
    lab, n = ndimage.label(free)
    out = lab[0, 0, 0]
    ext = lab == out
    sizes = ndimage.sum(free, lab, range(1, n + 1))
    sizes[out - 1] = 0
    chamber = lab == (1 + int(np.argmax(sizes)))
    depth = np.full(ext.shape, -1, np.int32)
    seed = np.zeros_like(ext)
    seed[[0, -1]] = True
    seed[:, [0, -1]] = True
    seed[:, :, [0, -1]] = True
    seed &= ext
    depth[seed] = 0
    front = seed
    k = 0
    st = ndimage.generate_binary_structure(3, 1)
    while front.any():
        k += 1
        nxt = ndimage.binary_dilation(front, st) & ext & (depth < 0)
        depth[nxt] = k
        front = nxt
    return ext, chamber, depth


def local_thickness(dist, mask, h, label, levels=48):
    R = np.zeros_like(dist)
    radii = np.linspace(h, dist[mask].max(), levels)
    for i, r in enumerate(radii):
        centres = mask & (dist >= r)
        if not centres.any():
            break
        cover = ndimage.distance_transform_edt(~centres) * h <= r
        R[cover & mask] = r
        bar(i + 1, levels, label)
    print()
    return R


def build():
    pts = surface()
    lo = pts.min(0) - 0.25
    hi = pts.max(0) + 0.25
    h = (hi - lo).max() / (G - 1)
    dist = distance_field(pts, lo, h)
    ext, chamber, depth = regions(dist, h)
    r_in = ndimage.gaussian_filter(
        local_thickness(dist, chamber, h, "chamber thickness"), 2.0
    )
    r_ex = local_thickness(dist, ext, h, "exterior thickness")
    r_t = R_FRAC * dist[chamber].max()
    gz = np.gradient(ndimage.gaussian_filter(dist, 1.5), h)
    gnorm = np.sqrt(sum(g * g for g in gz)) + 1e-9
    s_in = np.where(chamber, np.maximum(r_in - r_t, 0), 0)
    va = [GAIN * ndimage.gaussian_filter(s_in * g / gnorm, BLUR) for g in gz]
    gap = ext & (r_ex < 0.8 * r_t) & (depth > DEEP_FRAC * depth.max())
    phi = ndimage.gaussian_filter(gap.astype(np.float32), 0.7 * r_t / h)
    gp = np.gradient(phi, h)
    gmax = np.sqrt(sum(g * g for g in gp)).max()
    vb = [-GAP_SPEED * g / gmax for g in gp]
    V = np.stack([a + b for a, b in zip(va, vb, strict=True)], -1).astype(np.float32)
    print(
        f"grid {G}^3, h = {h:.4f}, chamber widest radius {dist[chamber].max():.3f}, r_t = {r_t:.3f}"
    )
    return V, lo, h


def pack(V, lo, h):
    coords = np.stack(
        np.meshgrid(*[np.arange(G_OUT) * (G - 1) / (G_OUT - 1)] * 3, indexing="ij"), 0
    )
    Vs = np.stack(
        [ndimage.map_coordinates(V[..., a], coords, order=1) for a in range(3)], -1
    )
    scale = float(np.abs(Vs).max() / 127)
    q = np.clip(np.round(Vs / scale), -127, 127).astype(np.int8)
    h_out = h * (G - 1) / (G_OUT - 1)
    data = base64.b64encode(zlib.compress(q.tobytes(), 9)).decode()
    return {
        "G": G_OUT,
        "lo": [float(x) for x in lo],
        "h": float(h_out),
        "scale": scale,
    }, data


if __name__ == "__main__":
    args = sys.argv[1:]
    meta, data = pack(*build())
    if args[:1] == ["--embed"]:
        path = args[1]
        with open(path, encoding="utf-8") as fh:
            html = fh.read()
        html = re.sub(
            r"const FLOW = \{.*?\};",
            lambda _: "const FLOW = " + json.dumps(meta) + ";",
            html,
            count=1,
        )
        html = re.sub(
            r'FLOW\.data = "[^"]+";', lambda _: f'FLOW.data = "{data}";', html, count=1
        )
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(html)
        print(f"embedded into {path} ({len(data) / 1024:.0f} KB)")
    else:
        out = args[0] if args else "slimming_field.json"
        with open(out, "w", encoding="utf-8") as fh:
            json.dump({**meta, "data": data}, fh)
        print(f"wrote {out} ({len(data) / 1024:.0f} KB)")
