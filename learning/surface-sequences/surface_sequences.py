"""From a glued square to a closed surface: sphere, torus, Klein bottle (two shapes), projective plane.

Usage:
    python surface_sequences.py SURFACE keys [out_dir]   -> captioned strip + stage PNGs
    python surface_sequences.py SURFACE anim [out_dir]   -> animated WebP
    python surface_sequences.py overview [out_dir]       -> the five gluing diagrams side by side
    python surface_sequences.py check                    -> numerical check of every gluing
SURFACE: sphere | torus | klein-bottle | klein-figure8 | projective-plane
Requires numpy, scipy, matplotlib, pillow.

Every frame is a continuous map of the square [-1, 1]^2; the square's grid, its edges (orange / blue
pairs) and its corners (coloured by which ones end up as the same point) are carried along to the
finished surface.  Surface colours are chosen to agree across each gluing, so the closed surface
shows no colour seam.
"""

import colorsys
import io
import os
import sys
from itertools import pairwise
from typing import ClassVar

import matplotlib
import numpy as np
from scipy.interpolate import CubicSpline

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection

N, LINE_EVERY = 160, 20
g = np.linspace(-1, 1, N + 1)
SX, SY = np.meshgrid(g, g, indexing="ij")  # i along x, j along y
ORANGE, BLUE = np.array([0.95, 0.45, 0.05]), np.array([0.10, 0.35, 0.95])
CLASS_COLOURS = {
    "white": [1, 1, 1],
    "black": [0.12, 0.12, 0.12],
    "grey": [0.6, 0.6, 0.6],
}
TOP = [(i, N) for i in range(N + 1)]
BOTTOM = [(i, 0) for i in range(N + 1)]
LEFT = [(0, j) for j in range(N + 1)]
RIGHT = [(N, j) for j in range(N + 1)]
CORNERS = {"TL": (0, N), "TR": (N, N), "BL": (0, 0), "BR": (N, 0)}
L_DIR = np.array([0.35, 0.55, 0.75]) / np.linalg.norm([0.35, 0.55, 0.75])


def smooth(t):
    t = np.clip(t, 0, 1)
    return t * t * (3 - 2 * t)


def normalise(X):
    X = X - (X.reshape(-1, 3).max(0) + X.reshape(-1, 3).min(0)) / 2
    return X / np.linalg.norm(X, axis=-1).max()


def view(elev, azim):
    ce, se, ca, sa = np.cos(elev), np.sin(elev), np.cos(azim), np.sin(azim)
    Rx = np.array([[1, 0, 0], [0, ce, -se], [0, se, ce]])
    Rz = np.array([[ca, -sa, 0], [sa, ca, 0], [0, 0, 1]])
    return Rx @ Rz


def periodic_colours(h_of_x=True):
    """hue periodic in x, saturation periodic and even in y: agrees across x- and y-gluings,
    including the flipped one (y -> -y)."""
    cx = 0.25 * (SX[:-1, :-1] + SX[1:, :-1] + SX[1:, 1:] + SX[:-1, 1:])
    cy = 0.25 * (SY[:-1, :-1] + SY[1:, :-1] + SY[1:, 1:] + SY[:-1, 1:])
    hue = ((cx + 1) / 2) % 1.0
    sat = 0.35 + 0.45 * (0.5 + 0.5 * np.cos(np.pi * cy))
    return hue, sat


# ---------------------------------------------------------------------------------------------
# Surfaces: each returns shape(t) for t in [0, 1] plus edges, corner classes, colours, captions
# ---------------------------------------------------------------------------------------------
class Surface:
    alpha_min = 0.5
    fade_from = 0.5
    cam_end = (-55.0, 25.0)
    stages: ClassVar = [0.0, 0.15, 0.3, 0.42, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]

    def alpha(self, t):
        return 1.0 - (1.0 - self.alpha_min) * smooth(
            (t - self.fade_from) / (1 - self.fade_from)
        )

    def cam_end_matrix(self):
        return view(np.radians(self.cam_end[0]), np.radians(self.cam_end[1]))

    def cam(self, t):
        M = (
            self.cam_end_matrix()
        )  # interpolate identity -> M along the shortest rotation (Rodrigues)
        ang = np.arccos(np.clip((np.trace(M) - 1) / 2, -1, 1))
        if ang < 1e-9:
            return np.eye(3)
        ax = np.array([M[2, 1] - M[1, 2], M[0, 2] - M[2, 0], M[1, 0] - M[0, 1]]) / (
            2 * np.sin(ang)
        )
        K = np.array([[0, -ax[2], ax[1]], [ax[2], 0, -ax[0]], [-ax[1], ax[0], 0]])
        a = smooth(t) * ang
        return np.eye(3) + np.sin(a) * K + (1 - np.cos(a)) * K @ K


