import json

import httpx
import pytest

from scientific_network.rag.llm import InvalidJSONError, LLMClient, LLMConfig, LLMError, validate_schema

SCHEMA = {"type": "object", "properties": {"keep": {"type": "boolean"}, "label": {"type": "string", "enum": ["Method", "Task"]}},
          "required": ["keep", "label"]}


def fake(replies, seen=None):
    queue = list(replies)

    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        if seen is not None:
            seen.append(body)
        content = queue.pop(0)
        return httpx.Response(200, json={"choices": [{"message": {"content": content}, "finish_reason": "stop"}],
                                         "usage": {"prompt_tokens": 11, "completion_tokens": 5}})
    return httpx.MockTransport(handler)


def make(tmp_path, replies, seen=None):
    config = LLMConfig(base_url="http://fake/v1", model="m", revision="r1", cache_dir=tmp_path / "cache",
                       log_path=tmp_path / "calls.jsonl")
    return LLMClient(config, transport=fake(replies, seen))


def test_schema_constrained_request_and_defaults(tmp_path):
    seen = []
    client = make(tmp_path, ['{"keep": true, "label": "Method"}'], seen)
    result = client.complete(prompt_version="p1", system="s", user="u", schema=SCHEMA)
    assert result.parsed == {"keep": True, "label": "Method"}
    body = seen[0]
    assert body["temperature"] == 0.0 and "seed" in body
    assert body["chat_template_kwargs"] == {"enable_thinking": False}
    assert body["response_format"]["type"] == "json_schema"


def test_retry_once_on_invalid_json_then_success(tmp_path):
    seen = []
    client = make(tmp_path, ["not json", '{"keep": false, "label": "Task"}'], seen)
    result = client.complete(prompt_version="p1", system="s", user="u", schema=SCHEMA)
    assert result.attempts == 2 and result.parsed["label"] == "Task"
    assert len(seen) == 2 and seen[1]["messages"][-1]["role"] == "user"
    assert result.prompt_tokens == 22


def test_two_failures_raise_and_are_logged(tmp_path):
    client = make(tmp_path, ["nope", '{"keep": "yes", "label": "Method"}'])
    with pytest.raises(InvalidJSONError):
        client.complete(prompt_version="p1", system="s", user="u", schema=SCHEMA)
    log = [json.loads(line) for line in (tmp_path / "calls.jsonl").read_text().splitlines()]
    assert log[-1]["error"] and log[-1]["attempts"] == 2


def test_cache_key_covers_model_revision_prompt_and_input(tmp_path):
    client = make(tmp_path, ['{"keep": true, "label": "Method"}'])
    first = client.complete(prompt_version="p1", system="s", user="u", schema=SCHEMA)
    again = client.complete(prompt_version="p1", system="s", user="u", schema=SCHEMA)  # no reply left: must be a cache hit
    assert not first.cache_hit and again.cache_hit and again.parsed == first.parsed
    with pytest.raises(IndexError):
        client.complete(prompt_version="p2", system="s", user="u", schema=SCHEMA)
    with pytest.raises(IndexError):
        client.complete(prompt_version="p1", system="s", user="other", schema=SCHEMA)
    other_revision = LLMClient(LLMConfig(base_url="http://fake/v1", model="m", revision="r2", cache_dir=tmp_path / "cache"),
                               transport=fake(['{"keep": false, "label": "Task"}']))
    assert other_revision.complete(prompt_version="p1", system="s", user="u", schema=SCHEMA).parsed["keep"] is False
    log = [json.loads(line) for line in (tmp_path / "calls.jsonl").read_text().splitlines()]
    assert [row["cache_hit"] for row in log] == [False, True]
    assert {"model", "provider", "prompt_version", "input_sha256", "output_sha256", "prompt_tokens", "completion_tokens"} <= set(log[0])


def test_http_error_raises(tmp_path):
    client = LLMClient(LLMConfig(base_url="http://fake/v1", model="m"),
                       transport=httpx.MockTransport(lambda request: httpx.Response(400, text="too long")))
    with pytest.raises(LLMError, match="HTTP 400"):
        client.complete(prompt_version="p", system="s", user="u")


def test_missing_api_key_env(monkeypatch):
    monkeypatch.delenv("FAKE_KEY", raising=False)
    with pytest.raises(LLMError, match="FAKE_KEY"):
        LLMClient(LLMConfig(base_url="http://x/v1", model="m", api_key_env="FAKE_KEY"))


def test_validate_schema_subset():
    assert validate_schema({"a": [1, 2]}, {"type": "object", "properties": {"a": {"type": "array", "items": {"type": "integer"}, "maxItems": 2}}}) == []
    assert validate_schema({"a": [1, True]}, {"type": "object", "properties": {"a": {"type": "array", "items": {"type": "integer"}}}})
    assert validate_schema(True, {"type": "integer"})
