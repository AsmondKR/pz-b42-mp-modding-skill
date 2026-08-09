# Copyright (c) 2026 pz-b42-mp-modding-skill contributors
"""Small parsers for Project Zomboid key/value metadata files."""

from __future__ import annotations

from typing import TYPE_CHECKING, final

if TYPE_CHECKING:
    from pathlib import Path


@final
class MetadataReadError(Exception):
    """A metadata file could not be read."""


def read_key_values(path: Path) -> dict[str, str]:
    """Read first-equals key/value lines without mutating the file."""
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError as error:
        raise MetadataReadError(str(error)) from error
    return {
        key.strip(): value.strip()
        for line in lines
        if "=" in line
        for key, value in (line.split("=", 1),)
    }


def missing_fields(metadata: dict[str, str], required: tuple[str, ...]) -> tuple[str, ...]:
    """Return required keys whose values are absent or empty."""
    return tuple(key for key in required if not metadata.get(key))


def semicolon_values(value: str) -> set[str]:
    """Parse trimmed, non-empty semicolon-delimited values."""
    return {part.strip() for part in value.split(";") if part.strip()}
