# Copyright (c) 2026 pz-b42-mp-modding-skill contributors
"""Tests for the installable Agent Skill package boundary."""

from __future__ import annotations

import unittest
from pathlib import Path

import pytest

SKILL_NAME = "pz-b42-mp-modding-skill"
REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = REPOSITORY_ROOT / "skills" / SKILL_NAME


def check_true(value: object) -> None:
    """Fail when a value is falsey."""
    if not value:
        pytest.fail(f"expected truthy value, received {value!r}")


def check_false(value: object) -> None:
    """Fail when a value is truthy."""
    if value:
        pytest.fail(f"expected falsey value, received {value!r}")


class SkillPackageTest(unittest.TestCase):
    """Keep runtime skill assets separate from repository-only files."""

    def test_distribution_contains_runtime_assets_only(self) -> None:
        """Ship the manifest, references, helpers, source, and license."""
        required = (
            SKILL_ROOT / "SKILL.md",
            SKILL_ROOT / "LICENSE",
            SKILL_ROOT / "references" / "source-of-truth.md",
            SKILL_ROOT / "references" / "api-query.md",
            SKILL_ROOT / "scripts" / "discover_pz.py",
            SKILL_ROOT / "scripts" / "query_pz_api.py",
            SKILL_ROOT / "scripts" / "report_pz_api.py",
            SKILL_ROOT / "scripts" / "validate_mod.py",
            SKILL_ROOT / "src" / "pz_b42_mp_skill" / "api_query.py",
            SKILL_ROOT / "src" / "pz_b42_mp_skill" / "evidence_report.py",
            SKILL_ROOT / "src" / "pz_b42_mp_skill" / "mod_metadata.py",
            SKILL_ROOT / "src" / "pz_b42_mp_skill" / "mod_validation_types.py",
            SKILL_ROOT / "src" / "pz_b42_mp_skill" / "mod_validator.py",
            SKILL_ROOT / "src" / "pz_b42_mp_skill" / "mod_validator_cli.py",
        )
        for path in required:
            check_true(path.is_file())

        repository_only = (
            ".github",
            "tests",
            "docs",
            "pyproject.toml",
            "README.md",
            "CHANGELOG.md",
            "CONTRIBUTING.md",
        )
        for name in repository_only:
            check_false((SKILL_ROOT / name).exists())


if __name__ == "__main__":
    unittest.main()
