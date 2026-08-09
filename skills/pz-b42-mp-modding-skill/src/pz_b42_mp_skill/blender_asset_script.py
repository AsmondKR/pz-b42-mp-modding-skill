# Copyright (c) 2026 pz-b42-mp-modding-skill contributors
"""Blender-facing script that loads the installed skill package."""

from __future__ import annotations

import importlib
import sys
from pathlib import Path
from typing import Protocol, cast


class BlenderEntryModule(Protocol):
    """Runtime shape of the installed Blender entry module."""

    def main(self, arguments: list[str] | None = None) -> int:
        """Run the Blender-internal entry point."""
        ...


def run() -> int:
    """Load the package and forward arguments after Blender's separator."""
    source_root = Path(__file__).resolve().parents[1]
    _ = sys.path.insert(0, str(source_root))
    entry = cast(
        "BlenderEntryModule",
        cast("object", importlib.import_module("pz_b42_mp_skill.blender_entry")),
    )
    arguments = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    return entry.main(arguments)


if __name__ == "__main__":
    raise SystemExit(run())
