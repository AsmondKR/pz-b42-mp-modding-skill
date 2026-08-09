# Copyright (c) 2026 pz-b42-mp-modding-skill contributors
"""Read-only preflight validation for Build 42 multiplayer mod packages."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import TYPE_CHECKING, final

from pz_b42_mp_skill.guard_paths import is_reparse
from pz_b42_mp_skill.mod_metadata import (
    MetadataReadError,
    missing_fields,
    read_key_values,
    semicolon_values,
)

if TYPE_CHECKING:
    from pathlib import Path

_WORKSHOP_FIELDS = ("version", "workshopid", "title", "description", "visibility", "tags")
_WORKSHOP_TAGS = ("Build 42", "Multiplayer")
_MOD_INFO_FIELDS = ("name", "author", "description")


class ValidationCode(StrEnum):
    """Stable structural preflight issue categories."""

    CLIENT_COMMAND_BOUNDARY_MISSING = "client_command_boundary_missing"
    CLIENT_LUA_MISSING = "client_lua_missing"
    LINK_PATH = "link_path"
    MOD_DIRECTORY_INVALID = "mod_directory_invalid"
    MOD_ID_MISMATCH = "mod_id_mismatch"
    MOD_ID_MISSING = "mod_id_missing"
    MOD_INFO_FIELD_MISSING = "mod_info_field_missing"
    MOD_INFO_MISSING = "mod_info_missing"
    READ_FAILED = "read_failed"
    SERVER_COMMAND_BOUNDARY_MISSING = "server_command_boundary_missing"
    SERVER_LUA_MISSING = "server_lua_missing"
    SHARED_LUA_MISSING = "shared_lua_missing"
    WORKSHOP_FIELD_MISSING = "workshop_field_missing"
    WORKSHOP_MISSING = "workshop_missing"
    WORKSHOP_TAG_MISSING = "workshop_tag_missing"


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
    _validate_workshop(root, issues)
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
        metadata = _validate_metadata(
            root,
            mod_info,
            _MOD_INFO_FIELDS,
            ValidationCode.MOD_INFO_FIELD_MISSING,
            issues,
        )
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


def _validate_workshop(root: Path, issues: list[ValidationIssue]) -> None:
    workshop = root / "workshop.txt"
    if not _require_file(root, workshop, ValidationCode.WORKSHOP_MISSING, issues):
        return
    metadata = _validate_metadata(
        root,
        workshop,
        _WORKSHOP_FIELDS,
        ValidationCode.WORKSHOP_FIELD_MISSING,
        issues,
    )
    tags = semicolon_values(metadata.get("tags", ""))
    issues.extend(
        _issue(
            ValidationCode.WORKSHOP_TAG_MISSING,
            workshop.relative_to(root),
            f"missing tag {tag!r}",
        )
        for tag in _WORKSHOP_TAGS
        if tag not in tags
    )


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


def _validate_metadata(
    root: Path,
    path: Path,
    required: tuple[str, ...],
    missing_code: ValidationCode,
    issues: list[ValidationIssue],
) -> dict[str, str]:
    try:
        metadata = read_key_values(path)
    except MetadataReadError as error:
        issues.append(_issue(ValidationCode.READ_FAILED, path.relative_to(root), str(error)))
        return {}
    issues.extend(
        _issue(
            missing_code,
            path.relative_to(root),
            f"missing field {field!r}",
        )
        for field in missing_fields(metadata, required)
    )
    return metadata


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
