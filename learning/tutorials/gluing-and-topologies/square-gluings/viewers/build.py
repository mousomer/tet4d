"""Build the square-gluing viewer pages and their menu page.

Each page is src/template.html with src/surfaces.js inlined and its surface selected, so every page is a
single self-contained HTML file (no network, no build step for the reader). Run from anywhere:

    ./scripts/resolve_python_env.sh   # then: $PYTHON_BIN learning/.../viewers/build.py
"""

from __future__ import annotations

import html
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent

# id, tutorial folder, title, word, chi, orientable, cone points (with) - the menu page's table.
# tools/check_viewers.py checks these against the modules in src/surfaces.js.
PAGES = [
    (
        "sphere",
        "sphere-revised",
        "Adjacent-edge sphere",
        "a b b⁻¹ a⁻¹",
        2,
        True,
        "three cone tips",
    ),
    (
        "rp2-adjacent",
        "direct-curl",
        "Adjacent-edge projective plane",
        "a b b a⁻¹",
        1,
        False,
        "two cone tips",
    ),
    (
        "rp2-opposite",
        "opposite-rp2",
        "Opposite-edge projective plane",
        "a b a b",
        1,
        False,
        "two cone tips",
    ),
    ("torus", "opposite-torus", "Opposite-edge torus", "a b a⁻¹ b⁻¹", 0, True, None),
    (
        "klein-adjacent",
        "adjacent-klein",
        "Adjacent-edge Klein bottle",
        "a b b a",
        0,
        False,
        None,
    ),
    (
        "klein-opposite",
        "opposite-klein",
        "Opposite-edge Klein bottle",
        "a b a⁻¹ b",
        0,
        False,
        None,
    ),
    (
        "klein-bottle",
        "opposite-klein",
        "Klein bottle, the glass bottle",
        "a b a⁻¹ b",
        0,
        False,
        None,
    ),
]
NAMES = {
    (2, True): "sphere",
    (1, False): "projective plane",
    (0, True): "torus",
    (0, False): "Klein bottle",
}


def page(surface_id: str, title: str, template: str, modules: str) -> str:
    out = template.replace("/*@SURFACES@*/", modules.strip())
    out = out.replace("@SURFACE_ID@", surface_id).replace("@TITLE@", html.escape(title))
    assert "@SURFACE" not in out and "/*@" not in out, "unfilled placeholder"
    return out


def word_html(word: str) -> str:
    return html.escape(word).replace("⁻¹", "<sup>−1</sup>")


def menu() -> str:
    cards = []
    for sid, folder, title, word, chi, orientable, cones in PAGES:
        kind = NAMES[(chi, orientable)]
        cone = cones or "no cone point"
        cards.append(
            f"""<a class="card" href="{sid}.html">
  <img src="img/{sid}.webp" alt="{html.escape(title)}, glued" loading="lazy">
  <h2>{html.escape(title)}</h2>
  <p class="word">{word_html(word)}</p>
  <p>{kind} · χ = {chi} · {"orientable" if orientable else "non-orientable"} · {cone}</p>
</a>"""
        )
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Square gluings — interactive viewers</title>
<style>
*{{box-sizing:border-box}}
body{{margin:0;background:#111b2a;color:#eef2f5;font:16px/1.55 system-ui,sans-serif}}
main{{max-width:1040px;margin:auto;padding:36px clamp(16px,4vw,48px)}}
h1{{margin:0 0 6px;font-size:30px}}
header p{{margin:0 0 6px;color:#a9bfd5;max-width:760px}}
a{{color:#ffb45c}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(290px,1fr));gap:18px;margin-top:26px}}
.card{{display:block;padding:12px 12px 14px;border:1px solid #34465c;border-radius:14px;background:#172335;color:inherit;text-decoration:none;transition:border-color .15s,transform .15s}}
.card:hover{{border-color:#64e2e9;transform:translateY(-2px)}}
.card img{{display:block;width:100%;aspect-ratio:4/3;object-fit:cover;border-radius:9px;background:#cfcfd1}}
.card h2{{margin:10px 0 2px;font-size:18px}}
.card p{{margin:0;color:#a9bfd5;font-size:14px}}
.card .word{{color:#fff3df;font:15px ui-monospace,SFMono-Regular,Menlo,monospace}}
footer{{margin-top:28px;color:#a9bfd5;font-size:14px}}
</style>
</head>
<body>
<main>
<header>
<h1>Square gluings, interactive</h1>
<p>The tutorial's six gluings and the classic glass Klein bottle. Each viewer glues one square into its closed surface. Corners A–D run clockwise from the upper left; the
orange edges a close first, then the cyan edges b. Drag the Glue slider or press ▶, set the speed, step
frame by frame, rotate at any moment, and switch cone points on or off where the corners meet at less than 360°.</p>
<p>Back to the <a href="../index.html">tutorial</a>.</p>
</header>
<div class="grid">
{chr(10).join(cards)}
</div>
<footer>Built from <code>src/</code> by <code>build.py</code>; see README.md.</footer>
</main>
</body>
</html>
"""


def main() -> int:
    template = (HERE / "src" / "template.html").read_text(encoding="utf-8")
    modules = (HERE / "src" / "surfaces.js").read_text(encoding="utf-8")
    modules = modules.replace(
        'if (typeof module !== "undefined") module.exports = SURFACES;', ""
    )
    only = set(sys.argv[1:])
    for sid, _folder, title, *_ in PAGES:
        if only and sid not in only:
            continue
        out = HERE / f"{sid}.html"
        out.write_text(page(sid, title, template, modules), encoding="utf-8")
        print(f"wrote {out.relative_to(HERE)} ({out.stat().st_size // 1024} KB)")
    (HERE / "index.html").write_text(menu(), encoding="utf-8")
    print("wrote index.html")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
