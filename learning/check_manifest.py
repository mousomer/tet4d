"""Check learning/manifest.json against the branch, the docs and the offline edition.

Checks:
  branch     the current branch is the locked learning branch, and its base commit is an ancestor
  components every path, entry page, generator, doc and check listed in the manifest exists; each
             component's entry page is linked from learning/README.md and from the release home page;
             INDEX.md is what build_index.py writes from the manifest
  docs       every relative link (site-absolute example paths such as /tet4d-learning/ are skipped) in the Markdown and HTML sources resolves to an existing file
  release    the offline edition holds exactly the files build_release.py would write; its local links
             resolve; its GitHub links point at files that exist at release.source_ref, an ancestor of HEAD

Usage: python3 learning/check_manifest.py [--any-branch]
Exit status 1 if any check fails.
"""

import json
import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import unquote, urlsplit

LEARNING = Path(__file__).resolve().parent
sys.path.insert(0, str(LEARNING))
import build_release  # reads the same manifest

MANIFEST = json.loads((LEARNING / "manifest.json").read_text(encoding="utf-8"))
LINK = re.compile(r'(?:\]\(|(?:href|src)=")([^)"\s]+)')
# Sources whose links are filled in by a builder, so they only resolve in the built page.
TEMPLATES = (
    "released/",
    "viewers/src/",
    "rebuild/templates/",
    "release_home.html",
    "release_embed.html",
)
results = []


def check(name, ok, detail=""):
    results.append(bool(ok))
    print(
        f"  {'ok  ' if ok else 'FAIL'} {name}{' - ' + detail if detail else ''}",
        flush=True,
    )


def step(i, n, label):
    k = int(24 * i / n)
    print(f"[{'#' * k}{'.' * (24 - k)}] {i}/{n} {label}", flush=True)


def git(*args):
    return subprocess.run(
        ["git", *args], cwd=LEARNING, capture_output=True, text=True, check=False
    )


def links(path):
    text = path.read_text(encoding="utf-8", errors="replace")
    for m in LINK.finditer(text):
        yield m.group(1)


def local_target(page, ref):
    u = urlsplit(ref)
    if (
        u.scheme
        or u.netloc
        or not u.path
        or u.path.startswith(("#", "/", "data:", "mailto:"))
        or "{" in u.path
    ):
        return None
    return (page.parent / unquote(u.path)).resolve()


def check_branch(any_branch):
    b = MANIFEST["branch"]
    current = git("branch", "--show-current").stdout.strip()
    check("branch is locked", b.get("locked") is True, b["name"])
    allowed = [b["name"], *b.get("work_branches", [])]
    check(
        "on the learning branch or one of its work branches",
        any_branch or current in allowed,
        f"current {current or '(detached)'}, allowed {', '.join(allowed)}",
    )
    check(
        "branch base is an ancestor of HEAD",
        git("merge-base", "--is-ancestor", b["base"], "HEAD").returncode == 0,
        b["base"],
    )


def check_components():
    # README.md lists the tutorials through tutorials/README.md, whose links are relative to tutorials/
    readme = (LEARNING / "README.md").read_text(encoding="utf-8")
    readme += re.sub(
        r"\]\((?!http)",
        "](tutorials/",
        (LEARNING / "tutorials" / "README.md").read_text(encoding="utf-8"),
    )
    home = (LEARNING / "release_home.html").read_text(encoding="utf-8")
    for c in MANIFEST["components"]:
        listed = [c["path"], c["entry"], *c["generators"], *c["docs"], *c["checks"]]
        missing = [p for p in listed if not (LEARNING / p).exists()]
        check(f"{c['id']}: listed files exist", not missing, ", ".join(missing))
        if c["kind"] == "release":
            continue
        entry = c["entry"]
        released = (
            str(Path(entry).with_suffix(".html")) if entry.endswith(".md") else entry
        )
        in_readme = entry in readme or c["path"] in readme
        in_home = released in home or str(Path(released).parent) + "/" in home
        check(
            f"{c['id']}: linked from README.md and the release home",
            in_readme and in_home,
        )
    index = subprocess.run(
        [sys.executable, str(LEARNING / "build_index.py"), "--check"], check=False
    )
    check("INDEX.md is current (build_index.py)", index.returncode == 0)
    for folder in MANIFEST["release"]["include"]:
        check(f"release includes {folder}/", (LEARNING / folder).is_dir())


def check_docs():
    pages = [
        p
        for p in sorted(LEARNING.rglob("*"))
        if p.suffix in (".md", ".html") and p.is_file()
    ]
    pages = [
        p
        for p in pages
        if not any(t in p.relative_to(LEARNING).as_posix() for t in TEMPLATES)
    ]
    broken = []
    for page in pages:
        for ref in links(page):
            target = local_target(page, ref)
            if target is not None and not target.exists():
                broken.append(f"{page.relative_to(LEARNING)} -> {ref}")
    check(
        f"links in {len(pages)} docs and pages resolve",
        not broken,
        "; ".join(broken[:5]),
    )


def check_release():
    rel = MANIFEST["release"]
    ref = rel["source_ref"]
    out = LEARNING / rel["output"]
    check("release.source_ref is pinned", ref != "PENDING", ref)
    check(
        "release.source_ref is on this branch",
        git("merge-base", "--is-ancestor", ref, "HEAD").returncode == 0,
    )
    expected = {p.resolve() for p in build_release.release_paths().values()}
    expected |= {
        (out / f).resolve()
        for f in ("index.html", "embed.html", "release.css", "tet4d-learning.js")
    }
    actual = {p.resolve() for p in out.rglob("*") if p.is_file()}
    check(
        "offline edition holds exactly the built files",
        expected == actual,
        f"missing {len(expected - actual)}, extra {len(actual - expected)}",
    )
    broken, online, absent = [], set(), []
    blob = f"https://github.com/mousomer/tet4d/blob/{ref}/"
    tree = f"https://github.com/mousomer/tet4d/tree/{ref}/"
    for page in sorted(out.rglob("*.html")):
        if any(t in page.relative_to(out).as_posix() for t in TEMPLATES):
            continue
        for link in links(page):
            if link.startswith((blob, tree)):
                online.add(unquote(urlsplit(link).path.split(f"/{ref}/", 1)[1]))
                continue
            target = local_target(page, link)
            if target is not None and not target.exists():
                broken.append(f"{page.relative_to(out)} -> {link}")
    check("offline edition: local links resolve", not broken, "; ".join(broken[:5]))
    for path in sorted(online):
        if git("cat-file", "-e", f"{ref}:{path}").returncode != 0:
            absent.append(path)
    check(
        f"offline edition: {len(online)} GitHub links exist at source_ref",
        not absent,
        ", ".join(absent[:5]),
    )


def main():
    any_branch = "--any-branch" in sys.argv[1:]
    parts = [
        ("branch", lambda: check_branch(any_branch)),
        ("components", check_components),
        ("docs", check_docs),
        ("release", check_release),
    ]
    for i, (label, fn) in enumerate(parts):
        step(i, len(parts), label)
        fn()
    step(len(parts), len(parts), "done")
    print(f"\n{sum(results)}/{len(results)} checks passed")
    return 0 if all(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