class Torus(Surface):
    name, title = "torus", "torus"
    chi, gluing = 0, "opposite edges glued straight (a b a⁻¹ b⁻¹)"
    alpha_min, fade_from = 0.72, 0.55
    edges: ClassVar = [(TOP, BLUE), (BOTTOM, BLUE), (LEFT, ORANGE), (RIGHT, ORANGE)]
    corner_classes: ClassVar = {
        "TL": "white",
        "TR": "white",
        "BL": "white",
        "BR": "white",
    }
    legend = "blue edges meet first (rolling), orange edges meet second (bending); all four corners become one point"

    def colours(self):
        return periodic_colours()

    def shape(self, t):
        u, v = SX / 2, SY / 2
        if t <= 0.5:  # roll the square into a cylinder (blue edges meet)
            a = smooth(2 * t)
            if a < 1e-6:
                return normalise(np.stack([u, v, 0 * u], -1))
            rho, phi = 1 / (2 * np.pi * a), 2 * np.pi * a * v
            return normalise(
                np.stack([u, rho * np.sin(phi), rho * (1 - np.cos(phi))], -1)
            )
        b = smooth(
            2 * t - 1
        )  # bend the cylinder into a ring (orange edges meet), stretching it
        rho, phi = 1 / (2 * np.pi), 2 * np.pi * v
        g1, g2 = rho * np.sin(phi), rho * (1 - np.cos(phi))
        L = 1 + 1.4 * b
        uu = u * L
        if b < 1e-6:
            A, Ny = np.stack([uu, 0 * uu, 0 * uu], -1), np.array([0.0, 1.0, 0.0])
            P = A + g1[..., None] * Ny
        else:
            Rb = L / (2 * np.pi * b)
            ang = uu / Rb
            A = np.stack([Rb * np.sin(ang), Rb * (1 - np.cos(ang)), 0 * ang], -1)
            Ny = np.stack([-np.sin(ang), np.cos(ang), 0 * ang], -1)
            P = A + g1[..., None] * Ny
        P[..., 2] += g2
        return normalise(P)

    def caption(self, k, t):
        if t == 0:
            return "1  flat square"
        return (
            f"{k + 1}  rolling"
            if t <= 0.5
            else (f"{k + 1}  bending" if t < 1 else f"{k + 1}  torus")
        )


