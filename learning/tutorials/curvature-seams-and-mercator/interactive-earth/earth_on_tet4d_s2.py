"""An explicitly defined homeomorphic Earth map on Tet4D's positive-adjacent S2 square.

The map is illustrative and deliberately not conformal or area preserving.
It is a mathematically consistent embedding of two hemispheres into the two
triangles of the square with paired-edge coordinates agreeing pointwise.

Uses Basemap's bundled low-resolution coastline polygons; no downloaded map
texture is needed. Requirements: numpy, pillow, matplotlib, scipy, basemap.
"""

from math import pi
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from mpl_toolkits.basemap import Basemap
from PIL import Image, ImageDraw

OUTPUT = Path(__file__).with_name("earth_on_tet4d_s2.png")
BOARD = Path(__file__).with_name("earth_on_tet4d_s2_board.png")

# Triangle quotient: L(t)=B(t), R(t)=T(t).
# Lower triangle ABC (x>=y) and upper ACD (y>=x) each represent a hemisphere.
# Each triangle uses barycentric coordinates (A,M,C), M=B~D.
# The shared triangle boundary maps to the equator; its three edges are
# parameterized in order A -> M -> C -> A along longitude.
THETA_M = 2 * pi / (2 + np.sqrt(2))
THETA_C = 2 * THETA_M
LON_ORIGIN = -165.0  # arbitrary rotation of Earth relative to labelled vertex A


def board_to_earth(x, y):
    x = np.asarray(x)
    y = np.asarray(y)
    north = y >= x  # upper-left triangle holds northern hemisphere
    low_w_a = 1 - x
    low_w_m = x - y
    low_w_c = y
    high_w_a = 1 - y
    high_w_m = y - x
    high_w_c = x
    wa = np.where(north, high_w_a, low_w_a)
    wm = np.where(north, high_w_m, low_w_m)
    wc = np.where(north, high_w_c, low_w_c)
    r = np.clip(1 - 3 * np.minimum(np.minimum(wa, wm), wc), 0, 1)
    inv_r = np.where(r > 1.0e-12, 1 / np.maximum(r, 1e-12), 0)
    a = 1 / 3 + (wa - 1 / 3) * inv_r
    m = 1 / 3 + (wm - 1 / 3) * inv_r
    c = 1 / 3 + (wc - 1 / 3) * inv_r
    theta = np.where(
        c < 1e-7,
        THETA_M * m,
        np.where(
            a < 1e-7,
            THETA_M + (THETA_C - THETA_M) * c,
            THETA_C + (2 * pi - THETA_C) * a,
        ),
    )
    theta = np.where(r < 1e-12, 0, theta)
    lat = np.where(north, 1, -1) * 90 * (1 - r)
    lon = ((LON_ORIGIN + np.rad2deg(theta) + 180) % 360) - 180
    return lon, lat


def earth_to_board(lon, lat):
    lon = np.asarray(lon)
    lat = np.asarray(lat)
    theta = np.deg2rad((lon - LON_ORIGIN) % 360)
    r = 1 - np.abs(lat) / 90
    t1 = theta / THETA_M
    t2 = (theta - THETA_M) / (THETA_C - THETA_M)
    t3 = (theta - THETA_C) / (2 * pi - THETA_C)
    bm = np.where(theta <= THETA_M, t1, np.where(theta <= THETA_C, 1 - t2, 0))
    bc = np.where(theta <= THETA_M, 0, np.where(theta <= THETA_C, t2, 1 - t3))
    m = 1 / 3 + r * (bm - 1 / 3)
    c = 1 / 3 + r * (bc - 1 / 3)
    north = lat >= 0
    x = np.where(north, c, m + c)
    y = np.where(north, m + c, c)
    return x, y


