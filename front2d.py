from pathlib import Path
import runpy

_REPO_ROOT = Path(__file__).resolve().parent
_TARGET = _REPO_ROOT / "cli" / "front2d.py"

if __name__ != "__main__":
    _exported = runpy.run_path(str(_TARGET), run_name=__name__)
    for _key in ("__name__", "__file__", "__package__", "__cached__", "__loader__", "__spec__"):
        _exported.pop(_key, None)
    globals().update(_exported)
    del _exported, _key

if __name__ == "__main__":
    runpy.run_path(str(_TARGET), run_name="__main__")
