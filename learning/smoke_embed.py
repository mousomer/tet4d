"""Test an embed from a different local origin with Playwright and Chromium."""

from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from shutil import which
from threading import Thread

from playwright.sync_api import expect, sync_playwright


class HostPage(SimpleHTTPRequestHandler):
    asset_origin = ""

    def do_GET(self):
        script = f"{self.asset_origin}/tet4d-learning.js"
        html = f"""<!doctype html><title>External Tet4D embed test</title>
<script src="{script}" defer></script>
<body><script src="{script}" data-view="domino" data-height="900" defer></script></body>"""
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(html.encode())


def run():
    release = Path(__file__).resolve().parent / "released"
    assets_handler = partial(SimpleHTTPRequestHandler, directory=release)
    with (
        ThreadingHTTPServer(("127.0.0.1", 0), assets_handler) as assets,
        ThreadingHTTPServer(("127.0.0.1", 0), HostPage) as host,
    ):
        HostPage.asset_origin = f"http://127.0.0.1:{assets.server_port}"
        servers = (assets, host)
        for server in servers:
            Thread(target=server.serve_forever, daemon=True).start()
        try:
            check_frames(f"http://127.0.0.1:{host.server_port}/")
        finally:
            for server in servers:
                server.shutdown()


def check_frames(host_url):
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            executable_path=which("chromium") or which("chromium-browser")
        )
        page = browser.new_page()
        page.goto(host_url)
        home = page.frame_locator('iframe[title="Tet4D Learning"]')
        expect(
            home.get_by_role("heading", name="Tet4D Learning", exact=True)
        ).to_be_visible()
        home.get_by_role("link", name="Lesson 03", exact=False).click()
        expect(home.get_by_role("heading", level=1)).to_contain_text(
            "come home mirrored"
        )
        selector = 'iframe[title="Tet4D Lesson 03 · Domino tutorial"]'
        expect(page.locator(selector)).to_have_attribute("height", "900")
        domino = page.frame_locator(selector)
        domino.locator("#domino-playground").press("ArrowLeft")
        expect(domino.locator("#sequence-cells-a")).to_have_text(
            "1 at (1, 0) · 2 at (0, 1)"
        )
        browser.close()
    print("Both Tet4D views work from a separate host page.")


if __name__ == "__main__":
    run()
