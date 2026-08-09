# Copyright (c) 2026 pz-b42-mp-modding-skill contributors
"""Validate one policy-bound Blender asset manifest."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import cast

from pz_b42_mp_skill import OUTPUT_SCHEMA_VERSION
from pz_b42_mp_skill.asset_manifest import AssetManifestError, load_asset_manifest
from pz_b42_mp_skill.guard_paths import Policy
from pz_b42_mp_skill.guard_types import GuardError


def parser() -> argparse.ArgumentParser:
    """Build the asset-manifest CLI parser."""
    result = argparse.ArgumentParser(description=__doc__)
    _ = result.add_argument("--manifest", required=True, type=Path)
    _ = result.add_argument("--policy", required=True, type=Path)
    return result


def main(arguments: list[str] | None = None) -> int:
    """Validate one manifest without starting Blender."""
    namespace = parser().parse_args(arguments)
    try:
        policy = Policy.load(cast("Path", namespace.policy))
        manifest = load_asset_manifest(cast("Path", namespace.manifest), policy)
    except (AssetManifestError, GuardError) as error:
        code = error.code.value
        document = {
            "error": code,
            "message": str(error),
            "schema_version": OUTPUT_SCHEMA_VERSION,
        }
        _ = sys.stderr.write(f"{json.dumps(document, sort_keys=True)}\n")
        return 2
    _ = sys.stdout.write(f"{json.dumps(manifest.to_document(), indent=2, sort_keys=True)}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
