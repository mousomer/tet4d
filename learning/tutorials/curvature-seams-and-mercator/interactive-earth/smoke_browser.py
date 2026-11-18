"""Optional browser smoke test; requires Playwright and Chromium.

Reads the same local HTML/CSS/JS assets as the offline demo and injects them
into a browser document; requires no localhost server or network access.
"""
from pathlib import Path
from shutil import which


def run():
    from playwright.sync_api import sync_playwright

    root = Path(__file__).resolve().parent
    html = (root / "index.html").read_text(encoding="utf-8")
    css = (root / "styles.css").read_text(encoding="utf-8")
    mask = (root / "gshhg_landmask.generated.js").read_text(encoding="utf-8")
    js = (root / "earth_s2.js").read_text(encoding="utf-8")
    html = html.replace('<link rel="stylesheet" href="styles.css">', f"<style>{css}</style>")
    html = html.replace('<script src="gshhg_landmask.generated.js"></script>', f"<script>{mask}</script>")
    html = html.replace('<script src="earth_s2.js"></script>', f"<script>{js}</script>")

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True, executable_path=which("chromium") or which("chromium-browser") or None,
            args=["--no-sandbox"],
        )
        page = browser.new_page(viewport={"width": 1280, "height": 850})
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.set_content(html, wait_until="load")
        page.locator("#world").wait_for()
        seam_errors = page.evaluate("""() => {
            const f = window.TET4D_EARTH_S2_DIAGNOSTICS.squarePoint;
            const dist = (a,b) => Math.hypot(...a.map((x,i) => x-b[i]));
            return [0,.1,.3,.5,.8,1].map(t =>
                [dist(f(0,t),f(t,0)),dist(f(1,t),f(t,1))]);
        }""")
        assert all(max(pair) < 1e-8 for pair in seam_errors), seam_errors

        pixel = "() => [...document.querySelector('#world').getContext('2d').getImageData(160,100,1,1).data]"
        before = page.evaluate(pixel)
        rect = page.locator("#world").bounding_box()
        assert rect is not None
        page.mouse.move(rect["x"] + 170, rect["y"] + 260)
        page.mouse.down()
        page.mouse.move(rect["x"] + 280, rect["y"] + 190, steps=12)
        page.mouse.up()
        page.wait_for_timeout(400)
        assert page.evaluate(pixel) != before, "drag did not change the map"
        page.get_by_text("Hide graticule").click()
        assert page.get_by_text("Show graticule").is_visible()
        page.get_by_text("Reset globe").click()
        page.wait_for_timeout(100)
        assert not errors, errors
        browser.close()
    print("Interactive Earth smoke test passed.")


if __name__ == "__main__":
    run()
