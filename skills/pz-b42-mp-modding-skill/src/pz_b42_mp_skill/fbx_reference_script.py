# Copyright (c) 2026 pz-b42-mp-modding-skill contributors
"""Bootstrap the installed FBX probe inside Blender."""

from __future__ import annotations

import importlib
import sys
from pathlib import Path
from typing import Protocol, cast


class EntryModule(Protocol):
    """Dynamic FBX probe entry surface."""

    def main(self, arguments: list[str] | None = None) -> int:
        """Run the probe."""
        ...


def run() -> int:
    """Load the package from either an Agent Skill or wheel installation."""
    source_root = Path(__file__).resolve().parents[1]
    _ = sys.path.insert(0, str(source_root))
    entry = cast(
        "EntryModule",
        cast("object", importlib.import_module("pz_b42_mp_skill.fbx_reference_entry")),
    )
    arguments = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    return entry.main(arguments)


if __name__ == "__main__":
    raise SystemExit(run())
