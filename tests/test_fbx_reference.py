# Copyright (c) 2026 pz-b42-mp-modding-skill contributors
"""Contracts for installed-build vanilla FBX evidence."""

from __future__ import annotations

import importlib
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import TYPE_CHECKING

import pytest

from pz_b42_mp_skill.discovery import DiscoveryResult

if TYPE_CHECKING:
    from types import ModuleType

ASCII_FBX = """
; FBX 7.4.0 project file
FBXVersion: 7400
GlobalSettings:  {
    Properties70:  {
        P: "UpAxis", "int", "Integer", "",1
        P: "UpAxisSign", "int", "Integer", "",1
        P: "FrontAxis", "int", "Integer", "",2
        P: "FrontAxisSign", "int", "Integer", "",1
        P: "CoordAxis", "int", "Integer", "",0
        P: "CoordAxisSign", "int", "Integer", "",1
        P: "UnitScaleFactor", "double", "Number", "",2.54
        P: "OriginalUnitScaleFactor", "double", "Number", "",2.54
    }
}
Objects:  {
    Geometry: 1, "Geometry::Sample", "Mesh" {
        Vertices: *12 {
            a: 0,0,0,2,0,0,2,3,0,0,3,0
        }
        PolygonVertexIndex: *4 {
            a: 0,1,2,-4
        }
    }
}
"""


def load_module(name: str) -> ModuleType:
    """Load production code or report the intended missing seam."""
    try:
        return importlib.import_module(name)
    except ModuleNotFoundError:
        pytest.fail(f"required production module is missing: {name}")


def check_equal(actual: object, expected: object) -> None:
    """Fail with values when equality does not hold."""
    if actual != expected:
        pytest.fail(f"expected {expected!r}, received {actual!r}")


class TestFbxAsciiContract:
    """Measure ASCII FBX without claiming Blender-imported space."""

    def test_parses_axis_units_bounds_and_triangles(self) -> None:
        """Extract exact metadata and geometry-array measurements."""
        module = load_module("pz_b42_mp_skill.fbx_reference")

        metrics = module.parse_ascii_fbx(ASCII_FBX)

        check_equal(metrics.version, 7400)
        check_equal(metrics.up_axis, "+Y")
        check_equal(metrics.front_axis, "+Z")
        check_equal(metrics.coord_axis, "+X")
        check_equal(metrics.unit_scale_factor, 2.54)
        check_equal(metrics.vertex_count, 4)
        check_equal(metrics.polygon_count, 1)
        check_equal(metrics.triangle_count, 2)
        check_equal(metrics.bounds_min, (0.0, 0.0, 0.0))
        check_equal(metrics.bounds_max, (2.0, 3.0, 0.0))
        check_equal(metrics.dimensions, (2.0, 3.0, 0.0))
        check_equal(metrics.measurement_space, "fbx_geometry_arrays")

    def test_rejects_missing_geometry_arrays(self) -> None:
        """Return a typed finding instead of empty plausible dimensions."""
        module = load_module("pz_b42_mp_skill.fbx_reference")

        with pytest.raises(module.FbxReferenceError) as caught:
            _ = module.parse_ascii_fbx("FBXVersion: 7400")

        check_equal(caught.value.code.value, "fbx_geometry_missing")


class TestFbxProbePlanContract:
    """Plan read-only Blender probes against explicit vanilla files."""

    def test_builds_hashable_autoexec_disabled_probe_plan(self) -> None:
        """Bind build, branch, Blender script, and exact sample paths."""
        module = load_module("pz_b42_mp_skill.fbx_reference_plan")
        with TemporaryDirectory() as directory:
            root = Path(directory)
            fbx = root / "media" / "models_X" / "Sample.fbx"
            fbx.parent.mkdir(parents=True)
            fbx.write_bytes(b"Kaydara FBX Binary  \x00")
            script = root / "fbx_reference_script.py"
            script.write_text("# probe", encoding="utf-8")
            manifest = root / "appmanifest_108600.acf"
            manifest.write_text("fixture", encoding="utf-8")
            discovery = DiscoveryResult(
                manifest=manifest,
                install_root=root,
                user_data_root=root / "userdata",
                build_id="24574865",
                branch="public",
                evidence={},
            )
            sample = module.ReferenceSample.parse("static=media/models_X/Sample.fbx")

            plan = module.build_probe_plan(
                root / "blender.exe",
                script,
                discovery,
                (sample,),
            )

            check_equal(plan.build_id, "24574865")
            check_equal(plan.branch, "public")
            check_equal(plan.samples, (sample,))
            if "--disable-autoexec" not in plan.command:
                pytest.fail("probe command must disable Blend auto-execution")
            if not any(value.endswith(str(fbx)) for value in plan.command):
                pytest.fail("probe command must bind the resolved vanilla FBX")
            check_equal(len(plan.command_sha256), 64)

    def test_rejects_sample_escape_and_non_fbx_paths(self) -> None:
        """Keep probes inside the installed vanilla models_X tree."""
        module = load_module("pz_b42_mp_skill.fbx_reference_plan")

        for value in ("bad=../outside.fbx", "bad=media/models_X/readme.txt"):
            with pytest.raises(module.FbxReferencePlanError):
                _ = module.ReferenceSample.parse(value)
