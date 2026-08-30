#!/usr/bin/env python3
"""Minimal reader for the Godot resource pack directory.

Only the directory is parsed. This lets packaging validation assert which
resources a platform export actually shipped without a Godot editor, a Godot
runtime, or a device, which keeps the packaging gate free of both.
"""

from __future__ import annotations

import struct
from pathlib import Path

PACK_MAGIC = 0x43504447  # "GDPC"
SUPPORTED_PACK_FORMATS = (2, 3, 4)
MD5_BYTES = 16


class PackFormatError(ValueError):
    """A file is not a Godot resource pack this reader understands."""


def read_pack_paths(pack_path: Path) -> list[str]:
    """Return every ``res://``-relative path recorded in the pack directory."""
    data = pack_path.read_bytes()
    if len(data) < 32:
        raise PackFormatError("file is too small to be a Godot pack")
    magic, pack_format, major, minor, patch, flags = struct.unpack_from("<6I", data, 0)
    if magic != PACK_MAGIC:
        raise PackFormatError("missing GDPC magic")
    if pack_format not in SUPPORTED_PACK_FORMATS:
        raise PackFormatError(f"unsupported pack format version {pack_format}")
    del major, minor, patch, flags
    # Format 4 stores the directory at an explicit offset after the file data;
    # earlier formats place it immediately behind the reserved header block.
    if pack_format >= 4:
        _file_base, directory_offset = struct.unpack_from("<QQ", data, 24)
        cursor = directory_offset
    else:
        cursor = 24 + 8 + (16 * 4)
    if cursor + 4 > len(data):
        raise PackFormatError("pack directory offset is outside the file")
    (file_count,) = struct.unpack_from("<I", data, cursor)
    cursor += 4
    paths: list[str] = []
    for _ in range(file_count):
        (path_length,) = struct.unpack_from("<I", data, cursor)
        cursor += 4
        raw = data[cursor : cursor + path_length]
        cursor += path_length
        paths.append(raw.rstrip(b"\x00").decode("utf-8"))
        cursor += 16 + MD5_BYTES  # offset, size, checksum
        if pack_format >= 2:
            cursor += 4  # per-entry flags
        if cursor > len(data):
            raise PackFormatError("pack directory is truncated")
    return paths
