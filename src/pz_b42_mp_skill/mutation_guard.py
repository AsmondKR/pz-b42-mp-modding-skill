# Copyright (c) 2026 pz-b42-mp-modding-skill contributors
"""Create-only file mutations constrained to an approved workspace."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import cast, final

from pz_b42_mp_skill.guard_paths import Policy, authorize_destination
from pz_b42_mp_skill.guard_types import (
    CreateManifest,
    GuardError,
    GuardErrorCode,
    sha256_bytes,
)

__all__ = [
    "CreateManifest",
    "GuardError",
    "GuardErrorCode",
    "MutationGuard",
    "Policy",
    "main",
]


@final
class MutationGuard:
    """Plan and apply create-only writes within a policy."""

    _policy: Policy

    def __init__(self, policy: Policy) -> None:
        """Bind the guard to one exact policy."""
        self._policy = policy

    def plan_create(self, destination: str, source: Path) -> CreateManifest:
        """Validate current state and return a reviewable manifest."""
        target = authorize_destination(self._policy, destination)
        if target.exists() or target.is_symlink():
            raise GuardError(GuardErrorCode.DESTINATION_EXISTS, str(target))
        content = read_source(source)
        return CreateManifest(
            destination,
            self._policy.fingerprint,
            sha256_bytes(content),
            len(content),
        )

    def apply_create(self, manifest: CreateManifest, source: Path) -> Path:
        """Apply unchanged bytes using kernel-enforced exclusive creation."""
        self._policy.ensure_current()
        if manifest.policy_sha256 != self._policy.fingerprint:
            raise GuardError(GuardErrorCode.POLICY_CHANGED, "policy_fingerprint")
        target = authorize_destination(self._policy, manifest.destination)
        if target.exists() or target.is_symlink():
            raise GuardError(GuardErrorCode.DESTINATION_EXISTS, str(target))
        content = read_source(source)
        if len(content) != manifest.source_size or sha256_bytes(content) != manifest.source_sha256:
            raise GuardError(GuardErrorCode.SOURCE_CHANGED, "source_bytes")
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
        try:
            descriptor = os.open(target, flags, 0o600)
        except FileExistsError as error:
            raise GuardError(GuardErrorCode.DESTINATION_EXISTS, str(target)) from error
        try:
            with os.fdopen(descriptor, "wb") as stream:
                _ = stream.write(content)
                stream.flush()
                os.fsync(stream.fileno())
        except BaseException:
            target.unlink(missing_ok=True)
            raise
        return target


def read_source(source: Path) -> bytes:
    """Read one ordinary, non-link source exactly once."""
    try:
        if source.is_symlink() or not source.is_file():
            raise GuardError(GuardErrorCode.SOURCE_INVALID, str(source))
        return source.read_bytes()
    except OSError as error:
        raise GuardError(GuardErrorCode.SOURCE_INVALID, str(error)) from error


def parser() -> argparse.ArgumentParser:
    """Build the CLI contract."""
    result = argparse.ArgumentParser(description=__doc__)
    subparsers = result.add_subparsers(dest="command", required=True)
    for command in ("plan", "apply"):
        subparser = subparsers.add_parser(command)
        _ = subparser.add_argument("--policy", required=True, type=Path)
        _ = subparser.add_argument("--source", required=True, type=Path)
        if command == "plan":
            _ = subparser.add_argument("--destination", required=True)
        else:
            _ = subparser.add_argument("--manifest", required=True, type=Path)
    return result


def main(arguments: list[str] | None = None) -> int:
    """Run the mutation guard CLI."""
    namespace = parser().parse_args(arguments)
    command = cast("str", namespace.command)
    policy_path = cast("Path", namespace.policy)
    source = cast("Path", namespace.source)
    try:
        guard = MutationGuard(Policy.load(policy_path))
        if command == "plan":
            destination = cast("str", namespace.destination)
            _ = sys.stdout.write(f"{guard.plan_create(destination, source).to_json()}\n")
        else:
            manifest_path = cast("Path", namespace.manifest)
            manifest = CreateManifest.from_json(manifest_path.read_text(encoding="utf-8"))
            _ = sys.stdout.write(f"{guard.apply_create(manifest, source)}\n")
    except (GuardError, OSError) as error:
        code = error.code if isinstance(error, GuardError) else GuardErrorCode.SOURCE_INVALID
        _ = sys.stderr.write(f"{json.dumps({'error': code, 'message': str(error)})}\n")
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
