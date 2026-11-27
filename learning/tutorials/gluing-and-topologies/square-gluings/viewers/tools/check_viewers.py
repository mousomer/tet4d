"""Browser checks for the square-gluing viewers and their menu page.

Runs every page headless (SwiftShader) and checks, per page:
  page      loads with WebGL2, renders, no page errors; title, word and cone switch match build.py
  seams     the module's two seams close exactly at the end of the run (max gap over 1001 points
            per seam, with and without cone points) and the flat square is flat at the start
  stages    two-stage motion: seam a closes before seam b, and once closed a seam stays closed
  start/end glue 0 is a disk (4 corners, chi 1); glue 1 is the expected closed surface - corner
            classes, chi, orientability - in both motions and both cone settings
  render    edges and arrows paint pixels; the glued surface differs from the flat square
  controls  play runs and stops at 1, the duration sets the speed, step buttons step, link
            parameters (?glue, ?motion, ?cones) are read, the cone switch is disabled without cones
  menu      index.html links every page and their thumbnails exist

Usage: python tools/check_viewers.py [--chrome /usr/bin/google-chrome] [--only torus,sphere]
Requires playwright and pillow. Exit status 1 if any check fails.
"""

import argparse
import asyncio
import importlib.util
import io
import re
import time
from pathlib import Path

from PIL import Image, ImageChops
from playwright.async_api import async_playwright

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
ARGS = [
    "--use-angle=swiftshader",
    "--enable-unsafe-swiftshader",
    "--ignore-gpu-blocklist",
]
READY = "window.__glue !== undefined && window.__glue.stats.frameCount > 0"
FINAL_CLASSES = {  # corner classes of the glued square (the tutorial's angle sums: 90 degrees per corner)
    "sphere": ["A", "BD", "C"],
    "rp2-adjacent": ["A", "BCD"],
    "rp2-opposite": ["AC", "BD"],
    "torus": ["ABCD"],
    "klein-adjacent": ["ABCD"],
    "klein-opposite": ["ABCD"],
    "klein-bottle": ["ABCD"],
}

spec = importlib.util.spec_from_file_location("build", ROOT / "build.py")
build = importlib.util.module_from_spec(spec)
spec.loader.exec_module(build)
PAGES = {p[0]: p for p in build.PAGES}

results = []


def check(name, ok, detail=""):
    results.append((name, bool(ok), detail))
    mark = "ok  " if ok else "FAIL"
    print(f"  {mark} {name}{' - ' + detail if detail else ''}", flush=True)


def bar(i, n, label):
    k = int(24 * i / n)
    print(f"[{'#' * k}{'.' * (24 - k)}] {i}/{n} {label}", flush=True)


SEAM_JS = """
(() => {
  const M = window.__glue.SURFACE, SIDE = {
    top: (p) => [-1 + 2 * p, 1], right: (p) => [1, 1 - 2 * p], bottom: (p) => [1 - 2 * p, -1], left: (p) => [-1, -1 + 2 * p] };
  const out = {};
  for (const cone of M.hasCones ? [1, 0] : [1]) {
    const s = M.params(M.span[1]);
    let worst = 0, size = 0;
    for (const pair of ["a", "b"]) {
      const [s1, s2] = Object.keys(M.sides).filter((k) => M.sides[k][0] === pair);
      for (let i = 0; i <= 1000; i++) {
        const f = i / 1000, p1 = M.sides[s1][1] > 0 ? f : 1 - f, p2 = M.sides[s2][1] > 0 ? f : 1 - f;
        const a = M.point(...SIDE[s1](p1), s, cone), b = M.point(...SIDE[s2](p2), s, cone);
        worst = Math.max(worst, Math.hypot(a[0] - b[0], a[1] - b[1], a[2] - b[2]));
        size = Math.max(size, Math.hypot(...a));
      }
    }
    let flat = 0;
    const s0 = M.params(M.span[0]);
    for (let i = 0; i <= 20; i++) for (let j = 0; j <= 20; j++) flat = Math.max(flat, Math.abs(M.point(-1 + i / 10, -1 + j / 10, s0, cone)[2]));
    out[cone] = { rel: worst / size, flat };
  }
  return out;
})()
"""


async def bg_shot(
    pg,
):  # the scene without the surface (moved far away), for the square's pixel area
    await pg.evaluate("__glue.pose({panX: 5}); __glue.renderNow()")
    img = await shot(pg)
    await pg.evaluate("__glue.pose({panX: 0}); __glue.renderNow()")
    return img


