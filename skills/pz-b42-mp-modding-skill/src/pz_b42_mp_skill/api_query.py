# Copyright (c) 2026 pz-b42-mp-modding-skill contributors
"""Read-only extraction of symbol evidence from installed Build 42 Lua."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from enum import StrEnum
from pathlib import Path
from typing import cast, final

_SYMBOL = re.compile(r"[A-Za-z_][A-Za-z0-9_.:]*\Z")
_FUNCTION_DECLARATION = re.compile(
    r"^\s*(?:local\s+)?function\s+([A-Za-z_][A-Za-z0-9_.:]*)\s*\(([^)]*)\)",
)
_FUNCTION_ASSIGNMENT = re.compile(
    r"^\s*([A-Za-z_][A-Za-z0-9_.:]*)\s*=\s*function\s*\(([^)]*)\)",
)
_EVENT = re.compile(
    r"Events\.([A-Za-z_][A-Za-z0-9_]*)\.Add\s*\(([^)]*)\)",
)
_DERIVATION_PREFIX = r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*"
_DERIVATION_SUFFIX = r'([A-Za-z_][A-Za-z0-9_.:]*)\:derive\s*\(\s*"([^"]+)"\s*\)'
_DERIVATION = re.compile(f"{_DERIVATION_PREFIX}{_DERIVATION_SUFFIX}")


class EvidenceKind(StrEnum):
    """Stable categories for source-backed Lua evidence."""

    CLASS_DERIVATION = "class_derivation"
    EVENT_REGISTRATION = "event_registration"
    FUNCTION = "function"
    REFERENCE = "reference"


class ApiQueryErrorCode(StrEnum):
    """Stable query failure categories."""

    INVALID_LIMIT = "invalid_limit"
    INVALID_SYMBOL = "invalid_symbol"
    LUA_ROOT_MISSING = "lua_root_missing"
    READ_FAILED = "read_failed"
    SYMBOL_NOT_FOUND = "symbol_not_found"


@final
class ApiQueryError(Exception):
    """A query refusal with a stable machine-readable code."""

    code: ApiQueryErrorCode

    def __init__(self, code: ApiQueryErrorCode, detail: str) -> None:
        """Create one typed failure."""
        super().__init__(detail)
        self.code = code


@dataclass(frozen=True)
class SymbolEvidence:
    """One exact source location that supports a symbol claim."""

    relative_path: str
    line_number: int
    kind: EvidenceKind
    symbol: str
    signature: str
    snippet: str


@dataclass(frozen=True)
class _SourceLine:
    relative_path: str
    line_number: int
    raw: str
    code: str


def find_symbol_evidence(
    install_root: Path,
    symbol: str,
    *,
    limit: int = 100,
) -> tuple[SymbolEvidence, ...]:
    """Find exact symbol definitions, registrations, derivations, and references."""
    if _SYMBOL.fullmatch(symbol) is None:
        raise ApiQueryError(ApiQueryErrorCode.INVALID_SYMBOL, symbol)
    if limit < 1:
        raise ApiQueryError(ApiQueryErrorCode.INVALID_LIMIT, str(limit))
    lua_root = install_root / "media" / "lua"
    if not lua_root.is_dir():
        raise ApiQueryError(ApiQueryErrorCode.LUA_ROOT_MISSING, str(lua_root))

    matches: list[SymbolEvidence] = []
    for path in sorted(lua_root.rglob("*.lua")):
        if not path.is_file():
            continue
        remaining = limit - len(matches)
        matches.extend(_scan_file(path, install_root, symbol)[:remaining])
        if len(matches) >= limit:
            break
    return tuple(matches)


def _scan_file(path: Path, install_root: Path, symbol: str) -> list[SymbolEvidence]:
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError as error:
        raise ApiQueryError(ApiQueryErrorCode.READ_FAILED, str(path)) from error
    relative_path = path.relative_to(install_root).as_posix()
    matches: list[SymbolEvidence] = []
    for line_number, raw in enumerate(lines, start=1):
        code = raw.split("--", 1)[0].strip()
        if not code:
            continue
        evidence = _classify_line(_SourceLine(relative_path, line_number, raw, code), symbol)
        if evidence is not None:
            matches.append(evidence)
    return matches


def _classify_line(source: _SourceLine, symbol: str) -> SymbolEvidence | None:
    function = _FUNCTION_DECLARATION.search(source.code)
    if function is None:
        function = _FUNCTION_ASSIGNMENT.search(source.code)
    if function is not None and symbol in re.split(r"[.:]", function.group(1)):
        return _evidence(source, EvidenceKind.FUNCTION, symbol)
    event = _EVENT.search(source.code)
    if event is not None and event.group(1) == symbol:
        return _evidence(source, EvidenceKind.EVENT_REGISTRATION, symbol)
    derivation = _DERIVATION.search(source.code)
    if derivation is not None and symbol in derivation.groups():
        return _evidence(source, EvidenceKind.CLASS_DERIVATION, symbol)
    exact_reference = re.compile(
        rf"(?<![A-Za-z0-9_]){re.escape(symbol)}(?![A-Za-z0-9_])",
    )
    if exact_reference.search(source.code) is not None:
        return _evidence(source, EvidenceKind.REFERENCE, symbol)
    return None


def _evidence(
    source: _SourceLine,
    kind: EvidenceKind,
    symbol: str,
) -> SymbolEvidence:
    return SymbolEvidence(
        relative_path=source.relative_path,
        line_number=source.line_number,
        kind=kind,
        symbol=symbol,
        signature=source.code,
        snippet=source.raw.strip(),
    )


def parser() -> argparse.ArgumentParser:
    """Build the read-only query CLI parser."""
    argument_parser = argparse.ArgumentParser(
        description="Query exact symbol evidence from installed Project Zomboid Lua.",
    )
    _ = argument_parser.add_argument("--install-root", required=True, type=Path)
    _ = argument_parser.add_argument("--symbol", required=True)
    _ = argument_parser.add_argument("--limit", default=100, type=int)
    _ = argument_parser.add_argument("--json", action="store_true")
    return argument_parser


def main(arguments: list[str] | None = None) -> int:
    """Run one read-only symbol evidence query."""
    namespace = parser().parse_args(arguments)
    symbol = cast("str", namespace.symbol)
    install_root = cast("Path", namespace.install_root)
    limit = cast("int", namespace.limit)
    try:
        matches = find_symbol_evidence(
            install_root,
            symbol,
            limit=limit,
        )
    except ApiQueryError as error:
        return _write_error(error)
    if not matches:
        return _write_error(
            ApiQueryError(ApiQueryErrorCode.SYMBOL_NOT_FOUND, symbol),
        )

    if cast("bool", namespace.json):
        document = {
            "install_root": str(install_root),
            "matches": [asdict(match) for match in matches],
            "symbol": symbol,
        }
        _ = sys.stdout.write(f"{json.dumps(document, indent=2, sort_keys=True)}\n")
    else:
        for match in matches:
            _ = sys.stdout.write(
                f"{match.relative_path}:{match.line_number} [{match.kind}] {match.signature}\n",
            )
    return 0


def _write_error(error: ApiQueryError) -> int:
    _ = sys.stderr.write(
        f"{json.dumps({'error': error.code, 'message': str(error)})}\n",
    )
    return 3 if error.code is ApiQueryErrorCode.SYMBOL_NOT_FOUND else 2


if __name__ == "__main__":
    raise SystemExit(main())
