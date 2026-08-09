# Copyright (c) 2026 pz-b42-mp-modding-skill contributors
"""Typed mutation policy errors and manifests."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from enum import StrEnum
from typing import cast, final


class GuardErrorCode(StrEnum):
    """Stable machine-readable refusal reasons."""

    DESTINATION_EXISTS = "destination_exists"
    FORBIDDEN_ROOT = "forbidden_root"
    INVALID_DESTINATION = "invalid_destination"
    INVALID_MANIFEST = "invalid_manifest"
    INVALID_POLICY = "invalid_policy"
    PATH_ESCAPE = "path_escape"
    POLICY_CHANGED = "policy_changed"
    SOURCE_CHANGED = "source_changed"
    SOURCE_INVALID = "source_invalid"


@final
class GuardError(Exception):
    """A mutation refusal with a stable code."""

    code: GuardErrorCode

    def __init__(self, code: GuardErrorCode, detail: str) -> None:
        """Create one typed refusal."""
        super().__init__(detail)
        self.code = code


@dataclass(frozen=True)
class CreateManifest:
    """Reviewed preconditions for one create-only operation."""

    destination: str
    policy_sha256: str
    source_sha256: str
    source_size: int
    version: int = 1

    def to_json(self) -> str:
        """Serialize deterministically for review or transport."""
        return json.dumps(
            {
                "destination": self.destination,
                "policy_sha256": self.policy_sha256,
                "source_sha256": self.source_sha256,
                "source_size": self.source_size,
                "version": self.version,
            },
            indent=2,
            sort_keys=True,
        )

    @classmethod
    def from_json(cls, value: str) -> CreateManifest:
        """Parse an untrusted manifest."""
        try:
            document = object_map(
                cast("object", json.loads(value)),
                GuardErrorCode.INVALID_MANIFEST,
            )
        except json.JSONDecodeError as error:
            raise GuardError(GuardErrorCode.INVALID_MANIFEST, str(error)) from error
        destination = document.get("destination")
        policy_hash = document.get("policy_sha256")
        source_hash = document.get("source_sha256")
        source_size = document.get("source_size")
        if (
            document.get("version") != 1
            or not isinstance(destination, str)
            or not isinstance(policy_hash, str)
            or not isinstance(source_hash, str)
            or type(source_size) is not int
            or source_size < 0
            or not is_sha256(policy_hash)
            or not is_sha256(source_hash)
        ):
            raise GuardError(GuardErrorCode.INVALID_MANIFEST, "invalid_fields")
        return cls(destination, policy_hash, source_hash, source_size)


def object_map(value: object, code: GuardErrorCode) -> dict[str, object]:
    """Narrow untrusted JSON to a string-keyed object."""
    if not isinstance(value, dict):
        raise GuardError(code, "expected_object")
    values = cast("dict[object, object]", value)
    if not all(isinstance(key, str) for key in values):
        raise GuardError(code, "expected_string_keys")
    return {cast("str", key): item for key, item in values.items()}


def string_list(value: object, field: str) -> list[str]:
    """Narrow untrusted JSON to a string list."""
    if not isinstance(value, list):
        raise GuardError(GuardErrorCode.INVALID_POLICY, field)
    values = cast("list[object]", value)
    if not all(isinstance(item, str) for item in values):
        raise GuardError(GuardErrorCode.INVALID_POLICY, field)
    return [cast("str", item) for item in values]


def sha256_bytes(value: bytes) -> str:
    """Hash exact reviewed bytes."""
    return hashlib.sha256(value).hexdigest()


def is_sha256(value: str) -> bool:
    """Return whether a value is a lowercase SHA-256 digest."""
    digest_length = 64
    return len(value) == digest_length and all(
        character in "0123456789abcdef" for character in value
    )
