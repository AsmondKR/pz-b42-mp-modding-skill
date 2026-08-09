# Copyright (c) 2026 pz-b42-mp-modding-skill contributors
"""Tests for typed Blender asset manifests and scene quality gates."""

from __future__ import annotations

import importlib
import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import TYPE_CHECKING

import pytest

from pz_b42_mp_skill.guard_paths import Policy

if TYPE_CHECKING:
    from types import ModuleType


def load_module(name: str) -> ModuleType:
    """Load a new production module or fail with the intended regression."""
    try:
        return importlib.import_module(name)
    except ModuleNotFoundError:
        pytest.fail(f"required production module is missing: {name}")


def check_equal(actual: object, expected: object) -> None:
    """Fail when two values differ."""
    if actual != expected:
        pytest.fail(f"expected {expected!r}, received {actual!r}")


def check_true(value: object) -> None:
    """Fail when a value is falsey."""
    if not value:
        pytest.fail(f"expected truthy value, received {value!r}")


def write_manifest(root: Path, *, profile: str = "static_model") -> Path:
    """Create one valid model manifest and its trusted inputs."""
    source = root / "source.blend"
    source.touch()
    texture = root / "textures" / "albedo.png"
    texture.parent.mkdir()
    texture.touch()
    output_root = root / "build"
    output_root.mkdir()
    profile_fields: dict[str, object] = {}
    if profile == "rigged_model":
        profile_fields = {
            "expected_armature": "PZ_Rig",
            "max_vertex_influences": 4,
        }
    manifest = root / "asset.json"
    manifest.write_text(
        json.dumps(
            {
                "asset_id": "ExampleAxe",
                "export_objects": ["ExampleAxe"],
                "output_fbx": "build/ExampleAxe.fbx",
                "profile": profile,
                "schema_version": 1,
                "source_blend": "source.blend",
                "texture_files": ["textures/albedo.png"],
                "topology_policy": "closed_solid",
                "triangle_budget": 2400,
                **profile_fields,
            }
        ),
        encoding="utf-8",
    )
    return manifest


def write_policy(root: Path) -> Policy:
    """Authorize only the fixture's dedicated build directory."""
    policy_path = root / ".pz-skill-policy.json"
    policy_path.write_text(
        json.dumps(
            {
                "allowed_output_roots": ["build"],
                "forbidden_roots": [],
                "version": 1,
                "workspace_root": str(root),
            }
        ),
        encoding="utf-8",
    )
    return Policy.load(policy_path)


class BlenderAssetManifestTest(unittest.TestCase):
    """Parse untrusted manifest JSON before Blender receives it."""

    def test_valid_manifest_resolves_workspace_paths(self) -> None:
        """Resolve relative inputs and output beneath the manifest directory."""
        module = load_module("pz_b42_mp_skill.asset_manifest")
        with TemporaryDirectory() as temp_directory:
            root = Path(temp_directory)
            manifest_path = write_manifest(root)
            result = module.load_asset_manifest(manifest_path, write_policy(root))

            check_equal(result.asset_id, "ExampleAxe")
            check_equal(result.profile.value, "static_model")
            check_equal(result.source_blend, (root / "source.blend").resolve())
            check_equal(
                result.output_fbx,
                (root / "build" / "ExampleAxe.fbx").resolve(),
            )
            check_equal(result.triangle_budget, 2400)

    def test_manifest_rejects_output_path_escape(self) -> None:
        """Keep Blender export destinations inside the manifest workspace."""
        module = load_module("pz_b42_mp_skill.asset_manifest")
        with TemporaryDirectory() as temp_directory:
            root = Path(temp_directory)
            manifest_path = write_manifest(root)
            document = json.loads(manifest_path.read_text(encoding="utf-8"))
            document["output_fbx"] = "../escape.fbx"
            manifest_path.write_text(json.dumps(document), encoding="utf-8")

            with pytest.raises(module.AssetManifestError) as caught:
                _ = module.load_asset_manifest(manifest_path, write_policy(root))

            check_equal(caught.value.code.value, "path_outside_manifest_root")


