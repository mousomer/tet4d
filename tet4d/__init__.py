from __future__ import annotations

from importlib import import_module
from pathlib import Path
from pkgutil import iter_modules

_SRC_PACKAGE_ROOT = Path(__file__).resolve().parent.parent / "src" / "tet4d"
__path__ = [str(_SRC_PACKAGE_ROOT)]


def __getattr__(name: str):
    target = f"{__name__}.{name}"
    try:
        module = import_module(target)
    except ModuleNotFoundError as exc:
        if exc.name != target:
            raise
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}") from exc
    globals()[name] = module
    return module


def __dir__() -> list[str]:
    names = {name for _, name, _ in iter_modules(__path__)}
    return sorted(set(globals()) | names)
