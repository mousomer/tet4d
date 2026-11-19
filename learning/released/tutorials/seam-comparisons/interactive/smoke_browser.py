"""Run with Python Playwright and Chromium installed."""

from pathlib import Path
from shutil import which

from playwright.sync_api import sync_playwright


def check_controls_and_bonds(page):
    compare = page.locator("#compare-right")
    back = page.locator("#compare-left")
    positions = [page.locator(f"#position-{board}") for board in "abc"]
    assert back.is_disabled()
    compare.click()
    assert [position.inner_text() for position in positions] == [
        "(1, 4)",
        "(1, 4)",
        "(0, 3)",
    ]
    page.keyboard.press("Enter")
    assert [position.inner_text() for position in positions] == [
        "(0, 4)",
        "(0, 4)",
        "(4, 1) · Home",
    ]
    page.get_by_role("button", name="Reset comparison").click()
    assert all(position.inner_text() == "(4, 1)" for position in positions)

    bond_pixels = """() => {
        const ctx = document.querySelector('#domino-board').getContext('2d');
        return [[652, 490], [88, 250]].map(([x, y]) =>
            [...ctx.getImageData(x, y, 1, 1).data]);
    }"""
    gold = [255, 209, 122, 255]
    assert page.evaluate(bond_pixels) == [gold, gold]
    page.locator("#domino-up").click()
    assert page.locator("#domino-position").inner_text() == "1 at (4, 2) · 2 at (0, 4)"
    assert "Bond broken" in page.locator("#domino-status").inner_text()
    assert all(pixel != gold for pixel in page.evaluate(bond_pixels))
    page.get_by_role("button", name="Reset domino").click()
    assert page.evaluate(bond_pixels) == [gold, gold]
    assert page.locator("#domino-position").inner_text() == "1 at (4, 1) · 2 at (0, 3)"


def check_domino_sequences(page, trace_path):
    expected = {}
    for row in trace_path.read_text().splitlines():
        code, trace_board, index, ax, ay, bx, by, bond = row.split()
        board = "acb"[int(trace_board)]
        expected[code, board, int(index)] = (
            f"1 at ({ax}, {ay}) · 2 at ({bx}, {by})",
            bond == "1",
        )

    picker = page.get_by_label("Sequence", exact=True)
    next_move = page.get_by_role("button", name="Next move")
    previous = page.get_by_role("button", name="Previous move")
    reset = page.get_by_role("button", name="Reset sequence")
    assert set(
        picker.locator("option").evaluate_all("(options) => options.map(o => o.value)")
    ) == {code for code, _, _ in expected} | {"free"}
    for code in ("LUR", "LTR", "LR", "LUL", "LDLRL"):
        picker.select_option(code)
        assert previous.is_disabled()
        for index in range(len(code) + 1):
            if index:
                next_move.click()
            for board in "abc":
                cells, bonded = (
                    expected[code, board, index]
                    if index
                    else ("1 at (0, 1) · 2 at (1, 1)", True)
                )
                assert page.locator(f"#sequence-cells-{board}").inner_text() == cells
                indicator = page.locator(f"#sequence-bond-{board}")
                assert indicator.get_attribute("data-bonded") == str(bonded).lower()
                gold_visible = page.locator(f"#sequence-board-{board}").evaluate(
                    """canvas => {
                        const data = canvas.getContext('2d')
                            .getImageData(0, 0, canvas.width, canvas.height).data;
                        for (let i = 0; i < data.length; i += 4) {
                            if (data[i] === 255 && data[i+1] === 209
                                && data[i+2] === 122) {
                                return true;
                            }
                        }
                        return false;
                    }"""
                )
                assert gold_visible == bonded
        assert next_move.is_disabled()
        if code == "LUL":
            assert page.locator("#sequence-bond-b").inner_text() == "Bond rejoined"
        previous.click()
        assert (
            f"Move {len(code) - 1} of {len(code)}"
            in page.locator("#sequence-progress").inner_text()
        )

    reset.click()
    assert previous.is_disabled() and reset.is_disabled()


def check_free_domino(page):
    picker = page.get_by_label("Sequence", exact=True)

    def move(key):
        page.keyboard.press(key)

    positions = [page.locator(f"#sequence-cells-{board}") for board in "abc"]
    start = "1 at (0, 1) · 2 at (1, 1)"
    assert page.evaluate("document.activeElement.id") == "domino-playground"
    assert picker.input_value() == "free"
    assert page.locator("[data-domino-direction]:visible").count() == 4
    assert not page.get_by_role("button", name="Next move").is_visible()
    assert all(position.inner_text() == start for position in positions)
    move("ArrowLeft")
    move("ArrowUp")
    assert page.locator("#sequence-bond-b").inner_text() == "Bond broken"
    move("ArrowLeft")
    assert page.locator("#sequence-bond-b").inner_text() == "Bond rejoined"
    reset = page.get_by_role("button", name="Reset free movement")
    reset.click()
    move("ArrowDown")
    before = [position.inner_text() for position in positions]
    move("ArrowLeft")
    assert "A blocked" in page.locator("#sequence-progress").inner_text()
    assert positions[0].inner_text() == before[0]
    assert positions[2].inner_text() != before[2]
    page.locator('[data-domino-direction="R"]').click()
    move("ArrowRight")
    reset.click()
    assert reset.is_disabled()
    assert all(position.inner_text() == start for position in positions)
    picker.select_option("LR")
    assert page.get_by_role("button", name="Next move").is_visible()
    assert page.locator("[data-domino-direction]:visible").count() == 0
    page.locator("#domino-playground").focus()
    move("ArrowLeft")
    assert all(position.inner_text() == start for position in positions)
    picker.select_option("free")
    picker.focus()
    move("ArrowDown")
    assert all(position.inner_text() == start for position in positions)
    picker.select_option("free")
    assert page.locator("[data-domino-direction]:visible").count() == 4


