# Copyright (c) 2026 pz-b42-mp-modding-skill contributors
"""Typed adapter around the Blender Python runtime."""

from __future__ import annotations

import importlib
import math
from collections import Counter
from pathlib import Path
from typing import TYPE_CHECKING, Protocol, cast

from pz_b42_mp_skill.blender_contract import MeshSnapshot, SceneSnapshot

if TYPE_CHECKING:
    from collections.abc import Iterator, Sequence

    from pz_b42_mp_skill.asset_manifest import BlenderAssetManifest

WEIGHT_TOLERANCE = 1e-4
DEGENERATE_AREA_TOLERANCE = 1e-12
EDGE_SIZE = 2
MANIFOLD_FACE_COUNT = 2
MAX_FACE_VERTICES = 4
VECTOR_SIZE = 3


class VertexGroupElement(Protocol):
    """One Blender vertex-group membership."""

    weight: float


class MeshVertex(Protocol):
    """One Blender mesh vertex."""

    index: int
    groups: Sequence[VertexGroupElement]


class MeshPolygon(Protocol):
    """One Blender mesh polygon."""

    area: float
    edge_keys: Sequence[tuple[int, int]]
    vertices: Sequence[int]


class BlenderMesh(Protocol):
    """Blender mesh members inspected by the quality gate."""

    loop_triangles: Sequence[object]
    materials: Sequence[object]
    polygons: Sequence[MeshPolygon]
    uv_layers: Sequence[object]
    vertices: Sequence[MeshVertex]

    def calc_loop_triangles(self) -> None:
        """Calculate loop triangles."""


class BlenderModifier(Protocol):
    """One Blender object modifier."""

    type: str


class BlenderObject(Protocol):
    """Blender object members needed for collection and export."""

    data: object
    dimensions: Sequence[float]
    modifiers: Sequence[BlenderModifier]
    name: str
    rotation_euler: Sequence[float]
    scale: Sequence[float]
    type: str

    def select_set(self, *, state: bool) -> None:
        """Select or deselect the object."""
        ...


class BlenderImage(Protocol):
    """One Blender image datablock."""

    filepath: str
    source: str


class BlenderObjects(Protocol):
    """Object collection contract."""

    def __iter__(self) -> Iterator[BlenderObject]:
        """Iterate Blender objects."""
        ...

    def get(self, name: str) -> BlenderObject | None:
        """Find an object by exact name."""
        ...


class BlenderImages(Protocol):
    """Image collection contract."""

    def __iter__(self) -> Iterator[BlenderImage]:
        """Iterate Blender images."""
        ...


class BlenderData(Protocol):
    """Blender data collections."""

    images: BlenderImages
    objects: BlenderObjects


class BlenderObjectOperators(Protocol):
    """Object selection operators."""

    def select_all(self, *, action: str) -> set[str]:
        """Select or deselect every object."""
        ...


class BlenderExportOperators(Protocol):
    """FBX export operator."""

    def fbx(self, **kwargs: object) -> set[str]:
        """Export selected objects to FBX."""
        ...


class BlenderImportOperators(Protocol):
    """FBX import operator."""

    def fbx(self, *, filepath: str) -> set[str]:
        """Import one FBX."""
        ...


class BlenderWindowOperators(Protocol):
    """Scene reset operator."""

    def read_factory_settings(self, *, use_empty: bool) -> set[str]:
        """Reset to an empty factory scene."""
        ...


class BlenderOperators(Protocol):
    """Blender operator namespaces."""

    export_scene: BlenderExportOperators
    import_scene: BlenderImportOperators
    object: BlenderObjectOperators
    wm: BlenderWindowOperators


class BlenderPath(Protocol):
    """Blender path resolver."""

    def abspath(self, path: str) -> str:
        """Resolve Blender's path notation."""
        ...


class BlenderApp(Protocol):
    """Blender runtime metadata."""

    version_string: str


class BlenderModule(Protocol):
    """Subset of the bpy module used by this package."""

    app: BlenderApp
    data: BlenderData
    ops: BlenderOperators
    path: BlenderPath


def load_blender_module() -> BlenderModule:
    """Load bpy only inside Blender's Python runtime."""
    return cast("BlenderModule", cast("object", importlib.import_module("bpy")))


def collect_scene(
    bpy: BlenderModule,
    manifest: BlenderAssetManifest,
) -> SceneSnapshot:
    """Measure only the manifest-declared export set."""
    objects: list[BlenderObject] = []
    missing: list[str] = []
    for name in manifest.export_objects:
        item = bpy.data.objects.get(name)
        if item is None:
            missing.append(name)
        else:
            objects.append(item)
    names = [item.name for item in objects]
    duplicate_names = tuple(sorted(name for name, count in Counter(names).items() if count > 1))
    meshes = tuple(_mesh_snapshot(item) for item in objects if item.type == "MESH")
    armatures = tuple(sorted(item.name for item in objects if item.type == "ARMATURE"))
    return SceneSnapshot(
        armature_names=armatures,
        duplicate_object_names=duplicate_names,
        meshes=meshes,
        missing_export_objects=tuple(missing),
        missing_images=_missing_images(bpy, manifest),
    )


