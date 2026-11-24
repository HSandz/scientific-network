"""Smoke test for the local llama-server (ops/llm/compose.yaml).

Standard library only. Checks health, model listing, plain chat with thinking
off, JSON-schema constrained extraction, tool calling, a thinking-mode answer,
throughput and GPU memory. The input text is a synthetic example, not a corpus
paper, and the results are runtime checks, not quality measurements.

    python3 ops/llm/smoke_test.py --base-url http://127.0.0.1:8080 \
        --output reports/runs/<work-id>/smoke-test.json
"""

from __future__ import annotations

import argparse
import json
import subprocess
import time
import urllib.request
from pathlib import Path

SYNTHETIC_ABSTRACT = (
    "We propose GraphMix, a contrastive pre-training method for graph neural "
    "networks, and apply it to molecular property prediction. On the OGB-MolHIV "
    "and Tox21 benchmarks GraphMix improves ROC-AUC over GraphCL by 2.1 points."
)

EXTRACTION_SCHEMA = {
    "type": "object",
    "properties": {
        "methods": {"type": "array", "items": {"type": "string"}},
        "tasks": {"type": "array", "items": {"type": "string"}},
        "datasets": {"type": "array", "items": {"type": "string"}},
        "relations": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "head": {"type": "string"},
                    "predicate": {
                        "type": "string",
                        "enum": ["USES_METHOD", "ADDRESSES_TASK", "USES_DATASET",
                                 "APPLIED_TO", "EVALUATED_ON"],
                    },
                    "tail": {"type": "string"},
                },
                "required": ["head", "predicate", "tail"],
            },
        },
    },
    "required": ["methods", "tasks", "datasets", "relations"],
}

TOOLS = [{
    "type": "function",
    "function": {
        "name": "top_organizations_for_topic",
        "description": "Return the organizations with most papers on a topic in a year range.",
        "parameters": {
            "type": "object",
            "properties": {
                "topic": {"type": "string"},
                "start_year": {"type": "integer"},
                "end_year": {"type": "integer"},
                "limit": {"type": "integer"},
            },
            "required": ["topic", "start_year", "end_year"],
        },
    },
}]


def call(base: str, path: str, body: dict | None = None, timeout: float = 300) -> tuple[dict, float]:
    data = None if body is None else json.dumps(body).encode()
    req = urllib.request.Request(base + path, data=data,
                                 headers={"Content-Type": "application/json"})
    start = time.perf_counter()
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        payload = json.loads(resp.read())
    return payload, time.perf_counter() - start


def chat(base: str, model: str, messages: list, thinking: bool, **extra) -> tuple[dict, float]:
    body = {"model": model, "messages": messages, "temperature": 0, "seed": 42,
            "chat_template_kwargs": {"enable_thinking": thinking}, **extra}
    return call(base, "/v1/chat/completions", body)


def gpu_memory() -> dict:
    out = subprocess.run(
        ["nvidia-smi", "--query-gpu=name,memory.total,memory.used", "--format=csv,noheader,nounits"],
        capture_output=True, text=True, check=True).stdout.strip()
    name, total, used = [p.strip() for p in out.split(",")]
    return {"gpu": name, "total_mib": int(total), "used_mib": int(used)}


def speed(resp: dict) -> dict:
    t = resp.get("timings", {})
    return {"prompt_tokens": t.get("prompt_n"), "prompt_tok_per_s": t.get("prompt_per_second"),
            "gen_tokens": t.get("predicted_n"), "gen_tok_per_s": t.get("predicted_per_second")}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-url", default="http://127.0.0.1:8080")
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    base = args.base_url.rstrip("/")
    results: dict = {"base_url": base, "checks": {}}
    checks = results["checks"]
    ok = True

    health, _ = call(base, "/health")
    checks["health"] = {"pass": health.get("status") == "ok", "response": health}

    models, _ = call(base, "/v1/models")
    model = models["data"][0]["id"]
    results["model"] = model
    props, _ = call(base, "/props")
    results["server"] = {k: props.get(k) for k in ("build_info", "total_slots", "model_path")}
    results["server"]["n_ctx"] = props.get("default_generation_settings", {}).get("n_ctx")

    # 1. Plain answer, thinking off.
    r, dt = chat(base, model, [{"role": "user", "content": "Reply with exactly: ready"}],
                 thinking=False, max_tokens=16)
    text = r["choices"][0]["message"].get("content", "").strip()
    checks["plain_chat"] = {"pass": "ready" in text.lower(), "content": text,
                            "seconds": round(dt, 2), **speed(r)}

    # 2. Schema-constrained extraction.
    prompt = ("Extract the methods, tasks and datasets mentioned in this abstract, and "
              "the relations between them. Use the paper's exact names.\n\n" + SYNTHETIC_ABSTRACT)
    r, dt = chat(base, model, [{"role": "user", "content": prompt}], thinking=False,
                 max_tokens=512,
                 response_format={"type": "json_schema",
                                  "json_schema": {"name": "extraction", "schema": EXTRACTION_SCHEMA}})
    raw = r["choices"][0]["message"].get("content", "")
    try:
        parsed = json.loads(raw)
        valid = all(k in parsed for k in EXTRACTION_SCHEMA["required"])
    except json.JSONDecodeError:
        parsed, valid = None, False
    checks["json_schema_extraction"] = {"pass": valid, "parsed": parsed,
                                        "seconds": round(dt, 2), **speed(r)}

    # 3. Tool calling.
    r, dt = chat(base, model, [{"role": "user", "content":
                 "Which organizations published the most on graph neural networks from 2023 to 2025? Top 5."}],
                 thinking=False, max_tokens=256, tools=TOOLS)
    calls = r["choices"][0]["message"].get("tool_calls") or []
    first = calls[0]["function"] if calls else {}
    try:
        tool_args = json.loads(first.get("arguments", "{}")) if first else {}
    except json.JSONDecodeError:
        tool_args = {}
    checks["tool_call"] = {"pass": first.get("name") == "top_organizations_for_topic"
                           and tool_args.get("start_year") == 2023 and tool_args.get("end_year") == 2025,
                           "function": first.get("name"), "arguments": tool_args,
                           "seconds": round(dt, 2), **speed(r)}

    # 4. Thinking mode on (for multi-hop answers).
    r, dt = chat(base, model, [{"role": "user", "content":
                 "Paper P cites paper Q. Q was written by researcher R at organization O. "
                 "Which organization is two citation-and-authorship hops from P? Answer with the letter only."}],
                 thinking=True, max_tokens=8192)
    msg = r["choices"][0]["message"]
    answer = (msg.get("content") or "").strip()
    checks["thinking_mode"] = {"pass": answer.rstrip(".").endswith("O"), "content": answer,
                               "reasoning_chars": len(msg.get("reasoning_content") or ""),
                               "seconds": round(dt, 2), **speed(r)}

    results["gpu_after"] = gpu_memory()
    ok = all(c["pass"] for c in checks.values())
    results["all_pass"] = ok
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(results, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps(results, indent=2, ensure_ascii=False))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
