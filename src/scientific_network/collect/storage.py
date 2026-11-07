"""Immutable public-source cache and small stage artifact helpers."""

from datetime import datetime, timezone
from hashlib import sha256
import json
import time
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit, parse_qsl

import httpx
import pyarrow as pa
import pyarrow.parquet as pq
import yaml


class SourceError(RuntimeError):
    """Sanitized source failure: never includes a credential-bearing request URL."""

    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code


class QuotaError(SourceError):
    pass


def digest(data: bytes) -> str:
    return sha256(data).hexdigest()


def read_config(path: Path) -> dict:
    value = yaml.safe_load(path.read_text())
    if not isinstance(value, dict):
        raise ValueError("configuration must be a mapping")
    return value


def write_bytes(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("xb") as stream:
            stream.write(data)
    except FileExistsError:
        if path.read_bytes() != data:
            raise ValueError(f"refusing to overwrite different artifact: {path}") from None


def write_json(path: Path, value) -> None:
    write_bytes(path, (json.dumps(value, indent=2, ensure_ascii=False) + "\n").encode())


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def write_jsonl(path: Path, rows: list[dict]) -> None:
    write_bytes(path, "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows).encode())


def write_table(path: Path, rows: list[dict]) -> None:
    """JSONL is the portable ledger; Parquet mirrors it for downstream joins."""
    write_jsonl(path.with_suffix(".jsonl"), rows)
    if not path.exists():
        pq.write_table(pa.Table.from_pylist(rows), path)
    elif pq.read_table(path).to_pylist() != rows:
        raise ValueError(f"refusing to overwrite different table: {path}")


class SourceCache:
    def __init__(self, root: Path, *, timeout: float = 30, attempts: int = 4,
                 client: httpx.Client | None = None, delay: float = 0.2):
        self.root, self.attempts, self.delay = root, attempts, delay
        self.client = client or httpx.Client(timeout=timeout, follow_redirects=True,
            headers={"User-Agent": "ScientificNetworkCourse/0.1 (research metadata pilot)"})
        self.owns_client = client is None

    def __enter__(self):
        return self

    def __exit__(self, *_):
        if self.owns_client:
            self.client.close()

    def get(self, url: str, *, params: dict | None = None,
            secret_params: dict | None = None) -> tuple[bytes, dict]:
        parts = urlsplit(url)
        params = {**dict(parse_qsl(parts.query, keep_blank_values=True)), **(params or {})}
        url = urlunsplit((parts.scheme, parts.netloc, parts.path, "", ""))
        if any(key.lower() in {"api_key", "token", "password", "authorization"} for key in params):
            raise ValueError("credentials must use secret_params, never public cache metadata")
        descriptor = {"url": url, "params": params}
        request_id = digest(json.dumps(descriptor, sort_keys=True).encode())
        metadata_path = self.root / "requests" / f"{request_id}.json"
        if metadata_path.exists():
            record = json.loads(metadata_path.read_text())
            body = (self.root / "objects" / record["sha256"]).read_bytes()
            if digest(body) != record["sha256"]:
                raise SourceError("cached source hash mismatch")
            return body, record
        for attempt in range(1, self.attempts + 1):
            try:
                response = self.client.get(url, params=({**params, **(secret_params or {})} or None))
            except httpx.RequestError as exc:
                if attempt == self.attempts:
                    raise SourceError(f"{urlsplit(url).netloc}: {type(exc).__name__}") from None
                time.sleep(min(2 ** (attempt - 1), 8))
                continue
            if response.status_code in {401, 402, 403, 429}:
                raise QuotaError(f"{urlsplit(url).netloc}: access/quota HTTP {response.status_code}; collection stopped")
            if response.status_code >= 500 and attempt < self.attempts:
                retry = response.headers.get("Retry-After", "")
                wait = float(retry) if retry.isdigit() else 2 ** (attempt - 1)
                if wait > 60:
                    raise SourceError("source requests retry after more than 60 seconds; resume later")
                time.sleep(wait)
                continue
            if response.status_code != 200:
                raise SourceError(f"{urlsplit(url).netloc}: HTTP {response.status_code}", response.status_code)
            body = response.content
            record = {**descriptor, "request_id": request_id, "sha256": digest(body),
                "retrieved_at": datetime.now(timezone.utc).isoformat(),
                "status": 200, "attempts": attempt,
                "content_type": response.headers.get("Content-Type", ""),
                "license": "unknown_unless_record_supplies_license"}
            write_bytes(self.root / "objects" / record["sha256"], body)
            write_json(metadata_path, record)
            if self.delay:
                time.sleep(self.delay)
            return body, record
        raise SourceError("source exhausted retries")
