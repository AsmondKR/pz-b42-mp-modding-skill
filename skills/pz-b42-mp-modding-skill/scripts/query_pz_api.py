# Copyright (c) 2026 pz-b42-mp-modding-skill contributors
"""Agent-facing entry point for local Project Zomboid Lua evidence queries."""

from __future__ import annotations

import runpy
import sys
from pathlib import Path


def run() -> int:
    """Load the package directly from a cloned skill repository."""
    _ = sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
    _ = runpy.run_module("pz_b42_mp_skill.api_query", run_name="__main__")
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