class Sphere(Surface):
    name, title = "sphere", "sphere"
    chi, gluing = 2, "adjacent edges folded together (a a⁻¹ b b⁻¹)"
    # the end camera puts all three cone points on the silhouette
    alpha_min, fade_from, cam_end = 0.62, 0.5, (-40.0, 60.0)
    edges: ClassVar = [(TOP, ORANGE), (RIGHT, ORANGE), (BOTTOM, BLUE), (LEFT, BLUE)]
    corner_classes: ClassVar = {
        "TL": "white",
        "BR": "white",
        "TR": "black",
        "BL": "grey",
    }
    legend = (
        "top edge folds onto right edge (orange), bottom onto left (blue); "
        "white corners meet, black and grey corners stay single: 3 points"
    )

    def colours(self):
        cx = 0.25 * (SX[:-1, :-1] + SX[1:, :-1] + SX[1:, 1:] + SX[:-1, 1:])
        cy = 0.25 * (SY[:-1, :-1] + SY[1:, :-1] + SY[1:, 1:] + SY[:-1, 1:])
        d, e = (
            (cx + cy) / np.sqrt(2),
            (cy - cx) / np.sqrt(2),
        )  # symmetric under the diagonal flip
        return (0.05 + 0.8 * (d / np.sqrt(2) + 1) / 2) % 1.0, 0.3 + 0.5 * np.abs(
            e
        ) / np.sqrt(2)

    @staticmethod
    def _sphere_map():
        d, e = (SX + SY) / np.sqrt(2), (SY - SX) / np.sqrt(2)
        q = np.stack([d, -np.abs(e)], -1)  # point of the folded triangle
        c = np.array(
            [0.0, -np.sqrt(2) / 3]
        )  # centroid of triangle (-r2,0),(r2,0),(0,-r2)
        tri = np.array([[-np.sqrt(2), 0.0], [np.sqrt(2), 0.0], [0.0, -np.sqrt(2)]])
        w = q - c
        lw = np.linalg.norm(w, axis=-1)
        dirn = w / np.maximum(lw, 1e-12)[..., None]
        reach = np.full(
            lw.shape, np.inf
        )  # distance from centroid to triangle boundary along dirn
        for a, b in pairwise(np.vstack([tri, tri[:1]])):
            ed = b - a
            den = dirn[..., 0] * ed[1] - dirn[..., 1] * ed[0]
            ac = a - c
            tt = (ac[0] * ed[1] - ac[1] * ed[0]) / np.where(
                np.abs(den) < 1e-12, np.nan, den
            )
            ss = (ac[0] * dirn[..., 1] - ac[1] * dirn[..., 0]) / np.where(
                np.abs(den) < 1e-12, np.nan, den
            )
            ok = (tt > 0) & (ss >= -1e-9) & (ss <= 1 + 1e-9)
            reach = np.where(ok & (tt < reach), tt, reach)
        r = np.clip(lw / reach, 0, 1)
        r = np.sin(
            np.pi / 2 * r
        )  # ease toward the rim so the equator is reached smoothly
        disk = dirn * r[..., None]
        z = np.sign(e + 1e-15) * np.sqrt(np.maximum(1 - r * r, 0))
        return np.stack([disk[..., 0], disk[..., 1], z], -1), d, e

    def shape(self, t):
        d, e = (SX + SY) / np.sqrt(2), (SY - SX) / np.sqrt(2)
        c45 = np.sqrt(0.5)

        def fold(
            ang,
        ):  # rotate the e > 0 half about the diagonal; then back to an upright square frame
            dd, ee = d, np.where(e > 0, e * np.cos(ang), e)
            zz = np.where(e > 0, e * np.sin(ang), 0)
            return np.stack([c45 * (dd - ee), c45 * (dd + ee), zz], -1)

        if t <= 0.5:  # fold along the diagonal: top edge swings onto the right edge
            return normalise(fold(0.92 * np.pi * smooth(2 * t)))
        b = smooth(2 * t - 1)  # inflate the folded envelope into a sphere
        S, _, _ = self._sphere_map()
        S = np.stack(
            [c45 * (S[..., 0] - S[..., 1]), c45 * (S[..., 0] + S[..., 1]), S[..., 2]],
            -1,
        )
        S = self._cone_tips(S)
        F = fold(0.92 * np.pi)
        F = F / np.linalg.norm(F, axis=-1).max()
        return normalise((1 - b) * F + b * S)

    # cone tips: height and angular radius per corner point. A falloff (1 - angle/radius)**power gives a
    # true cone point; single corners (90 degrees of the square) are sharper than the merged pair (180).
    # A power > 1 makes the flanks concave, so the tips read as sharp cones rather than mounds.
    TIPS: ClassVar = {"TR": (0.6, 0.42), "BL": (0.6, 0.42), "TL": (0.4, 0.5)}
    TIP_POWER = 1.6

    def _cone_tips(self, S):
        u = S / np.linalg.norm(S, axis=-1, keepdims=True)
        r = np.ones(S.shape[:2])
        for key, (h, rad) in self.TIPS.items():
            c = u[CORNERS[key]]
            ang = np.arccos(np.clip(u @ c, -1, 1))
            r += h * np.clip(1 - ang / rad, 0, None) ** self.TIP_POWER
        return S * r[..., None]

    def caption(self, k, t):
        if t == 0:
            return "1  flat square"
        return (
            f"{k + 1}  folding"
            if t <= 0.5
            else (f"{k + 1}  inflating" if t < 1 else f"{k + 1}  sphere")
        )


# Classic bottle as a tube swept along a centreline in the (x, height) plane: centre c(u), radius
# r(u), and circles in the plane spanned by e1(u) and the y axis, e1 = (cos th, -sin th). The frame
# angle th turns by pi over one loop, so the last circle is the first one mirrored (v -> pi - v):
# that is the Klein gluing. The loop closes in a rounded U-shaped base where the circles are
# horizontal and centred on the axis, so the closing circle has the same radius from both sides.
# Columns: u (fraction of the loop), centre x, centre height, tube radius, th / pi.
BOTTLE_KEYS = np.array(
    [
        [0.000, 0.00, 0.00, 0.75, 0.00],  # closing circle, bottom of the U-shaped base
        [0.040, 0.00, 0.09, 0.96, 0.00],
        [0.080, 0.00, 0.30, 1.05, 0.00],  # outer wall of the body
        [0.180, 0.00, 1.25, 1.08, 0.00],
        [0.250, 0.00, 1.95, 0.95, 0.00],  # shoulder
        [0.310, 0.02, 2.50, 0.72, 0.00],
        [0.365, 0.20, 2.95, 0.56, 0.14],  # handle
        [0.440, 0.85, 3.40, 0.50, 0.45],
        [0.510, 1.60, 3.30, 0.50, 0.70],
        [0.570, 2.10, 2.60, 0.48, 0.95],
        [0.630, 2.05, 1.85, 0.46, 1.15],
        [0.690, 1.50, 1.45, 0.45, 1.40],  # neck passes through the wall
        [0.750, 0.65, 1.30, 0.45, 1.30],
        [0.810, 0.10, 0.90, 0.45, 1.08],
        [0.860, 0.00, 0.55, 0.45, 1.00],  # neck runs down the axis inside the body
        [0.910, 0.00, 0.30, 0.45, 1.00],
        [0.955, 0.00, 0.09, 0.54, 1.00],  # inner side of the U
    ]
)


