# Copyright (c) 2026 pz-b42-mp-modding-skill contributors
"""Canonical workspace policy and path authorization."""

from __future__ import annotations

import json
import stat
from dataclasses import dataclass
from pathlib import Path
from typing import cast

from pz_b42_mp_skill.guard_types import (
    GuardError,
    GuardErrorCode,
    object_map,
    sha256_bytes,
    string_list,
)


@dataclass(frozen=True)
class Policy:
    """Canonical workspace authorization policy."""

    policy_path: Path
    workspace_root: Path
    allowed_output_roots: tuple[Path, ...]
    forbidden_roots: tuple[Path, ...]
    fingerprint: str

    @classmethod
    def load(cls, policy_path: Path) -> Policy:
        """Parse an exact workspace-root policy file."""
        try:
            policy_bytes = policy_path.read_bytes()
            document = object_map(
                cast("object", json.loads(policy_bytes.decode("utf-8"))),
                GuardErrorCode.INVALID_POLICY,
            )
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
            raise GuardError(GuardErrorCode.INVALID_POLICY, str(error)) from error
        if document.get("version") != 1:
            raise GuardError(GuardErrorCode.INVALID_POLICY, "invalid_version")
        workspace_value = document.get("workspace_root")
        if not isinstance(workspace_value, str):
            raise GuardError(GuardErrorCode.INVALID_POLICY, "workspace_root")
        workspace = resolve_directory(Path(workspace_value), GuardErrorCode.INVALID_POLICY)
        if known_forbidden(workspace):
            raise GuardError(GuardErrorCode.FORBIDDEN_ROOT, str(workspace))

        policy_location = policy_path.resolve(strict=True)
        if (
            policy_path.is_symlink()
            or is_reparse(policy_path)
            or policy_location != workspace / ".pz-skill-policy.json"
        ):
            raise GuardError(GuardErrorCode.INVALID_POLICY, "policy_location")

        allowed_values = string_list(document.get("allowed_output_roots"), "allowed_output_roots")
        if not allowed_values:
            raise GuardError(GuardErrorCode.INVALID_POLICY, "allowed_output_roots")
        allowed = tuple(resolve_relative_root(workspace, value) for value in allowed_values)
        forbidden_values = string_list(document.get("forbidden_roots", []), "forbidden_roots")
        forbidden = tuple(resolve_absolute_root(value) for value in forbidden_values)
        for output_root in allowed:
            if known_forbidden(output_root) or any(
                is_within(output_root, denied) for denied in forbidden
            ):
                raise GuardError(GuardErrorCode.FORBIDDEN_ROOT, str(output_root))
        return cls(
            policy_location,
            workspace,
            allowed,
            forbidden,
            sha256_bytes(policy_bytes),
        )

    def ensure_current(self) -> None:
        """Reject a policy changed after review."""
        try:
            current = self.policy_path.read_bytes()
        except OSError as error:
            raise GuardError(GuardErrorCode.POLICY_CHANGED, str(error)) from error
        if sha256_bytes(current) != self.fingerprint:
            raise GuardError(GuardErrorCode.POLICY_CHANGED, "policy_bytes_changed")


def authorize_destination(policy: Policy, destination: str) -> Path:
    """Resolve a relative destination and enforce every policy boundary."""
    relative = Path(destination)
    if (
        not destination
        or relative.is_absolute()
        or relative.drive
        or any(part in {"", ".", ".."} for part in relative.parts)
        or any(invalid_windows_name(part) for part in relative.parts)
    ):
        raise GuardError(GuardErrorCode.INVALID_DESTINATION, destination)
    lexical = policy.workspace_root / relative
    try:
        parent = lexical.parent.resolve(strict=True)
    except OSError as error:
        raise GuardError(GuardErrorCode.INVALID_DESTINATION, str(error)) from error
    if contains_link_or_reparse(policy.workspace_root, lexical.parent):
        raise GuardError(GuardErrorCode.PATH_ESCAPE, destination)
    target = parent / lexical.name
    if not is_within(target, policy.workspace_root):
        raise GuardError(GuardErrorCode.PATH_ESCAPE, destination)
    if not any(is_within(target, root) for root in policy.allowed_output_roots):
        raise GuardError(GuardErrorCode.PATH_ESCAPE, destination)
    if known_forbidden(target) or any(is_within(target, root) for root in policy.forbidden_roots):
        raise GuardError(GuardErrorCode.FORBIDDEN_ROOT, destination)
    return target


