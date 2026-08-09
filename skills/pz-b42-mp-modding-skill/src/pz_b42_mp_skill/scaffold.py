# Copyright (c) 2026 pz-b42-mp-modding-skill contributors
"""Create-only Build 42 multiplayer mod scaffolding."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path, PurePosixPath
from typing import cast, final

from pz_b42_mp_skill import guard_paths
from pz_b42_mp_skill.mutation_guard import GuardError, GuardErrorCode, Policy

_MOD_ID = re.compile(r"[A-Za-z][A-Za-z0-9_]{2,63}\Z")


class ScaffoldErrorCode(StrEnum):
    """Stable scaffold input and plan failures."""

    EXPECTED_OBJECT = "expected_object"
    EXPECTED_STRING = "expected_string"
    INVALID_FIELDS = "invalid_fields"
    INVALID_JSON = "invalid_json"
    INVALID_METADATA = "invalid_metadata"
    INVALID_MOD_ID = "invalid_mod_id"
    INVALID_OUTPUT_ROOT = "invalid_output_root"
    INVALID_PLANNED_FILE = "invalid_planned_file"
    INVALID_VERSION = "invalid_version"


@final
class ScaffoldSpecError(ValueError):
    """A stable invalid scaffold specification."""

    def __init__(self, code: ScaffoldErrorCode, detail: str = "") -> None:
        """Create a specification failure."""
        message = f"{code}: {detail}" if detail else code
        super().__init__(message)


@final
class ScaffoldPlanTypeError(TypeError):
    """A stable malformed scaffold-plan failure."""

    def __init__(self, code: ScaffoldErrorCode, detail: str = "") -> None:
        """Create a plan-shape failure."""
        message = f"{code}: {detail}" if detail else code
        super().__init__(message)


@dataclass(frozen=True)
class ScaffoldSpec:
    """Human-reviewed identity and output location."""

    mod_id: str
    display_name: str
    author: str
    output_root: str

    def __post_init__(self) -> None:
        """Validate values that become file names or metadata."""
        if not _MOD_ID.fullmatch(self.mod_id):
            raise ScaffoldSpecError(ScaffoldErrorCode.INVALID_MOD_ID, self.mod_id)
        for field in (self.display_name, self.author):
            if not field.strip() or "\n" in field or "\r" in field:
                raise ScaffoldSpecError(ScaffoldErrorCode.INVALID_METADATA)
        output = PurePosixPath(self.output_root)
        if output.is_absolute() or ".." in output.parts or len(output.parts) != 1:
            raise ScaffoldSpecError(ScaffoldErrorCode.INVALID_OUTPUT_ROOT, self.output_root)


@dataclass(frozen=True)
class PlannedFile:
    """One deterministic generated file."""

    destination: str
    sha256: str


@dataclass(frozen=True)
class ScaffoldPlan:
    """Dry-run output tied to one policy and one deterministic spec."""

    policy_sha256: str
    spec: ScaffoldSpec
    files: tuple[PlannedFile, ...]

    def to_json(self) -> str:
        """Serialize a deterministic plan for human review."""
        return json.dumps(
            {
                "files": [
                    {"destination": item.destination, "sha256": item.sha256} for item in self.files
                ],
                "policy_sha256": self.policy_sha256,
                "spec": {
                    "author": self.spec.author,
                    "display_name": self.spec.display_name,
                    "mod_id": self.spec.mod_id,
                    "output_root": self.spec.output_root,
                },
                "version": 1,
            },
            indent=2,
            sort_keys=True,
        )

    @classmethod
    def from_json(cls, value: str) -> ScaffoldPlan:
        """Parse a reviewed plan without trusting its shape."""
        try:
            raw = cast("object", json.loads(value))
        except json.JSONDecodeError as error:
            raise ScaffoldPlanTypeError(ScaffoldErrorCode.INVALID_JSON, str(error)) from error
        if not isinstance(raw, dict):
            raise ScaffoldPlanTypeError(ScaffoldErrorCode.EXPECTED_OBJECT)
        document = cast("dict[object, object]", raw)
        if document.get("version") != 1:
            raise ScaffoldPlanTypeError(ScaffoldErrorCode.INVALID_VERSION)
        spec_raw = document.get("spec")
        files_raw = document.get("files")
        fingerprint = document.get("policy_sha256")
        if (
            not isinstance(spec_raw, dict)
            or not isinstance(files_raw, list)
            or not isinstance(fingerprint, str)
        ):
            raise ScaffoldPlanTypeError(ScaffoldErrorCode.INVALID_FIELDS)
        spec_document = cast("dict[object, object]", spec_raw)
        spec = ScaffoldSpec(
            _required_string(spec_document, "mod_id"),
            _required_string(spec_document, "display_name"),
            _required_string(spec_document, "author"),
            _required_string(spec_document, "output_root"),
        )
        files: list[PlannedFile] = []
        for item in cast("list[object]", files_raw):
            if not isinstance(item, dict):
                raise ScaffoldPlanTypeError(ScaffoldErrorCode.INVALID_PLANNED_FILE)
            item_document = cast("dict[object, object]", item)
            files.append(
                PlannedFile(
                    _required_string(item_document, "destination"),
                    _required_string(item_document, "sha256"),
                ),
            )
        return cls(fingerprint, spec, tuple(files))


def build_plan(policy: Policy, spec: ScaffoldSpec) -> ScaffoldPlan:
    """Return a no-write plan after checking the approved root."""
    _ = _approved_root(policy, spec)
    files = _render_files(spec)
    planned = tuple(
        PlannedFile(destination, hashlib.sha256(content).hexdigest())
        for destination, content in sorted(files.items())
    )
    return ScaffoldPlan(policy.fingerprint, spec, planned)


def apply_plan(policy: Policy, plan: ScaffoldPlan) -> tuple[Path, ...]:
    """Create a complete new mod root without touching existing content."""
    policy.ensure_current()
    if policy.fingerprint != plan.policy_sha256:
        raise GuardError(GuardErrorCode.POLICY_CHANGED, "policy fingerprint changed")
    output_root = _approved_root(policy, plan.spec)
    mod_root = output_root / plan.spec.mod_id
    if mod_root.exists() or mod_root.is_symlink():
        raise GuardError(GuardErrorCode.DESTINATION_EXISTS, str(mod_root))

    files = _render_files(plan.spec)
    actual = tuple(
        PlannedFile(destination, hashlib.sha256(content).hexdigest())
        for destination, content in sorted(files.items())
    )
    if actual != plan.files:
        raise GuardError(GuardErrorCode.INVALID_MANIFEST, "scaffold plan content changed")

    mod_root.mkdir(mode=0o700)
    created: list[Path] = []
    try:
        for relative, content in sorted(files.items()):
            lexical = policy.workspace_root / Path(relative)
            lexical.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
            destination = guard_paths.authorize_destination(policy, relative)
            with destination.open("xb") as stream:
                _ = stream.write(content)
                stream.flush()
            created.append(destination)
    except BaseException:
        for destination in reversed(created):
            destination.unlink(missing_ok=True)
        raise
    return tuple(created)


def _approved_root(policy: Policy, spec: ScaffoldSpec) -> Path:
    candidate = (policy.workspace_root / spec.output_root).resolve(strict=True)
    if candidate not in policy.allowed_output_roots:
        raise GuardError(GuardErrorCode.PATH_ESCAPE, spec.output_root)
    return candidate


def _render_files(spec: ScaffoldSpec) -> dict[str, bytes]:
    root = PurePosixPath(spec.output_root) / spec.mod_id
    versioned = root / "Contents" / "mods" / spec.mod_id / "42"
    lua_root = versioned / "media" / "lua"
    files = {
        root / "workshop.txt": (
            "version=1\n"
            "workshopid=0\n"
            f"title={spec.display_name}\n"
            "description=Build 42 multiplayer mod\n"
            "visibility=public\n"
            "tags=Build 42;Multiplayer\n"
        ),
        versioned / "mod.info": (
            f"name={spec.display_name}\n"
            f"id={spec.mod_id}\n"
            f"author={spec.author}\n"
            "description=Server-authoritative Build 42 multiplayer mod.\n"
        ),
        lua_root / "shared" / f"{spec.mod_id}Shared.lua": (
            f'{spec.mod_id} = {spec.mod_id} or {{}}\n{spec.mod_id}.MODULE = "{spec.mod_id}"\n'
        ),
        lua_root / "client" / f"{spec.mod_id}Client.lua": _client_template(spec),
        lua_root / "server" / f"{spec.mod_id}Server.lua": _server_template(spec),
    }
    return {path.as_posix(): value.encode() for path, value in files.items()}


def _client_template(spec: ScaffoldSpec) -> str:
    return (
        f'require "{spec.mod_id}Shared"\n\n'
        "local function onServerCommand(module, command, args)\n"
        f"    if module ~= {spec.mod_id}.MODULE then return end\n"
        "    -- Render only server-confirmed state here.\n"
        "end\n\n"
        "Events.OnServerCommand.Add(onServerCommand)\n"
    )


def _server_template(spec: ScaffoldSpec) -> str:
    return (
        f'require "{spec.mod_id}Shared"\n\n'
        "local function onClientCommand(module, command, player, args)\n"
        f"    if module ~= {spec.mod_id}.MODULE then return end\n"
        "    -- Treat args as untrusted. Validate player, permission, and world state.\n"
        "end\n\n"
        "Events.OnClientCommand.Add(onClientCommand)\n"
    )


def _required_string(document: dict[object, object], key: str) -> str:
    value = document.get(key)
    if not isinstance(value, str):
        raise ScaffoldPlanTypeError(ScaffoldErrorCode.EXPECTED_STRING, key)
    return value
