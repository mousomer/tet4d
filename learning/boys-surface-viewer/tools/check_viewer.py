"""Browser checks for the Boy's surface viewer.

Usage:  python check_viewer.py [--chrome PATH] [--page PATH]

Requires playwright (python -m pip install playwright; python -m playwright install chromium), pillow and
numpy. Runs headless with SwiftShader, so no GPU is needed. Exits non-zero if any check fails.

Checks:
  - the page loads, both embedded fields decode, and no console or page errors occur;
  - the panel: presets and Custom detection, every menu and toggle, collapsing a section survives a
    reload, Reset restores the defaults, the panel toggle and the H key;
  - rendering: each visual switch (membranes, self-intersections, grid, glued edges) changes the image;
  - gluing: the glue slider stretches the flat square into the surface, and the play button completes it;
  - interaction: right-drag moves the shape, double-click recentres it;
  - geometry: antipodal corners and the three preimages of the triple point land on the same 3D point.
"""

import argparse
import asyncio
import io
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from playwright.async_api import async_playwright

HERE = Path(__file__).resolve().parent
ARGS = [
    "--use-angle=swiftshader",
    "--enable-unsafe-swiftshader",
    "--ignore-gpu-blocklist",
]
READY = (
    "window.__boy !== undefined && window.__boy.stats.flowReady && window.__boy.stats.membraneReady"
    " && window.__boy.stats.gapReady"
)

results = []


def bar(i, n, label):
    k = int(24 * i / n)
    print(f"\r[{'#' * k}{'.' * (24 - k)}] {i}/{n} {label:<46}", end="", flush=True)


def check(name, ok, detail=""):
    results.append((name, bool(ok), detail))


async def shot(pg):
    await pg.evaluate("window.__boy.renderNow()")
    return np.asarray(
        Image.open(io.BytesIO(await pg.screenshot())).convert("RGB")
    ).astype(int)


def changed(a, b, frac=0.002):
    """True if more than `frac` of the pixels differ noticeably."""
    return (np.abs(a - b).max(-1) > 24).mean() > frac


