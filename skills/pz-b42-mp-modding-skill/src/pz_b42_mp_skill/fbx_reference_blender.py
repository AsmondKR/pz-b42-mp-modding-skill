# Copyright (c) 2026 pz-b42-mp-modding-skill contributors
"""Observe one binary FBX through Blender without writing assets."""

from __future__ import annotations

import importlib
import math
from typing import TYPE_CHECKING, Protocol, cast

from pz_b42_mp_skill.fbx_reference import (
    AXIS_NAMES,
    FbxReferenceError,
    FbxReferenceErrorCode,
)

if TYPE_CHECKING:
    from collections.abc import Iterator, Sequence
    from pathlib import Path

    from pz_b42_mp_skill.blender_adapter import BlenderApp, BlenderOperators

VECTOR_COMPONENT_COUNT = 3


class ProbeVector(Protocol):
    """Indexable Blender vector."""

    def __getitem__(self, index: int) -> float:
        """Read one component."""
        ...


class ProbeMatrix(Protocol):
    """Blender object transform matrix."""

    def __matmul__(self, value: object) -> ProbeVector:
        """Transform one bound-box corner."""
        ...


class ProbeMesh(Protocol):
    """Mesh data needed for reference metrics."""

    loop_triangles: Sequence[object]

    def calc_loop_triangles(self) -> None:
        """Refresh triangulated loop data."""
        ...


class ProbeObject(Protocol):
    """Imported Blender object metrics."""

    bound_box: Sequence[Sequence[float]]
    data: ProbeMesh
    dimensions: Sequence[float]
    location: Sequence[float]
    matrix_world: ProbeMatrix
    name: str
    rotation_euler: Sequence[float]
    scale: Sequence[float]
    type: str


class ProbeObjects(Protocol):
    """Iterable Blender object collection."""

    def __iter__(self) -> Iterator[ProbeObject]:
        """Iterate imported objects."""
        ...


class ProbeData(Protocol):
    """Blender data surface for imported objects."""

    objects: ProbeObjects


class ProbeBlender(Protocol):
    """Blender surface required by this analyzer."""

    app: BlenderApp
    data: ProbeData
    ops: BlenderOperators


class ParseFbxModule(Protocol):
    """Binary FBX parser surface shipped with Blender."""

    def parse(self, filepath: str) -> tuple[object, int]:
        """Parse one binary FBX element tree."""
        ...


class ImportFbxHelpers(Protocol):
    """GlobalSettings helpers shipped with Blender."""

    def elem_find_first(self, element: object, element_id: bytes) -> object | None:
        """Find one FBX element."""
        ...

    def elem_props_get_integer(
        self,
        element: object,
        property_id: bytes,
        default: int,
    ) -> int:
        """Read one integer property."""
        ...

    def elem_props_get_number(
        self,
        element: object,
        property_id: bytes,
        default: float,
    ) -> float:
        """Read one numeric property."""
        ...


class VectorFactory(Protocol):
    """Construct Blender vectors without a static bpy dependency."""

    def __call__(self, values: Sequence[float]) -> object:
        """Create one vector."""
        ...


class MathutilsModule(Protocol):
    """Runtime mathutils surface."""

    Vector: VectorFactory


def analyze_binary_fbx(runtime: ProbeBlender, path: Path) -> dict[str, object]:
    """Import one binary FBX and emit observed Blender-space metrics."""
    metadata = _global_settings(path)
    reset = runtime.ops.wm.read_factory_settings(use_empty=True)
    if "FINISHED" not in reset:
        raise FbxReferenceError(FbxReferenceErrorCode.PROPERTY_INVALID, "factory_reset")
    imported = runtime.ops.import_scene.fbx(filepath=str(path))
    if "FINISHED" not in imported:
        raise FbxReferenceError(FbxReferenceErrorCode.PROPERTY_INVALID, "fbx_import")
    objects = tuple(runtime.data.objects)
    meshes = tuple(item for item in objects if item.type == "MESH")
    if not meshes:
        raise FbxReferenceError(FbxReferenceErrorCode.GEOMETRY_MISSING, path.name)
    minimum, maximum = _bounds(meshes)
    dimensions = (
        maximum[0] - minimum[0],
        maximum[1] - minimum[1],
        maximum[2] - minimum[2],
    )
    records = tuple(_mesh_record(item) for item in meshes)
    return {
        "armature_names": sorted(item.name for item in objects if item.type == "ARMATURE"),
        "bounds_max": list(maximum),
        "bounds_min": list(minimum),
        "dimensions": list(dimensions),
        "measurement_space": "blender_imported_scene",
        "meshes": list(records),
        "triangle_count": sum(cast("int", record["triangle_count"]) for record in records),
        **metadata,
    }


