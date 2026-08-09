# Copyright (c) 2026 pz-b42-mp-modding-skill contributors
"""Pure parsing contracts for installed vanilla FBX evidence."""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import StrEnum
from typing import cast, final

AXIS_NAMES = ("X", "Y", "Z")
FLOAT_PATTERN = r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[Ee][-+]?\d+)?"


class FbxReferenceErrorCode(StrEnum):
    """Stable FBX evidence parsing failures."""

    ARRAY_INVALID = "fbx_array_invalid"
    GEOMETRY_MISSING = "fbx_geometry_missing"
    PROPERTY_INVALID = "fbx_property_invalid"


@final
class FbxReferenceError(Exception):
    """One typed FBX evidence parsing failure."""

    code: FbxReferenceErrorCode

    def __init__(self, code: FbxReferenceErrorCode, detail: str) -> None:
        """Create a stable parsing failure."""
        super().__init__(detail)
        self.code = code


@dataclass(frozen=True)
class AsciiFbxMetrics:
    """Observed ASCII FBX metadata and raw geometry-array measurements."""

    bounds_max: tuple[float, float, float]
    bounds_min: tuple[float, float, float]
    coord_axis: str
    dimensions: tuple[float, float, float]
    front_axis: str
    measurement_space: str
    original_unit_scale_factor: float | None
    polygon_count: int
    triangle_count: int
    unit_scale_factor: float | None
    up_axis: str
    version: int | None
    vertex_count: int

    def to_document(self) -> dict[str, object]:
        """Return a JSON-compatible evidence record fragment."""
        return {
            "bounds_max": list(self.bounds_max),
            "bounds_min": list(self.bounds_min),
            "coord_axis": self.coord_axis,
            "dimensions": list(self.dimensions),
            "front_axis": self.front_axis,
            "measurement_space": self.measurement_space,
            "original_unit_scale_factor": self.original_unit_scale_factor,
            "polygon_count": self.polygon_count,
            "triangle_count": self.triangle_count,
            "unit_scale_factor": self.unit_scale_factor,
            "up_axis": self.up_axis,
            "version": self.version,
            "vertex_count": self.vertex_count,
        }


def parse_ascii_fbx(document: str) -> AsciiFbxMetrics:
    """Parse exact ASCII FBX global settings and raw geometry arrays."""
    vertices = _vertices(document)
    faces = _faces(document)
    minimum = (
        min(vertex[0] for vertex in vertices),
        min(vertex[1] for vertex in vertices),
        min(vertex[2] for vertex in vertices),
    )
    maximum = (
        max(vertex[0] for vertex in vertices),
        max(vertex[1] for vertex in vertices),
        max(vertex[2] for vertex in vertices),
    )
    dimensions = (
        maximum[0] - minimum[0],
        maximum[1] - minimum[1],
        maximum[2] - minimum[2],
    )
    return AsciiFbxMetrics(
        bounds_max=maximum,
        bounds_min=minimum,
        coord_axis=_axis(document, "CoordAxis", "CoordAxisSign", 0),
        dimensions=dimensions,
        front_axis=_axis(document, "FrontAxis", "FrontAxisSign", 1),
        measurement_space="fbx_geometry_arrays",
        original_unit_scale_factor=_property(
            document,
            "OriginalUnitScaleFactor",
            required=False,
        ),
        polygon_count=len(faces),
        triangle_count=sum(max(0, len(face) - 2) for face in faces),
        unit_scale_factor=_property(document, "UnitScaleFactor", required=False),
        up_axis=_axis(document, "UpAxis", "UpAxisSign", 2),
        version=_version(document),
        vertex_count=len(vertices),
    )


def _vertices(document: str) -> tuple[tuple[float, float, float], ...]:
    arrays = _arrays(document, "Vertices")
    values = [_float(value, "Vertices") for array in arrays for value in array]
    if not values or len(values) % 3:
        raise FbxReferenceError(FbxReferenceErrorCode.ARRAY_INVALID, "Vertices")
    return tuple(
        (values[index], values[index + 1], values[index + 2]) for index in range(0, len(values), 3)
    )


def _faces(document: str) -> tuple[tuple[int, ...], ...]:
    arrays = _arrays(document, "PolygonVertexIndex")
    values = [_integer(value, "PolygonVertexIndex") for array in arrays for value in array]
    faces: list[tuple[int, ...]] = []
    current: list[int] = []
    for value in values:
        current.append(-value - 1 if value < 0 else value)
        if value < 0:
            faces.append(tuple(current))
            current = []
    if not values or current:
        raise FbxReferenceError(
            FbxReferenceErrorCode.ARRAY_INVALID,
            "PolygonVertexIndex",
        )
    return tuple(faces)


def _arrays(document: str, name: str) -> tuple[tuple[str, ...], ...]:
    pattern = re.compile(
        rf"{re.escape(name)}:\s*\*\d+\s*\{{\s*a:\s*(.*?)\s*\}}",
        flags=re.DOTALL,
    )
    matches = cast("list[str]", pattern.findall(document))
    if not matches:
        raise FbxReferenceError(FbxReferenceErrorCode.GEOMETRY_MISSING, name)
    return tuple(
        tuple(value.strip() for value in match.split(",") if value.strip()) for match in matches
    )


def _axis(document: str, name: str, sign_name: str, default: int) -> str:
    axis_value = _property(document, name, required=False)
    sign_value = _property(document, sign_name, required=False)
    axis_index = default if axis_value is None else int(axis_value)
    if axis_index not in range(len(AXIS_NAMES)):
        raise FbxReferenceError(FbxReferenceErrorCode.PROPERTY_INVALID, name)
    sign = 1 if sign_value is None else int(sign_value)
    return f"{'-' if sign < 0 else '+'}{AXIS_NAMES[axis_index]}"


def _property(document: str, name: str, *, required: bool) -> float | None:
    pattern = re.compile(
        rf'P:\s*"{re.escape(name)}"[^\r\n]*,\s*({FLOAT_PATTERN})\s*$',
        flags=re.MULTILINE,
    )
    match = pattern.search(document)
    if match is None:
        if required:
            raise FbxReferenceError(FbxReferenceErrorCode.PROPERTY_INVALID, name)
        return None
    return _float(match.group(1), name)


def _version(document: str) -> int | None:
    match = re.search(r"FBXVersion:\s*(\d+)", document)
    return None if match is None else int(match.group(1))


def _float(value: str, field: str) -> float:
    try:
        return float(value)
    except ValueError as error:
        raise FbxReferenceError(FbxReferenceErrorCode.ARRAY_INVALID, field) from error


def _integer(value: str, field: str) -> int:
    try:
        return int(value)
    except ValueError as error:
        raise FbxReferenceError(FbxReferenceErrorCode.ARRAY_INVALID, field) from error
