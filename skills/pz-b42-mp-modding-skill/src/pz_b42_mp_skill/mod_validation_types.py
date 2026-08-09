# Copyright (c) 2026 pz-b42-mp-modding-skill contributors
"""Typed results and stable codes for multiplayer mod preflight."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import TYPE_CHECKING, final

from pz_b42_mp_skill import OUTPUT_SCHEMA_VERSION

if TYPE_CHECKING:
    from pathlib import Path


class ValidationCode(StrEnum):
    """Stable structural preflight issue categories."""

    BUILD_42_DIRECTORY_MISSING = "build_42_directory_missing"
    CLIENT_COMMAND_BOUNDARY_MISSING = "client_command_boundary_missing"
    CLIENT_LUA_MISSING = "client_lua_missing"
    LEGACY_UNVERSIONED_LAYOUT = "legacy_unversioned_layout"
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
            "schema_version": OUTPUT_SCHEMA_VERSION,
            "valid": self.valid,
        }
