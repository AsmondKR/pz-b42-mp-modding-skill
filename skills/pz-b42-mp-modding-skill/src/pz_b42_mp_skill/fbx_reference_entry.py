# Copyright (c) 2026 pz-b42-mp-modding-skill contributors
"""Blender-internal read-only probe for installed vanilla FBX evidence."""

from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import sys
from pathlib import Path
from typing import TYPE_CHECKING, cast

from pz_b42_mp_skill import OUTPUT_SCHEMA_VERSION
from pz_b42_mp_skill.fbx_reference import FbxReferenceError, parse_ascii_fbx
from pz_b42_mp_skill.fbx_reference_blender import ProbeBlender, analyze_binary_fbx
from pz_b42_mp_skill.fbx_reference_plan import (
    FbxReferencePlanError,
    ReferenceSample,
)
from pz_b42_mp_skill.guard_paths import (
    is_within,
    path_contains_link_or_reparse,
)

RESULT_PREFIX = "PZ_FBX_REFERENCE="
BINARY_MAGIC = b"Kaydara FBX Binary  \x00"

if TYPE_CHECKING:
    from collections.abc import Mapping


def parser() -> argparse.ArgumentParser:
    """Build the Blender-internal probe parser."""
    result = argparse.ArgumentParser(description=__doc__)
    _ = result.add_argument("--branch", required=True)
    _ = result.add_argument("--build-id", required=True)
    _ = result.add_argument("--game-root", required=True, type=Path)
    _ = result.add_argument("--sample", action="append", default=[], required=True)
    return result


def main(arguments: list[str] | None = None) -> int:
    """Probe explicit vanilla FBX files and emit no asset bytes."""
    namespace = parser().parse_args(arguments)
    try:
        game_root = cast("Path", namespace.game_root).resolve(strict=True)
        runtime = cast(
            "ProbeBlender",
            cast("object", importlib.import_module("bpy")),
        )
        records = [
            _observe(runtime, game_root, cast("str", raw))
            for raw in cast("list[object]", namespace.sample)
        ]
        document = {
            "branch": cast("str", namespace.branch),
            "build_id": cast("str", namespace.build_id),
            "claims_excluded": {
                "loader_behavior": True,
                "runtime_metres": True,
                "universal_axis_convention": True,
            },
            "population_claimed": False,
            "record_kind": "fbx_observation_set",
            "records": records,
            "schema_version": OUTPUT_SCHEMA_VERSION,
            "tool_versions": {
                "blender": runtime.app.version_string,
                "probe": "1",
            },
        }
    except (
        FbxReferenceError,
        FbxReferencePlanError,
        OSError,
        RuntimeError,
        ValueError,
    ) as error:
        document = {
            "error": "fbx_reference_failed",
            "message": str(error),
            "schema_version": OUTPUT_SCHEMA_VERSION,
        }
        _emit(document)
        return 2
    _emit(document)
    return 0


def _observe(runtime: ProbeBlender, game_root: Path, raw: str) -> dict[str, object]:
    label, raw_path = raw.split("=", 1)
    path = Path(raw_path)
    resolved = path.resolve(strict=True)
    models_root = (game_root / "media" / "models_X").resolve(strict=True)
    if (
        not resolved.is_file()
        or not is_within(resolved, models_root)
        or path_contains_link_or_reparse(path)
    ):
        detail = f"fbx_reference_path_invalid:{path}"
        raise RuntimeError(detail)
    relative = resolved.relative_to(game_root)
    sample = ReferenceSample.parse(f"{label}={relative.as_posix()}")
    encoding = _encoding(resolved)
    metrics = (
        parse_ascii_fbx(resolved.read_text(encoding="utf-8-sig")).to_document()
        if encoding == "ascii"
        else analyze_binary_fbx(runtime, resolved)
    )
    return {
        "encoding": encoding,
        "evidence_class": "verified",
        "file_size_bytes": resolved.stat().st_size,
        "label": sample.label,
        "metrics": metrics,
        "relative_path": sample.relative_path.as_posix(),
        "script_refs": [],
        "sha256": _sha256(resolved),
    }


def _encoding(path: Path) -> str:
    with path.open("rb") as stream:
        return "binary" if stream.read(len(BINARY_MAGIC)) == BINARY_MAGIC else "ascii"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while block := stream.read(1024 * 1024):
            digest.update(block)
    return digest.hexdigest()


def _emit(document: Mapping[str, object]) -> None:
    _ = sys.stdout.write(f"{RESULT_PREFIX}{json.dumps(document, sort_keys=True)}\n")


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []))
