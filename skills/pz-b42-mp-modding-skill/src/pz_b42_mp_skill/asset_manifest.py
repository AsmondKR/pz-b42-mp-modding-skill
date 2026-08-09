# Copyright (c) 2026 pz-b42-mp-modding-skill contributors
"""Typed, policy-bound Blender asset manifests."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import TypeVar, cast, final

from pz_b42_mp_skill import OUTPUT_SCHEMA_VERSION
from pz_b42_mp_skill.guard_paths import (
    Policy,
    authorize_destination,
    contains_link_or_reparse,
    invalid_windows_name,
    is_reparse,
    is_within,
)
from pz_b42_mp_skill.guard_types import GuardError

ASSET_ID_PATTERN = re.compile(r"[A-Za-z][A-Za-z0-9_-]{0,63}")
IMAGE_SUFFIXES = frozenset({".bmp", ".exr", ".jpeg", ".jpg", ".png", ".tga", ".tif", ".tiff"})
EnumField = TypeVar("EnumField", bound=StrEnum)


class AssetProfile(StrEnum):
    """Blender production profiles with separate evidence needs."""

    HELD_MODEL = "held_model"
    RIGGED_MODEL = "rigged_model"
    STATIC_MODEL = "static_model"
    VEHICLE_MODEL = "vehicle_model"


class TopologyPolicy(StrEnum):
    """Declared geometry boundary policy."""

    CLOSED_SOLID = "closed_solid"
    MIXED = "mixed"
    OPEN_SURFACE = "open_surface"


class AssetManifestErrorCode(StrEnum):
    """Stable asset-manifest refusal categories."""

    ASSET_ID_INVALID = "asset_id_invalid"
    DESTINATION_EXISTS = "destination_exists"
    EXPORT_OBJECTS_INVALID = "export_objects_invalid"
    FIELD_INVALID = "field_invalid"
    INPUT_MISSING = "input_missing"
    INPUT_SUFFIX_INVALID = "input_suffix_invalid"
    JSON_INVALID = "json_invalid"
    LINK_PATH = "link_path"
    MANIFEST_INVALID = "manifest_invalid"
    MANIFEST_MISSING = "manifest_missing"
    PATH_OUTSIDE_MANIFEST_ROOT = "path_outside_manifest_root"
    PROFILE_INVALID = "profile_invalid"
    SCHEMA_UNSUPPORTED = "schema_unsupported"


@final
class AssetManifestError(Exception):
    """One typed refusal while parsing an untrusted asset manifest."""

    code: AssetManifestErrorCode

    def __init__(self, code: AssetManifestErrorCode, detail: str) -> None:
        """Create a refusal with a stable code."""
        super().__init__(detail)
        self.code = code


@dataclass(frozen=True)
class BlenderAssetManifest:
    """Canonical inputs and policy-authorized output for one Blender asset."""

    asset_id: str
    export_objects: tuple[str, ...]
    expected_armature: str | None
    manifest_path: Path
    max_vertex_influences: int | None
    output_fbx: Path
    profile: AssetProfile
    source_blend: Path
    texture_files: tuple[Path, ...]
    topology_policy: TopologyPolicy
    triangle_budget: int
    workspace_root: Path

    def to_document(self) -> dict[str, object]:
        """Return a JSON-compatible, workspace-relative manifest."""
        relative = self.workspace_root_relative
        return {
            "asset_id": self.asset_id,
            "export_objects": list(self.export_objects),
            "expected_armature": self.expected_armature,
            "manifest": relative(self.manifest_path),
            "max_vertex_influences": self.max_vertex_influences,
            "output_fbx": relative(self.output_fbx),
            "profile": self.profile,
            "schema_version": OUTPUT_SCHEMA_VERSION,
            "source_blend": relative(self.source_blend),
            "texture_files": [relative(path) for path in self.texture_files],
            "topology_policy": self.topology_policy,
            "triangle_budget": self.triangle_budget,
        }

    def workspace_root_relative(self, path: Path) -> str:
        """Render one canonical path relative to the authorized workspace."""
        return path.relative_to(self.workspace_root).as_posix()


def load_asset_manifest(manifest_path: Path, policy: Policy) -> BlenderAssetManifest:
    """Parse one exact asset manifest inside an authorized workspace."""
    path = _resolve_manifest_path(manifest_path, policy)
    try:
        value = cast("object", json.loads(path.read_text(encoding="utf-8")))
    except json.JSONDecodeError as error:
        raise AssetManifestError(AssetManifestErrorCode.JSON_INVALID, str(error)) from error
    except OSError as error:
        raise AssetManifestError(AssetManifestErrorCode.MANIFEST_MISSING, str(error)) from error
    document = _object_map(value)
    if document.get("schema_version") != OUTPUT_SCHEMA_VERSION:
        raise AssetManifestError(
            AssetManifestErrorCode.SCHEMA_UNSUPPORTED,
            str(document.get("schema_version")),
        )
    asset_id = _asset_id(document.get("asset_id"))
    profile = _enum_field(AssetProfile, document.get("profile"), "profile")
    topology = _enum_field(
        TopologyPolicy,
        document.get("topology_policy"),
        "topology_policy",
    )
    source = _input_path(policy, document.get("source_blend"), ".blend")
    textures = tuple(
        _input_path(policy, item, IMAGE_SUFFIXES)
        for item in _string_list(document.get("texture_files"), "texture_files")
    )
    if not textures:
        raise AssetManifestError(AssetManifestErrorCode.FIELD_INVALID, "texture_files")
    output = _output_path(policy, document.get("output_fbx"))
    export_objects = _unique_names(document.get("export_objects"))
    triangle_budget = _positive_int(document.get("triangle_budget"), "triangle_budget")
    expected_armature, max_influences = _rig_fields(document, profile)
    _reject_unknown_fields(document, profile)
    policy.ensure_current()
    return BlenderAssetManifest(
        asset_id=asset_id,
        export_objects=export_objects,
        expected_armature=expected_armature,
        manifest_path=path,
        max_vertex_influences=max_influences,
        output_fbx=output,
        profile=profile,
        source_blend=source,
        texture_files=textures,
        topology_policy=topology,
        triangle_budget=triangle_budget,
        workspace_root=policy.workspace_root,
    )


def _resolve_manifest_path(path: Path, policy: Policy) -> Path:
    try:
        lexical = path.absolute()
        resolved = path.resolve(strict=True)
    except OSError as error:
        raise AssetManifestError(AssetManifestErrorCode.MANIFEST_MISSING, str(error)) from error
    if (
        not resolved.is_file()
        or not is_within(resolved, policy.workspace_root)
        or contains_link_or_reparse(policy.workspace_root, lexical)
        or lexical.is_symlink()
        or is_reparse(lexical)
    ):
        raise AssetManifestError(AssetManifestErrorCode.LINK_PATH, str(path))
    return resolved


def _object_map(value: object) -> dict[str, object]:
    if not isinstance(value, dict):
        raise AssetManifestError(AssetManifestErrorCode.MANIFEST_INVALID, "expected_object")
    values = cast("dict[object, object]", value)
    if not all(isinstance(key, str) for key in values):
        raise AssetManifestError(AssetManifestErrorCode.MANIFEST_INVALID, "string_keys")
    return {cast("str", key): item for key, item in values.items()}


def _asset_id(value: object) -> str:
    if not isinstance(value, str) or ASSET_ID_PATTERN.fullmatch(value) is None:
        raise AssetManifestError(AssetManifestErrorCode.ASSET_ID_INVALID, str(value))
    return value


def _enum_field(kind: type[EnumField], value: object, field: str) -> EnumField:
    if not isinstance(value, str):
        raise AssetManifestError(AssetManifestErrorCode.FIELD_INVALID, field)
    try:
        return kind(value)
    except ValueError as error:
        code = (
            AssetManifestErrorCode.PROFILE_INVALID
            if field == "profile"
            else AssetManifestErrorCode.FIELD_INVALID
        )
        raise AssetManifestError(code, f"{field}:{value}") from error


def _relative_value(value: object, field: str) -> str:
    if not isinstance(value, str):
        raise AssetManifestError(AssetManifestErrorCode.FIELD_INVALID, field)
    relative = Path(value)
    if (
        not value
        or relative.is_absolute()
        or relative.drive
        or any(part in {"", ".", ".."} or invalid_windows_name(part) for part in relative.parts)
    ):
        raise AssetManifestError(AssetManifestErrorCode.PATH_OUTSIDE_MANIFEST_ROOT, field)
    return value


def _input_path(policy: Policy, value: object, suffixes: str | frozenset[str]) -> Path:
    relative = _relative_value(value, "input")
    lexical = policy.workspace_root / relative
    try:
        resolved = lexical.resolve(strict=True)
    except OSError as error:
        raise AssetManifestError(AssetManifestErrorCode.INPUT_MISSING, relative) from error
    if (
        not resolved.is_file()
        or not is_within(resolved, policy.workspace_root)
        or contains_link_or_reparse(policy.workspace_root, lexical)
        or lexical.is_symlink()
        or is_reparse(lexical)
    ):
        raise AssetManifestError(AssetManifestErrorCode.LINK_PATH, relative)
    allowed = {suffixes} if isinstance(suffixes, str) else suffixes
    if resolved.suffix.casefold() not in allowed:
        raise AssetManifestError(AssetManifestErrorCode.INPUT_SUFFIX_INVALID, relative)
    return resolved


def _output_path(policy: Policy, value: object) -> Path:
    relative = _relative_value(value, "output_fbx")
    try:
        output = authorize_destination(policy, relative)
    except GuardError as error:
        code = (
            AssetManifestErrorCode.PATH_OUTSIDE_MANIFEST_ROOT
            if error.code.value in {"invalid_destination", "path_escape"}
            else AssetManifestErrorCode.LINK_PATH
        )
        raise AssetManifestError(code, str(error)) from error
    if output.suffix.casefold() != ".fbx":
        raise AssetManifestError(AssetManifestErrorCode.INPUT_SUFFIX_INVALID, relative)
    return output


def _string_list(value: object, field: str) -> list[str]:
    if not isinstance(value, list):
        raise AssetManifestError(AssetManifestErrorCode.FIELD_INVALID, field)
    values = cast("list[object]", value)
    if not all(isinstance(item, str) for item in values):
        raise AssetManifestError(AssetManifestErrorCode.FIELD_INVALID, field)
    return [cast("str", item) for item in values]


def _unique_names(value: object) -> tuple[str, ...]:
    names = tuple(_string_list(value, "export_objects"))
    if not names or len(names) != len(set(names)) or any(not name.strip() for name in names):
        raise AssetManifestError(
            AssetManifestErrorCode.EXPORT_OBJECTS_INVALID,
            "export_objects",
        )
    return names


def _positive_int(value: object, field: str) -> int:
    if type(value) is not int or value <= 0:
        raise AssetManifestError(AssetManifestErrorCode.FIELD_INVALID, field)
    return value


def _rig_fields(
    document: dict[str, object],
    profile: AssetProfile,
) -> tuple[str | None, int | None]:
    if profile is not AssetProfile.RIGGED_MODEL:
        return None, None
    armature = document.get("expected_armature")
    if not isinstance(armature, str) or not armature.strip():
        raise AssetManifestError(AssetManifestErrorCode.FIELD_INVALID, "expected_armature")
    return armature, _positive_int(document.get("max_vertex_influences"), "max_vertex_influences")


def _reject_unknown_fields(document: dict[str, object], profile: AssetProfile) -> None:
    fields = {
        "asset_id",
        "export_objects",
        "output_fbx",
        "profile",
        "schema_version",
        "source_blend",
        "texture_files",
        "topology_policy",
        "triangle_budget",
    }
    if profile is AssetProfile.RIGGED_MODEL:
        fields.update({"expected_armature", "max_vertex_influences"})
    unknown = set(document) - fields
    if unknown:
        raise AssetManifestError(
            AssetManifestErrorCode.MANIFEST_INVALID,
            f"unknown_fields:{','.join(sorted(unknown))}",
        )
