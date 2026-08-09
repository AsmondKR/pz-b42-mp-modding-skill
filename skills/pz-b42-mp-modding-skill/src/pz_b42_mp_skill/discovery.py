# Copyright (c) 2026 pz-b42-mp-modding-skill contributors
"""Read-only discovery of a local Project Zomboid Build 42 installation."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import asdict, dataclass
from enum import StrEnum
from pathlib import Path
from typing import cast, final

from pz_b42_mp_skill import OUTPUT_SCHEMA_VERSION


class DiscoveryErrorCode(StrEnum):
    """Stable discovery failure categories."""

    INSTALL_MISSING = "install_missing"
    INSTALLATION_NOT_FOUND = "installation_not_found"
    MANIFEST_KEY_MISSING = "manifest_key_missing"
    MANIFEST_READ_FAILED = "manifest_read_failed"
    VANILLA_EVIDENCE_MISSING = "vanilla_evidence_missing"
    WRONG_APP_ID = "wrong_app_id"


@final
class DiscoveryError(Exception):
    """A stable local-installation discovery failure."""

    def __init__(self, code: DiscoveryErrorCode, detail: str = "") -> None:
        """Create one discovery failure."""
        message = f"{code}: {detail}" if detail else code
        super().__init__(message)


@dataclass(frozen=True)
class DiscoveryResult:
    """Version and evidence roots observed without changing local files."""

    manifest: Path
    install_root: Path
    user_data_root: Path
    build_id: str
    branch: str
    evidence: dict[str, Path]

    def to_json(self) -> str:
        """Return stable machine-readable discovery output."""
        document = asdict(self)
        document["schema_version"] = OUTPUT_SCHEMA_VERSION
        document["manifest"] = str(self.manifest)
        document["install_root"] = str(self.install_root)
        document["user_data_root"] = str(self.user_data_root)
        document["evidence"] = {key: str(value) for key, value in self.evidence.items()}
        return json.dumps(document, indent=2, sort_keys=True)


def discover_from_manifest(manifest: Path, user_data_root: Path) -> DiscoveryResult:
    """Resolve one Steam manifest into verified Build 42 evidence paths."""
    try:
        content = manifest.read_text(encoding="utf-8")
    except OSError as error:
        raise DiscoveryError(DiscoveryErrorCode.MANIFEST_READ_FAILED, str(manifest)) from error
    app_id = value_for(content, "appid")
    build_id = value_for(content, "buildid")
    install_dir = value_for(content, "installdir")
    branch = value_for(content, "BetaKey", default="public")
    if app_id != "108600":
        raise DiscoveryError(DiscoveryErrorCode.WRONG_APP_ID, app_id)
    install_root = (manifest.parent / "common" / install_dir).resolve(strict=False)
    if not install_root.is_dir():
        raise DiscoveryError(DiscoveryErrorCode.INSTALL_MISSING, str(install_root))
    candidates = {
        "client_commands": install_root / "media/lua/server/ClientCommands.lua",
        "server_commands": install_root / "media/lua/client/ServerCommands.lua",
        "ui_panel": install_root / "media/lua/client/ISUI/ISPanel.lua",
    }
    missing = [str(path) for path in candidates.values() if not path.is_file()]
    if missing:
        raise DiscoveryError(DiscoveryErrorCode.VANILLA_EVIDENCE_MISSING, ", ".join(missing))
    return DiscoveryResult(
        manifest=manifest.resolve(strict=True),
        install_root=install_root.resolve(strict=True),
        user_data_root=user_data_root.resolve(strict=False),
        build_id=build_id,
        branch=branch,
        evidence={key: path.resolve(strict=True) for key, path in candidates.items()},
    )


def discover(manifest: Path | None = None) -> DiscoveryResult:
    """Find the first verified local Steam installation."""
    candidates: list[Path] = [manifest] if manifest is not None else manifest_candidates()
    failures: list[str] = []
    for candidate in candidates:
        if not candidate.is_file():
            continue
        try:
            return discover_from_manifest(candidate, Path.home() / "Zomboid")
        except DiscoveryError as error:
            failures.append(str(error))
    details = "; ".join(failures) if failures else "no Steam appmanifest_108600.acf found"
    raise DiscoveryError(DiscoveryErrorCode.INSTALLATION_NOT_FOUND, details)


def manifest_candidates() -> list[Path]:
    """Return conventional Steam manifest locations without scanning disks."""
    if os.name == "nt":
        return [
            Path(os.environ.get("PROGRAMFILES(X86)", r"C:\Program Files (x86)"))
            / "Steam/steamapps/appmanifest_108600.acf",
            Path(os.environ.get("PROGRAMFILES", r"C:\Program Files"))
            / "Steam/steamapps/appmanifest_108600.acf",
        ]
    return [
        Path.home() / ".steam/steam/steamapps/appmanifest_108600.acf",
        Path.home() / ".local/share/Steam/steamapps/appmanifest_108600.acf",
        Path.home() / "Library/Application Support/Steam/steamapps/appmanifest_108600.acf",
    ]


def value_for(document: str, key: str, default: str | None = None) -> str:
    """Read one quoted key/value pair from a Steam VDF document."""
    match = re.search(rf'"{re.escape(key)}"\s+"([^"]+)"', document)
    if match is not None:
        return match.group(1)
    if default is not None:
        return default
    raise DiscoveryError(DiscoveryErrorCode.MANIFEST_KEY_MISSING, key)


def parser() -> argparse.ArgumentParser:
    """Build the discovery CLI."""
    result = argparse.ArgumentParser(description=__doc__)
    _ = result.add_argument("--manifest", type=Path, help="explicit appmanifest_108600.acf")
    _ = result.add_argument("--json", action="store_true", help="emit JSON")
    return result


def main(arguments: list[str] | None = None) -> int:
    """Run read-only discovery."""
    namespace = parser().parse_args(arguments)
    manifest = cast("Path | None", namespace.manifest)
    emit_json = cast("bool", namespace.json)
    try:
        result = discover(manifest)
    except DiscoveryError as error:
        document = {
            "error": "discovery_failed",
            "message": str(error),
            "schema_version": OUTPUT_SCHEMA_VERSION,
        }
        _ = sys.stderr.write(f"{json.dumps(document)}\n")
        return 2
    if emit_json:
        _ = sys.stdout.write(f"{result.to_json()}\n")
    else:
        _ = sys.stdout.write(
            f"Build {result.build_id} ({result.branch}) at {result.install_root}\n",
        )
        for name, path in result.evidence.items():
            _ = sys.stdout.write(f"{name}: {path}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
