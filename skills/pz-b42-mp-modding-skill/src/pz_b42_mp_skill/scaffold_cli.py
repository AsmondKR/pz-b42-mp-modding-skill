# Copyright (c) 2026 pz-b42-mp-modding-skill contributors
"""Plan and apply deterministic Build 42 mod scaffolds."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import cast

from pz_b42_mp_skill.guard_paths import Policy
from pz_b42_mp_skill.guard_types import GuardError
from pz_b42_mp_skill.scaffold import (
    ScaffoldPlan,
    ScaffoldPlanTypeError,
    ScaffoldSpec,
    ScaffoldSpecError,
    apply_plan,
    build_plan,
)


def parser() -> argparse.ArgumentParser:
    """Build the command-line contract."""
    result = argparse.ArgumentParser(description=__doc__)
    subparsers = result.add_subparsers(dest="mode", required=True)
    plan = subparsers.add_parser("plan")
    _ = plan.add_argument("--policy", required=True, type=Path)
    _ = plan.add_argument("--mod-id", required=True)
    _ = plan.add_argument("--name", required=True)
    _ = plan.add_argument("--author", required=True)
    _ = plan.add_argument("--output-root", default="generated")
    apply = subparsers.add_parser("apply")
    _ = apply.add_argument("--policy", required=True, type=Path)
    _ = apply.add_argument("--plan", required=True, help="reviewed plan path, or - for stdin")
    return result


def main(arguments: list[str] | None = None) -> int:
    """Plan or apply one deterministic scaffold."""
    namespace = parser().parse_args(arguments)
    mode = cast("str", namespace.mode)
    try:
        policy = Policy.load(cast("Path", namespace.policy))
        if mode == "plan":
            spec = ScaffoldSpec(
                cast("str", namespace.mod_id),
                cast("str", namespace.name),
                cast("str", namespace.author),
                cast("str", namespace.output_root),
            )
            _ = sys.stdout.write(f"{build_plan(policy, spec).to_json()}\n")
            return 0
        plan_argument = cast("str", namespace.plan)
        plan_text = (
            sys.stdin.read()
            if plan_argument == "-"
            else Path(plan_argument).read_text(encoding="utf-8")
        )
        plan = ScaffoldPlan.from_json(plan_text)
        for path in apply_plan(policy, plan):
            _ = sys.stdout.write(f"{path}\n")
    except (GuardError, ScaffoldPlanTypeError, ScaffoldSpecError, OSError) as error:
        code = error.code if isinstance(error, GuardError) else "invalid_scaffold"
        _ = sys.stderr.write(f"{json.dumps({'error': code, 'message': str(error)})}\n")
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
