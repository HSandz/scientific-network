"""In-process SQLite vector artifact store for GraphRAG embeddings (spec §6.2)."""

from __future__ import annotations

import json
from pathlib import Path
import sqlite3
from typing import Any

import numpy as np


class SQLiteVectorStore:
    """Stores L2-normalized float32 embeddings in SQLite for portable CPU cosine search."""

    def __init__(self, db_path: Path) -> None:
        self.db_path = Path(db_path)

    def write(self, records: list[dict[str, Any]], *, dim: int = 384) -> dict[str, int]:
        """Replace vectors table with ``records``: [{kind, id, text, metadata, embedding}]."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.db_path.with_suffix(".tmp")
        if tmp.exists():
            tmp.unlink()
        conn = sqlite3.connect(str(tmp))
        try:
            conn.execute(
                "CREATE TABLE vectors ("
                "kind TEXT NOT NULL, "
                "id TEXT NOT NULL, "
                "text TEXT NOT NULL, "
                "metadata_json TEXT NOT NULL, "
                "dim INTEGER NOT NULL, "
                "embedding BLOB NOT NULL, "
                "PRIMARY KEY (kind, id))"
            )
            conn.execute("CREATE INDEX idx_vectors_kind ON vectors(kind)")
            counts: dict[str, int] = {}
            rows = []
            for rec in records:
                vec = np.asarray(rec["embedding"], dtype=np.float32)
                if vec.shape != (dim,):
                    raise ValueError(f"Expected dim {dim}, got {vec.shape} for {rec['id']}")
                norm = float(np.linalg.norm(vec))
                if norm > 0:
                    vec = vec / norm
                kind = str(rec["kind"])
                counts[kind] = counts.get(kind, 0) + 1
                rows.append((
                    kind,
                    str(rec["id"]),
                    str(rec["text"]),
                    json.dumps(rec.get("metadata") or {}, ensure_ascii=False),
                    dim,
                    vec.tobytes(),
                ))
            conn.executemany(
                "INSERT INTO vectors(kind, id, text, metadata_json, dim, embedding) VALUES (?, ?, ?, ?, ?, ?)",
                rows,
            )
            conn.commit()
        finally:
            conn.close()
        tmp.replace(self.db_path)
        return counts

    def load_kind(self, kind: str) -> tuple[list[dict[str, Any]], np.ndarray]:
        if not self.db_path.exists():
            return [], np.zeros((0, 384), dtype=np.float32)
        conn = sqlite3.connect(f"file:{self.db_path}?mode=ro", uri=True)
        try:
            cur = conn.execute(
                "SELECT id, text, metadata_json, dim, embedding FROM vectors WHERE kind = ? ORDER BY id",
                (kind,),
            )
            items: list[dict[str, Any]] = []
            vecs: list[np.ndarray] = []
            for rid, text, meta_s, dim, blob in cur:
                items.append({"kind": kind, "id": rid, "text": text, "metadata": json.loads(meta_s)})
                vecs.append(np.frombuffer(blob, dtype=np.float32, count=dim))
        finally:
            conn.close()
        if not vecs:
            return [], np.zeros((0, 384), dtype=np.float32)
        return items, np.vstack(vecs)

    def search(self, kind: str, query_vec: np.ndarray, top_k: int = 10) -> list[dict[str, Any]]:
        items, mat = self.load_kind(kind)
        if not items:
            return []
        q = np.asarray(query_vec, dtype=np.float32)
        norm = float(np.linalg.norm(q))
        if norm > 0:
            q = q / norm
        scores = mat @ q
        k = min(max(int(top_k), 1), len(items))
        idx = np.argpartition(-scores, k - 1)[:k]
        idx = idx[np.argsort(-scores[idx])]
        return [{**items[i], "score": float(scores[i])} for i in idx]
