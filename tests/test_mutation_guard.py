# Copyright (c) 2026 pz-b42-mp-modding-skill contributors
"""Regression tests for the create-only workspace mutation guard."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import patch

import pytest

if TYPE_CHECKING:
    from collections.abc import Callable

from pz_b42_mp_skill.mutation_guard import (
    GuardError,
    GuardErrorCode,
    MutationGuard,
    Policy,
)


def check_equal(actual: object, expected: object) -> None:
    """Fail with useful values when equality is false."""
    if actual != expected:
        pytest.fail(f"{actual!r} != {expected!r}")


def check_false(value: object) -> None:
    """Fail when a value is truthy."""
    if value:
        pytest.fail(f"expected false, received {value!r}")


class MutationGuardTest(unittest.TestCase):
    """Exercise every authorization boundary with isolated real files."""

    def setUp(self) -> None:
        """Create an approved workspace and source file."""
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.root = Path(self.temporary_directory.name)
        self.workspace = self.root / "workspace"
        self.output = self.workspace / "generated"
        self.inputs = self.workspace / "inputs"
        self.output.mkdir(parents=True)
        self.inputs.mkdir()
        self.policy_path = self.workspace / ".pz-skill-policy.json"
        self.write_policy(["generated"])
        self.policy = Policy.load(self.policy_path)
        self.guard = MutationGuard(self.policy)
        self.source = self.inputs / "hello.txt"
        self.source.write_text("hello from approved input\n", encoding="utf-8")

    def write_policy(self, allowed_output_roots: list[str]) -> None:
        """Write one policy fixture."""
        document = {
            "version": 1,
            "workspace_root": str(self.workspace),
            "allowed_output_roots": allowed_output_roots,
            "forbidden_roots": [],
        }
        self.policy_path.write_text(json.dumps(document), encoding="utf-8")

    def check_guard_error(
        self,
        expected: GuardErrorCode,
        operation: Callable[[], object],
    ) -> None:
        """Check one typed refusal."""
        with pytest.raises(GuardError) as captured:
            operation()
        check_equal(captured.value.code, expected)

    def test_plan_and_apply_create_inside_approved_root(self) -> None:
        """Create exactly one reviewed file."""
        manifest = self.guard.plan_create("generated/hello.txt", self.source)
        created = self.guard.apply_create(manifest, self.source)
        check_equal(created, self.output / "hello.txt")
        check_equal(created.read_text(encoding="utf-8"), "hello from approved input\n")
        check_equal(manifest.destination, "generated/hello.txt")

    def test_parent_traversal_is_rejected(self) -> None:
        """Reject a parent traversal destination."""
        self.check_guard_error(
            GuardErrorCode.INVALID_DESTINATION,
            lambda: self.guard.plan_create("../outside.txt", self.source),
        )

    def test_absolute_destination_is_rejected(self) -> None:
        """Reject an absolute destination."""
        self.check_guard_error(
            GuardErrorCode.INVALID_DESTINATION,
            lambda: self.guard.plan_create(str(self.root / "outside.txt"), self.source),
        )

    def test_existing_file_is_never_overwritten(self) -> None:
        """Preserve an existing destination byte-for-byte."""
        destination = self.output / "hello.txt"
        destination.write_text("keep me\n", encoding="utf-8")
        self.check_guard_error(
            GuardErrorCode.DESTINATION_EXISTS,
            lambda: self.guard.plan_create("generated/hello.txt", self.source),
        )
        check_equal(destination.read_text(encoding="utf-8"), "keep me\n")

    def test_source_change_after_plan_is_rejected(self) -> None:
        """Reject bytes changed after dry-run review."""
        manifest = self.guard.plan_create("generated/hello.txt", self.source)
        self.source.write_text("changed after approval\n", encoding="utf-8")
        self.check_guard_error(
            GuardErrorCode.SOURCE_CHANGED,
            lambda: self.guard.apply_create(manifest, self.source),
        )
        check_false((self.output / "hello.txt").exists())

    def test_policy_change_after_plan_is_rejected(self) -> None:
        """Reject a semantically changed policy."""
        manifest = self.guard.plan_create("generated/hello.txt", self.source)
        (self.workspace / "other").mkdir()
        self.write_policy(["generated", "other"])
        changed_guard = MutationGuard(Policy.load(self.policy_path))
        self.check_guard_error(
            GuardErrorCode.POLICY_CHANGED,
            lambda: changed_guard.apply_create(manifest, self.source),
        )
        check_false((self.output / "hello.txt").exists())

    def test_loaded_policy_rejects_byte_change_before_apply(self) -> None:
        """Reject any exact policy-byte change after loading."""
        manifest = self.guard.plan_create("generated/hello.txt", self.source)
        original = self.policy_path.read_text(encoding="utf-8")
        self.policy_path.write_text(f"{original}\n", encoding="utf-8")
        self.check_guard_error(
            GuardErrorCode.POLICY_CHANGED,
            lambda: self.guard.apply_create(manifest, self.source),
        )

    def test_workspace_inside_project_zomboid_install_is_rejected(self) -> None:
        """Reject a workspace nested in the game installation."""
        forbidden = self.root / "Steam/steamapps/common/ProjectZomboid/modwork"
        forbidden.mkdir(parents=True)
        policy_path = forbidden / ".pz-skill-policy.json"
        policy_path.write_text(
            json.dumps(
                {
                    "version": 1,
                    "workspace_root": str(forbidden),
                    "allowed_output_roots": ["generated"],
                    "forbidden_roots": [],
                },
            ),
            encoding="utf-8",
        )
        self.check_guard_error(GuardErrorCode.FORBIDDEN_ROOT, lambda: Policy.load(policy_path))

    def test_reparse_escape_is_rejected(self) -> None:
        """Reject a destination component identified as a reparse point."""
        outside = self.root / "outside"
        outside.mkdir()
        link = self.output / "escape"
        link.mkdir()
        with patch("pz_b42_mp_skill.guard_paths.is_reparse", return_value=True):
            self.check_guard_error(
                GuardErrorCode.PATH_ESCAPE,
                lambda: self.guard.plan_create("generated/escape/pwned.txt", self.source),
            )
        check_false((outside / "pwned.txt").exists())


if __name__ == "__main__":
    unittest.main()