def resolve_directory(path: Path, code: GuardErrorCode) -> Path:
    """Strictly resolve an existing ordinary directory."""
    try:
        resolved = path.resolve(strict=True)
    except OSError as error:
        raise GuardError(code, str(error)) from error
    if not resolved.is_dir():
        raise GuardError(code, str(resolved))
    return resolved


def resolve_relative_root(workspace: Path, value: str) -> Path:
    """Resolve one policy output root."""
    relative = Path(value)
    if relative.is_absolute() or relative.drive or not relative.parts or ".." in relative.parts:
        raise GuardError(GuardErrorCode.INVALID_POLICY, value)
    resolved = resolve_directory(workspace / relative, GuardErrorCode.INVALID_POLICY)
    if not is_within(resolved, workspace):
        raise GuardError(GuardErrorCode.PATH_ESCAPE, value)
    return resolved


def resolve_absolute_root(value: str) -> Path:
    """Resolve one explicit forbidden root."""
    path = Path(value)
    if not path.is_absolute():
        raise GuardError(GuardErrorCode.INVALID_POLICY, value)
    return path.resolve(strict=False)


def is_within(path: Path, root: Path) -> bool:
    """Use path components, not prefixes, for containment."""
    try:
        _ = path.relative_to(root)
    except ValueError:
        return False
    return True


def contains_link_or_reparse(workspace: Path, parent: Path) -> bool:
    """Detect static link/reparse escapes below a canonical workspace."""
    try:
        relative = parent.relative_to(workspace)
    except ValueError:
        return True
    cursor = workspace
    for part in relative.parts:
        cursor /= part
        if cursor.is_symlink() or is_reparse(cursor):
            return True
    return False


def path_contains_link_or_reparse(path: Path) -> bool:
    """Inspect a path spelling without requiring its canonical workspace prefix."""
    absolute = path.absolute()
    return any(
        candidate.is_symlink() or is_reparse(candidate)
        for candidate in (absolute, *absolute.parents)
    )


def is_reparse(path: Path) -> bool:
    """Return whether Windows marks a path as a reparse point."""
    try:
        attributes = getattr(path.lstat(), "st_file_attributes", 0)
    except OSError:
        return False
    return bool(attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT)


def known_forbidden(path: Path) -> bool:
    """Match protected roots by complete path components."""
    parts = tuple(part.casefold() for part in path.parts)
    sequences = (
        ("steamapps", "common", "projectzomboid"),
        ("steamapps", "workshop", "content", "108600"),
        ("zomboid", "saves"),
        ("zomboid", "server"),
    )
    credentials = {".ssh", ".aws", ".azure", ".kube"}
    return any(contains_sequence(parts, sequence) for sequence in sequences) or any(
        part in credentials for part in parts
    )


def contains_sequence(parts: tuple[str, ...], sequence: tuple[str, ...]) -> bool:
    """Match a path sequence with component boundaries."""
    width = len(sequence)
    return any(parts[index : index + width] == sequence for index in range(len(parts) - width + 1))


def invalid_windows_name(part: str) -> bool:
    """Reject Windows devices, ADS syntax, and ambiguous trailing characters."""
    if ":" in part or part.endswith((" ", ".")):
        return True
    stem = part.split(".", 1)[0].casefold()
    reserved = {"con", "prn", "aux", "nul", "clock$"}
    reserved.update(f"{prefix}{number}" for prefix in ("com", "lpt") for number in range(1, 10))
    return stem in reserved
