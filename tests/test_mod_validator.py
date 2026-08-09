# Copyright (c) 2026 pz-b42-mp-modding-skill contributors
"""Tests for read-only Build 42 multiplayer mod preflight validation."""

from __future__ import annotations

import json
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path

import pytest

from pz_b42_mp_skill.guard_paths import Policy
from pz_b42_mp_skill.mod_validation_types import ValidationCode
from pz_b42_mp_skill.mod_validator import validate_mod_root
from pz_b42_mp_skill.mod_validator_cli import main
from pz_b42_mp_skill.scaffold import ScaffoldSpec, apply_plan, build_plan


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


class ModValidatorTest(unittest.TestCase):
    """Validate real generated files inside an isolated workspace."""

    def setUp(self) -> None:
        """Create one valid generated multiplayer mod."""
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.root = Path(self.temporary_directory.name)
        self.workspace = self.root / "workspace"
        (self.workspace / "generated").mkdir(parents=True)
        policy_path = self.workspace / ".pz-skill-policy.json"
        policy_path.write_text(
            json.dumps(
                {
                    "version": 1,
                    "workspace_root": str(self.workspace),
                    "allowed_output_roots": ["generated"],
                    "forbidden_roots": [],
                },
            ),
            encoding="utf-8",
        )
        policy = Policy.load(policy_path)
        spec = ScaffoldSpec("ExampleMod", "Example Mod", "Example Author", "generated")
        apply_plan(policy, build_plan(policy, spec))
        self.mod_root = self.workspace / "generated" / "ExampleMod"
        self.version_root = self.mod_root / "Contents" / "mods" / "ExampleMod" / "42"

    def test_generated_multiplayer_mod_passes_preflight(self) -> None:
        """Accept the complete generated B42 client/server/shared boundary."""
        result = validate_mod_root(self.mod_root)
        check_true(result.valid)
        check_equal(result.mod_id, "ExampleMod")
        check_equal(result.issues, ())

    def test_missing_server_lua_and_boundary_are_reported(self) -> None:
        """Report structural and command-boundary defects together."""
        server_file = self.version_root / "media" / "lua" / "server" / "ExampleModServer.lua"
        server_file.unlink()
        result = validate_mod_root(self.mod_root)
        codes = {issue.code for issue in result.issues}
        check_true(ValidationCode.SERVER_LUA_MISSING in codes)
        check_true(ValidationCode.SERVER_COMMAND_BOUNDARY_MISSING in codes)

    def test_mod_info_identifier_must_match_directory(self) -> None:
        """Reject a package whose mod.info identity targets another mod."""
        mod_info = self.version_root / "mod.info"
        mod_info.write_text(
            mod_info.read_text(encoding="utf-8").replace(
                "id=ExampleMod",
                "id=OtherMod",
            ),
            encoding="utf-8",
        )
        result = validate_mod_root(self.mod_root)
        check_equal(
            {issue.code for issue in result.issues},
            {ValidationCode.MOD_ID_MISMATCH},
        )

    def test_publishing_tags_and_mod_metadata_are_required(self) -> None:
        """Report missing Build 42 tags and required identity fields."""
        workshop = self.mod_root / "workshop.txt"
        workshop.write_text(
            workshop.read_text(encoding="utf-8").replace(
                "tags=Build 42;Multiplayer",
                "tags=Multiplayer",
            ),
            encoding="utf-8",
        )
        mod_info = self.version_root / "mod.info"
        mod_info.write_text(
            mod_info.read_text(encoding="utf-8").replace(
                "author=Example Author\n",
                "",
            ),
            encoding="utf-8",
        )
        result = validate_mod_root(self.mod_root)
        check_equal(
            {issue.code for issue in result.issues},
            {
                ValidationCode.MOD_INFO_FIELD_MISSING,
                ValidationCode.WORKSHOP_TAG_MISSING,
            },
        )

    def test_legacy_unversioned_layout_gets_migration_finding(self) -> None:
        """Identify a B41-style media tree instead of cascading missing files."""
        mod_directory = self.version_root.parent
        for child in tuple(self.version_root.iterdir()):
            child.rename(mod_directory / child.name)
        self.version_root.rmdir()
        result = validate_mod_root(self.mod_root)
        check_equal(
            {issue.code for issue in result.issues},
            {
                ValidationCode.BUILD_42_DIRECTORY_MISSING,
                ValidationCode.LEGACY_UNVERSIONED_LAYOUT,
            },
        )

    def test_cli_emits_json_and_typed_missing_root_error(self) -> None:
        """Expose deterministic machine output without creating missing paths."""
        output = StringIO()
        with redirect_stdout(output):
            check_equal(main(["--mod-root", str(self.mod_root), "--json"]), 0)
        document = json.loads(output.getvalue())
        check_equal(document["schema_version"], 1)
        check_true(document["valid"])
        check_equal(document["mod_id"], "ExampleMod")

        missing = self.root / "missing"
        error_output = StringIO()
        with redirect_stderr(error_output):
            check_equal(main(["--mod-root", str(missing), "--json"]), 2)
        error = json.loads(error_output.getvalue())
        check_equal(error["error"], "mod_root_missing")
        check_false(missing.exists())


if __name__ == "__main__":
    unittest.main()
