# Copyright (c) 2026 pz-b42-mp-modding-skill contributors
"""Tests for multi-symbol Build 42 evidence reports."""

from __future__ import annotations

import json
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path

import pytest

from pz_b42_mp_skill.evidence_report import build_evidence_report, main


def check_equal(actual: object, expected: object) -> None:
    """Fail with useful values when equality is false."""
    if actual != expected:
        pytest.fail(f"{actual!r} != {expected!r}")


def check_true(value: object) -> None:
    """Fail when a value is falsey."""
    if not value:
        pytest.fail(f"expected truthy value, received {value!r}")


def check_false(value: object) -> None:
    """Fail when a value is truthy."""
    if value:
        pytest.fail(f"expected falsey value, received {value!r}")


class EvidenceReportTest(unittest.TestCase):
    """Build complete and partial reports from one verified manifest."""

    def setUp(self) -> None:
        """Create an isolated fake Steam Build 42 installation."""
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.root = Path(self.temporary_directory.name)
        self.steamapps = self.root / "Steam" / "steamapps"
        self.install_root = self.steamapps / "common" / "ProjectZomboid"
        client_commands = self.install_root / "media" / "lua" / "server" / "ClientCommands.lua"
        server_commands = self.install_root / "media" / "lua" / "client" / "ServerCommands.lua"
        panel = self.install_root / "media" / "lua" / "client" / "ISUI" / "ISPanel.lua"
        for path in (client_commands, server_commands, panel):
            path.parent.mkdir(parents=True, exist_ok=True)
        client_commands.write_text(
            "ClientCommands.OnClientCommand = function(module, command, player, args)\n"
            "end\n"
            "Events.OnClientCommand.Add(ClientCommands.OnClientCommand)\n",
            encoding="utf-8",
        )
        server_commands.write_text(
            "Events.OnServerCommand.Add(onServerCommand)\n",
            encoding="utf-8",
        )
        panel.write_text(
            'ISPanel = ISUIElement:derive("ISPanel")\n',
            encoding="utf-8",
        )
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

    def test_report_preserves_build_context_and_input_order(self) -> None:
        """Collect multiple exact symbols under one discovered build."""
        report = build_evidence_report(
            ("OnClientCommand", "ISPanel"),
            manifest=self.manifest,
            limit=10,
        )
        check_true(report.complete)
        check_equal(report.build_id, "12345678")
        check_equal([query.symbol for query in report.queries], ["OnClientCommand", "ISPanel"])
        check_equal([len(query.matches) for query in report.queries], [2, 1])

    def test_missing_symbol_produces_partial_report(self) -> None:
        """Retain found evidence while marking absent claims explicitly."""
        report = build_evidence_report(
            ("OnServerCommand", "MissingSymbol"),
            manifest=self.manifest,
            limit=10,
        )
        check_false(report.complete)
        check_equal([query.found for query in report.queries], [True, False])

    def test_cli_uses_stable_complete_partial_and_error_exit_codes(self) -> None:
        """Return 0 for complete, 1 for partial, and 2 for invalid input."""
        complete_output = StringIO()
        with redirect_stdout(complete_output):
            check_equal(
                main(
                    [
                        "--manifest",
                        str(self.manifest),
                        "--symbol",
                        "OnClientCommand",
                        "--symbol",
                        "ISPanel",
                        "--json",
                    ],
                ),
                0,
            )
        complete_document = json.loads(complete_output.getvalue())
        check_equal(complete_document["schema_version"], 1)
        check_true(complete_document["complete"])

        partial_output = StringIO()
        with redirect_stdout(partial_output):
            check_equal(
                main(
                    [
                        "--manifest",
                        str(self.manifest),
                        "--symbol",
                        "MissingSymbol",
                        "--json",
                    ],
                ),
                1,
            )
        check_false(json.loads(partial_output.getvalue())["complete"])

        error_output = StringIO()
        with redirect_stderr(error_output):
            check_equal(
                main(
                    [
                        "--manifest",
                        str(self.manifest),
                        "--symbol",
                        "bad/id",
                        "--json",
                    ],
                ),
                2,
            )
        check_equal(json.loads(error_output.getvalue())["error"], "invalid_symbol")


if __name__ == "__main__":
    unittest.main()
