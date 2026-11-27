"""Render the square gluings from the viewer pages: any surfaces, glue values, views, cone settings, motions.

Usage examples:
  python tools/render_gluing.py --surface torus                       # 13 steps, home and back views
  python tools/render_gluing.py --surface all --glue 0:1:25 --anim    # every page, animated WebP per view
  python tools/render_gluing.py --surface sphere --cones both --glue 0.5,0.8,1
  python tools/render_gluing.py --surface klein-adjacent --motion stretch --view 20,40 --view back
  python tools/render_gluing.py --thumbs                              # the menu page's img/<id>.webp

Requires playwright and pillow (python -m pip install playwright pillow; python -m playwright install
chromium, or pass --chrome). Frames are rendered by the viewer pages themselves (headless, SwiftShader),
so they match what a reader sees.

Options:
  --surface  repeatable: sphere, rp2-adjacent, rp2-opposite, torus, klein-adjacent, klein-opposite, klein-bottle, rp2-boy,
             or all.
  --glue     START:END:COUNT (evenly spaced, inclusive) or a comma list; default 0:1:13. The pages re-time
             the slider so equal steps make equally large changes.
  --view     repeatable. home (the page's default view), back, top, side, or TILT,TURN in degrees added
             to the default view (TILT about the screen's horizontal axis, TURN about the vertical one,
             as dragging does). Default: home and back.
  --cones    with, without or both (pages without cone points always render once). Default: with.
  --motion   stages (default) or stretch.
  --style    viewer (the page's own look; default) or edges (clear glass, faint grid, wide edges).
  --set      extra page parameters as JSON, applied last, e.g. '{"labelsOn": false, "edgeW": 6}'.
  --size     frame size in pixels (default 560); --cols strip columns (default 7); --fps for --anim.
  --out      output folder (default gluing_frames); one subfolder per surface and setting with
             glue_<g>_<view>.png, strip.png and, with --anim, gluing_<view>.webp.
  --chrome   a Chrome/Chromium binary, if playwright's own is not installed.
"""

import argparse
import asyncio
import io
import json
import math
from pathlib import Path

from PIL import Image, ImageDraw
from playwright.async_api import async_playwright

HERE = Path(__file__).resolve().parent
PAGES = HERE.parent
SURFACES = [
    "sphere",
    "rp2-adjacent",
    "rp2-opposite",
    "torus",
    "klein-adjacent",
    "klein-opposite",
    "klein-bottle",
    "rp2-boy",
]
ARGS = [
    "--use-angle=swiftshader",
    "--enable-unsafe-swiftshader",
    "--ignore-gpu-blocklist",
]
READY = "window.__glue !== undefined && window.__glue.stats.frameCount > 0"
NAMED_VIEWS = {
    "home": (0.0, 0.0),
    "back": (0.0, 180.0),
    "top": (75.0, 0.0),
    "side": (0.0, 90.0),
}  # degrees
THUMB_DIST = {"sphere": 3.6}
STYLES = {
    "viewer": {},
    "edges": {"opa": 0.1, "frost": 0, "clar": 1, "gridS": 0.15, "gridN": 8, "edgeW": 6},
}


def bar(i, n, label):
    k = int(24 * i / n)
    print(f"\r{label} [{'#' * k}{'.' * (24 - k)}] {i}/{n}", end="", flush=True)
    if i == n:
        print()


def parse_glue(text):
    if ":" in text:
        a, b, n = text.split(":")
        n = int(n)
        return [float(a) + (float(b) - float(a)) * i / max(n - 1, 1) for i in range(n)]
    return [float(x) for x in text.split(",")]


def parse_view(text):
    if text in NAMED_VIEWS:
        return text, NAMED_VIEWS[text]
    tilt, turn = (float(x) for x in text.split(","))
    return f"t{tilt:g}_r{turn:g}", (tilt, turn)


async def open_page(browser, sid, size, params):
    pg = await browser.new_page(viewport={"width": size[0], "height": size[1]})
    errors = []
    pg.on("pageerror", lambda e: errors.append(str(e)))
    await pg.goto((PAGES / f"{sid}.html").resolve().as_uri() + "?play=0&glue=0")
    await pg.wait_for_function(READY, timeout=120000)
    await pg.evaluate(
        "document.getElementById('ui').style.display = 'none';"
        " document.getElementById('ui-toggle').style.display = 'none';"
        f" window.__glue.set(Object.assign({{spin: 0}}, {json.dumps(params)}))"
    )
    base = await pg.evaluate(
        "[window.__glue.SURFACE.view || {}].map((v) => [v.rotX || 0, v.rotY || 0])[0]"
    )
    return pg, base, errors


async def shoot(pg, base, view, glue):
    tilt, turn = view
    await pg.evaluate(
        f"window.__glue.pose({{rotX: {base[0] + math.radians(tilt)}, rotY: {base[1] + math.radians(turn)}, spin: 0}});"
        f" window.__glue.set({{glue: {glue}}}); window.__glue.renderNow()"
    )
    return Image.open(io.BytesIO(await pg.screenshot())).convert("RGB")


