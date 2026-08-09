# Copyright (c) 2026 pz-b42-mp-modding-skill contributors
"""Tests for safe Build 42 multiplayer mod scaffolding."""

from __future__ import annotations

import json
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path

import pytest

from pz_b42_mp_skill.mutation_guard import GuardError, GuardErrorCode, Policy
from pz_b42_mp_skill.scaffold import (
    ScaffoldPlan,
    ScaffoldSpec,
    ScaffoldSpecError,
    apply_plan,
    build_plan,
)
from pz_b42_mp_skill.scaffold_cli import main as scaffold_main


def check_equal(actual: object, expected: object) -> None:
    """Fail with useful values when equality is false."""
    if actual != expected:
        pytest.fail(f"{actual!r} != {expected!r}")


def check_contains(needle: str, value: str) -> None:
    """Fail when text does not contain an expected value."""
    if needle not in value:
        pytest.fail(f"{needle!r} not found in {value!r}")


class ScaffoldTest(unittest.TestCase):
    """Exercise plan/apply behavior through real generated files."""

    def setUp(self) -> None:
        """Create one empty approved output root."""
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.root = Path(self.temporary_directory.name)
        self.workspace = self.root / "workspace"
        (self.workspace / "generated").mkdir(parents=True)
        self.policy_path = self.workspace / ".pz-skill-policy.json"
        self.policy_path.write_text(
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
        self.policy = Policy.load(self.policy_path)
        self.spec = ScaffoldSpec(
            mod_id="ExampleMod",
            display_name="Example Mod",
            author="Example Author",
            output_root="generated",
        )

    def test_plan_and_apply_generate_b42_mp_boundaries(self) -> None:
        """Generate the expected B42 client/server/shared layout."""
        plan = ScaffoldPlan.from_json(build_plan(self.policy, self.spec).to_json())
        created = apply_plan(self.policy, plan)
        mod_root = self.workspace / "generated" / "ExampleMod"
        expected = {
            mod_root / "workshop.txt",
            mod_root / "Contents/mods/ExampleMod/42/mod.info",
            mod_root / "Contents/mods/ExampleMod/42/media/lua/client/ExampleModClient.lua",
            mod_root / "Contents/mods/ExampleMod/42/media/lua/server/ExampleModServer.lua",
            mod_root / "Contents/mods/ExampleMod/42/media/lua/shared/ExampleModShared.lua",
        }
        check_equal(set(created), expected)
        mod_info = (mod_root / "Contents/mods/ExampleMod/42/mod.info").read_text()
        check_contains("id=ExampleMod", mod_info)

    def test_apply_refuses_existing_file_without_partial_overwrite(self) -> None:
        """Refuse an existing mod root and preserve its content."""
        plan = build_plan(self.policy, self.spec)
        existing = self.workspace / "generated" / "ExampleMod" / "workshop.txt"
        existing.parent.mkdir(parents=True)
        existing.write_text("keep\n", encoding="utf-8")
        with pytest.raises(GuardError) as captured:
            apply_plan(self.policy, plan)
        check_equal(captured.value.code, GuardErrorCode.DESTINATION_EXISTS)
        check_equal(existing.read_text(encoding="utf-8"), "keep\n")
        check_equal(list(existing.parent.rglob("*.lua")), [])

    def test_invalid_mod_identifier_is_rejected(self) -> None:
        """Reject identifiers that cannot safely become paths and Lua names."""
        with pytest.raises(ScaffoldSpecError):
            ScaffoldSpec("bad/id", "Bad", "Author", "generated")

    def test_cli_returns_typed_error_without_traceback_on_overwrite(self) -> None:
        """Expose a clean refusal when the reviewed mod root already exists."""
        plan_path = self.workspace / "plan.json"
        plan_path.write_text(build_plan(self.policy, self.spec).to_json(), encoding="utf-8")
        arguments = [
            "apply",
            "--policy",
            str(self.policy_path),
            "--plan",
            str(plan_path),
        ]
        with redirect_stdout(StringIO()):
            check_equal(scaffold_main(arguments), 0)
        error_output = StringIO()
        with redirect_stderr(error_output):
            check_equal(scaffold_main(arguments), 2)
        check_contains("destination_exists", error_output.getvalue())
        if "Traceback" in error_output.getvalue():
            pytest.fail(error_output.getvalue())


if __name__ == "__main__":
    unittest.main()
