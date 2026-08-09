# Copyright (c) 2026 pz-b42-mp-modding-skill contributors
"""Tests for read-only local Project Zomboid discovery."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import pytest

from pz_b42_mp_skill.discovery import DiscoveryError, discover_from_manifest


def check_equal(actual: object, expected: object) -> None:
    """Fail with useful values when equality is false."""
    if actual != expected:
        pytest.fail(f"{actual!r} != {expected!r}")


class DiscoveryTest(unittest.TestCase):
    """Prove build and evidence detection against an isolated fake install."""

    def setUp(self) -> None:
        """Create one fake Steam installation."""
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.root = Path(self.temporary_directory.name)
        self.steamapps = self.root / "Steam" / "steamapps"
        self.install = self.steamapps / "common" / "ProjectZomboid"
        self.server_commands = self.install / "media" / "lua" / "server" / "ClientCommands.lua"
        self.client_commands = self.install / "media" / "lua" / "client" / "ServerCommands.lua"
        self.ui_panel = self.install / "media" / "lua" / "client" / "ISUI" / "ISPanel.lua"
        for path in (self.server_commands, self.client_commands, self.ui_panel):
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("-- fixture\n", encoding="utf-8")
        self.manifest = self.steamapps / "appmanifest_108600.acf"
        self.manifest.write_text(
            '"AppState"\n{\n'
            '  "appid" "108600"\n'
            '  "installdir" "ProjectZomboid"\n'
            '  "buildid" "12345678"\n'
            '  "UserConfig" { "BetaKey" "public" }\n'
            "}\n",
            encoding="utf-8",
        )

    def test_discovers_build_install_and_verified_surfaces(self) -> None:
        """Return the build and three required vanilla evidence files."""
        result = discover_from_manifest(self.manifest, self.root / "Zomboid")
        check_equal(result.build_id, "12345678")
        check_equal(result.branch, "public")
        check_equal(result.install_root, self.install.resolve())
        check_equal(set(result.evidence), {"client_commands", "server_commands", "ui_panel"})
        check_equal(json.loads(result.to_json())["schema_version"], 1)

    def test_missing_install_is_reported_without_creating_files(self) -> None:
        """Refuse a stale manifest without changing the fixture tree."""
        self.install.rename(self.root / "moved")
        before = sorted(path.relative_to(self.root) for path in self.root.rglob("*"))
        with pytest.raises(DiscoveryError):
            discover_from_manifest(self.manifest, self.root / "Zomboid")
        after = sorted(path.relative_to(self.root) for path in self.root.rglob("*"))
        check_equal(after, before)


if __name__ == "__main__":
    unittest.main()