def _bottle_spline():
    u = np.r_[BOTTLE_KEYS[:, 0], 1.0]
    vals = np.vstack([BOTTLE_KEYS[:, 1:], BOTTLE_KEYS[:1, 1:]])
    vals[-1, 3] += 1.0  # th ends at pi ...
    vals[:, 3] -= u  # ... so th / pi - u is periodic
    return CubicSpline(u, vals, bc_type="periodic")


BOTTLE_SPLINE = _bottle_spline()


def bottle(u, v):
    """u in [0, 1] along the loop, v the angle around the tube. Returns (x, height, y)."""
    x, h, r, th = np.moveaxis(BOTTLE_SPLINE(u % 1.0), -1, 0)
    th = np.pi * (th + u)
    rc = r * np.cos(v)
    return np.stack([x + rc * np.cos(th), h - rc * np.sin(th), r * np.sin(v)], -1)


class KleinBottle(Surface):
    name, title = "klein-bottle", "Klein bottle (classic bottle)"
    chi, gluing = 0, "one pair straight, one pair flipped (a b a b⁻¹)"
    alpha_min, fade_from, cam_end = 0.5, 0.45, (-70.0, 30.0)
    stages: ClassVar = [0.0, 0.17, 0.35, 0.5, 0.62, 0.72, 0.8, 0.87, 0.94, 1.0]
    edges: ClassVar = [(TOP, BLUE), (BOTTOM, BLUE), (LEFT, ORANGE), (RIGHT, ORANGE)]
    corner_classes: ClassVar = {
        "TL": "white",
        "TR": "white",
        "BL": "white",
        "BR": "white",
    }
    legend = (
        "blue edges meet first (rolling); orange edges meet with a flip as the neck passes through the wall; "
        "all four corners become one point"
    )
    S0 = 0.25

    def colours(self):
        return periodic_colours()

    def cam_end_matrix(self):
        _, R = self._aligned_piece()
        zb = R @ np.array(
            [0.0, 0.0, 1.0]
        )  # bottle's symmetry-plane normal, in display coordinates
        xb = R @ np.array([1.0, 0.0, 0.0])
        f = zb / np.linalg.norm(zb)
        r = xb - f * (xb @ f)
        r /= np.linalg.norm(r)
        up = np.cross(f, r)
        M = np.vstack([r, up, f])  # rows: screen x, screen y, toward viewer
        tilt = np.radians(-22)
        Rt = np.array(
            [
                [1, 0, 0],
                [0, np.cos(tilt), -np.sin(tilt)],
                [0, np.sin(tilt), np.cos(tilt)],
            ]
        )
        return Rt @ M

    def piece(
        self, s
    ):  # x -> u in 0.5 + s/2*[-1,1];  y -> v = pi/2 + pi*y, so the end gluing is y -> -y
        return bottle(0.5 + s / 2 * SX, np.pi / 2 + np.pi * SY)

    def _cylinder(self, a, sign):
        u, v = SX / 2, SY / 2
        if a < 1e-6:
            return np.stack([u, v, 0 * u], -1)
        rho, phi = 1 / (2 * np.pi * a), sign * 2 * np.pi * a * v
        return np.stack([u, rho * np.sin(phi), rho * (1 - np.cos(phi))], -1)

    def _aligned_piece(self):
        if not hasattr(
            self, "_R"
        ):  # rotation (Kabsch) taking the short bottle piece onto the rolled cylinder
            best = None
            for sign in (1, -1):
                C = normalise(self._cylinder(1.0, sign)).reshape(-1, 3)
                Pc = normalise(self.piece(self.S0)).reshape(-1, 3)
                H = (Pc - Pc.mean(0)).T @ (C - C.mean(0))
                U_, _, Vt = np.linalg.svd(H)
                D = np.diag([1, 1, np.sign(np.linalg.det(Vt.T @ U_.T))])
                R = Vt.T @ D @ U_.T
                err = np.linalg.norm((Pc - Pc.mean(0)) @ R.T - (C - C.mean(0)))
                if best is None or err < best[0]:
                    best = (err, sign, R)
            _, self._sign, self._R = best
        return self._sign, self._R

    def shape(self, t):
        sign, R = self._aligned_piece()
        if t <= 0.35:  # roll into a cylinder (blue edges meet)
            return normalise(self._cylinder(smooth(t / 0.35), sign))
        if t <= 0.5:  # ease the cylinder into a short piece of the bottle
            a = smooth((t - 0.35) / 0.15)
            return normalise(
                (1 - a) * normalise(self._cylinder(1.0, sign))
                + a * normalise(self.piece(self.S0) @ R.T)
            )
        x = np.clip(
            (t - 0.5) / 0.5, 0, 1
        )  # grow the tube along the bottle; ease out hard at the gluing
        s = self.S0 + (1 - self.S0) * (1 - (1 - smooth(x)) ** 2)
        return normalise(self.piece(s) @ R.T)

    def caption(self, k, t):
        if t == 0:
            return "1  flat square"
        if t <= 0.35:
            return f"{k + 1}  rolling"
        if t < 1:
            return f"{k + 1}  growing the tube"
        return f"{k + 1}  Klein bottle"