class BlenderSceneContractTest(unittest.TestCase):
    """Reject scene defects before exporting production FBX files."""

    def test_clean_static_scene_passes(self) -> None:
        """Accept a bounded, textured, manifold mesh with applied transforms."""
        manifest_module = load_module("pz_b42_mp_skill.asset_manifest")
        contract = load_module("pz_b42_mp_skill.blender_contract")
        with TemporaryDirectory() as temp_directory:
            root = Path(temp_directory)
            manifest = manifest_module.load_asset_manifest(
                write_manifest(root),
                write_policy(root),
            )
            mesh = contract.MeshSnapshot(
                armature_modifiers=0,
                dimensions=(1.0, 0.2, 0.05),
                material_slots=1,
                max_vertex_influences=0,
                name="ExampleAxe",
                non_manifold_edges=0,
                rotation_radians=(0.0, 0.0, 0.0),
                scale=(1.0, 1.0, 1.0),
                triangles=1800,
                unnormalized_vertices=0,
                unapplied_modifiers=0,
                uv_layers=1,
            )
            scene = contract.SceneSnapshot(
                armature_names=(),
                duplicate_object_names=(),
                meshes=(mesh,),
                missing_images=(),
            )

            check_equal(contract.validate_scene(scene, manifest), ())

    def test_scene_reports_every_objective_quality_failure(self) -> None:
        """Return stable codes for defects instead of exporting a weak asset."""
        manifest_module = load_module("pz_b42_mp_skill.asset_manifest")
        contract = load_module("pz_b42_mp_skill.blender_contract")
        with TemporaryDirectory() as temp_directory:
            root = Path(temp_directory)
            manifest = manifest_module.load_asset_manifest(
                write_manifest(root),
                write_policy(root),
            )
            mesh = contract.MeshSnapshot(
                armature_modifiers=0,
                dimensions=(0.0, 0.2, 0.05),
                material_slots=0,
                max_vertex_influences=0,
                name="ExampleAxe",
                non_manifold_edges=4,
                rotation_radians=(0.0, 0.0, 0.25),
                scale=(2.0, 1.0, 1.0),
                triangles=3000,
                unnormalized_vertices=0,
                unapplied_modifiers=2,
                uv_layers=0,
            )
            scene = contract.SceneSnapshot(
                armature_names=(),
                duplicate_object_names=("ExampleAxe",),
                meshes=(mesh,),
                missing_images=("textures/albedo.png",),
            )

            codes = {issue.code.value for issue in contract.validate_scene(scene, manifest)}

            check_equal(
                codes,
                {
                    "degenerate_dimensions",
                    "duplicate_object_name",
                    "material_missing",
                    "missing_image",
                    "non_manifold_geometry",
                    "transforms_unapplied",
                    "triangle_budget_exceeded",
                    "unapplied_modifier",
                    "uv_missing",
                },
            )

    def test_rigged_scene_requires_bounded_normalized_weights(self) -> None:
        """Enforce one armature and game-friendly vertex influences."""
        manifest_module = load_module("pz_b42_mp_skill.asset_manifest")
        contract = load_module("pz_b42_mp_skill.blender_contract")
        with TemporaryDirectory() as temp_directory:
            root = Path(temp_directory)
            manifest = manifest_module.load_asset_manifest(
                write_manifest(root, profile="rigged_model"),
                write_policy(root),
            )
            mesh = contract.MeshSnapshot(
                armature_modifiers=0,
                dimensions=(1.0, 1.0, 1.0),
                material_slots=1,
                max_vertex_influences=6,
                name="Jacket",
                non_manifold_edges=0,
                rotation_radians=(0.0, 0.0, 0.0),
                scale=(1.0, 1.0, 1.0),
                triangles=1200,
                unnormalized_vertices=3,
                unapplied_modifiers=0,
                uv_layers=1,
            )
            scene = contract.SceneSnapshot(
                armature_names=(),
                duplicate_object_names=(),
                meshes=(mesh,),
                missing_images=(),
            )

            codes = {issue.code.value for issue in contract.validate_scene(scene, manifest)}

            check_equal(
                codes,
                {
                    "armature_count_invalid",
                    "armature_modifier_missing",
                    "vertex_influence_limit_exceeded",
                    "vertex_weights_unnormalized",
                },
            )


class BlenderLauncherContractTest(unittest.TestCase):
    """Launch Blender with an explicit safe command contract."""

    def test_command_disables_autoexec_and_loads_declared_source(self) -> None:
        """Load only the manifest source and forward exact policy arguments."""
        manifest_module = load_module("pz_b42_mp_skill.asset_manifest")
        runner = load_module("pz_b42_mp_skill.blender_runner")
        with TemporaryDirectory() as temp_directory:
            root = Path(temp_directory)
            manifest_path = write_manifest(root)
            policy = write_policy(root)
            manifest = manifest_module.load_asset_manifest(manifest_path, policy)
            blender = root / "blender.exe"
            script = root / "asset_pipeline.py"

            command = runner.build_blender_command(
                blender,
                script,
                manifest,
                policy.policy_path,
                "validate",
            )

            check_equal(command[0], str(blender))
            check_true("--background" in command)
            check_true("--factory-startup" in command)
            check_true("--disable-autoexec" in command)
            check_true(str(manifest.source_blend) in command)
            check_equal(
                command[-6:],
                (
                    "--manifest",
                    str(manifest.manifest_path),
                    "--mode",
                    "validate",
                    "--policy",
                    str(policy.policy_path),
                ),
            )

    def test_only_export_plans_refuse_an_existing_destination(self) -> None:
        """Keep validation repeatable while preserving create-only FBX output."""
        manifest_module = load_module("pz_b42_mp_skill.asset_manifest")
        runner = load_module("pz_b42_mp_skill.blender_runner")
        with TemporaryDirectory() as temp_directory:
            root = Path(temp_directory)
            manifest_path = write_manifest(root)
            policy = write_policy(root)
            manifest = manifest_module.load_asset_manifest(manifest_path, policy)
            manifest.output_fbx.touch()
            blender = root / "blender.exe"

            plan = runner.plan_blender_asset(
                blender,
                manifest,
                policy.policy_path,
                "validate",
            )
            check_equal(plan.mode.value, "validate")

            with pytest.raises(runner.BlenderRunError) as caught:
                _ = runner.plan_blender_asset(
                    blender,
                    manifest,
                    policy.policy_path,
                    "export",
                )
            check_equal(caught.value.code.value, "destination_exists")


if __name__ == "__main__":
    unittest.main()
