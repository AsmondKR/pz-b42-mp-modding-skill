# Copyright (c) 2026 pz-b42-mp-modding-skill contributors
"""Launch Blender without a shell and parse its versioned result."""

from __future__ import annotations

import os
import shutil
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import TYPE_CHECKING, final

from pz_b42_mp_skill.blender_entry import BlenderMode
from pz_b42_mp_skill.guard_types import sha256_bytes

if TYPE_CHECKING:
    from pz_b42_mp_skill.asset_manifest import BlenderAssetManifest


class BlenderRunErrorCode(StrEnum):
    """Stable launcher failure categories."""

    BLENDER_MISSING = "blender_missing"
    BLENDER_SCRIPT_MISSING = "blender_script_missing"
    DESTINATION_EXISTS = "destination_exists"


@final
class BlenderRunError(Exception):
    """One typed Blender launcher failure."""

    code: BlenderRunErrorCode

    def __init__(self, code: BlenderRunErrorCode, detail: str) -> None:
        """Create one stable launcher failure."""
        super().__init__(detail)
        self.code = code


@dataclass(frozen=True)
class BlenderLaunchPlan:
    """Reviewable command for one Blender validation or export."""

    command: tuple[str, ...]
    command_sha256: str
    mode: BlenderMode

    def to_document(self) -> dict[str, object]:
        """Return a JSON-compatible launch plan."""
        return {
            "command": list(self.command),
            "command_sha256": self.command_sha256,
            "mode": self.mode,
            "schema_version": 1,
        }


def discover_blender(explicit: Path | None = None) -> Path:
    """Resolve an explicit, PATH, or conventional Blender executable."""
    if explicit is not None:
        return _executable(explicit)
    command = shutil.which("blender")
    if command is not None:
        return _executable(Path(command))
    candidates: list[Path] = []
    for variable in ("ProgramFiles", "ProgramW6432"):
        root = os.environ.get(variable)
        if root:
            candidates.extend(Path(root).glob("Blender Foundation/Blender */blender.exe"))
    if candidates:
        return _executable(max(candidates))
    raise BlenderRunError(BlenderRunErrorCode.BLENDER_MISSING, "blender executable")


def installed_blender_script() -> Path:
    """Return the Blender-internal script shipped with the skill."""
    path = Path(__file__).resolve().with_name("blender_asset_script.py")
    if not path.is_file():
        raise BlenderRunError(BlenderRunErrorCode.BLENDER_SCRIPT_MISSING, str(path))
    return path


def build_blender_command(
    blender: Path,
    script: Path,
    manifest: BlenderAssetManifest,
    policy_path: Path,
    mode: BlenderMode | str,
) -> tuple[str, ...]:
    """Build one shell-free, auto-execution-disabled Blender command."""
    selected_mode = BlenderMode(mode)
    return (
        str(blender),
        "--background",
        "--factory-startup",
        "--disable-autoexec",
        str(manifest.source_blend),
        "--python",
        str(script),
        "--",
        "--manifest",
        str(manifest.manifest_path),
        "--mode",
        selected_mode,
        "--policy",
        str(policy_path),
    )


def plan_blender_asset(
    blender: Path,
    manifest: BlenderAssetManifest,
    policy_path: Path,
    mode: BlenderMode | str,
) -> BlenderLaunchPlan:
    """Build and hash a reviewable Blender command without executing it."""
    selected_mode = BlenderMode(mode)
    if selected_mode is BlenderMode.EXPORT and manifest.output_fbx.exists():
        raise BlenderRunError(
            BlenderRunErrorCode.DESTINATION_EXISTS,
            manifest.workspace_root_relative(manifest.output_fbx),
        )
    script = installed_blender_script()
    command = build_blender_command(
        blender,
        script,
        manifest,
        policy_path,
        selected_mode,
    )
    command_bytes = "\0".join(command).encode()
    return BlenderLaunchPlan(command, sha256_bytes(command_bytes), selected_mode)


def _executable(path: Path) -> Path:
    try:
        resolved = path.resolve(strict=True)
    except OSError as error:
        raise BlenderRunError(BlenderRunErrorCode.BLENDER_MISSING, str(path)) from error
    if not resolved.is_file():
        raise BlenderRunError(BlenderRunErrorCode.BLENDER_MISSING, str(resolved))
    return resolved
