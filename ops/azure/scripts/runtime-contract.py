#!/usr/bin/env python3
"""Conservative compatibility fingerprint; changes require operator review.

Hash the release assumptions and artifact readers. The VM pins this value
separately from code delivery; an image cannot approve its own contract change.
"""
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
FILES = (
    'apps/research-explorer/backend/config.py',
    'apps/research-explorer/backend/repositories/artifact_store.py',
    'apps/research-explorer/backend/repositories/sqlite_ledger.py',
)


def fingerprint(root=ROOT):
    h = hashlib.sha256()
    for name in FILES:
        h.update(name.encode() + b'\0' + (root / name).read_bytes() + b'\0')
    return h.hexdigest()


if __name__ == '__main__':
    print(fingerprint())
