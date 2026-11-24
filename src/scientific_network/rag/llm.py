"""OpenAI-compatible chat client with schema-constrained JSON, a disk cache and a call log.

Specification §6.1: one base URL and model name from config, so switching between
the local llama.cpp server and a hosted endpoint changes no code. Every call is cached
on (model, revision, prompt version, input hash) and logged with model, provider,
prompt version, token counts and hashes. Invalid JSON is retried once, then raised.
No API key is read from the repository; the key comes from an environment variable.
"""

from dataclasses import dataclass, field
import hashlib
import json
import os
from pathlib import Path
import time

import httpx


class LLMError(RuntimeError):
    pass


class InvalidJSONError(LLMError):
    def __init__(self, message: str, raw: str):
        super().__init__(message)
        self.raw = raw


@dataclass(frozen=True)
class LLMConfig:
    base_url: str
    model: str
    revision: str = "unknown"
    provider: str = "local-llama.cpp"
    api_key_env: str | None = None
    temperature: float = 0.0
    seed: int = 0
    max_tokens: int = 1024
    enable_thinking: bool = False
    timeout: float = 300.0
    cache_dir: Path | None = None
    log_path: Path | None = None
    extra_body: dict = field(default_factory=dict)

    @classmethod
    def from_mapping(cls, data: dict) -> "LLMConfig":
        values = dict(data)
        for key in ("cache_dir", "log_path"):
            if values.get(key) is not None:
                values[key] = Path(values[key])
        return cls(**values)


@dataclass
class LLMResult:
    content: str
    parsed: object | None
    prompt_tokens: int
    completion_tokens: int
    finish_reason: str | None
    cache_hit: bool
    attempts: int
    input_sha256: str
    output_sha256: str


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def canonical(value: object) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


_TYPES = {"object": dict, "array": list, "string": str, "boolean": bool, "null": type(None)}


def validate_schema(value: object, schema: dict, path: str = "$") -> list[str]:
    """Small JSON-Schema subset: type, enum, required, properties, items, min/maxItems, min/max."""
    errors: list[str] = []
    expected = schema.get("type")
    if expected is not None:
        names = expected if isinstance(expected, list) else [expected]
        ok = False
        for name in names:
            if name == "integer":
                ok = ok or (isinstance(value, int) and not isinstance(value, bool))
            elif name == "number":
                ok = ok or (isinstance(value, (int, float)) and not isinstance(value, bool))
            else:
                ok = ok or (isinstance(value, _TYPES[name]) and not (name != "boolean" and isinstance(value, bool)))
        if not ok:
            return [f"{path}: expected {expected}, got {type(value).__name__}"]
    if "enum" in schema and value not in schema["enum"]:
        errors.append(f"{path}: {value!r} not in enum")
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if "minimum" in schema and value < schema["minimum"]:
            errors.append(f"{path}: below minimum")
        if "maximum" in schema and value > schema["maximum"]:
            errors.append(f"{path}: above maximum")
    if isinstance(value, dict):
        for key in schema.get("required", []):
            if key not in value:
                errors.append(f"{path}: missing required {key!r}")
        for key, sub in (schema.get("properties") or {}).items():
            if key in value:
                errors.extend(validate_schema(value[key], sub, f"{path}.{key}"))
    if isinstance(value, list):
        if "minItems" in schema and len(value) < schema["minItems"]:
            errors.append(f"{path}: fewer than {schema['minItems']} items")
        if "maxItems" in schema and len(value) > schema["maxItems"]:
            errors.append(f"{path}: more than {schema['maxItems']} items")
        if "items" in schema:
            for index, item in enumerate(value):
                errors.extend(validate_schema(item, schema["items"], f"{path}[{index}]"))
    return errors


