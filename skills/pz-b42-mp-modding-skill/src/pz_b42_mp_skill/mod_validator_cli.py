# Copyright (c) 2026 pz-b42-mp-modding-skill contributors
"""CLI for read-only Build 42 multiplayer mod package preflight."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import cast

from pz_b42_mp_skill.mod_validator import ModValidationError, validate_mod_root


def parser() -> argparse.ArgumentParser:
    """Build the preflight CLI parser."""
    result = argparse.ArgumentParser(description=__doc__)
    _ = result.add_argument("--mod-root", required=True, type=Path)
    _ = result.add_argument("--json", action="store_true")
    return result


def main(arguments: list[str] | None = None) -> int:
    """Run one read-only mod preflight."""
    namespace = parser().parse_args(arguments)
    try:
        result = validate_mod_root(cast("Path", namespace.mod_root))
    except ModValidationError as error:
        _ = sys.stderr.write(
            f"{json.dumps({'error': error.code, 'message': str(error)})}\n",
        )
        return 2
    if cast("bool", namespace.json):
        _ = sys.stdout.write(f"{json.dumps(result.to_document(), indent=2, sort_keys=True)}\n")
    elif result.valid:
        _ = sys.stdout.write(f"PASS {result.mod_id} at {result.mod_root}\n")
    else:
        for issue in result.issues:
            _ = sys.stdout.write(f"{issue.code} {issue.relative_path}: {issue.message}\n")
    return 0 if result.valid else 1


if __name__ == "__main__":
    raise SystemExit(main())
