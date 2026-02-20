# -*- mode: python ; coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path


try:
    _SPEC_DIR = Path(SPECPATH).resolve()
except NameError:
    _SPEC_DIR = (Path.cwd() / "packaging" / "pyinstaller").resolve()

ROOT = _SPEC_DIR.parents[1]
ENTRY = ROOT / "front.py"


def _bundle_tree(rel: str) -> list[tuple[str, str]]:
    src = ROOT / rel
    if not src.exists():
        return []
    return [(str(src), rel)]


datas: list[tuple[str, str]] = []
for relative in ("assets", "config", "keybindings", "docs/help"):
    datas.extend(_bundle_tree(relative))

a = Analysis(
    [str(ENTRY)],
    pathex=[str(ROOT)],
    binaries=[],
    datas=datas,
    hiddenimports=["pygame"],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="tet4d",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="tet4d",
)
