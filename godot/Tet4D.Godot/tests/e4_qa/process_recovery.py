"""Exercise Godot process-kill recovery on the named host."""

import argparse
import selectors
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory

PROJECT = Path(__file__).resolve().parents[2]


def _kill_at_boundary(command):
    with subprocess.Popen(
        command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT
    ) as child:
        with selectors.DefaultSelector() as selector:
            selector.register(child.stdout, selectors.EVENT_READ)
            output = bytearray()
            try:
                while b"E4_KILL_BOUNDARY\n" not in output:
                    if not selector.select(timeout=10):
                        raise RuntimeError("Godot did not reach the crash boundary")
                    data = child.stdout.read1()
                    if not data:
                        raise RuntimeError(output.decode(errors="replace"))
                    output.extend(data)
            finally:
                if child.poll() is None:
                    child.kill()
        child.wait(timeout=10)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--godot", required=True)
    args = parser.parse_args()
    with TemporaryDirectory(prefix="tet4d-e4-process-") as directory:
        root = Path(directory)
        command = [
            args.godot,
            "--headless",
            "--log-file",
            str(root / "godot.log"),
            "--path",
            str(PROJECT),
            "--script",
            "tests/e4_qa/process_probe.gd",
            "--",
        ]
        for mode, expected in (
            ("before_publish", "pending"),
            ("after_publish", "pending"),
            ("after_ack", "synced"),
        ):
            journal = str(root / mode)
            _kill_at_boundary([*command, journal, mode])
            subprocess.run(
                [*command, journal, "verify", expected], check=True, timeout=10
            )
            print(f"Godot process recovery passed: {mode}")


if __name__ == "__main__":
    main()
