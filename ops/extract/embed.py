"""Embed strings with all-MiniLM-L6-v2 (mean pooling, L2-normalised) for entity merging and linking.

Runs in the ``ops/extract`` environment. Input: JSONL ``{"id", "text"}``; output: ``<output>.npy``
(float32, rows in input order) and ``<output>.ids.json``. Same model as the v4 topic classifier.

    uv run --project ops/extract python ops/extract/embed.py --input in.jsonl --output out --device cuda
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import torch
from huggingface_hub import snapshot_download
from transformers import AutoModel, AutoTokenizer

REPO = "sentence-transformers/all-MiniLM-L6-v2"
REVISION = "1110a243fdf4706b3f48f1d95db1a4f5529b4d41"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--device", choices=["cpu", "cuda"], default="cpu")
    parser.add_argument("--batch", type=int, default=128)
    args = parser.parse_args()
    with args.input.open(encoding="utf-8") as handle:
        rows = [json.loads(line) for line in handle if line.strip()]
    path = snapshot_download(REPO, revision=REVISION)
    tokenizer = AutoTokenizer.from_pretrained(path)
    model = AutoModel.from_pretrained(path).to(args.device).eval()
    vectors = []
    for index in range(0, len(rows), args.batch):
        chunk = [r["text"] for r in rows[index:index + args.batch]]
        batch = tokenizer(chunk, padding=True, truncation=True, max_length=256, return_tensors="pt").to(args.device)
        with torch.no_grad():
            hidden = model(**batch).last_hidden_state
        mask = batch["attention_mask"].unsqueeze(-1).to(hidden.dtype)
        pooled = (hidden * mask).sum(1) / mask.sum(1).clamp(min=1e-9)
        vectors.append(torch.nn.functional.normalize(pooled, dim=1).cpu().numpy())
    matrix = np.concatenate(vectors) if vectors else np.zeros((0, 384), dtype=np.float32)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    np.save(str(args.output) + ".npy", matrix.astype(np.float32))
    Path(str(args.output) + ".ids.json").write_text(json.dumps({"model": REPO, "revision": REVISION,
                                                                 "ids": [r["id"] for r in rows]}))
    print(json.dumps({"rows": len(rows), "dim": int(matrix.shape[1]), "model": REPO}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