class KleinFigure8(Surface):
    name, title = "klein-figure8", "Klein bottle (figure-8 immersion)"
    chi, gluing = 0, "one pair straight, one pair flipped (a b a b⁻¹)"
    alpha_min, fade_from, cam_end = 0.5, 0.45, (-60.0, 20.0)
    edges: ClassVar = [(TOP, BLUE), (BOTTOM, BLUE), (LEFT, ORANGE), (RIGHT, ORANGE)]
    corner_classes: ClassVar = {
        "TL": "white",
        "TR": "white",
        "BL": "white",
        "BR": "white",
    }
    legend = (
        "blue edges meet first (the cross-section closes into a figure 8); "
        "orange edges meet with a half twist; all four corners become one point"
    )
    R_RING = 2.2

    def colours(self):
        return periodic_colours()

    def shape(self, t):
        v = np.pi * (SY + 1)  # around the cross-section
        w = SX  # along the ring
        L = 2 * np.pi * self.R_RING
        a = smooth(t / 0.45)  # cross-section: straight segment -> figure 8
        p = (1 - a) * (SY * L / 2) + a * np.sin(v)
        q = a * np.sin(2 * v)
        b = smooth((t - 0.45) / 0.55)  # bend into a ring while twisting a half turn
        tw = b * np.pi * w / 2
        pr, qr = np.cos(tw) * p - np.sin(tw) * q, np.sin(tw) * p + np.cos(tw) * q
        if b < 1e-6:
            P = np.stack([w * L / 2, -pr, qr], -1)
        else:
            Rb = L / (2 * np.pi * b)
            al = np.pi * b * w
            out = np.stack([np.sin(al), -np.cos(al), 0 * al], -1)
            A = np.stack([Rb * np.sin(al), Rb * (1 - np.cos(al)), 0 * al], -1)
            P = A + pr[..., None] * out
            P[..., 2] += qr
        return normalise(P)

    def caption(self, k, t):
        if t == 0:
            return "1  flat square"
        if t <= 0.45:
            return f"{k + 1}  closing the figure 8"
        return f"{k + 1}  bending + twist" if t < 1 else f"{k + 1}  Klein bottle"


S5 = np.sqrt(5.0)


def bk(w, c=0.5):
    w3 = w**3
    w6 = w3 * w3
    d = w6 + S5 * w3 - 1.0
    n1, n2, n3 = w * (1 - w**4), w * (1 + w**4), 1 + w6
    dd = np.abs(d) ** 2
    h1 = -1.5 * np.imag(n1 * np.conj(d))
    h2 = -1.5 * np.real(n2 * np.conj(d))
    h3 = np.imag(n3 * np.conj(d)) - c * dd
    s = dd / np.maximum(h1**2 + h2**2 + h3**2, 1e-300)
    return np.stack([h1 * s, h2 * s, h3 * s], -1)


