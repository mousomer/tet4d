#!/usr/bin/env python3
"""Minimal reader for the Godot resource pack directory and raw entries.

The directory is parsed for inventory, and an unencrypted raw entry can be read
for provenance validation. This lets packaging checks inspect what a platform
export actually shipped without a Godot editor, runtime, or device.
"""

from __future__ import annotations

import struct
from pathlib import Path

PACK_MAGIC = 0x43504447  # "GDPC"
SUPPORTED_PACK_FORMATS = (2, 3, 4)
MD5_BYTES = 16


class PackFormatError(ValueError):
    """A file is not a Godot resource pack this reader understands."""


def _pack_directory_location(data: bytes) -> tuple[int, int, int, int]:
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
        file_base, directory_offset = struct.unpack_from("<QQ", data, 24)
        cursor = directory_offset
    else:
        file_base = 0
        cursor = 24 + 8 + (16 * 4)
    if cursor + 4 > len(data):
        raise PackFormatError("pack directory offset is outside the file")
    (file_count,) = struct.unpack_from("<I", data, cursor)
    return pack_format, file_base, cursor + 4, file_count


def _read_pack_directory_data(data: bytes) -> tuple[bytes, int, list[tuple[str, int, int, int]]]:
    pack_format, file_base, cursor, file_count = _pack_directory_location(data)
    entries: list[tuple[str, int, int, int]] = []
    for _ in range(file_count):
        if cursor + 4 > len(data):
            raise PackFormatError("pack directory is truncated")
        (path_length,) = struct.unpack_from("<I", data, cursor)
        cursor += 4
        if cursor + path_length + 36 > len(data):
            raise PackFormatError("pack directory entry is truncated")
        raw = data[cursor : cursor + path_length]
        cursor += path_length
        path = raw.rstrip(b"\x00").decode("utf-8")
        offset, size = struct.unpack_from("<QQ", data, cursor)
        cursor += 16 + MD5_BYTES  # offset, size, checksum
        entry_flags = 0
        if pack_format >= 2:
            (entry_flags,) = struct.unpack_from("<I", data, cursor)
            cursor += 4  # per-entry flags
        if cursor > len(data):
            raise PackFormatError("pack directory is truncated")
        entries.append((path, file_base + offset, size, entry_flags))
    return data, pack_format, entries


def _read_pack_directory(
    pack_path: Path,
) -> tuple[bytes, int, list[tuple[str, int, int, int]]]:
    return _read_pack_directory_data(pack_path.read_bytes())


def read_pack_paths(pack_path: Path) -> list[str]:
    """Return every ``res://``-relative path recorded in the pack directory."""
    _data, _format, entries = _read_pack_directory(pack_path)
    return [path for path, _offset, _size, _flags in entries]


def read_pack_paths_from_bytes(data: bytes) -> list[str]:
    """Return resource paths from an already-extracted Godot pack."""
    _data, _format, entries = _read_pack_directory_data(data)
    return [path for path, _offset, _size, _flags in entries]


def read_pack_file(pack_path: Path, resource_path: str) -> bytes:
    """Return one unencrypted raw resource from a Godot pack."""
    data, _format, entries = _read_pack_directory(pack_path)
    for path, offset, size, flags in entries:
        if path != resource_path:
            continue
        if flags:
            raise PackFormatError(
                f"resource {resource_path!r} uses unsupported entry flags {flags}"
            )
        if offset < 0 or offset + size > len(data):
            raise PackFormatError(f"resource {resource_path!r} is outside the pack")
        return data[offset : offset + size]
    raise PackFormatError(f"resource {resource_path!r} is absent from the pack")
