# Copyright (c) 2026 pz-b42-mp-modding-skill contributors
"""Build reviewable, read-only Blender commands for vanilla FBX evidence."""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import TYPE_CHECKING, final

from pz_b42_mp_skill import OUTPUT_SCHEMA_VERSION
from pz_b42_mp_skill.guard_paths import (
    is_within,
    path_contains_link_or_reparse,
)
from pz_b42_mp_skill.guard_types import sha256_bytes

if TYPE_CHECKING:
    from pz_b42_mp_skill.discovery import DiscoveryResult

LABEL_PATTERN = re.compile(r"[A-Za-z][A-Za-z0-9_-]{0,63}")
MIN_SAMPLE_PATH_PARTS = 3


class FbxReferencePlanErrorCode(StrEnum):
    """Stable FBX reference planning failures."""

    PATH_INVALID = "fbx_reference_path_invalid"
    PATH_LINKED = "fbx_reference_path_linked"
    SAMPLE_INVALID = "fbx_reference_sample_invalid"


@final
class FbxReferencePlanError(Exception):
    """One typed FBX reference planning failure."""

    code: FbxReferencePlanErrorCode

    def __init__(self, code: FbxReferencePlanErrorCode, detail: str) -> None:
        """Create a stable planning failure."""
        super().__init__(detail)
        self.code = code


@dataclass(frozen=True)
class ReferenceSample:
    """One explicit installed vanilla FBX sample."""

    label: str
    relative_path: Path

    @classmethod
    def parse(cls, value: str) -> ReferenceSample:
        """Parse `label=media/models_X/path.fbx` without resolving it."""
        if "=" not in value:
            raise FbxReferencePlanError(
                FbxReferencePlanErrorCode.SAMPLE_INVALID,
                value,
            )
        label, raw_path = value.split("=", 1)
        relative = Path(raw_path)
        parts = tuple(part.casefold() for part in relative.parts)
        if (
            LABEL_PATTERN.fullmatch(label) is None
            or relative.is_absolute()
            or relative.drive
            or ".." in relative.parts
            or len(parts) < MIN_SAMPLE_PATH_PARTS
            or parts[:2] != ("media", "models_x")
            or relative.suffix.casefold() != ".fbx"
        ):
            raise FbxReferencePlanError(
                FbxReferencePlanErrorCode.SAMPLE_INVALID,
                value,
            )
        return cls(label, relative)

    def to_argument(self, resolved: Path) -> str:
        """Bind this label to one canonical installed file."""
        return f"{self.label}={resolved}"

    def to_document(self) -> dict[str, str]:
        """Return privacy-safe sample metadata."""
        return {
            "label": self.label,
            "relative_path": self.relative_path.as_posix(),
        }


@dataclass(frozen=True)
class FbxProbePlan:
    """Hash-bound Blender command for read-only FBX observations."""

    branch: str
    build_id: str
    command: tuple[str, ...]
    command_sha256: str
    samples: tuple[ReferenceSample, ...]

    def to_document(self) -> dict[str, object]:
        """Return a JSON-compatible probe plan."""
        return {
            "branch": self.branch,
            "build_id": self.build_id,
            "command": list(self.command),
            "command_sha256": self.command_sha256,
            "samples": [sample.to_document() for sample in self.samples],
            "schema_version": OUTPUT_SCHEMA_VERSION,
        }


def build_probe_plan(
    blender: Path,
    script: Path,
    discovery: DiscoveryResult,
    samples: tuple[ReferenceSample, ...],
) -> FbxProbePlan:
    """Resolve samples and build one deterministic Blender command."""
    resolved = tuple(_resolve_sample(discovery.install_root, sample) for sample in samples)
    arguments: list[str] = [
        str(blender),
        "--background",
        "--factory-startup",
        "--disable-autoexec",
        "--python",
        str(script),
        "--",
        "--game-root",
        str(discovery.install_root),
        "--build-id",
        discovery.build_id,
        "--branch",
        discovery.branch,
    ]
    for sample, path in zip(samples, resolved, strict=True):
        arguments.extend(("--sample", sample.to_argument(path)))
    command = tuple(arguments)
    command_sha256 = sha256_bytes("\0".join(command).encode())
    return FbxProbePlan(
        branch=discovery.branch,
        build_id=discovery.build_id,
        command=command,
        command_sha256=command_sha256,
        samples=samples,
    )


def _resolve_sample(install_root: Path, sample: ReferenceSample) -> Path:
    models_root = (install_root / "media" / "models_X").resolve(strict=True)
    lexical = (install_root / sample.relative_path).absolute()
    try:
        resolved = lexical.resolve(strict=True)
    except OSError as error:
        raise FbxReferencePlanError(
            FbxReferencePlanErrorCode.PATH_INVALID,
            sample.relative_path.as_posix(),
        ) from error
    if not resolved.is_file() or not is_within(resolved, models_root):
        raise FbxReferencePlanError(
            FbxReferencePlanErrorCode.PATH_INVALID,
            sample.relative_path.as_posix(),
        )
    if path_contains_link_or_reparse(lexical):
        raise FbxReferencePlanError(
            FbxReferencePlanErrorCode.PATH_LINKED,
            sample.relative_path.as_posix(),
        )
    return resolved