class ProjectivePlane(Surface):
    name, title = "projective-plane", "projective plane (Boy's surface)"
    chi, gluing = 1, "both pairs flipped (a b a b)"
    alpha_min, fade_from, cam_end = 0.48, 0.5, (-58.0, 25.0)
    edges: ClassVar = [(TOP, BLUE), (BOTTOM, BLUE), (LEFT, ORANGE), (RIGHT, ORANGE)]
    corner_classes: ClassVar = {
        "TR": "white",
        "BL": "white",
        "BR": "black",
        "TL": "black",
    }
    legend = "each edge meets the opposite one with a flip; white corners meet, black corners meet: 2 points"
    S0 = 0.22

    def colours(self):
        U = SX * np.sqrt(1 - SY**2 / 2)
        V = SY * np.sqrt(1 - SX**2 / 2)
        cu = 0.25 * (U[:-1, :-1] + U[1:, :-1] + U[1:, 1:] + U[:-1, 1:])
        cv = 0.25 * (V[:-1, :-1] + V[1:, :-1] + V[1:, 1:] + V[:-1, 1:])
        return (2 * np.arctan2(cv, cu) / (2 * np.pi)) % 1.0, np.clip(
            np.hypot(cu, cv), 0, 1
        ) ** 0.8 * 0.8

    def shape(self, t):
        U = SX * np.sqrt(1 - SY**2 / 2)
        V = SY * np.sqrt(1 - SX**2 / 2)
        pole = bk(np.array([0j]))[0]
        piece = lambda s: bk(s * (U + 1j * V)) - pole
        cap = piece(self.S0)
        cap = cap / np.linalg.norm(cap, axis=-1).max()
        A, *_ = np.linalg.lstsq(
            np.c_[U.ravel(), V.ravel()], cap.reshape(-1, 3), rcond=None
        )
        square = (np.c_[SX.ravel(), SY.ravel()] @ A).reshape(N + 1, N + 1, 3)
        if t <= 0.5:
            a = smooth(2 * t)
            return normalise((1 - a) * square + a * cap)
        return normalise(piece(self.S0 + (1 - self.S0) * smooth(2 * t - 1)))

    def caption(self, k, t):
        if t == 0:
            return "1  flat square"
        return (
            f"{k + 1}  bending"
            if t <= 0.5
            else (f"{k + 1}  growing" if t < 1 else f"{k + 1}  Boy's surface")
        )


SURFACES = {
    s.name: s
    for s in (Sphere(), Torus(), KleinBottle(), KleinFigure8(), ProjectivePlane())
}


# ---------------------------------------------------------------------------------------------
# Rendering (painter's algorithm; edges and corners depth-sorted together with the surface)
# ---------------------------------------------------------------------------------------------
def base_colours(surf):
    hue, sat = surf.colours()
    rgb = np.array(
        [
            colorsys.hsv_to_rgb(h, s, 0.95)
            for h, s in zip(hue.ravel(), sat.ravel(), strict=True)
        ]
    )
    rgb = rgb.reshape(N, N, 3)
    ii, jj = np.meshgrid(np.arange(N), np.arange(N), indexing="ij")
    rgb[
        (ii % LINE_EVERY == 0) | (jj % LINE_EVERY == 0) | (ii == N - 1) | (jj == N - 1)
    ] *= 0.4
    return rgb


def render(ax, surf, t, base):
    P = surf.shape(t)
    Q = P @ surf.cam(t).T
    al = surf.alpha(t)
    q = np.stack([Q[:-1, :-1], Q[1:, :-1], Q[1:, 1:], Q[:-1, 1:]], 2).reshape(-1, 4, 3)
    n = np.cross(q[:, 2] - q[:, 0], q[:, 3] - q[:, 1])
    n /= np.linalg.norm(n, axis=1, keepdims=True) + 1e-12
    n *= np.sign(n[:, 2:3] + 1e-12)
    lam = 0.5 + 0.5 * np.clip(n @ L_DIR, 0, 1)
    col = np.c_[np.clip(base.reshape(-1, 3) * lam[:, None], 0, 1), np.full(len(q), al)]
    polys, depth, cols = list(q[:, :, :2]), list(q[:, :, 2].mean(1)), list(col)
    w = 0.022
    for path, c in surf.edges:
        pts = np.array([Q[i, j] for i, j in path])
        for a, b in pairwise(pts):
            dv = b[:2] - a[:2]
            ln = np.linalg.norm(dv)
            if ln < 1e-9:
                continue
            ext = dv / ln * 0.25 * w
            for width, colr, bias in (
                (1.55 * w, np.r_[0.04, 0.04, 0.04, 1.0], 0.02),
                (w, np.r_[c, 1.0], 0.021),
            ):
                nn = np.array([-dv[1], dv[0]]) / ln * width
                polys.append(
                    np.array(
                        [
                            a[:2] - ext + nn,
                            b[:2] + ext + nn,
                            b[:2] + ext - nn,
                            a[:2] - ext - nn,
                        ]
                    )
                )
                depth.append(0.5 * (a[2] + b[2]) + bias)
                cols.append(colr)
    ring = np.c_[
        np.cos(np.linspace(0, 2 * np.pi, 13)[:-1]),
        np.sin(np.linspace(0, 2 * np.pi, 13)[:-1]),
    ]
    for key, cls in surf.corner_classes.items():
        p = Q[CORNERS[key]]
        polys.append(p[:2] + ring * 0.055)
        depth.append(p[2] + 0.03)
        cols.append(np.r_[0.05, 0.05, 0.05, 1.0])
        polys.append(p[:2] + ring * 0.04)
        depth.append(p[2] + 0.031)
        cols.append(np.r_[CLASS_COLOURS[cls], 1.0])
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