async def run(chrome, page):
    url = page.resolve().as_uri()
    async with async_playwright() as p:
        kw = {"headless": True, "args": ARGS}
        if chrome:
            kw["executable_path"] = chrome
        br = await p.chromium.launch(**kw)
        pg = await br.new_page(viewport={"width": 800, "height": 800})
        errors = []
        pg.on("pageerror", lambda e: errors.append(str(e)))
        pg.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
        ev = pg.evaluate
        steps = 9

        bar(1, steps, "load")
        await pg.goto(url)
        await pg.wait_for_function(READY, timeout=60000)
        check("page loads, both fields decode", True)

        bar(2, steps, "panel: presets")
        await pg.select_option("#preset", "slim")
        check(
            "preset Slim tubes sets slimming 1.3",
            await ev("window.__boy.P.slim") == 1.3,
        )
        await pg.select_option("#preset", "classic")
        check("preset Classic sets gap width 0", await ev("window.__boy.P.gap") == 0)
        await pg.fill("#len", "1.1")
        await pg.dispatch_event("#len", "input")
        check(
            "editing a shape slider shows Custom",
            await pg.eval_on_selector("#preset", "e => e.value") == "custom",
        )

        bar(3, steps, "panel: menus and toggles")
        await pg.click("#sec-scene > summary")  # the Scene section starts collapsed
        for sel, val in (
            ("#membranes", "faded"),
            ("#gridType", "polar"),
            ("#axis", "vert"),
        ):
            await pg.select_option(sel, val)
            key = sel[1:]
            check(f"menu {key} -> {val}", await ev(f"window.__boy.P['{key}']") == val)
        for box in ("edges", "corners", "curves"):
            before = await ev(f"window.__boy.P.{box}")
            await pg.click(f"#{box}")
            check(f"toggle {box}", await ev(f"window.__boy.P.{box}") == (not before))
        await pg.click("#reset")
        check(
            "Reset restores the defaults",
            await ev(
                "(() => { const P = window.__boy.P; return P.membranes === 'removed' && P.gridType === 'square'"
                " && P.edges && P.corners && !P.curves && P.axis === 'sym' && P.glue === 1 && P.gap === 1; })()"
            )
            and await pg.eval_on_selector("#preset", "e => e.value") == "reference",
        )

        bar(4, steps, "panel: hide and show")
        await pg.click("#ui-toggle")
        hidden = await ev("document.getElementById('ui').classList.contains('hidden')")
        await pg.keyboard.press("h")
        shown = not await ev(
            "document.getElementById('ui').classList.contains('hidden')"
        )
        check("panel toggle button and H key", hidden and shown)

        bar(5, steps, "panel: collapsed section after reload")
        await pg.click("#sec-material > summary")
        await pg.reload()
        await pg.wait_for_function(READY, timeout=60000)
        check(
            "collapsed section is remembered",
            await ev("!document.getElementById('sec-material').open"),
        )
        await pg.click("#sec-material > summary")

        bar(6, steps, "rendering: visual switches")
        await ev(
            "document.getElementById('ui').classList.add('hidden');"
            " window.__boy.set({spin: 0, opa: 0.15, frost: 0, gridType: 'off', curves: false})"
        )
        base = await shot(pg)
        for name, on, off in (
            (
                "membranes Shown vs Removed",
                "{membranes: 'shown'}",
                "{membranes: 'removed'}",
            ),
            ("self-intersections on", "{curves: true}", "{curves: false}"),
            ("square grid on", "{gridType: 'square'}", "{gridType: 'off'}"),
            (
                "glued edges off",
                "{edges: false, corners: false}",
                "{edges: true, corners: true}",
            ),
            ("gap width 0", "{gap: 0}", "{gap: 1}"),
        ):
            await ev(f"window.__boy.set({on})")
            img = await shot(pg)
            await ev(f"window.__boy.set({off})")
            check(f"render changes: {name}", changed(img, base))

        await ev("window.__boy.set({glue: 0})")
        flat = await shot(pg)
        await ev("window.__boy.set({glue: 0.5})")
        half = await shot(pg)
        await ev("window.__boy.set({glue: 1})")
        full = await shot(pg)
        check(
            "glue slider: flat square, piece and surface differ",
            changed(flat, half) and changed(half, full),
        )
        nopiece = await ev(
            "window.__boy.set({glue: 0.3}); window.__boy.renderNow(); tripleVerts() === null"
        )
        await ev("window.__boy.set({glue: 1})")
        check(
            "no triple point (nor membranes, nor curve) until the square is glued",
            nopiece,
        )
        await ev(
            "document.getElementById('ui').classList.remove('hidden'); window.__boy.set({glue: 0})"
        )
        await pg.click("#glue-play")
        await pg.wait_for_function("window.__boy.P.glue >= 1", timeout=60000)
        check(
            "play button glues the square up to the finished surface",
            await ev("window.__boy.P.glue") == 1,
        )
        await ev("document.getElementById('ui').classList.add('hidden')")

        bar(7, steps, "interaction: move and recentre")
        await pg.mouse.move(400, 400)
        await pg.mouse.down(button="right")
        for i in range(10):
            await pg.mouse.move(400 - 15 * (i + 1), 400 + 6 * (i + 1))
        await pg.mouse.up(button="right")
        pan = await ev("window.__boy.internals().cam.shift")
        await pg.mouse.dblclick(300, 300)
        pan0 = await ev("window.__boy.internals().cam.shift")
        check("right-drag moves the shape", pan[0] < -0.2 and pan[1] < -0.1, str(pan))
        check("double-click recentres", pan0 == [0, 0], str(pan0))

        bar(8, steps, "geometry: gluing")
        gap = await ev(
            """(() => {
              const at = (i, j) => { const v = 3 * (i * ROW + j); return [posData[v], posData[v + 1], posData[v + 2]]; };
              const dist = (a, b) => Math.hypot(a[0] - b[0], a[1] - b[1], a[2] - b[2]);
              const c = [dist(at(NR, NT / 8), at(NR, 5 * NT / 8)), dist(at(NR, 3 * NT / 8), at(NR, 7 * NT / 8))];
              const t = tripleVerts().map((v) => [posData[v], posData[v + 1], posData[v + 2]]);
              return { corners: Math.max(...c), triple: Math.max(dist(t[0], t[1]), dist(t[1], t[2]), dist(t[0], t[2])) };
            })()"""
        )
        check(
            "antipodal corners coincide", gap["corners"] < 1e-5, f"{gap['corners']:.1e}"
        )
        check(
            "triple point preimages meet (mesh resolution)",
            gap["triple"] < 0.03,
            f"{gap['triple']:.3f}",
        )

        bar(9, steps, "console")
        check("no console or page errors", not errors, "; ".join(errors[:3]))
        await br.close()
    print()


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument(
        "--chrome", help="Chrome/Chromium binary (default: playwright's chromium)"
    )
    ap.add_argument("--page", default=str(HERE.parent / "boys-surface-viewer.html"))
    a = ap.parse_args()
    asyncio.run(run(a.chrome, Path(a.page)))
    for name, ok, detail in results:
        print(
            f"  {'ok  ' if ok else 'FAIL'}  {name}"
            + (f"  ({detail})" if detail and not ok else "")
        )
    failed = sum(not ok for _, ok, _ in results)
    print(f"{len(results) - failed}/{len(results)} checks passed")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
