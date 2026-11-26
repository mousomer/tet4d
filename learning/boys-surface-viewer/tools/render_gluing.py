"""Render the gluing of the square into Boy's surface: any glue values, any view angles.

Usage examples:
  python render_gluing.py                                    # 13 steps, front and back, edge style
  python render_gluing.py --glue 0:1:25 --view front --anim  # 25 steps, one view, plus an animated WebP
  python render_gluing.py --glue 0,0.3,0.31,0.32,1           # explicit glue values
  python render_gluing.py --view 30,20 --view -30,200        # views as (tilt, turn) in degrees
  python render_gluing.py --style glass --size 800 --out my_frames

Requires playwright (python -m pip install playwright; python -m playwright install chromium), pillow.
Frames are rendered by the viewer page itself (headless, SwiftShader), so they match it exactly.

Options:
  --glue    values as START:END:COUNT (evenly spaced, inclusive) or a comma list; default 0:1:13.
            The viewer re-times the slider so equal steps make equally large changes.
  --view    repeatable. A name (front, back, top, side) or TILT,TURN in degrees: TILT rotates about the
            screen's horizontal axis, TURN about the vertical one (the viewer's drag rotation).
            Default: front and back.
  --style   edges (nearly clear glass, faint grid, thick edges and corners; default) or glass (the
            viewer's default look).
  --set     extra viewer parameters as JSON, applied last, e.g. '{"gap": 0, "edgeW": 4}'.
  --chrome  a Chrome/Chromium binary, if playwright's own is not installed.
  --size    frame size in pixels (default 560).
  --out     output folder (default gluing_frames). Writes glue_<g>_<view>.png per frame, strip.png
            (rows: views; columns: glue values, wrapped in blocks of --cols), and with --anim one
            animated WebP per view.
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
PAGE = HERE.parent / "boys-surface-viewer.html"
ARGS = [
    "--use-angle=swiftshader",
    "--enable-unsafe-swiftshader",
    "--ignore-gpu-blocklist",
]
READY = (
    "window.__boy !== undefined && window.__boy.stats.flowReady && window.__boy.stats.membraneReady"
    " && window.__boy.stats.gapReady"
)
NAMED_VIEWS = {  # (tilt, turn) in degrees
    "front": (28.6, 22.9),
    "back": (-28.6, 202.9),
    "top": (80.0, 0.0),
    "side": (0.0, 90.0),
}
STYLES = {
    "edges": {
        "opa": 0.1,
        "frost": 0,
        "clar": 1,
        "gridType": "square",
        "gridS": 0.15,
        "gridN": 8,
        "edgeW": 5,
        "edges": True,
        "corners": True,
    },
    "glass": {},
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


async def render(glues, views, params, size, out, page, chrome=None):
    frames = {}
    async with async_playwright() as p:
        kw = {"headless": True, "args": ARGS}
        if chrome:
            kw["executable_path"] = chrome
        br = await p.chromium.launch(**kw)
        pg = await br.new_page(viewport={"width": size, "height": size})
        await pg.goto(page.resolve().as_uri())
        await pg.wait_for_function(READY, timeout=60000)
        await pg.evaluate(
            f"document.getElementById('ui').classList.add('hidden');"
            f" document.getElementById('ui-toggle').style.display = 'none';"
            f" window.__boy.set(Object.assign({{spin: 0}}, {json.dumps(params)}))"
        )
        total, n = len(glues) * len(views), 0
        for vname, (tilt, turn) in views:
            await pg.evaluate(
                f"window.__boy.pose({{rotX: {math.radians(tilt)}, rotY: {math.radians(turn)}, spin: 0}})"
            )
            for g in glues:
                await pg.evaluate(
                    f"window.__boy.set({{glue: {g}}}); window.__boy.renderNow()"
                )
                img = Image.open(io.BytesIO(await pg.screenshot())).convert("RGB")
                img.save(out / f"glue_{g:.3f}_{vname}.png")
                frames[(vname, g)] = img
                n += 1
                bar(n, total, "frames")
        await br.close()
    return frames


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
    ap.add_argument("--glue", default="0:1:13")
    ap.add_argument("--view", action="append")
    ap.add_argument("--style", choices=sorted(STYLES), default="edges")
    ap.add_argument("--set", default="{}")
    ap.add_argument("--size", type=int, default=560)
    ap.add_argument("--cols", type=int, default=7)
    ap.add_argument(
        "--anim", action="store_true", help="also write an animated WebP per view"
    )
    ap.add_argument("--fps", type=float, default=12)
    ap.add_argument("--out", default="gluing_frames")
    ap.add_argument("--page", default=str(PAGE))
    ap.add_argument(
        "--chrome", help="Chrome/Chromium binary (default: playwright's chromium)"
    )
    a = ap.parse_args()
    glues = parse_glue(a.glue)
    views = [parse_view(v) for v in (a.view or ["front", "back"])]
    params = {**STYLES[a.style], **json.loads(a.set)}
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    frames = asyncio.run(
        render(glues, views, params, a.size, out, Path(a.page), a.chrome)
    )
    strip(frames, glues, views, a.cols, a.size, out / "strip.png")
    print(f"wrote {len(frames)} frames and {out / 'strip.png'}")
    if a.anim:
        for vname, _ in views:
            seq = [frames[(vname, g)] for g in glues]
            seq[0].save(
                out / f"gluing_{vname}.webp",
                save_all=True,
                append_images=seq[1:],
                duration=int(1000 / a.fps),
                loop=0,
                quality=82,
                method=6,
            )
            print(f"wrote {out / f'gluing_{vname}.webp'}")


if __name__ == "__main__":
    main()
