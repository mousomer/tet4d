"""The learning branch's own gate. It replaces the game's verifier on learning and learning-surfaces.

    python3 learning/gate.py                 # pre-push: scope, whitespace, manifest, index, secrets
    python3 learning/gate.py --full          # CI and CD: also rebuild the offline edition and run
                                             # the browser checks (needs ci/requirements.txt)
    python3 learning/gate.py --base REF      # compare against REF instead of origin/learning
    python3 learning/gate.py --any-branch    # allow a detached checkout (CI)

The learning branch never touches the game: a change may only add or edit files under the
folders in manifest.json flow.owned_paths. The game's CI, packaging and verifier do not run here.
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

LEARNING = Path(__file__).resolve().parent
ROOT = LEARNING.parent
VIEWERS = LEARNING / "tutorials/gluing-and-topologies/square-gluings/viewers"
MANIFEST = json.loads((LEARNING / "manifest.json").read_text(encoding="utf-8"))
# Folders a learning change may touch: the material, and the branch's own CI/CD and hooks.
LEARNING_OWNED = tuple(MANIFEST["flow"]["owned_paths"])


def git(*args):
    return subprocess.run(
        ["git", *args], cwd=ROOT, capture_output=True, text=True, check=False
    )


def check_scope(base):
    if git("rev-parse", "--verify", "--quiet", base).returncode != 0:
        raise SystemExit(
            f"Base {base} not found: fetch it (git fetch origin learning) or pass --base."
        )
    changed = git("diff", "--name-only", f"{base}...HEAD").stdout.split()
    outside = [path for path in changed if not path.startswith(LEARNING_OWNED)]
    if outside:
        print("\n".join(f"  {path}" for path in outside))
        raise SystemExit(
            f"{len(outside)} changed file(s) outside {', '.join(LEARNING_OWNED)}: the learning branch "
            "does not touch the game. Game changes go to master."
        )
    print(f"  {len(changed)} changed file(s), all learning-owned.")


def check_pandoc():
    reference = MANIFEST["release"]["pandoc"]["reference"]
    found = subprocess.check_output(["pandoc", "--version"], text=True).splitlines()[0]
    if found != f"pandoc {reference}":
        raise SystemExit(
            f"Expected Pandoc {reference} to rebuild the offline edition, saw {found}."
        )
    print(f"  {found}")


def check_rebuild():
    output = MANIFEST["release"]["output"]
    subprocess.run([sys.executable, "learning/build_release.py"], cwd=ROOT, check=True)
    drift = git(
        "status", "--porcelain", "--untracked-files=all", "--", f"learning/{output}"
    ).stdout
    if drift:
        print(drift)
        raise SystemExit(
            "The committed offline edition differs from a rebuild of its sources: run "
            "learning/release_cycle.py on learning-surfaces and commit the result."
        )
    print("  The committed offline edition matches a rebuild of its sources.")


def run(*command, cwd=ROOT):
    return lambda: subprocess.run(list(command), cwd=cwd, check=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--full", action="store_true", help="also rebuild and run the browser checks"
    )
    parser.add_argument(
        "--base", default="origin/learning", help="ref the change is compared with"
    )
    parser.add_argument(
        "--any-branch", action="store_true", help="allow a detached checkout"
    )
    parser.add_argument("--chrome", help="Chrome executable for the viewer checks")
    args = parser.parse_args()

    manifest = [sys.executable, "learning/check_manifest.py"]
    if args.any_branch:
        manifest.append("--any-branch")
    steps = [
        ("Scope: learning-owned files only", lambda: check_scope(args.base)),
        ("Whitespace", run("git", "diff", "--check", f"{args.base}...HEAD")),
        ("Manifest", run(*manifest)),
        ("Index", run(sys.executable, "learning/build_index.py", "--check")),
        ("Secrets", run(sys.executable, "tools/governance/scan_secrets.py")),
    ]
    if args.full:
        viewers = [sys.executable, "tools/check_viewers.py"]
        if args.chrome:
            viewers.extend(("--chrome", args.chrome))
        steps += [
            ("Pandoc version", check_pandoc),
            ("Rebuild the offline edition", check_rebuild),
            ("Smoke-test the embed", run(sys.executable, "learning/smoke_embed.py")),
            ("Square gluing viewers", run(*viewers, cwd=VIEWERS)),
        ]
    for index, (label, step) in enumerate(steps, 1):
        bar = "#" * index + "-" * (len(steps) - index)
        print(f"[{bar}] {index}/{len(steps)} {label}", flush=True)
        step()
    print(f"Learning gate passed ({'full' if args.full else 'fast'}).")


if __name__ == "__main__":
    os.environ.setdefault("PYTHONDONTWRITEBYTECODE", "1")
    try:
        main()
    except (OSError, subprocess.CalledProcessError) as error:
        raise SystemExit(f"Learning gate stopped: {error}") from error
