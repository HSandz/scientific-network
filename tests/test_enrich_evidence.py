import json

from scientific_network.enrich.evidence import build_manifest


def test_manifest_hashes_files_and_reads_session_models(tmp_path):
    (tmp_path / "codex-sessions").mkdir()
    (tmp_path / "codex-sessions" / "rollout-1.jsonl").write_text("\n".join(json.dumps(r) for r in [
        {"type": "session_meta", "payload": {"id": "s1", "cwd": "/x/B-2", "model_provider": "p", "timestamp": "t"}},
        {"type": "turn_context", "payload": {"model": "m1"}}]))
    (tmp_path / "claude-subagents").mkdir()
    (tmp_path / "claude-subagents" / "agent-a1.jsonl").write_text(json.dumps({"message": {"model": "c1"}, "timestamp": "2026"}))
    (tmp_path / "claude-subagents" / "agent-a1.meta.json").write_text(json.dumps({"description": "d", "model": "opus"}))
    manifest = build_manifest(tmp_path, "t")
    assert manifest["file_count"] == 3 and all(len(h) == 64 for h in manifest["files_sha256"].values())
    assert manifest["codex_sessions"][0]["packet"] == "B-2" and manifest["codex_sessions"][0]["models"] == ["m1"]
    assert manifest["claude_subagents"][0]["models_logged"] == ["c1"] and manifest["claude_subagents"][0]["agent_id"] == "a1"
