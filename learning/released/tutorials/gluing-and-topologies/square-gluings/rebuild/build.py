"""Rebuild the collection without using pre-rendered media."""

import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from importlib import import_module
from pathlib import Path
from zipfile import ZipFile

import imageio_ffmpeg
from PIL import ImageFont
from viewer import write_viewer

SOURCE = Path(__file__).resolve().parent
COLLECTION = SOURCE.parent
RECIPES = {
    "sphere-revised": ("tet4d_sphere_revised", "adjacent-edge-sphere"),
    "direct-curl": ("directboy", "boys-surface"),
    "adjacent-klein": ("klein_direct", "klein-bottle"),
    "opposite-torus": ("torus_direct", "torus"),
    "opposite-klein": ("opklein", "klein-bottle"),
    "opposite-rp2": ("orp", "rp2"),
}
STAGES = [
    0,
    60,
    96,
    132,
    168,
    208,
    250,
    276,
    300,
    324,
    348,
    373,
    396,
    432,
    464,
    490,
    520,
    575,
]
SPHERE_STAGES = list(
    zip(
        [0, 72, 112, 145, 176, 248],
        [
            "square",
            "orange-edges-approach",
            "orange-seam-closed",
            "cyan-edges-approach",
            "sphere-front",
            "sphere-rotated",
        ],
    )
)


def write_collection_page(source, target):
    # In the source edition media links open the guide. Rebuilt pages link to the generated media.
    text = source.read_text()
    text = re.sub(
        r'href="REBUILD\.md\?output=([^"]+)">Build ([^<]+)',
        lambda m: f'href="{m[1]}">{m[2].capitalize()}',
        text,
    )
    text = re.sub(
        r"\[Build ([^\]]+)\]\((?:\.\./)?REBUILD\.md\?output=([^)]+)\)",
        lambda m: f"[{m[1].capitalize()}]({m[2]})",
        text,
    )
    target.write_text(text)


def render_batch(args):
    subprocess.run(args, check=True)


def build(name, output, jobs):
    module, stem = RECIPES[name]
    directory = output / name
    directory.mkdir()
    os.environ["SPHERE_OUTPUT"] = str(directory)
    sphere = name == "sphere-revised"
    total = 264 if sphere else 576
    commands = []
    for start in range(0, total, 48):
        commands.append(
            [
                sys.executable,
                str(SOURCE / (module + ".py")),
                *map(str, range(start, min(start + 48, total))),
            ]
        )
    with ThreadPoolExecutor(max_workers=jobs) as pool:
        list(pool.map(render_batch, commands))
    frames = directory / "frames"
    assert len(list(frames.glob("*.png"))) == total
    subprocess.run(
        [
            imageio_ffmpeg.get_ffmpeg_exe(),
            "-nostdin",
            "-loglevel",
            "error",
            "-framerate",
            "24",
            "-i",
            str(frames / "%04d.png"),
            "-c:v",
            "libx264",
            "-crf",
            "17",
            "-pix_fmt",
            "yuv420p",
            "-movflags",
            "+faststart",
            str(directory / (stem + ".mp4")),
        ],
        check=True,
    )
    stills = directory / "stills"
    stills.mkdir()
    stages = SPHERE_STAGES if sphere else [(frame, "") for frame in STAGES]
    if name == "opposite-rp2":
        stages[-2] = (515, "")
    for i, (frame, label) in enumerate(stages, 1):
        suffix = "-" + label if label else ""
        shutil.copyfile(frames / f"{frame + 1:04}.png", stills / f"{i:02}{suffix}.png")
    for folder, archive in [
        (stills, stem + "-stills" if sphere else "stills"),
        (frames, stem + "-all-frames" if sphere else "frames"),
    ]:
        with ZipFile(directory / (archive + ".zip"), "w") as z:
            for file in sorted(folder.glob("*.png")):
                z.write(file, file.name)
    write_viewer(
        name,
        import_module(module),
        directory,
        "rotate-sphere.html" if sphere else "rotate.html",
    )
    notes = COLLECTION / name / "construction.md"
    if notes.is_file():
        write_collection_page(notes, directory / notes.name)
    print(f"{name}: {total} frames, {len(stages)} stills, movie and viewer", flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output", type=Path, required=True, help="New or empty output directory"
    )
    parser.add_argument("--only", choices=RECIPES)
    parser.add_argument("--jobs", type=int, default=min(8, os.cpu_count() or 1))
    args = parser.parse_args()
    dest = args.output.resolve()
    if args.jobs < 1 or (dest.exists() and any(dest.iterdir())):
        parser.error("Use a positive job count and a new or empty output directory.")
    dest.mkdir(parents=True, exist_ok=True)
    mac_font = Path("/System/Library/Fonts/Supplemental/Arial Unicode.ttf")
    os.environ.setdefault(
        "GLUING_FONT", str(mac_font) if mac_font.is_file() else "DejaVuSans.ttf"
    )
    ImageFont.truetype(os.environ["GLUING_FONT"], 18)
    with tempfile.TemporaryDirectory() as tmp:
        library = Path(tmp) / "raster.so"
        subprocess.run(
            [
                os.environ.get("CC", "cc"),
                "-O3",
                "-shared",
                "-fPIC",
                str(SOURCE / "raster.c"),
                "-o",
                str(library),
                "-lm",
            ],
            check=True,
        )
        os.environ["GLUING_RASTER"] = str(library)
        for name in [args.only] if args.only else RECIPES:
            build(name, dest, args.jobs)
    write_collection_page(COLLECTION / "square-gluings.md", dest / "square-gluings.md")
    if not args.only:
        write_collection_page(COLLECTION / "index.html", dest / "index.html")


if __name__ == "__main__":
    main()
