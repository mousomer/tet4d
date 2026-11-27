"""Render the standalone learning pack with Pandoc and offline MathML."""

import re
import shutil
import subprocess
from html import escape, unescape
from os.path import relpath
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

LEARNING = Path(__file__).resolve().parent
REPOSITORY = LEARNING.parent
RELEASE = LEARNING / "released"
SOURCE_REF = "ef98d1100ddd53bb07ac15872a982ac0f864ef81"
SOURCE_URL = f"https://github.com/mousomer/tet4d/blob/{SOURCE_REF}/"
ASSET_TYPES = {".cpp", ".css", ".gif", ".html", ".js", ".md", ".py", ".svg", ".txt"}
ATTRIBUTE = re.compile(r'(?P<attribute>\b(?:href|src)=")(?P<target>[^"]*)')
FIXTURE = REPOSITORY / "tests/fixtures/explorer_topology/transport_v1.json"


def target_for(source, destination, reference, paths):
    url = urlsplit(unescape(reference))
    if url.scheme or url.netloc or not url.path:
        return reference
    path = (source.parent / url.path).resolve()
    if path in paths:
        local = Path(relpath(paths[path], destination.parent)).as_posix()
        return escape(urlunsplit(("", "", local, url.query, url.fragment)), quote=True)
    if not path.is_file():
        raise FileNotFoundError(f"{source.name}: missing asset {reference}")
    online = SOURCE_URL + path.relative_to(REPOSITORY).as_posix()
    if url.fragment:
        online += f"#{url.fragment}"
    return escape(online, quote=True)


def rewrite_links(content, source, destination, paths):
    def replace(match):
        target = target_for(source, destination, match["target"], paths)
        return match["attribute"] + target

    return ATTRIBUTE.sub(replace, content)


def page(title, body, root):
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escape(title)} · Tet4D Learning</title>
  <link rel="stylesheet" href="{root}release.css">
</head>
<body>
  <header class="site-header"><a href="{root}index.html">Tet4D Learning</a></header>
  <main>{body}</main>
</body>
</html>
"""


def render_markdown(source):
    # GitHub-style heading identifiers preserve links between the lesson sources.
    rendered = subprocess.run(
        [
            "pandoc",
            "--from=markdown+gfm_auto_identifiers",
            "--to=html5",
            "--math-method=mathml",
            "--fail-if-warnings",
            f"--lua-filter={LEARNING / 'display_equations.lua'}",
            str(source),
        ],
        check=True,
        stdout=subprocess.PIPE,
        text=True,
    ).stdout

    if re.search(r'<pre class="math(?: |")', rendered):
        raise ValueError(f"{source.name}: a fenced equation was rendered as code")
    return rendered


def build():
    if not shutil.which("pandoc"):
        raise SystemExit("Pandoc is required to rebuild learning/released.")
    paths = {
        source: RELEASE / source.relative_to(LEARNING)
        for source in sorted((LEARNING / "tutorials").rglob("*"))
        if source.is_file() and source.suffix in ASSET_TYPES
    }
    paths.update(
        {
            source: destination.with_suffix(".html")
            for source, destination in paths.items()
            if source.suffix == ".md"
        }
    )
    # Release test sources as readable files without collecting a second test suite.
    paths.update(
        {
            source: destination.with_suffix(".py.txt")
            for source, destination in paths.items()
            if source.match("test_*.py")
        }
    )
    paths[FIXTURE] = RELEASE / "references" / FIXTURE.name

    RELEASE.mkdir(exist_ok=True)
    shutil.copyfile(LEARNING / "release.css", RELEASE / "release.css")
    shutil.copyfile(LEARNING / "tet4d-learning.js", RELEASE / "tet4d-learning.js")
    (RELEASE / "embed.html").write_text(
        page(
            "Embed", (LEARNING / "release_embed.html").read_text(encoding="utf-8"), ""
        ),
        encoding="utf-8",
    )
    (RELEASE / "index.html").write_text(
        page("Home", (LEARNING / "release_home.html").read_text(encoding="utf-8"), ""),
        encoding="utf-8",
    )
    for source, destination in paths.items():
        destination.parent.mkdir(parents=True, exist_ok=True)
        if source.suffix == ".md":
            title = (
                source.read_text(encoding="utf-8").splitlines()[0].lstrip("# ").strip()
            )
            body = rewrite_links(render_markdown(source), source, destination, paths)
            root = "../" * len(destination.parent.relative_to(RELEASE).parts)
            destination.write_text(page(title, body, root), encoding="utf-8")
        elif source.suffix == ".html":
            html = source.read_text(encoding="utf-8")
            destination.write_text(
                rewrite_links(html, source, destination, paths), encoding="utf-8"
            )
        else:
            shutil.copyfile(source, destination)


if __name__ == "__main__":
    build()