def make_earth_texture(width=2400, height=1200):
    # Built-in GSHHS coastlines. type=1 land, 2 water holes, 3 islands, ...
    b = Basemap(
        projection="cyl",
        llcrnrlon=-180,
        urcrnrlon=180,
        llcrnrlat=-90,
        urcrnrlat=90,
        resolution="l",
    )
    mask = Image.new("L", (width, height), 0)
    draw = ImageDraw.Draw(mask)
    for (lons, lats), kind in zip(b.coastpolygons, b.coastpolygontypes):
        pts = [
            ((lo + 180) / 360 * (width - 1), (90 - la) / 180 * (height - 1))
            for lo, la in zip(lons, lats)
        ]
        if len(pts) > 2:
            draw.polygon(pts, fill=255 if int(kind) % 2 == 1 else 0)
    land = np.asarray(mask, dtype=np.uint8) > 127
    yy, xx = np.mgrid[0:height, 0:width]
    lat = 90 - 180 * yy / height
    lon = -180 + 360 * xx / width
    # Stylized topography colors: geographic land outlines are true GSHHS,
    # within-continent coloration is decorative rather than measured relief.
    ocean = np.zeros((height, width, 3), dtype=np.float32)
    wave = (np.sin(xx / 150) + np.cos(yy / 125)) * 3
    ocean[..., 0] = 18 + wave
    ocean[..., 1] = 65 + wave
    ocean[..., 2] = 91 + wave
    land_rgb = np.zeros_like(ocean)
    land_rgb[..., 0] = 182 + 8 * np.sin(xx / 73)
    land_rgb[..., 1] = 174 + 12 * np.sin(yy / 91)
    land_rgb[..., 2] = 122 + 5 * np.cos(xx / 83)
    # Add stylized Sahara, Arabia, Australia; relief coloring is illustrative.
    desert = ((lon > -19) & (lon < 55) & (lat > 12) & (lat < 34)) | (
        (lon > 110) & (lon < 155) & (lat < -17) & (lat > -35)
    )
    land_rgb[desert, :] = np.array([216, 185, 126])
    ice = np.abs(lat) > 70
    land_rgb[ice, :] = np.array([224, 232, 226])
    tex = np.where(land[..., None], land_rgb, ocean).clip(0, 255).astype("uint8")
    return Image.fromarray(tex, "RGB")


def warp_texture(texture, n=980):
    xs = (np.arange(n) + 0.5) / n
    ys = 1 - (np.arange(n) + 0.5) / n
    x, y = np.meshgrid(xs, ys)
    lon, lat = board_to_earth(x, y)
    tex = np.asarray(texture)
    h, w = tex.shape[:2]
    u = (lon + 180) / 360 * w
    v = (90 - lat) / 180 * (h - 1)
    # Bilinear sampling; horizontal wrap at dateline.
    ux = np.floor(u).astype(int) % w
    ux1 = (ux + 1) % w
    vy = np.floor(v).astype(int).clip(0, h - 1)
    vy1 = (vy + 1).clip(0, h - 1)
    du = (u - np.floor(u))[..., None]
    dv = (v - np.floor(v))[..., None]
    a = tex[vy, ux].astype(float)
    b = tex[vy, ux1].astype(float)
    c = tex[vy1, ux].astype(float)
    d = tex[vy1, ux1].astype(float)
    col = (a * (1 - du) + b * du) * (1 - dv) + (c * (1 - du) + d * du) * dv
    return Image.fromarray(np.clip(col, 0, 255).astype("uint8"), "RGB")


def draw_graticule(ax):
    def line(lons, lats, alpha=0.22, width=0.7, color="#F2F2E8"):
        lons = np.asarray(lons)
        lats = np.asarray(lats)
        x, y = earth_to_board(lons, lats)
        jump = np.hypot(np.diff(x), np.diff(y)) > 0.05
        xx = x.copy()
        yy = y.copy()
        for i, j in enumerate(jump):
            if j:
                xx[i + 1] = np.nan
                yy[i + 1] = np.nan
        ax.plot(xx, yy, color=color, lw=width, alpha=alpha, zorder=4)

    for lat in [-60, -30, 30, 60]:
        line(np.linspace(-180, 180, 721), np.full(721, lat))
    for lon in range(-180, 181, 45):
        lat = np.linspace(-89.95, 89.95, 721)
        # Split at equator to avoid artificial line across cut.
        line(np.full(360, lon), lat[:360])
        line(np.full(361, lon), lat[360:])
    for pt, caption, offset in [
        ((1 / 3, 2 / 3), "N pole", (-22, 12)),
        ((2 / 3, 1 / 3), "S pole", (12, -19)),
    ]:
        ax.plot(
            *pt,
            marker="o",
            markersize=4,
            color="white",
            markeredgecolor="#203844",
            zorder=8,
        )
        ax.annotate(
            caption,
            pt,
            xytext=offset,
            textcoords="offset points",
            fontsize=9,
            weight="bold",
            color="white",
            ha="center",
            bbox={
                "boxstyle": "round,pad=.28",
                "fc": "#163046",
                "ec": "none",
                "alpha": 0.8,
            },
            zorder=9,
        )
    ax.plot([0, 1], [0, 1], color="#ffe7b4", lw=1.8, ls="--", alpha=0.9, zorder=7)


