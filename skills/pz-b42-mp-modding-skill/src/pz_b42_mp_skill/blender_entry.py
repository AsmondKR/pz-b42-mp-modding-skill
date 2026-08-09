# Copyright (c) 2026 pz-b42-mp-modding-skill contributors
"""Blender-internal validation, export, and round-trip entry point."""

from __future__ import annotations

import argparse
import json
import sys
from enum import StrEnum
from pathlib import Path
from typing import TYPE_CHECKING, cast

from pz_b42_mp_skill import OUTPUT_SCHEMA_VERSION
from pz_b42_mp_skill.asset_manifest import (
    AssetManifestError,
    AssetManifestErrorCode,
    load_asset_manifest,
)
from pz_b42_mp_skill.blender_adapter import (
    BlenderModule,
    collect_scene,
    export_fbx,
    load_blender_module,
    reset_and_import_fbx,
    select_export_objects,
)
from pz_b42_mp_skill.blender_contract import compare_roundtrip, validate_scene
from pz_b42_mp_skill.guard_paths import Policy
from pz_b42_mp_skill.guard_types import GuardError

if TYPE_CHECKING:
    from collections.abc import Mapping

RESULT_PREFIX = "PZ_ASSET_RESULT="


class BlenderMode(StrEnum):
    """Available Blender-internal operations."""

    EXPORT = "export"
    VALIDATE = "validate"


def parser() -> argparse.ArgumentParser:
    """Build the Blender-internal parser."""
    result = argparse.ArgumentParser(description=__doc__)
    _ = result.add_argument("--manifest", required=True, type=Path)
    _ = result.add_argument("--mode", choices=tuple(BlenderMode), required=True)
    _ = result.add_argument("--policy", required=True, type=Path)
    return result


def main(
    arguments: list[str] | None = None,
    *,
    bpy: BlenderModule | None = None,
) -> int:
    """Validate or export one explicit Blender asset set."""
    namespace = parser().parse_args(arguments)
    mode = BlenderMode(cast("str", namespace.mode))
    runtime = load_blender_module() if bpy is None else bpy
    try:
        document, valid = _run(
            runtime,
            mode,
            cast("Path", namespace.manifest),
            cast("Path", namespace.policy),
        )
    except (AssetManifestError, GuardError, OSError, RuntimeError) as error:
        code = (
            error.code.value
            if isinstance(error, (AssetManifestError, GuardError))
            else "blender_failed"
        )
        _emit(
            {
                "error": code,
                "message": str(error),
                "schema_version": OUTPUT_SCHEMA_VERSION,
            }
        )
        return 2
    else:
        _emit(document)
        return 0 if valid else 1


def _run(
    runtime: BlenderModule,
    mode: BlenderMode,
    manifest_path: Path,
    policy_path: Path,
) -> tuple[dict[str, object], bool]:
    policy = Policy.load(policy_path)
    manifest = load_asset_manifest(manifest_path, policy)
    source = collect_scene(runtime, manifest)
    issues = list(validate_scene(source, manifest))
    exported = False
    imported = None
    if mode is BlenderMode.EXPORT and not issues:
        policy.ensure_current()
        _ensure_destination_absent(manifest.output_fbx)
        select_export_objects(runtime, manifest)
        export_fbx(runtime, manifest)
        exported = True
        reset_and_import_fbx(runtime, manifest.output_fbx)
        imported = collect_scene(runtime, manifest)
        issues.extend(compare_roundtrip(source, imported))
    document: dict[str, object] = {
        "asset_id": manifest.asset_id,
        "blender_version": runtime.app.version_string,
        "exported": exported,
        "issues": [issue.to_document() for issue in issues],
        "mode": mode,
        "profile": manifest.profile,
        "roundtrip": None if imported is None else imported.to_document(),
        "schema_version": OUTPUT_SCHEMA_VERSION,
        "source": source.to_document(),
        "valid": not issues,
    }
    return document, not issues


def _ensure_destination_absent(path: Path) -> None:
    if path.exists():
        raise AssetManifestError(
            AssetManifestErrorCode.DESTINATION_EXISTS,
            path.name,
        )


def _emit(document: Mapping[str, object]) -> None:
    _ = sys.stdout.write(f"{RESULT_PREFIX}{json.dumps(document, sort_keys=True)}\n")


if __name__ == "__main__":
    raise SystemExit(main())