def bar(k, n, label):
    j = int(24 * k / n)
    print(f"\r{label} [{'#' * j}{'.' * (24 - j)}] {k}/{n}", end="", flush=True)
    if k == n:
        print()


def keys(surf, out):
    base = base_colours(surf)
    fig, axs = plt.subplots(2, 5, figsize=(22, 10.2), facecolor="white")
    for k, t in enumerate(surf.stages):
        render(axs.flat[k], surf, t, base)
        axs.flat[k].set_title(surf.caption(k, t), fontsize=14)
        f2, a2 = plt.subplots(figsize=(6, 6), facecolor="white")
        render(a2, surf, t, base)
        f2.savefig(f"{out}/stage_{k + 1:02d}.png", dpi=120, bbox_inches="tight")
        plt.close(f2)
        bar(k + 1, len(surf.stages), f"{surf.name} stages")
    fig.suptitle(
        f"From a square to the {surf.title}:  {surf.gluing},  χ = {surf.chi}",
        fontsize=17,
    )
    fig.text(0.5, 0.012, surf.legend, ha="center", fontsize=14)
    fig.subplots_adjust(
        left=0.01, right=0.99, top=0.9, bottom=0.06, wspace=0.04, hspace=0.14
    )
    fig.savefig(f"{out}/{surf.name}-sequence.png", dpi=85)
    plt.close(fig)


def anim(surf, out):
    from PIL import Image

    base = base_colours(surf)
    ts = (
        list(np.linspace(0, 1, 100))
        + [1.0] * 20
        + list(np.linspace(1, 0, 50))
        + [0.0] * 12
    )
    frames = []
    for k, t in enumerate(ts):
        f, a = plt.subplots(figsize=(4.8, 4.8), facecolor="white")
        render(a, surf, t, base)
        buf = io.BytesIO()
        f.savefig(buf, dpi=100, bbox_inches="tight")
        plt.close(f)
        frames.append(Image.open(buf).convert("RGB"))
        bar(k + 1, len(ts), f"{surf.name} animation")
    frames[0].save(
        f"{out}/{surf.name}-sequence.webp",
        save_all=True,
        append_images=frames[1:],
        duration=50,
        loop=0,
        quality=80,
    )


