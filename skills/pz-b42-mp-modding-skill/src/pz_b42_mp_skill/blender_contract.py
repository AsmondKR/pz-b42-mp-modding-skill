# Copyright (c) 2026 pz-b42-mp-modding-skill contributors
"""Pure scene snapshots and objective Blender quality gates."""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import StrEnum

from pz_b42_mp_skill.asset_manifest import (
    AssetProfile,
    BlenderAssetManifest,
    TopologyPolicy,
)

TRANSFORM_TOLERANCE = 1e-6


class AssetIssueClass(StrEnum):
    """Evidence class for one objective finding."""

    INVARIANT = "invariant"
    PROJECT_BUDGET = "project_budget"
    PROJECT_POLICY = "project_policy"


class AssetIssueCode(StrEnum):
    """Stable machine-readable Blender scene issue codes."""

    ARMATURE_COUNT_INVALID = "armature_count_invalid"
    ARMATURE_MODIFIER_MISSING = "armature_modifier_missing"
    ARMATURE_NAME_INVALID = "armature_name_invalid"
    DEGENERATE_DIMENSIONS = "degenerate_dimensions"
    DEGENERATE_FACE = "degenerate_face"
    DUPLICATE_OBJECT_NAME = "duplicate_object_name"
    LOOSE_GEOMETRY = "loose_geometry"
    MATERIAL_MISSING = "material_missing"
    MESH_MISSING = "mesh_missing"
    MISSING_EXPORT_OBJECT = "missing_export_object"
    MISSING_IMAGE = "missing_image"
    NGON_PRESENT = "ngon_present"
    NON_MANIFOLD_GEOMETRY = "non_manifold_geometry"
    ROUNDTRIP_MISMATCH = "roundtrip_mismatch"
    TRANSFORMS_UNAPPLIED = "transforms_unapplied"
    TRIANGLE_BUDGET_EXCEEDED = "triangle_budget_exceeded"
    UNAPPLIED_MODIFIER = "unapplied_modifier"
    UV_MISSING = "uv_missing"
    VERTEX_INFLUENCE_LIMIT_EXCEEDED = "vertex_influence_limit_exceeded"
    VERTEX_WEIGHTS_UNNORMALIZED = "vertex_weights_unnormalized"


@dataclass(frozen=True)
class MeshSnapshot:
    """Objective measurements for one declared export mesh."""

    armature_modifiers: int
    dimensions: tuple[float, float, float]
    material_slots: int
    max_vertex_influences: int
    name: str
    non_manifold_edges: int
    rotation_radians: tuple[float, float, float]
    scale: tuple[float, float, float]
    triangles: int
    unnormalized_vertices: int
    unapplied_modifiers: int
    uv_layers: int
    degenerate_faces: int = 0
    loose_vertices: int = 0
    ngons: int = 0

    def to_document(self) -> dict[str, object]:
        """Return a JSON-compatible measurement document."""
        return {
            "armature_modifiers": self.armature_modifiers,
            "degenerate_faces": self.degenerate_faces,
            "dimensions": list(self.dimensions),
            "loose_vertices": self.loose_vertices,
            "material_slots": self.material_slots,
            "max_vertex_influences": self.max_vertex_influences,
            "name": self.name,
            "ngons": self.ngons,
            "non_manifold_edges": self.non_manifold_edges,
            "rotation_radians": list(self.rotation_radians),
            "scale": list(self.scale),
            "triangles": self.triangles,
            "unnormalized_vertices": self.unnormalized_vertices,
            "unapplied_modifiers": self.unapplied_modifiers,
            "uv_layers": self.uv_layers,
        }


@dataclass(frozen=True)
class SceneSnapshot:
    """Objective measurements for an explicit Blender export set."""

    armature_names: tuple[str, ...]
    duplicate_object_names: tuple[str, ...]
    meshes: tuple[MeshSnapshot, ...]
    missing_images: tuple[str, ...]
    missing_export_objects: tuple[str, ...] = ()

    def to_document(self) -> dict[str, object]:
        """Return a JSON-compatible scene measurement document."""
        return {
            "armature_names": list(self.armature_names),
            "duplicate_object_names": list(self.duplicate_object_names),
            "meshes": [mesh.to_document() for mesh in self.meshes],
            "missing_export_objects": list(self.missing_export_objects),
            "missing_images": list(self.missing_images),
        }


@dataclass(frozen=True)
class AssetIssue:
    """One objective scene finding."""

    code: AssetIssueCode
    issue_class: AssetIssueClass
    message: str
    object_name: str | None = None

    def to_document(self) -> dict[str, object]:
        """Return a JSON-compatible issue document."""
        return {
            "class": self.issue_class,
            "code": self.code,
            "message": self.message,
            "object_name": self.object_name,
        }


def validate_scene(
    scene: SceneSnapshot,
    manifest: BlenderAssetManifest,
) -> tuple[AssetIssue, ...]:
    """Apply objective, manifest-declared quality gates."""
    issues = [
        _invariant(AssetIssueCode.MISSING_EXPORT_OBJECT, name, name)
        for name in scene.missing_export_objects
    ]
    issues.extend(
        _invariant(AssetIssueCode.DUPLICATE_OBJECT_NAME, name, name)
        for name in scene.duplicate_object_names
    )
    issues.extend(_invariant(AssetIssueCode.MISSING_IMAGE, path) for path in scene.missing_images)
    if not scene.meshes:
        issues.append(_invariant(AssetIssueCode.MESH_MISSING, "no export mesh"))
    for mesh in scene.meshes:
        issues.extend(_validate_mesh(mesh, manifest))
    triangles = sum(mesh.triangles for mesh in scene.meshes)
    if triangles > manifest.triangle_budget:
        issues.append(
            AssetIssue(
                AssetIssueCode.TRIANGLE_BUDGET_EXCEEDED,
                AssetIssueClass.PROJECT_BUDGET,
                f"{triangles}>{manifest.triangle_budget}",
            )
        )
    if manifest.profile is AssetProfile.RIGGED_MODEL:
        issues.extend(_validate_rig(scene, manifest))
    return tuple(issues)


