# Copyright (c) 2026 pz-b42-mp-modding-skill contributors
"""Tests for read-only Build 42 Lua symbol evidence queries."""

from __future__ import annotations

import json
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path

import pytest

from pz_b42_mp_skill.api_query import EvidenceKind, find_symbol_evidence, main


def check_equal(actual: object, expected: object) -> None:
    """Fail with useful values when equality is false."""
    if actual != expected:
        pytest.fail(f"{actual!r} != {expected!r}")


def check_false(value: object) -> None:
    """Fail when a value is truthy."""
    if value:
        pytest.fail(f"expected falsey value, received {value!r}")


class ApiQueryTest(unittest.TestCase):
    """Prove exact, read-only symbol extraction from vanilla-style Lua."""

    def setUp(self) -> None:
        """Create an isolated fake Project Zomboid Lua tree."""
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.root = Path(self.temporary_directory.name)
        self.steamapps = self.root / "Steam" / "steamapps"
        self.install_root = self.steamapps / "common" / "ProjectZomboid"
        self.lua_root = self.install_root / "media" / "lua"
        server_file = self.lua_root / "server" / "ClientCommands.lua"
        server_dispatch = self.lua_root / "client" / "ServerCommands.lua"
        client_file = self.lua_root / "client" / "ISUI" / "ISPanel.lua"
        server_file.parent.mkdir(parents=True)
        client_file.parent.mkdir(parents=True)
        server_file.write_text(
            "ClientCommands.OnClientCommand = function(module, command, player, args)\n"
            "end\n"
            "local function OnClientCommand(module, command, player, args)\n"
            "end\n"
            "Events.OnClientCommand.Add(OnClientCommand)\n"
            "-- Events.OnClientCommand.Add(CommentedOut)\n"
            "Events.OnClientCommandExtra.Add(OtherHandler)\n",
            encoding="utf-8",
        )
        client_file.write_text(
            'ISPanel = ISUIElement:derive("ISPanel")\n'
            "function ISPanel:new(x, y, width, height)\n"
            "end\n",
            encoding="utf-8",
        )
        server_dispatch.write_text("-- fixture\n", encoding="utf-8")
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

    def test_extracts_exact_function_event_and_class_evidence(self) -> None:
        """Return structured definitions without comments or substring matches."""
        command_matches = find_symbol_evidence(self.install_root, "OnClientCommand")
        check_equal(
            {match.kind for match in command_matches},
            {EvidenceKind.EVENT_REGISTRATION, EvidenceKind.FUNCTION},
        )
        check_equal([match.line_number for match in command_matches], [1, 3, 5])
        panel_matches = find_symbol_evidence(self.install_root, "ISPanel")
        check_equal(
            {match.kind for match in panel_matches},
            {EvidenceKind.CLASS_DERIVATION, EvidenceKind.FUNCTION},
        )

    def test_cli_emits_json_and_typed_not_found_error(self) -> None:
        """Provide machine-readable evidence and a stable missing-symbol refusal."""
        output = StringIO()
        with redirect_stdout(output):
            check_equal(
                main(
                    [
                        "--install-root",
                        str(self.install_root),
                        "--symbol",
                        "OnClientCommand",
                        "--json",
                    ],
                ),
                0,
            )
        document = json.loads(output.getvalue())
        check_equal(document["symbol"], "OnClientCommand")
        check_equal(len(document["matches"]), 3)

        error_output = StringIO()
        with redirect_stderr(error_output):
            check_equal(
                main(
                    [
                        "--install-root",
                        str(self.install_root),
                        "--symbol",
                        "MissingSymbol",
                        "--json",
                    ],
                ),
                3,
            )
        error = json.loads(error_output.getvalue())
        check_equal(error["error"], "symbol_not_found")

    def test_cli_discovers_build_context_from_manifest(self) -> None:
        """Resolve an exact manifest and include its build provenance."""
        output = StringIO()
        with redirect_stdout(output):
            check_equal(
                main(
                    [
                        "--manifest",
                        str(self.manifest),
                        "--symbol",
                        "ISPanel",
                        "--json",
                    ],
                ),
                0,
            )
        document = json.loads(output.getvalue())
        check_equal(document["build_id"], "12345678")
        check_equal(document["branch"], "public")
        check_equal(document["install_root"], str(self.install_root.resolve()))
        check_equal(len(document["matches"]), 2)

    def test_missing_lua_root_is_read_only_failure(self) -> None:
        """Reject a non-installation without creating any directories."""
        missing = self.install_root / "missing"
        error_output = StringIO()
        with redirect_stderr(error_output):
            check_equal(
                main(["--install-root", str(missing), "--symbol", "ISPanel", "--json"]),
                2,
            )
        check_false(missing.exists())
        error = json.loads(error_output.getvalue())
        check_equal(error["error"], "lua_root_missing")


if __name__ == "__main__":
    unittest.main()