def run():
    tex = make_earth_texture()
    board = warp_texture(tex, 950)
    board.save(BOARD)
    fig = plt.figure(figsize=(15, 8), facecolor="#F7F8FB")
    ax = fig.add_axes([0.05, 0.12, 0.53, 0.78])
    ax.set_aspect("equal")
    ax.imshow(board, extent=[0, 1, 0, 1], origin="upper")
    draw_graticule(ax)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_color("#30475b")
        spine.set_linewidth(2)
    ax.set_title(
        "Earth on Tet4D’s S² square",
        fontsize=21,
        weight="bold",
        loc="left",
        pad=19,
        color="#172d40",
    )
    for pos, name, dx, dy in [
        ((0, 0), "A", -12, -16),
        ((1, 0), "B", 9, -16),
        ((1, 1), "C", 11, 11),
        ((0, 1), "D", -12, 11),
    ]:
        ax.annotate(
            name,
            pos,
            xytext=(dx, dy),
            textcoords="offset points",
            fontweight="bold",
            fontsize=12,
            color="#1f2e36",
            ha="center",
        )
    ax.text(
        0.5,
        -0.055,
        "L(t) ≡ B(t)     R(t) ≡ T(t)",
        ha="center",
        transform=ax.transAxes,
        fontsize=12,
        color="#3C5062",
    )
    ax2 = fig.add_axes([0.64, 0.52, 0.32, 0.37])
    ax2.imshow(tex, extent=[-180, 180, -90, 90])
    ax2.set_title(
        "Reference: equirectangular Earth",
        fontsize=12,
        loc="left",
        pad=10,
        color="#172d40",
    )
    ax2.set_xlabel("Longitude")
    ax2.set_ylabel("Latitude")
    ax2.set_xticks([-180, -90, 0, 90, 180])
    ax2.set_yticks([-90, -45, 0, 45, 90])
    ax2.tick_params(labelsize=8)
    for sp in ax2.spines.values():
        sp.set_color("#8494a1")
    ax3 = fig.add_axes([0.64, 0.12, 0.32, 0.27])
    ax3.axis("off")
    msg = (
        "ONE VALID PROJECTION — NOT UNIQUE\n\n"
        "Upper-left triangle  → Northern hemisphere\n"
        "Lower-right triangle → Southern hemisphere\n"
        "Their boundaries     → The equator\n\n"
        "The dashed diagonal is part of the equator.\n"
        "Paired outer edges are the other equator arcs.\n"
        "The layout preserves identifications, not distances."
    )
    ax3.text(
        0.02,
        0.92,
        msg,
        fontsize=11,
        va="top",
        ha="left",
        color="#233a4a",
        linespacing=1.45,
    )
    fig.text(
        0.05,
        0.012,
        "Coastlines: bundled GSHHS low-resolution data · Illustrative, non-conformal triangle-to-hemisphere map · Background colors stylized",
        fontsize=8.5,
        color="#687a87",
    )
    fig.savefig(OUTPUT, dpi=170, bbox_inches="tight", facecolor="#F7F8FB")
    plt.close(fig)
    # Numeric consistency of edge pairings and round-trip, at many points.
    t = np.linspace(0, 1, 101)
    l1, phi1 = board_to_earth(np.zeros_like(t), t)
    l2, phi2 = board_to_earth(t, np.zeros_like(t))
    assert np.max(np.abs(phi1 - phi2)) < 1e-10
    assert np.max(np.abs(((l1 - l2 + 180) % 360) - 180)) < 1e-10
    l1, phi1 = board_to_earth(np.ones_like(t), t)
    l2, phi2 = board_to_earth(t, np.ones_like(t))
    assert np.max(np.abs(phi1 - phi2)) < 1e-10
    assert np.max(np.abs(((l1 - l2 + 180) % 360) - 180)) < 1e-10
    for p in [(0.2, 0.7), (0.8, 0.3), (0.12, 0.85), (0.83, 0.71), (0.28, 0.17)]:
        lon, lat = board_to_earth(*p)
        xx, yy = earth_to_board(lon, lat)
        assert np.hypot(xx - p[0], yy - p[1]) < 1e-10, (p, (xx, yy))
    print("Projection verified. Outputs:", OUTPUT, BOARD)


if __name__ == "__main__":
    run()