def compare_roundtrip(
    source: SceneSnapshot,
    imported: SceneSnapshot,
) -> tuple[AssetIssue, ...]:
    """Compare FBX reimport semantics without requiring byte equality."""
    issues: list[AssetIssue] = []
    if source.armature_names != imported.armature_names:
        issues.append(
            _invariant(
                AssetIssueCode.ROUNDTRIP_MISMATCH,
                "armature_names",
            )
        )
    source_meshes = {mesh.name: mesh for mesh in source.meshes}
    imported_meshes = {mesh.name: mesh for mesh in imported.meshes}
    if source_meshes.keys() != imported_meshes.keys():
        issues.append(_invariant(AssetIssueCode.ROUNDTRIP_MISMATCH, "mesh_names"))
        return tuple(issues)
    for name, source_mesh in source_meshes.items():
        imported_mesh = imported_meshes[name]
        if (
            source_mesh.triangles != imported_mesh.triangles
            or source_mesh.material_slots != imported_mesh.material_slots
            or source_mesh.uv_layers != imported_mesh.uv_layers
            or not _dimensions_close(source_mesh.dimensions, imported_mesh.dimensions)
        ):
            issues.append(_invariant(AssetIssueCode.ROUNDTRIP_MISMATCH, "mesh_semantics", name))
    return tuple(issues)


def _validate_mesh(
    mesh: MeshSnapshot,
    manifest: BlenderAssetManifest,
) -> list[AssetIssue]:
    issues: list[AssetIssue] = []
    if not _is_unit_scale(mesh.scale) or not _is_zero_rotation(mesh.rotation_radians):
        issues.append(_policy(AssetIssueCode.TRANSFORMS_UNAPPLIED, mesh.name))
    if not all(math.isfinite(value) and value > TRANSFORM_TOLERANCE for value in mesh.dimensions):
        issues.append(_invariant(AssetIssueCode.DEGENERATE_DIMENSIONS, mesh.name, mesh.name))
    if mesh.uv_layers < 1:
        issues.append(_policy(AssetIssueCode.UV_MISSING, mesh.name))
    if mesh.material_slots < 1:
        issues.append(_policy(AssetIssueCode.MATERIAL_MISSING, mesh.name))
    if mesh.unapplied_modifiers:
        issues.append(_policy(AssetIssueCode.UNAPPLIED_MODIFIER, mesh.name))
    if manifest.topology_policy is TopologyPolicy.CLOSED_SOLID and mesh.non_manifold_edges:
        issues.append(_policy(AssetIssueCode.NON_MANIFOLD_GEOMETRY, mesh.name))
    if mesh.degenerate_faces:
        issues.append(_invariant(AssetIssueCode.DEGENERATE_FACE, mesh.name, mesh.name))
    if mesh.loose_vertices:
        issues.append(_policy(AssetIssueCode.LOOSE_GEOMETRY, mesh.name))
    if mesh.ngons:
        issues.append(_policy(AssetIssueCode.NGON_PRESENT, mesh.name))
    return issues


def _validate_rig(
    scene: SceneSnapshot,
    manifest: BlenderAssetManifest,
) -> list[AssetIssue]:
    issues: list[AssetIssue] = []
    if len(scene.armature_names) != 1:
        issues.append(_policy(AssetIssueCode.ARMATURE_COUNT_INVALID, "scene"))
    elif scene.armature_names[0] != manifest.expected_armature:
        issues.append(_policy(AssetIssueCode.ARMATURE_NAME_INVALID, scene.armature_names[0]))
    for mesh in scene.meshes:
        if mesh.armature_modifiers != 1:
            issues.append(_policy(AssetIssueCode.ARMATURE_MODIFIER_MISSING, mesh.name))
        if (
            manifest.max_vertex_influences is not None
            and mesh.max_vertex_influences > manifest.max_vertex_influences
        ):
            issues.append(_policy(AssetIssueCode.VERTEX_INFLUENCE_LIMIT_EXCEEDED, mesh.name))
        if mesh.unnormalized_vertices:
            issues.append(_policy(AssetIssueCode.VERTEX_WEIGHTS_UNNORMALIZED, mesh.name))
    return issues


def _is_unit_scale(values: tuple[float, float, float]) -> bool:
    return all(math.isclose(value, 1.0, abs_tol=TRANSFORM_TOLERANCE) for value in values)


def _is_zero_rotation(values: tuple[float, float, float]) -> bool:
    return all(math.isclose(value, 0.0, abs_tol=TRANSFORM_TOLERANCE) for value in values)


def _dimensions_close(
    left: tuple[float, float, float],
    right: tuple[float, float, float],
) -> bool:
    return all(
        math.isclose(first, second, rel_tol=1e-5, abs_tol=TRANSFORM_TOLERANCE)
        for first, second in zip(left, right, strict=True)
    )


def _invariant(
    code: AssetIssueCode,
    message: str,
    object_name: str | None = None,
) -> AssetIssue:
    return AssetIssue(code, AssetIssueClass.INVARIANT, message, object_name)


def _policy(code: AssetIssueCode, object_name: str) -> AssetIssue:
    return AssetIssue(code, AssetIssueClass.PROJECT_POLICY, object_name, object_name)