async def render(jobs, glues, views, size, chrome):
    """jobs: list of (folder name, surface id, params). Returns {folder: {(view, glue): image}}."""
    out = {}
    total, n = len(jobs) * len(glues) * len(views), 0
    async with async_playwright() as p:
        kw = {"headless": True, "args": ARGS}
        if chrome:
            kw["executable_path"] = chrome
        br = await p.chromium.launch(**kw)
        for folder, sid, params in jobs:
            pg, base, errors = await open_page(br, sid, (size, size), params)
            frames = out[folder] = {}
            for vname, view in views:
                for g in glues:
                    frames[(vname, g)] = await shoot(pg, base, view, g)
                    n += 1
                    bar(n, total, "frames")
            if errors:
                print(f"\n{sid}: page errors: {errors[:3]}")
            await pg.close()
        await br.close()
    return out


async def thumbs(chrome):
    async with async_playwright() as p:
        kw = {"headless": True, "args": ARGS}
        if chrome:
            kw["executable_path"] = chrome
        br = await p.chromium.launch(**kw)
        (PAGES / "img").mkdir(exist_ok=True)
        for i, sid in enumerate(SURFACES):
            pg, base, _ = await open_page(br, sid, (640, 480), {"labelsOn": False})
            if (
                sid in THUMB_DIST
            ):  # the sphere's flat diamond sets its scale: move in on the pillow
                await pg.evaluate(f"window.__glue.pose({{dist: {THUMB_DIST[sid]}}})")
            img = await shoot(pg, base, (0.0, 0.0), 1.0)
            img.save(PAGES / "img" / f"{sid}.webp", quality=84, method=6)
            await pg.close()
            bar(i + 1, len(SURFACES), "thumbnails")
        await br.close()


def strip(frames, glues, views, cols, size, path):
    cell = min(size, 360)
    cols = min(cols, len(glues))
    label_w = 70 if len(views) > 1 else 0
    blocks = [glues[i : i + cols] for i in range(0, len(glues), cols)]
    block_h = 24 + cell * len(views)
    sheet = Image.new("RGB", (label_w + cols * cell, block_h * len(blocks)), "white")
    d = ImageDraw.Draw(sheet)
    for bi, blk in enumerate(blocks):
        y0 = bi * block_h
        for k, g in enumerate(blk):
            d.text(
                (label_w + k * cell + cell // 2 - 28, y0 + 6),
                f"glue {g:.2f}",
                fill="black",
            )
            for vi, (vname, _) in enumerate(views):
                im = frames[(vname, g)].resize((cell, cell), Image.LANCZOS)
                sheet.paste(im, (label_w + k * cell, y0 + 24 + vi * cell))
        if label_w:
            for vi, (vname, _) in enumerate(views):
                d.text((6, y0 + 24 + vi * cell + cell // 2), vname, fill="black")
    sheet.save(path)


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--surface", action="append")
    ap.add_argument("--glue", default="0:1:13")
    ap.add_argument("--view", action="append")
    ap.add_argument("--cones", choices=["with", "without", "both"], default="with")
    ap.add_argument("--motion", choices=["stages", "stretch"], default="stages")
    ap.add_argument("--style", choices=sorted(STYLES), default="viewer")
    ap.add_argument("--set", default="{}")
    ap.add_argument("--size", type=int, default=560)
    ap.add_argument("--cols", type=int, default=7)
    ap.add_argument(
        "--anim", action="store_true", help="also write an animated WebP per view"
    )
    ap.add_argument("--fps", type=float, default=12)
    ap.add_argument("--out", default="gluing_frames")
    ap.add_argument(
        "--thumbs",
        action="store_true",
        help="write the menu page's thumbnails and stop",
    )
    ap.add_argument(
        "--chrome", help="Chrome/Chromium binary (default: playwright's chromium)"
    )
    a = ap.parse_args()
    if a.thumbs:
        asyncio.run(thumbs(a.chrome))
        return
    surfaces = SURFACES if not a.surface or "all" in a.surface else a.surface
    unknown = set(surfaces) - set(SURFACES)
    if unknown:
        ap.error(f"unknown surface(s): {', '.join(sorted(unknown))}")
    glues = parse_glue(a.glue)
    views = [parse_view(v) for v in (a.view or ["home", "back"])]
    base = {**STYLES[a.style], "motion": a.motion, **json.loads(a.set)}
    jobs = []
    for sid in surfaces:
        has_cones = sid in ("sphere", "rp2-adjacent", "rp2-opposite")
        settings = (
            {"with": [True], "without": [False], "both": [True, False]}[a.cones]
            if has_cones
            else [True]
        )
        for cones in settings:
            folder = (
                sid
                + ("" if cones or not has_cones else "-nocones")
                + ("-stretch" if a.motion == "stretch" else "")
            )
            jobs.append((folder, sid, {**base, "cones": cones}))
    out = Path(a.out)
    rendered = asyncio.run(render(jobs, glues, views, a.size, a.chrome))
    for folder, frames in rendered.items():
        d = out / folder
        d.mkdir(parents=True, exist_ok=True)
        for (vname, g), img in frames.items():
            img.save(d / f"glue_{g:.3f}_{vname}.png")
        strip(frames, glues, views, a.cols, a.size, d / "strip.png")
        if a.anim:
            for vname, _ in views:
                seq = [frames[(vname, g)] for g in glues]
                seq[0].save(
                    d / f"gluing_{vname}.webp",
                    save_all=True,
                    append_images=seq[1:],
                    duration=int(1000 / a.fps),
                    loop=0,
                    quality=82,
                    method=6,
                )
        print(f"wrote {d} ({len(frames)} frames{', animations' if a.anim else ''})")


if __name__ == "__main__":
    main()