def select_export_objects(
    bpy: BlenderModule,
    manifest: BlenderAssetManifest,
) -> None:
    """Select the explicit manifest set and nothing else."""
    _ = bpy.ops.object.select_all(action="DESELECT")
    for name in manifest.export_objects:
        item = bpy.data.objects.get(name)
        if item is None:
            detail = f"missing_export_object:{name}"
            raise RuntimeError(detail)
        item.select_set(state=True)


def export_fbx(bpy: BlenderModule, manifest: BlenderAssetManifest) -> None:
    """Export through one checked-in, reviewable baseline preset."""
    result = bpy.ops.export_scene.fbx(
        add_leaf_bones=False,
        apply_scale_options="FBX_SCALE_NONE",
        apply_unit_scale=True,
        axis_forward="-Z",
        axis_up="Y",
        bake_anim=False,
        check_existing=False,
        embed_textures=False,
        filepath=str(manifest.output_fbx),
        global_scale=1.0,
        mesh_smooth_type="OFF",
        object_types={"ARMATURE", "MESH"},
        path_mode="AUTO",
        use_custom_props=False,
        use_mesh_modifiers=True,
        use_selection=True,
        use_triangles=False,
    )
    if "FINISHED" not in result:
        detail = f"fbx_export_failed:{sorted(result)}"
        raise RuntimeError(detail)


def reset_and_import_fbx(bpy: BlenderModule, path: Path) -> None:
    """Reimport an FBX into an empty factory scene."""
    reset = bpy.ops.wm.read_factory_settings(use_empty=True)
    if "FINISHED" not in reset:
        detail = f"factory_reset_failed:{sorted(reset)}"
        raise RuntimeError(detail)
    imported = bpy.ops.import_scene.fbx(filepath=str(path))
    if "FINISHED" not in imported:
        detail = f"fbx_import_failed:{sorted(imported)}"
        raise RuntimeError(detail)


def _mesh_snapshot(item: BlenderObject) -> MeshSnapshot:
    mesh = cast("BlenderMesh", item.data)
    mesh.calc_loop_triangles()
    edge_use: Counter[tuple[int, int]] = Counter()
    used_vertices: set[int] = set()
    degenerate_faces = 0
    ngons = 0
    for polygon in mesh.polygons:
        edge_use.update(_edge_key(edge) for edge in polygon.edge_keys)
        used_vertices.update(polygon.vertices)
        degenerate_faces += int(
            not math.isfinite(polygon.area) or polygon.area <= DEGENERATE_AREA_TOLERANCE
        )
        ngons += int(len(polygon.vertices) > MAX_FACE_VERTICES)
    influences = [
        tuple(group.weight for group in vertex.groups if group.weight > 0)
        for vertex in mesh.vertices
    ]
    return MeshSnapshot(
        armature_modifiers=sum(modifier.type == "ARMATURE" for modifier in item.modifiers),
        degenerate_faces=degenerate_faces,
        dimensions=_vector3(item.dimensions),
        loose_vertices=sum(vertex.index not in used_vertices for vertex in mesh.vertices),
        material_slots=len(mesh.materials),
        max_vertex_influences=max((len(weights) for weights in influences), default=0),
        name=item.name,
        ngons=ngons,
        non_manifold_edges=sum(count != MANIFOLD_FACE_COUNT for count in edge_use.values()),
        rotation_radians=_vector3(item.rotation_euler),
        scale=_vector3(item.scale),
        triangles=len(mesh.loop_triangles),
        unnormalized_vertices=sum(
            not weights or not math.isclose(sum(weights), 1.0, abs_tol=WEIGHT_TOLERANCE)
            for weights in influences
        ),
        unapplied_modifiers=sum(modifier.type != "ARMATURE" for modifier in item.modifiers),
        uv_layers=len(mesh.uv_layers),
    )


def _missing_images(
    bpy: BlenderModule,
    manifest: BlenderAssetManifest,
) -> tuple[str, ...]:
    loaded = {
        Path(bpy.path.abspath(image.filepath)).resolve(strict=False)
        for image in bpy.data.images
        if image.source == "FILE" and image.filepath
    }
    return tuple(
        manifest.workspace_root_relative(path)
        for path in manifest.texture_files
        if path not in loaded
    )


def _vector3(values: Sequence[float]) -> tuple[float, float, float]:
    if len(values) != VECTOR_SIZE:
        detail = f"expected_vector3:{len(values)}"
        raise RuntimeError(detail)
    return float(values[0]), float(values[1]), float(values[2])


def _edge_key(values: Sequence[int]) -> tuple[int, int]:
    if len(values) != EDGE_SIZE:
        detail = f"expected_edge_pair:{len(values)}"
        raise RuntimeError(detail)
    first, second = sorted(values)
    return first, second
