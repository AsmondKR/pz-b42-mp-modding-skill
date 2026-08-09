# Copyright (c) 2026 pz-b42-mp-modding-skill contributors
"""Validate or export one Blender-authoritative PZ asset."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import cast

from pz_b42_mp_skill import OUTPUT_SCHEMA_VERSION
from pz_b42_mp_skill.asset_manifest import AssetManifestError, load_asset_manifest
from pz_b42_mp_skill.blender_entry import BlenderMode
from pz_b42_mp_skill.blender_runner import (
    BlenderRunError,
    discover_blender,
    plan_blender_asset,
)
from pz_b42_mp_skill.guard_paths import Policy
from pz_b42_mp_skill.guard_types import GuardError


def parser() -> argparse.ArgumentParser:
    """Build the user-facing Blender asset parser."""
    result = argparse.ArgumentParser(description=__doc__)
    subparsers = result.add_subparsers(dest="mode", required=True)
    for mode in BlenderMode:
        command = subparsers.add_parser(mode)
        _ = command.add_argument("--blender", type=Path)
        _ = command.add_argument("--manifest", required=True, type=Path)
        _ = command.add_argument("--policy", required=True, type=Path)
    return result


def main(arguments: list[str] | None = None) -> int:
    """Run one policy-bound Blender validation or export."""
    namespace = parser().parse_args(arguments)
    try:
        policy = Policy.load(cast("Path", namespace.policy))
        manifest = load_asset_manifest(cast("Path", namespace.manifest), policy)
        blender_value = cast("Path | None", namespace.blender)
        blender = discover_blender(blender_value)
        plan = plan_blender_asset(
            blender,
            manifest,
            policy.policy_path,
            BlenderMode(cast("str", namespace.mode)),
        )
    except (AssetManifestError, BlenderRunError, GuardError) as error:
        _ = sys.stderr.write(f"{json.dumps(_error_document(error), sort_keys=True)}\n")
        return 2
    _ = sys.stdout.write(f"{json.dumps(plan.to_document(), indent=2, sort_keys=True)}\n")
    return 0


def _error_document(
    error: AssetManifestError | BlenderRunError | GuardError,
) -> dict[str, object]:
    return {
        "error": error.code.value,
        "message": str(error),
        "schema_version": OUTPUT_SCHEMA_VERSION,
    }


if __name__ == "__main__":
    raise SystemExit(main())
