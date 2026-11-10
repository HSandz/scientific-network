"""Indexed read-only evidence access, without materializing the full graph ledger."""

from collections.abc import Mapping, Iterator
import json
from pathlib import Path
import sqlite3
from typing import Any


class LedgerMapping(Mapping):
    """Small mapping adapter matching ArtifactStore's existing lookup contract.

    Each lookup has its own connection so FastAPI worker threads never share one.
    SQLite's page cache is bounded; immutable mode is safe for versioned artifacts.
    """

    def __init__(self, path: Path, kind: str) -> None:
        self.path = path
        self.kind = kind

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(f"{self.path.resolve().as_uri()}?mode=ro&immutable=1", uri=True)
        conn.execute("PRAGMA cache_size=-2048")
        return conn

    def __getitem__(self, key: Any) -> Any:
        conn = self._connect()
        try:
            if self.kind == "evidence":
                row = conn.execute("SELECT payload FROM evidence WHERE id=?", (key,)).fetchone()
                if row is None:
                    raise KeyError(key)
                return json.loads(row[0])
            predicates = {
                "researcher": ("researcher_id=?", (key,)),
                "organization": ("organization_id=?", (key,)),
                "paper": ("paper_id=?", (key,)),
                "pair": ("researcher_id=? AND organization_id=?", tuple(key)),
            }
            clause, params = predicates[self.kind]
            rows = conn.execute(f"SELECT payload FROM affiliations WHERE {clause} ORDER BY seq", params)
            result = [json.loads(row[0]) for row in rows]
            if not result:
                raise KeyError(key)
            return result
        finally:
            conn.close()

    def __len__(self) -> int:
        conn = self._connect()
        try:
            if self.kind == "evidence":
                return conn.execute("SELECT count(*) FROM evidence").fetchone()[0]
            columns = {"researcher": "researcher_id", "organization": "organization_id", "paper": "paper_id", "pair": "researcher_id, organization_id"}[self.kind]
            return conn.execute(f"SELECT count(*) FROM (SELECT DISTINCT {columns} FROM affiliations)").fetchone()[0]
        finally:
            conn.close()

    def __iter__(self) -> Iterator:
        conn = self._connect()
        try:
            columns = {"evidence": "id", "researcher": "researcher_id", "organization": "organization_id", "paper": "paper_id", "pair": "researcher_id, organization_id"}[self.kind]
            table = "evidence" if self.kind == "evidence" else "affiliations"
            for row in conn.execute(f"SELECT DISTINCT {columns} FROM {table}"):
                yield tuple(row) if self.kind == "pair" else row[0]
        finally:
            conn.close()
