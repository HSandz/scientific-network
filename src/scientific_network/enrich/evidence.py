"""Evaluator evidence manifest: SHA-256 of every archived file plus the session and model identifiers read from the logs."""

from __future__ import annotations

import argparse
import json
from hashlib import sha256
from pathlib import Path


def codex_sessions(directory: Path) -> list[dict]:
    """One row per Codex rollout log: session id, working directory (names the packet), model and provider as logged."""
    rows = []
    for path in sorted(directory.glob("rollout-*.jsonl")):
        row = {"file": path.name, "session_id": None, "packet": None, "models": set(), "providers": set(), "started": None}
        for line in path.read_text(encoding="utf-8").splitlines():
            record = json.loads(line)
            payload = record.get("payload") or {}
            if record.get("type") == "session_meta":
                row["session_id"] = payload.get("id")
                row["packet"] = Path(payload.get("cwd") or "").name or None
                row["started"] = payload.get("timestamp")
            if isinstance(payload, dict):
                if payload.get("model"):
                    row["models"].add(payload["model"])
                if payload.get("model_provider"):
                    row["providers"].add(payload["model_provider"])
        row["models"], row["providers"] = sorted(row["models"]), sorted(row["providers"])
        rows.append(row)
    return rows


def claude_subagents(directory: Path) -> list[dict]:
    rows = []
    for path in sorted(directory.glob("agent-*.jsonl")):
        models, stamps = set(), []
        for line in path.read_text(encoding="utf-8").splitlines():
            record = json.loads(line)
            if (record.get("message") or {}).get("model"):
                models.add(record["message"]["model"])
            if record.get("timestamp"):
                stamps.append(record["timestamp"])
        meta = json.loads(path.with_suffix(".meta.json").read_text())
        rows.append({"file": path.name, "agent_id": path.stem.removeprefix("agent-"), "description": meta.get("description"),
                     "requested_model": meta.get("model"), "models_logged": sorted(models),
                     "first_timestamp": min(stamps) if stamps else None, "last_timestamp": max(stamps) if stamps else None})
    return rows


def build_manifest(archive: Path, label: str) -> dict:
    files = {str(p.relative_to(archive)): sha256(p.read_bytes()).hexdigest() for p in sorted(archive.rglob("*")) if p.is_file()}
    manifest = {"label": label, "archive_dir": str(archive), "files_sha256": files, "file_count": len(files)}
    if (archive / "codex-sessions").is_dir():
        manifest["codex_sessions"] = codex_sessions(archive / "codex-sessions")
    if (archive / "claude-subagents").is_dir():
        manifest["claude_subagents"] = claude_subagents(archive / "claude-subagents")
    return manifest


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--archive", type=Path, required=True)
    ap.add_argument("--label", required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    manifest = build_manifest(args.archive, args.label)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(manifest, indent=1, ensure_ascii=False, sort_keys=True) + "\n")
    print(json.dumps({k: v for k, v in manifest.items() if k in ("label", "file_count")}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
