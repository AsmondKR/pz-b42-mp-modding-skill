# Copyright (c) 2026 pz-b42-mp-modding-skill contributors
"""Read-only preflight validation for Build 42 multiplayer mod packages."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import cast, final

from pz_b42_mp_skill.guard_paths import is_reparse


class ValidationCode(StrEnum):
    """Stable structural preflight issue categories."""

    CLIENT_COMMAND_BOUNDARY_MISSING = "client_command_boundary_missing"
    CLIENT_LUA_MISSING = "client_lua_missing"
    LINK_PATH = "link_path"
    MOD_DIRECTORY_INVALID = "mod_directory_invalid"
    MOD_ID_MISMATCH = "mod_id_mismatch"
    MOD_ID_MISSING = "mod_id_missing"
    MOD_INFO_MISSING = "mod_info_missing"
    READ_FAILED = "read_failed"
    SERVER_COMMAND_BOUNDARY_MISSING = "server_command_boundary_missing"
    SERVER_LUA_MISSING = "server_lua_missing"
    SHARED_LUA_MISSING = "shared_lua_missing"
    WORKSHOP_MISSING = "workshop_missing"


class ModValidationErrorCode(StrEnum):
    """Stable invocation failure categories."""

    MOD_ROOT_LINKED = "mod_root_linked"
    MOD_ROOT_MISSING = "mod_root_missing"


@final
class ModValidationError(Exception):
    """A preflight invocation failure with a stable code."""

    code: ModValidationErrorCode

    def __init__(self, code: ModValidationErrorCode, detail: str) -> None:
        """Create one typed invocation failure."""
        super().__init__(detail)
        self.code = code


@dataclass(frozen=True)
class ValidationIssue:
    """One deterministic package preflight issue."""

    code: ValidationCode
    relative_path: str
    message: str


@dataclass(frozen=True)
class ModValidationResult:
    """Complete read-only validation result for one mod root."""

    mod_root: Path
    mod_id: str | None
    issues: tuple[ValidationIssue, ...]

    @property
    def valid(self) -> bool:
        """Return whether no structural issues were found."""
        return not self.issues

    def to_document(self) -> dict[str, object]:
        """Return a JSON-compatible result."""
        return {
            "issues": [
                {
                    "code": issue.code,
                    "message": issue.message,
                    "relative_path": issue.relative_path,
                }
                for issue in self.issues
            ],
            "mod_id": self.mod_id,
            "mod_root": str(self.mod_root),
            "valid": self.valid,
        }


@dataclass(frozen=True)
class _BoundaryRequirement:
    directory: Path
    token: str
    code: ValidationCode


def validate_mod_root(mod_root: Path) -> ModValidationResult:
    """Validate package structure without changing the mod."""
    if mod_root.is_symlink() or is_reparse(mod_root):
        raise ModValidationError(ModValidationErrorCode.MOD_ROOT_LINKED, str(mod_root))
    if not mod_root.is_dir():
        raise ModValidationError(ModValidationErrorCode.MOD_ROOT_MISSING, str(mod_root))
    root = mod_root.resolve(strict=True)
    linked = _linked_paths(root)
    if linked:
        link_issues = tuple(
            _issue(ValidationCode.LINK_PATH, path.relative_to(root), "linked path")
            for path in linked
        )
        return ModValidationResult(root, None, link_issues)

    issues: list[ValidationIssue] = []
    _ = _require_file(root, root / "workshop.txt", ValidationCode.WORKSHOP_MISSING, issues)
    mods_root = root / "Contents" / "mods"
    mod_directories = (
        sorted(path for path in mods_root.iterdir() if path.is_dir()) if mods_root.is_dir() else []
    )
    if len(mod_directories) != 1:
        issues.append(
            _issue(
                ValidationCode.MOD_DIRECTORY_INVALID,
                mods_root.relative_to(root),
                "expected exactly one Contents/mods child directory",
            ),
        )
        return ModValidationResult(root, None, tuple(issues))

    mod_directory = mod_directories[0]
    mod_id = mod_directory.name
    version_root = mod_directory / "42"
    mod_info = version_root / "mod.info"
    if _require_file(root, mod_info, ValidationCode.MOD_INFO_MISSING, issues):
        metadata = _read_metadata(root, mod_info, issues)
        declared_id = metadata.get("id")
        if declared_id is None:
            issues.append(
                _issue(ValidationCode.MOD_ID_MISSING, mod_info.relative_to(root), "missing id"),
            )
        elif declared_id != mod_id:
            issues.append(
                _issue(
                    ValidationCode.MOD_ID_MISMATCH,
                    mod_info.relative_to(root),
                    f"declared {declared_id!r}, directory {mod_id!r}",
                ),
            )

    lua_root = version_root / "media" / "lua"
    client_files = _lua_files(root, lua_root / "client", ValidationCode.CLIENT_LUA_MISSING, issues)
    server_files = _lua_files(root, lua_root / "server", ValidationCode.SERVER_LUA_MISSING, issues)
    _ = _lua_files(root, lua_root / "shared", ValidationCode.SHARED_LUA_MISSING, issues)
    _require_boundary(
        root,
        client_files,
        _BoundaryRequirement(
            lua_root / "client",
            "Events.OnServerCommand.Add",
            ValidationCode.CLIENT_COMMAND_BOUNDARY_MISSING,
        ),
        issues,
    )
    _require_boundary(
        root,
        server_files,
        _BoundaryRequirement(
            lua_root / "server",
            "Events.OnClientCommand.Add",
            ValidationCode.SERVER_COMMAND_BOUNDARY_MISSING,
        ),
        issues,
    )
    return ModValidationResult(root, mod_id, tuple(issues))


def _linked_paths(root: Path) -> list[Path]:
    return sorted(path for path in root.rglob("*") if path.is_symlink() or is_reparse(path))


def _require_file(
    root: Path,
    path: Path,
    code: ValidationCode,
    issues: list[ValidationIssue],
) -> bool:
    if path.is_file():
        return True
    issues.append(_issue(code, path.relative_to(root), "required file missing"))
    return False


def _read_metadata(
    root: Path,
    path: Path,
    issues: list[ValidationIssue],
) -> dict[str, str]:
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError as error:
        issues.append(_issue(ValidationCode.READ_FAILED, path.relative_to(root), str(error)))
        return {}
    return {
        key.strip(): value.strip()
        for line in lines
        if "=" in line
        for key, value in (line.split("=", 1),)
    }


def _lua_files(
    root: Path,
    directory: Path,
    code: ValidationCode,
    issues: list[ValidationIssue],
) -> tuple[Path, ...]:
    files = tuple(sorted(directory.rglob("*.lua"))) if directory.is_dir() else ()
    if not files:
        issues.append(_issue(code, directory.relative_to(root), "Lua file missing"))
    return files


def _require_boundary(
    root: Path,
    files: tuple[Path, ...],
    requirement: _BoundaryRequirement,
    issues: list[ValidationIssue],
) -> None:
    for path in files:
        try:
            if requirement.token in path.read_text(encoding="utf-8", errors="replace"):
                return
        except OSError as error:
            issues.append(_issue(ValidationCode.READ_FAILED, path.relative_to(root), str(error)))
    issues.append(
        _issue(
            requirement.code,
            requirement.directory.relative_to(root),
            f"missing {requirement.token}",
        ),
    )


def _issue(code: ValidationCode, path: Path, message: str) -> ValidationIssue:
    return ValidationIssue(code, path.as_posix(), message)


def parser() -> argparse.ArgumentParser:
    """Build the preflight CLI parser."""
    result = argparse.ArgumentParser(description=__doc__)
    _ = result.add_argument("--mod-root", required=True, type=Path)
    _ = result.add_argument("--json", action="store_true")
    return result


def main(arguments: list[str] | None = None) -> int:
    """Run one read-only mod preflight."""
    namespace = parser().parse_args(arguments)
    try:
        result = validate_mod_root(cast("Path", namespace.mod_root))
    except ModValidationError as error:
        _ = sys.stderr.write(
            f"{json.dumps({'error': error.code, 'message': str(error)})}\n",
        )
        return 2
    if cast("bool", namespace.json):
        _ = sys.stdout.write(f"{json.dumps(result.to_document(), indent=2, sort_keys=True)}\n")
    elif result.valid:
        _ = sys.stdout.write(f"PASS {result.mod_id} at {result.mod_root}\n")
    else:
        for issue in result.issues:
            _ = sys.stdout.write(f"{issue.code} {issue.relative_path}: {issue.message}\n")
    return 0 if result.valid else 1


if __name__ == "__main__":
    raise SystemExit(main())