async def shot(pg):
    return Image.open(io.BytesIO(await pg.screenshot())).convert("RGB")


def colour_pixels(img, rgb, tol=40):
    r, g, b = rgb
    px = img.getdata()
    return sum(
        1
        for p in px
        if abs(p[0] - r) < tol and abs(p[1] - g) < tol and abs(p[2] - b) < tol
    )


async def check_page(br, sid):
    _, _folder, title, word, chi, orientable, cones = PAGES[sid]
    url = (ROOT / f"{sid}.html").resolve().as_uri()
    pg = await br.new_page(viewport={"width": 720, "height": 560})
    errors = []
    pg.on("pageerror", lambda e: errors.append(str(e)))
    await pg.goto(url + "?play=0&glue=0")
    await pg.wait_for_function(READY, timeout=120000)
    meta = await pg.evaluate(
        "({title: __glue.SURFACE.title, word: __glue.SURFACE.word, cones: __glue.SURFACE.hasCones,"
        " floatRT: __glue.stats.floatRT, disabled: document.getElementById('cones').disabled})"
    )
    check(
        f"{sid}: page title and word match build.py",
        meta["title"] == title and meta["word"] == word,
        f"{meta['title']} / {meta['word']}",
    )
    check(
        f"{sid}: cone switch {'enabled' if cones else 'disabled'}",
        meta["cones"] == bool(cones) and meta["disabled"] == (not cones),
    )

    seams = await pg.evaluate(SEAM_JS)
    for cone, r in seams.items():
        check(
            f"{sid}: seams close exactly (cones={cone})",
            r["rel"] < 1e-6,
            f"max gap / size {r['rel']:.1e}",
        )
        check(
            f"{sid}: flat square at the start (cones={cone})",
            r["flat"] < 1e-9,
            f"max |z| {r['flat']:.1e}",
        )

    # two-stage order on 61 slider values
    first, ok_mono, prev = [None, None], True, [False, False]
    for k in range(61):
        g = k / 60
        st = await pg.evaluate(
            f"__glue.set({{glue: {g}}}); __glue.renderNow(); __glue.stats"
        )
        for n in (0, 1):
            if st["closed"][n] and first[n] is None:
                first[n] = g
            if prev[n] and not st["closed"][n]:
                ok_mono = False
        prev = st["closed"]
    check(
        f"{sid}: seam a closes before seam b",
        first[0] is not None and first[1] is not None and first[0] < first[1],
        f"a at {first[0]}, b at {first[1]}",
    )
    check(f"{sid}: a closed seam stays closed", ok_mono)

    expect_name = build.NAMES[(chi, orientable)]
    for motion in ("stages", "stretch"):
        for cone in [True, False] if cones else [True]:
            st0 = await pg.evaluate(
                f"__glue.set({{motion: '{motion}', cones: {str(cone).lower()}, glue: 0}}); __glue.renderNow(); __glue.stats"
            )
            t0 = st0["topology"]
            check(
                f"{sid}: {motion}, cones={cone}: flat square is a disk",
                t0["name"] == "disk" and t0["chi"] == 1 and len(st0["classes"]) == 4,
            )
            st = await pg.evaluate(
                "__glue.set({glue: 1}); __glue.renderNow(); __glue.stats"
            )
            t = st["topology"]
            ok = (
                sorted(st["classes"]) == FINAL_CLASSES[sid]
                and t["chi"] == chi
                and t["orientable"] == orientable
                and t["circles"] == 0
                and t["name"] == expect_name
                and all(st["closed"])
            )
            check(
                f"{sid}: {motion}, cones={cone}: glued square is the {expect_name}",
                ok,
                f"classes {sorted(st['classes'])}, chi {t['chi']}, {'orientable' if t['orientable'] else 'non-orientable'}, {st['buildMs']:.0f} ms/build",
            )
    await pg.evaluate("__glue.set({motion: 'stages', cones: true})")

    # rendering: edges and arrows paint; the glued surface differs from the flat square
    await pg.evaluate(
        "document.getElementById('ui').style.display = 'none'; document.getElementById('labels').style.display = 'none'"
    )
    await pg.evaluate(
        "__glue.set({glue: 0, edges: true, arrows: true}); __glue.renderNow()"
    )
    flat_on = await shot(pg)
    await pg.evaluate("__glue.set({edges: false, arrows: false}); __glue.renderNow()")
    flat_off = await shot(pg)
    diff = sum(
        1
        for p in ImageChops.difference(flat_on, flat_off).convert("L").getdata()
        if p > 30
    )
    square = sum(
        1
        for p in ImageChops.difference(flat_off, await bg_shot(pg))
        .convert("L")
        .getdata()
        if p > 30
    )
    check(
        f"{sid}: edges and arrows paint the flat square",
        diff > 0.08 * square,
        f"{diff} px changed, square covers {square} px",
    )
    orange = colour_pixels(flat_on, (225, 150, 70), 45)
    check(f"{sid}: orange edge a visible", orange > 150, f"{orange} px")
    await pg.evaluate(
        "__glue.set({glue: 1, edges: true, arrows: true}); __glue.renderNow()"
    )
    glued = await shot(pg)
    diff = sum(
        1
        for p in ImageChops.difference(flat_on, glued).convert("L").getdata()
        if p > 30
    )
    check(
        f"{sid}: glued surface differs from the flat square",
        diff > 20000,
        f"{diff} px changed",
    )

    # controls
    await pg.evaluate("document.getElementById('ui').style.display = ''")
    await pg.evaluate("__glue.set({glue: 0, dur: 3}); __glue.play(true)")
    t_start = time.time()
    await pg.wait_for_timeout(1200)
    mid = await pg.evaluate("__glue.P.glue")
    await pg.wait_for_function("!__glue.stats.playing", timeout=20000)
    took = time.time() - t_start
    end = await pg.evaluate("__glue.P.glue")
    check(
        f"{sid}: play runs at the set duration and stops at 1",
        0.1 < mid < 0.9 and end == 1 and 2.0 < took < 8.0,
        f"glue {mid:.2f} after 1.2 s, done in {took:.1f} s (duration 3 s)",
    )
    await pg.evaluate("__glue.set({glue: 0.5, stepS: 0.02})")
    await pg.click("#fwd")
    g1 = await pg.evaluate("__glue.P.glue")
    await pg.click("#back")
    await pg.click("#back")
    g2 = await pg.evaluate("__glue.P.glue")
    check(
        f"{sid}: step buttons step by the set size",
        abs(g1 - 0.52) < 1e-9 and abs(g2 - 0.48) < 1e-9,
        f"{g1:.3f}, {g2:.3f}",
    )
    check(f"{sid}: no page errors", not errors, "; ".join(errors[:3]))
    await pg.close()

    pg = await br.new_page(viewport={"width": 480, "height": 360})
    await pg.goto(url + "?glue=0.4&motion=stretch&cones=0")
    await pg.wait_for_function(READY, timeout=120000)
    P = await pg.evaluate(
        "({glue: __glue.P.glue, motion: __glue.P.motion, cones: __glue.P.cones, playing: __glue.stats.playing})"
    )
    check(
        f"{sid}: link parameters are read",
        P == {"glue": 0.4, "motion": "stretch", "cones": False, "playing": False},
        str(P),
    )
    await pg.close()