def check_benchmark(page):
    metric = page.get_by_label("Benchmark outcome")
    counts = page.locator("#benchmark-counts tr td:first-of-type")
    for index, expected in enumerate(
        (
            ["28/32", "32/32", "0/32"],
            ["40/496", "20/496", "0/496"],
            ["476/1,824", "462/1,904", "0/1,984"],
            ["816/1,824", "912/1,904", "840/1,984"],
        )
    ):
        metric.select_option(index=index)
        assert counts.all_text_contents() == expected

    next_stage = page.get_by_role("button", name="Next stage")
    previous = page.get_by_role("button", name="Previous stage")
    reset = page.get_by_role("button", name="Reset example")
    source = page.locator("#benchmark-source-cells")
    target = page.locator("#benchmark-target-cells")
    status = page.locator("#benchmark-status")
    initial = source.inner_text()
    next_stage.click()
    assert "1 at (1, 0)" in target.inner_text() and "4 at (1, 0)" in target.inner_text()
    next_stage.click()
    assert source.inner_text() == target.inner_text() == initial
    assert "Blocked" in status.inner_text() and next_stage.is_disabled()
    previous.click()
    assert "Proposed arrivals" == page.locator("#benchmark-target-title").inner_text()

    page.get_by_label("Example", exact=True).select_option("loss")
    assert previous.is_disabled() and "Stage 1 of 3" in status.inner_text()
    next_stage.click()
    assert "1 at (7, 6)" in target.inner_text() and "4 at (0, 1)" in target.inner_text()
    pixel = (
        """canvas => [...canvas.getContext('2d').getImageData(668, 183, 1, 1).data]"""
    )
    gold = [255, 209, 122, 255]
    assert page.locator("#benchmark-target").evaluate(pixel) == gold
    next_stage.click()
    assert (
        target.inner_text() == "1 at (7, 7) · 2 at (7, 6) · 3 at (7, 5) · 4 at (0, 2)"
    )
    assert (
        "Up succeeds" in status.inner_text()
        and "no longer share" in status.inner_text()
    )
    assert page.locator("#benchmark-source").evaluate(pixel) == gold
    assert page.locator("#benchmark-target").evaluate(pixel) != gold
    reset.click()
    assert previous.is_disabled() and "Stage 1 of 3" in status.inner_text()


def run():
    demo = Path(__file__).resolve().with_name("index.html")
    positions = [(0, 2), (2, 0), (1, 0), (0, 0), (0, 1)]
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            executable_path=which("chromium") or which("chromium-browser")
        )
        page = browser.new_page(
            viewport={"width": 1100, "height": 840},
            reduced_motion="reduce",
            offline=True,
        )
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.goto(demo.as_uri() + "#controls-and-bonds")
        check_benchmark(page)
        check_controls_and_bonds(page)
        page.goto(demo.as_uri() + "#domino-sequences")
        page.reload()
        check_free_domino(page)
        check_domino_sequences(
            page, demo.parent.parent / "domino-comparisons" / "native_traces.txt"
        )
        previous = page.get_by_role("button", name="Previous step")
        next_step = page.get_by_role("button", name="Next step")
        reset = page.get_by_role("button", name="Reset", exact=True)
        for step in range(11):
            if step:
                next_step.click()
            if step == 0:
                frame_a = "Red right, blue up"
            elif step <= 5:
                frame_a = "Red down, blue right"
            else:
                frame_a = "Red left, blue down"
            frame_b = "Red down, blue left" if 1 <= step <= 5 else "Red right, blue up"
            for board, frame in (("a", frame_a), ("b", frame_b)):
                assert page.locator(f"#frame-{board}").inner_text() == (
                    f"{positions[step % 5]} · {frame}"
                )

        assert next_step.is_disabled()
        previous.click()
        assert "Step 4 of 5" in page.locator("#progress").inner_text()
        reset.click()
        assert previous.is_disabled() and reset.is_disabled()
        for width in (375, 320):
            page.set_viewport_size({"width": width, "height": 780})
            left, right = [
                page.locator(f"#board-{board}").bounding_box() for board in "ab"
            ]
            assert left["y"] == right["y"] and left["x"] + left["width"] < right["x"]
            assert page.evaluate("document.documentElement.scrollWidth") == width
            a, b, c = [
                page.locator(f"#compare-{board}").bounding_box() for board in "abc"
            ]
            assert a["y"] == b["y"] == c["y"] and a["x"] < b["x"] < c["x"]

        next_step.focus()
        page.keyboard.press("Enter")
        assert "crossing" in page.locator("#progress").inner_text()
        reset.click()
        page.emulate_media(reduced_motion="no-preference")
        page.clock.install()
        next_step.click()
        image = "() => document.querySelector('#board-b').toDataURL()"
        page.clock.run_for(160)
        departure = page.evaluate(image)
        page.clock.run_for(430)
        arrival = page.evaluate(image)
        page.clock.run_for(500)
        assert len({departure, arrival, page.evaluate(image)}) == 3
        assert not errors, errors
        browser.close()
    print("Lesson 03 browser smoke test passed.")


if __name__ == "__main__":
    run()
