# Copyright (c) 2026 pz-b42-mp-modding-skill contributors
"""Machine-consumed routing contracts for the asset production workflow."""

from __future__ import annotations

import unittest
from pathlib import Path

import pytest

SKILL_ROOT = Path(__file__).resolve().parents[1] / "skills" / "pz-b42-mp-modding-skill"


def check_true(value: object) -> None:
    """Fail when a value is falsey."""
    if not value:
        pytest.fail(f"expected truthy value, received {value!r}")


class AssetPromptContractTest(unittest.TestCase):
    """Keep asset requests routed to installed production references."""

    def test_asset_references_ship_with_the_skill(self) -> None:
        """Install the art, image-prompt, and Blender workflow contracts."""
        references = SKILL_ROOT / "references"
        required = (
            references / "asset-art-direction.md",
            references / "codex-image-prompts.md",
            references / "blender-fbx-pipeline.md",
        )
        for path in required:
            check_true(path.is_file())

    def test_skill_description_routes_asset_requests(self) -> None:
        """Expose stable routing terms through Agent Skill frontmatter."""
        skill_text = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
        frontmatter = skill_text.split("---", maxsplit=2)[1]
        for route in ("Blender", "FBX", "image assets"):
            check_true(route in frontmatter)


if __name__ == "__main__":
    unittest.main()