def check_menu():
    html = (ROOT / "index.html").read_text(encoding="utf-8")
    links = re.findall(r'href="([a-z0-9-]+)\.html"', html)
    check("menu: links every page", sorted(links) == sorted(PAGES), ", ".join(links))
    missing = [
        s
        for s in PAGES
        if not (ROOT / f"{s}.html").exists()
        or not (ROOT / "img" / f"{s}.webp").exists()
    ]
    check("menu: pages and thumbnails exist", not missing, ", ".join(missing))


async def main(chrome, only):
    ids = [s for s in PAGES if not only or s in only]
    async with async_playwright() as p:
        kw = {"headless": True, "args": ARGS}
        if chrome:
            kw["executable_path"] = chrome
        br = await p.chromium.launch(**kw)
        for i, sid in enumerate(ids):
            bar(i, len(ids) + 1, sid)
            await check_page(br, sid)
        await br.close()
    bar(len(ids), len(ids) + 1, "menu")
    check_menu()
    bar(len(ids) + 1, len(ids) + 1, "done")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--chrome")
    ap.add_argument("--only", default="")
    a = ap.parse_args()
    asyncio.run(main(a.chrome, set(filter(None, a.only.split(",")))))
    failed = [r for r in results if not r[1]]
    print(f"\n{len(results) - len(failed)}/{len(results)} checks passed")
    raise SystemExit(1 if failed else 0)
