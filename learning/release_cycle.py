"""Rebuild, verify, and commit the offline edition from learning-surfaces."""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

LEARNING = Path(__file__).resolve().parent
ROOT = LEARNING.parent
VIEWERS = LEARNING / "tutorials/gluing-and-topologies/square-gluings/viewers"


def git_output(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pandoc-dir", type=Path, help="Directory containing Pandoc")
    parser.add_argument(
        "--chrome", type=Path, help="Chrome executable for the viewer checks"
    )
    args = parser.parse_args()

    if git_output("branch", "--show-current") != "learning-surfaces":
        raise SystemExit("Run this command on learning-surfaces.")

    release = json.loads((LEARNING / "manifest.json").read_text())["release"]
    generated = [
        f"learning/{release['output']}",
        "learning/manifest.json",
        "learning/INDEX.md",
    ]
    included = [f"learning/{folder}" for folder in release["include"]]
    if git_output(
        "status", "--porcelain", "--untracked-files=all", "--", *included, *generated
    ):
        raise SystemExit(
            "Commit changes to the included folders and release files before rebuilding."
        )
    source_ref = git_output("rev-parse", "HEAD")
    env = os.environ.copy()
    if args.pandoc_dir:
        env["PATH"] = os.pathsep.join(
            (str(args.pandoc_dir.resolve()), env.get("PATH", ""))
        )

    version_line = subprocess.check_output(
        ["pandoc", "--version"], env=env, text=True
    ).splitlines()[0]
    reference = release["pandoc"]["reference"]
    if version_line != f"pandoc {reference}":
        raise SystemExit(f"Expected Pandoc {reference}, saw {version_line}.")

    viewers = [sys.executable, "tools/check_viewers.py"]
    if args.chrome:
        viewers.extend(("--chrome", str(args.chrome.resolve())))
    message = f"learning: rebuild the offline edition at {source_ref}"
    steps = [
        (
            "Build offline edition",
            [sys.executable, "learning/build_release.py", "--lock"],
            ROOT,
        ),
        ("Build index", [sys.executable, "learning/build_index.py"], ROOT),
        ("Check manifest", [sys.executable, "learning/check_manifest.py"], ROOT),
        ("Smoke-test embed", [sys.executable, "learning/smoke_embed.py"], ROOT),
        ("Check square gluing viewers", viewers, VIEWERS),
        ("Stage release files", ["git", "add", "--", *generated], ROOT),
        (
            "Commit release",
            [
                "git",
                "commit",
                "--only",
                "-m",
                message,
                "-m",
                "Co-authored-by: Codex <codex@openai.com>",
                "--",
                *generated,
            ],
            ROOT,
        ),
    ]
    for index, (label, command, cwd) in enumerate(steps, 1):
        bar = "#" * index + "-" * (len(steps) - index)
        print(f"[{bar}] {index}/{len(steps)} {label}", flush=True)
        subprocess.run(command, cwd=cwd, env=env, check=True)
    print(
        "Push learning-surfaces, open a PR into learning, merge with a merge commit, and tag learning-vN."
    )


if __name__ == "__main__":
    try:
        main()
    except (OSError, subprocess.CalledProcessError) as error:
        raise SystemExit(f"Release cycle stopped: {error}") from error
