"""Render the standalone learning pack with Pandoc and offline MathML.

The pack covers the directories listed in manifest.json (release.include). Files it does not copy
(archives, folders) link to GitHub at release.source_ref, a commit on the locked learning branch.

    python3 learning/build_release.py          # rebuild learning/released
    python3 learning/build_release.py --lock   # first pin release.source_ref to HEAD, then rebuild
"""

import json
import re
import shutil
import subprocess
import sys
from html import escape, unescape
from os.path import relpath
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

LEARNING = Path(__file__).resolve().parent
REPOSITORY = LEARNING.parent
MANIFEST_PATH = LEARNING / "manifest.json"
MANIFEST = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
RELEASE = LEARNING / MANIFEST["release"]["output"]
INCLUDE = MANIFEST["release"]["include"]
SOURCE_REF = MANIFEST["release"]["source_ref"]
SOURCE_URL = f"https://github.com/mousomer/tet4d/blob/{SOURCE_REF}/"
TREE_URL = f"https://github.com/mousomer/tet4d/tree/{SOURCE_REF}/"
ASSET_TYPES = {
    ".cpp",
    ".css",
    ".gif",
    ".html",
    ".jpg",
    ".js",
    ".md",
    ".png",
    ".py",
    ".svg",
    ".txt",
    ".webp",
}
# Pages copied as they are: builder templates whose links are filled in later, and very large pages.
VERBATIM = ("rebuild/templates/", "viewers/src/")
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
    if path.is_dir():  # folders (e.g. stages/) open on GitHub
        return escape(TREE_URL + path.relative_to(REPOSITORY).as_posix(), quote=True)
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
            "--mathml",
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


def release_paths():
    """Source file -> released file, for every file the pack carries."""
    paths = {
        source: RELEASE / source.relative_to(LEARNING)
        for folder in INCLUDE
        for source in sorted((LEARNING / folder).rglob("*"))
        if source.is_file()
        and source.suffix in ASSET_TYPES
        and "__pycache__" not in source.parts
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
    return paths


def lock():
    """Pin release.source_ref to HEAD (the commit the online links point at)."""
    head = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=LEARNING,
        check=True,
        stdout=subprocess.PIPE,
        text=True,
    ).stdout.strip()
    dirty = subprocess.run(
        ["git", "status", "--porcelain", "--", *INCLUDE],
        cwd=LEARNING,
        check=True,
        stdout=subprocess.PIPE,
        text=True,
    ).stdout
    if dirty.strip():
        raise SystemExit(
            "Commit the included folders first: the release links to the commit it is built from."
        )
    MANIFEST["release"]["source_ref"] = head
    MANIFEST_PATH.write_text(
        json.dumps(MANIFEST, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return head


def build():
    if not shutil.which("pandoc"):
        raise SystemExit("Pandoc is required to rebuild learning/released.")
    if SOURCE_REF == "PENDING":
        raise SystemExit(
            "manifest.json has no release.source_ref yet: run with --lock."
        )
    paths = release_paths()
    if RELEASE.exists():  # stale files from earlier builds would otherwise linger
        shutil.rmtree(RELEASE)
    RELEASE.mkdir()
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
        elif source.suffix == ".html" and not any(
            v in source.as_posix() for v in VERBATIM
        ):
            html = source.read_text(encoding="utf-8")
            destination.write_text(
                rewrite_links(html, source, destination, paths), encoding="utf-8"
            )
        else:
            shutil.copyfile(source, destination)


if __name__ == "__main__":
    if "--lock" in sys.argv[1:]:
        SOURCE_REF = lock()
        SOURCE_URL = f"https://github.com/mousomer/tet4d/blob/{SOURCE_REF}/"
        TREE_URL = f"https://github.com/mousomer/tet4d/tree/{SOURCE_REF}/"
    build()