def overview(out):
    """The gluing diagrams: arrows show the direction each edge is glued in (single = orange pair, double = blue)."""
    from matplotlib.patches import Polygon

    def arrow(ax, p0, p1, c, double):
        d = np.array(p1, float) - np.array(p0, float)
        d /= np.linalg.norm(d)
        nrm = np.array([-d[1], d[0]])
        for off in (0.0,) if not double else (-0.11, 0.11):
            tip = (np.array(p0) + np.array(p1)) / 2 + d * (off + 0.09)
            tri = [tip, tip - d * 0.2 + nrm * 0.11, tip - d * 0.2 - nrm * 0.11]
            ax.add_patch(
                Polygon(tri, closed=True, facecolor=c, edgecolor="k", lw=1.5, zorder=4)
            )

    # direction of each edge as (start, end) so that glued points correspond
    spec = {
        "sphere": [
            ("top", ORANGE, (-1, 1), (1, 1), False),
            ("right", ORANGE, (1, -1), (1, 1), False),
            ("bottom", BLUE, (1, -1), (-1, -1), True),
            ("left", BLUE, (-1, 1), (-1, -1), True),
        ],
        "torus": [
            ("top", BLUE, (-1, 1), (1, 1), True),
            ("bottom", BLUE, (-1, -1), (1, -1), True),
            ("left", ORANGE, (-1, -1), (-1, 1), False),
            ("right", ORANGE, (1, -1), (1, 1), False),
        ],
        "klein-bottle": [
            ("top", BLUE, (-1, 1), (1, 1), True),
            ("bottom", BLUE, (-1, -1), (1, -1), True),
            ("left", ORANGE, (-1, -1), (-1, 1), False),
            ("right", ORANGE, (1, 1), (1, -1), False),
        ],
        "projective-plane": [
            ("top", BLUE, (-1, 1), (1, 1), True),
            ("bottom", BLUE, (1, -1), (-1, -1), True),
            ("left", ORANGE, (-1, -1), (-1, 1), False),
            ("right", ORANGE, (1, 1), (1, -1), False),
        ],
    }
    names = {
        "sphere": "sphere  χ = 2",
        "torus": "torus  χ = 0",
        "klein-bottle": "Klein bottle  χ = 0",
        "projective-plane": "projective plane  χ = 1",
    }
    pos = {"TL": (-1, 1), "TR": (1, 1), "BL": (-1, -1), "BR": (1, -1)}
    fig, axs = plt.subplots(1, 4, figsize=(18, 5.2), facecolor="white")
    for ax, key in zip(axs, spec, strict=True):
        for _, c, p0, p1, dbl in spec[key]:
            ax.plot(
                [p0[0], p1[0]], [p0[1], p1[1]], color="k", lw=7, solid_capstyle="round"
            )
            ax.plot(
                [p0[0], p1[0]], [p0[1], p1[1]], color=c, lw=4.5, solid_capstyle="round"
            )
            arrow(ax, p0, p1, c, dbl)
        cls = SURFACES[key].corner_classes
        for k2, (x, y) in pos.items():
            ax.plot(
                x, y, "o", ms=17, mfc=CLASS_COLOURS[cls[k2]], mec="k", mew=2.2, zorder=5
            )
        nv = len(set(cls.values()))
        ax.set_title(f"{names[key]}\n{nv} − 2 + 1 = {nv - 1}", fontsize=15)
        ax.set_xlim(-1.4, 1.4)
        ax.set_ylim(-1.4, 1.4)
        ax.set_aspect("equal")
        ax.axis("off")
    fig.text(
        0.5,
        0.03,
        "χ = corners after gluing − edge pairs + 1 face.   Arrows show which way the edges of a pair "
        "are matched; corners of one colour become a single point.",
        ha="center",
        fontsize=13,
    )
    fig.subplots_adjust(left=0.01, right=0.99, top=0.84, bottom=0.12, wspace=0.08)
    fig.savefig(f"{out}/gluing-diagrams.png", dpi=90)
    plt.close(fig)


def check():
    """Numerically confirm each finished surface glues its square the way the diagram says."""
    gl = {
        "sphere": [(TOP, RIGHT, False), (BOTTOM, LEFT, False)],
        "torus": [(TOP, BOTTOM, False), (LEFT, RIGHT, False)],
        "klein-bottle": [(TOP, BOTTOM, False), (LEFT, RIGHT, True)],
        "klein-figure8": [(TOP, BOTTOM, False), (LEFT, RIGHT, True)],
        "projective-plane": [(TOP, BOTTOM, True), (LEFT, RIGHT, True)],
    }
    for name, pairs in gl.items():
        X = SURFACES[name].shape(1.0)
        errs = []
        for e1, e2, flip in pairs:
            a = np.array([X[p] for p in e1])
            b = np.array([X[p] for p in (e2[::-1] if flip else e2)])
            errs.append(np.abs(a - b).max())
        cls = SURFACES[name].corner_classes
        pts = {}
        for k2, c in cls.items():
            pts.setdefault(c, []).append(X[CORNERS[k2]])
        spread = max(np.ptp(np.array(v), axis=0).max() for v in pts.values())
        print(
            f"{name:17s} edge mismatch {max(errs):.2e}   corner classes {len(pts)} (max spread {spread:.1e})"
        )


if __name__ == "__main__":
    if sys.argv[1] == "check":
        check()
    elif sys.argv[1] == "overview":
        out = sys.argv[2] if len(sys.argv) > 2 else "."
        os.makedirs(out, exist_ok=True)
        overview(out)
    else:
        surf, mode = SURFACES[sys.argv[1]], sys.argv[2]
        out = sys.argv[3] if len(sys.argv) > 3 else f"{surf.name}-sequence"
        os.makedirs(out, exist_ok=True)
        (keys if mode == "keys" else anim)(surf, out)
