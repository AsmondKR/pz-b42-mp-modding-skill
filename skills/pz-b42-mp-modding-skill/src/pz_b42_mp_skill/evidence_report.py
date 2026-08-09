# Copyright (c) 2026 pz-b42-mp-modding-skill contributors
"""Read-only multi-symbol evidence reports for one verified Build 42 install."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import cast

from pz_b42_mp_skill.api_query import (
    ApiQueryError,
    ApiQueryErrorCode,
    SymbolEvidence,
    find_symbol_evidence,
    resolve_query_target,
)


@dataclass(frozen=True)
class SymbolReport:
    """Evidence and explicit found status for one requested symbol."""

    symbol: str
    matches: tuple[SymbolEvidence, ...]

    @property
    def found(self) -> bool:
        """Return whether at least one exact source location was found."""
        return bool(self.matches)

    def to_document(self) -> dict[str, object]:
        """Return one JSON-compatible symbol report."""
        return {
            "found": self.found,
            "matches": [asdict(match) for match in self.matches],
            "symbol": self.symbol,
        }


@dataclass(frozen=True)
class EvidenceReport:
    """One ordered batch of claims under shared build provenance."""

    install_root: Path
    build_id: str | None
    branch: str | None
    queries: tuple[SymbolReport, ...]

    @property
    def complete(self) -> bool:
        """Return whether every requested symbol has evidence."""
        return all(query.found for query in self.queries)

    def to_document(self) -> dict[str, object]:
        """Return the complete JSON-compatible report."""
        return {
            "branch": self.branch,
            "build_id": self.build_id,
            "complete": self.complete,
            "install_root": str(self.install_root),
            "queries": [query.to_document() for query in self.queries],
        }


def build_evidence_report(
    symbols: tuple[str, ...],
    *,
    manifest: Path | None = None,
    install_root: Path | None = None,
    limit: int = 25,
) -> EvidenceReport:
    """Collect ordered symbol evidence after resolving one installation."""
    if not symbols:
        raise ApiQueryError(ApiQueryErrorCode.INVALID_SYMBOL, "at least one symbol required")
    target = resolve_query_target(install_root, manifest)
    queries = tuple(
        SymbolReport(
            symbol,
            find_symbol_evidence(target.install_root, symbol, limit=limit),
        )
        for symbol in symbols
    )
    return EvidenceReport(
        install_root=target.install_root,
        build_id=target.build_id,
        branch=target.branch,
        queries=queries,
    )


def parser() -> argparse.ArgumentParser:
    """Build the batch evidence CLI parser."""
    result = argparse.ArgumentParser(description=__doc__)
    location = result.add_mutually_exclusive_group()
    _ = location.add_argument("--install-root", type=Path)
    _ = location.add_argument("--manifest", type=Path)
    _ = result.add_argument("--symbol", action="append", required=True)
    _ = result.add_argument("--limit", default=25, type=int)
    _ = result.add_argument("--json", action="store_true")
    return result


def main(arguments: list[str] | None = None) -> int:
    """Run one read-only batch evidence report."""
    namespace = parser().parse_args(arguments)
    try:
        report = build_evidence_report(
            tuple(cast("list[str]", namespace.symbol)),
            manifest=cast("Path | None", namespace.manifest),
            install_root=cast("Path | None", namespace.install_root),
            limit=cast("int", namespace.limit),
        )
    except ApiQueryError as error:
        _ = sys.stderr.write(
            f"{json.dumps({'error': error.code, 'message': str(error)})}\n",
        )
        return 2
    if cast("bool", namespace.json):
        _ = sys.stdout.write(f"{json.dumps(report.to_document(), indent=2, sort_keys=True)}\n")
    else:
        if report.build_id is not None:
            _ = sys.stdout.write(
                f"Build {report.build_id} ({report.branch}) at {report.install_root}\n",
            )
        for query in report.queries:
            state = "FOUND" if query.found else "MISSING"
            _ = sys.stdout.write(f"{state} {query.symbol}: {len(query.matches)} matches\n")
    return 0 if report.complete else 1


if __name__ == "__main__":
    raise SystemExit(main())
