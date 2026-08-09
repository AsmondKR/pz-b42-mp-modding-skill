# Copyright (c) 2026 pz-b42-mp-modding-skill contributors
"""Plan a read-only Blender probe of installed vanilla FBX files."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import cast

from pz_b42_mp_skill import OUTPUT_SCHEMA_VERSION
from pz_b42_mp_skill.blender_runner import BlenderRunError, discover_blender
from pz_b42_mp_skill.discovery import DiscoveryError, discover
from pz_b42_mp_skill.fbx_reference_plan import (
    FbxReferencePlanError,
    ReferenceSample,
    build_probe_plan,
)


def parser() -> argparse.ArgumentParser:
    """Build the user-facing FBX probe plan parser."""
    result = argparse.ArgumentParser(description=__doc__)
    _ = result.add_argument("--blender", type=Path)
    _ = result.add_argument("--manifest", type=Path)
    _ = result.add_argument("--sample", action="append", required=True)
    return result


def main(arguments: list[str] | None = None) -> int:
    """Discover the build and emit one hash-bound Blender command."""
    namespace = parser().parse_args(arguments)
    try:
        discovery = discover(cast("Path | None", namespace.manifest))
        blender = discover_blender(cast("Path | None", namespace.blender))
        script = Path(__file__).resolve().with_name("fbx_reference_script.py")
        samples = tuple(
            ReferenceSample.parse(cast("str", value))
            for value in cast("list[object]", namespace.sample)
        )
        plan = build_probe_plan(blender, script, discovery, samples)
    except BlenderRunError as error:
        return _error(error.code.value, error)
    except FbxReferencePlanError as error:
        return _error(error.code.value, error)
    except DiscoveryError as error:
        return _error("discovery_failed", error)
    except OSError as error:
        return _error("fbx_reference_plan_failed", error)
    _ = sys.stdout.write(f"{json.dumps(plan.to_document(), indent=2, sort_keys=True)}\n")
    return 0


def _error(code: str, error: Exception) -> int:
    """Emit one typed plan failure."""
    document = {
        "error": code,
        "message": str(error),
        "schema_version": OUTPUT_SCHEMA_VERSION,
    }
    _ = sys.stderr.write(f"{json.dumps(document, sort_keys=True)}\n")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