class LLMClient:
    def __init__(self, config: LLMConfig, *, transport: httpx.BaseTransport | None = None):
        self.config = config
        headers = {"Content-Type": "application/json"}
        if config.api_key_env:
            key = os.environ.get(config.api_key_env)
            if not key:
                raise LLMError(f"environment variable {config.api_key_env} is not set")
            headers["Authorization"] = f"Bearer {key}"
        self._http = httpx.Client(base_url=config.base_url.rstrip("/"), headers=headers,
                                  timeout=config.timeout, transport=transport)

    def close(self) -> None:
        self._http.close()

    def __enter__(self) -> "LLMClient":
        return self

    def __exit__(self, *exc) -> None:
        self.close()

    # -- request construction -------------------------------------------------
    def _body(self, messages: list[dict], schema: dict | None, schema_name: str, max_tokens: int | None) -> dict:
        body = {
            "model": self.config.model, "messages": messages,
            "temperature": self.config.temperature, "seed": self.config.seed,
            "max_tokens": max_tokens or self.config.max_tokens,
            "chat_template_kwargs": {"enable_thinking": self.config.enable_thinking},
        }
        if schema is not None:
            body["response_format"] = {"type": "json_schema",
                                       "json_schema": {"name": schema_name, "strict": True, "schema": schema}}
        body.update(self.config.extra_body)
        return body

    def _cache_key(self, prompt_version: str, body: dict) -> tuple[str, str]:
        input_hash = sha256_text(canonical(body))
        key = sha256_text(canonical([self.config.model, self.config.revision, prompt_version, input_hash]))
        return key, input_hash

    def _cache_path(self, key: str) -> Path | None:
        if self.config.cache_dir is None:
            return None
        return self.config.cache_dir / key[:2] / f"{key}.json"

    def _log(self, record: dict) -> None:
        if self.config.log_path is None:
            return
        self.config.log_path.parent.mkdir(parents=True, exist_ok=True)
        with self.config.log_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, sort_keys=True, ensure_ascii=False) + "\n")

    def _post(self, body: dict) -> dict:
        try:
            response = self._http.post("/chat/completions", json=body)
        except httpx.HTTPError as exc:
            raise LLMError(f"request failed: {exc}") from exc
        if response.status_code != 200:
            raise LLMError(f"HTTP {response.status_code}: {response.text[:300]}")
        return response.json()

    # -- public API ------------------------------------------------------------
    def complete(self, *, prompt_version: str, system: str, user: str, schema: dict | None = None,
                 schema_name: str = "answer", max_tokens: int | None = None) -> LLMResult:
        """Return a completion. With ``schema`` the content is parsed and validated, retried once."""
        messages = [{"role": "system", "content": system}, {"role": "user", "content": user}]
        body = self._body(messages, schema, schema_name, max_tokens)
        key, input_hash = self._cache_key(prompt_version, body)
        cache_path = self._cache_path(key)
        if cache_path is not None and cache_path.exists():
            cached = json.loads(cache_path.read_text(encoding="utf-8"))
            result = LLMResult(**{**cached["result"], "cache_hit": True})
            self._log_call(prompt_version, result, 0.0, True, None)
            return result

        started = time.perf_counter()
        attempts = 0
        prompt_tokens = completion_tokens = 0
        error: str | None = None
        raw = ""
        finish = None
        parsed = None
        current = body
        while attempts < 2:
            attempts += 1
            payload = self._post(current)
            usage = payload.get("usage") or {}
            prompt_tokens += int(usage.get("prompt_tokens", 0))
            completion_tokens += int(usage.get("completion_tokens", 0))
            choice = (payload.get("choices") or [{}])[0]
            raw = (choice.get("message") or {}).get("content") or ""
            finish = choice.get("finish_reason")
            if schema is None:
                error = None
                break
            error = None
            try:
                parsed = json.loads(raw)
            except json.JSONDecodeError as exc:
                error = f"invalid JSON: {exc}"
            else:
                problems = validate_schema(parsed, schema)
                if problems:
                    error = "schema violation: " + "; ".join(problems[:3])
            if error is None:
                break
            correction = {"role": "user", "content": f"Your previous answer was rejected ({error}). "
                          "Reply again with only valid JSON that matches the required schema."}
            current = self._body(messages + [{"role": "assistant", "content": raw}, correction],
                                 schema, schema_name, max_tokens)
        elapsed = time.perf_counter() - started
        if error is not None:
            self._log_call(prompt_version, LLMResult(raw, None, prompt_tokens, completion_tokens, finish, False,
                                                     attempts, input_hash, sha256_text(raw)), elapsed, False, error)
            raise InvalidJSONError(error, raw)
        result = LLMResult(raw, parsed if schema is not None else None, prompt_tokens, completion_tokens, finish,
                           False, attempts, input_hash, sha256_text(raw))
        if cache_path is not None:
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            tmp = cache_path.with_suffix(".tmp")
            tmp.write_text(json.dumps({"key": key, "model": self.config.model, "revision": self.config.revision,
                                       "prompt_version": prompt_version,
                                       "result": {**result.__dict__, "cache_hit": False}},
                                      sort_keys=True, ensure_ascii=False), encoding="utf-8")
            tmp.replace(cache_path)
        self._log_call(prompt_version, result, elapsed, False, None)
        return result

    def _log_call(self, prompt_version: str, result: LLMResult, elapsed: float, cache_hit: bool, error: str | None) -> None:
        self._log({
            "logged_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            "model": self.config.model, "revision": self.config.revision, "provider": self.config.provider,
            "base_url": self.config.base_url, "prompt_version": prompt_version,
            "input_sha256": result.input_sha256, "output_sha256": result.output_sha256,
            "prompt_tokens": result.prompt_tokens, "completion_tokens": result.completion_tokens,
            "finish_reason": result.finish_reason, "attempts": result.attempts,
            "cache_hit": cache_hit, "latency_s": round(elapsed, 3), "error": error,
        })