def _global_settings(path: Path) -> dict[str, object]:
    parser = cast(
        "ParseFbxModule",
        cast("object", importlib.import_module("io_scene_fbx.parse_fbx")),
    )
    helpers = cast(
        "ImportFbxHelpers",
        cast("object", importlib.import_module("io_scene_fbx.import_fbx")),
    )
    root, version = parser.parse(str(path))
    settings = helpers.elem_find_first(root, b"GlobalSettings")
    properties = None if settings is None else helpers.elem_find_first(settings, b"Properties70")
    if properties is None:
        raise FbxReferenceError(
            FbxReferenceErrorCode.PROPERTY_INVALID,
            "GlobalSettings/Properties70",
        )
    return {
        "coord_axis": _axis(helpers, properties, b"CoordAxis", b"CoordAxisSign", 0),
        "fbx_version": version,
        "front_axis": _axis(helpers, properties, b"FrontAxis", b"FrontAxisSign", 1),
        "original_unit_scale_factor": helpers.elem_props_get_number(
            properties,
            b"OriginalUnitScaleFactor",
            1.0,
        ),
        "unit_scale_factor": helpers.elem_props_get_number(
            properties,
            b"UnitScaleFactor",
            1.0,
        ),
        "up_axis": _axis(helpers, properties, b"UpAxis", b"UpAxisSign", 2),
    }


def _axis(
    helpers: ImportFbxHelpers,
    properties: object,
    axis_name: bytes,
    sign_name: bytes,
    default: int,
) -> str:
    axis_index = helpers.elem_props_get_integer(properties, axis_name, default)
    sign = helpers.elem_props_get_integer(properties, sign_name, 1)
    if axis_index not in range(len(AXIS_NAMES)):
        raise FbxReferenceError(
            FbxReferenceErrorCode.PROPERTY_INVALID,
            axis_name.decode(),
        )
    return f"{'-' if sign < 0 else '+'}{AXIS_NAMES[axis_index]}"


def _bounds(
    meshes: tuple[ProbeObject, ...],
) -> tuple[tuple[float, float, float], tuple[float, float, float]]:
    mathutils = cast(
        "MathutilsModule",
        cast("object", importlib.import_module("mathutils")),
    )
    points = tuple(
        item.matrix_world @ mathutils.Vector(corner) for item in meshes for corner in item.bound_box
    )
    minimum = (
        min(point[0] for point in points),
        min(point[1] for point in points),
        min(point[2] for point in points),
    )
    maximum = (
        max(point[0] for point in points),
        max(point[1] for point in points),
        max(point[2] for point in points),
    )
    return _rounded_vector(minimum), _rounded_vector(maximum)


def _mesh_record(item: ProbeObject) -> dict[str, object]:
    item.data.calc_loop_triangles()
    return {
        "dimensions": list(_rounded_vector(item.dimensions)),
        "location": list(_rounded_vector(item.location)),
        "name": item.name,
        "rotation_degrees": list(
            _rounded_vector(tuple(math.degrees(value) for value in item.rotation_euler))
        ),
        "scale": list(_rounded_vector(item.scale)),
        "triangle_count": len(item.data.loop_triangles),
    }


def _rounded_vector(values: Sequence[float]) -> tuple[float, float, float]:
    if len(values) != VECTOR_COMPONENT_COUNT:
        raise FbxReferenceError(FbxReferenceErrorCode.ARRAY_INVALID, "vector3")
    return round(float(values[0]), 6), round(float(values[1]), 6), round(float(values[2]), 6)
