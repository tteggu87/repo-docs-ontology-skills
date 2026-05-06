#!/usr/bin/env python3
"""Repo-local configured LLM client for DocTology.

This module reads `wikiconfig.json`, normalizes OpenAI-compatible chat /
embedding / reranker model settings, exposes small probe commands, and provides
bounded API helpers for higher-level ingest workflows.

It does not make semantic decisions and does not write wiki or warehouse files.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable
from urllib import error as urlerror
from urllib import request as urlrequest

try:  # Prefer httpx when available; keep urllib fallback for minimal vaults.
    import httpx  # type: ignore[import-untyped]
except Exception:  # pragma: no cover - fallback path is intentionally supported
    httpx = None  # type: ignore[assignment]


HELPER_CONFIG_FILENAME = "wikiconfig.json"
SUPPORTED_PROVIDERS = {"openai"}
PLACEHOLDER_PREFIXES = ("YOUR_", "REPLACE_", "PASTE_")
PLACEHOLDER_SUFFIXES = ("_IF_ANY", "_HERE")


@dataclass(frozen=True)
class ModelConfig:
    provider: str
    model: str
    api_key: str
    api_base: str
    title: str | None = None

    def public_dict(self) -> dict[str, Any]:
        return {
            "provider": self.provider,
            "model": self.model,
            "api_base": self.api_base,
            "title": self.title,
            "api_key": "set" if self.api_key else "missing",
        }


@dataclass(frozen=True)
class HelperLLMConfig:
    source_path: str
    enabled: bool
    chat_model: ModelConfig | None
    embeddings_provider: ModelConfig | None
    reranker_provider: ModelConfig | None
    warnings: tuple[str, ...]

    def public_dict(self) -> dict[str, Any]:
        return {
            "source_path": self.source_path,
            "enabled": self.enabled,
            "chat_model": self.chat_model.public_dict() if self.chat_model else None,
            "embeddings_provider": self.embeddings_provider.public_dict() if self.embeddings_provider else None,
            "reranker_provider": self.reranker_provider.public_dict() if self.reranker_provider else None,
            "warnings": list(self.warnings),
        }


def _is_placeholder(value: str) -> bool:
    text = value.strip()
    if not text:
        return True
    upper = text.upper()
    return (
        any(upper.startswith(prefix) for prefix in PLACEHOLDER_PREFIXES)
        or any(upper.endswith(suffix) for suffix in PLACEHOLDER_SUFFIXES)
        or "YOUR_API_KEY" in upper
        or "YOUR_" in upper
    )


def _clean_setting(value: Any) -> str:
    text = str(value or "").strip()
    return "" if _is_placeholder(text) else text


def _require_mapping(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be an object")
    return value


def _display_path(root: Path, path: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def _normalize_provider(
    value: Any,
    label: str,
    *,
    required: bool,
    warnings: list[str],
) -> ModelConfig | None:
    if value is None:
        if required:
            raise ValueError(f"{label} is required")
        warnings.append(f"{label} is not configured")
        return None

    data = _require_mapping(value, label)
    provider = _clean_setting(data.get("provider"))
    model = _clean_setting(data.get("model"))
    api_key = _clean_setting(data.get("apiKey"))
    api_base = _clean_setting(data.get("apiBase"))
    title = _clean_setting(data.get("title")) or None

    missing = [
        name
        for name, actual in (
            ("provider", provider),
            ("model", model),
            ("apiKey", api_key),
            ("apiBase", api_base),
        )
        if not actual
    ]
    if missing:
        message = f"{label} missing required field(s): {', '.join(missing)}"
        if required:
            raise ValueError(message)
        warnings.append(message)
        return None

    if provider not in SUPPORTED_PROVIDERS:
        supported = ", ".join(sorted(SUPPORTED_PROVIDERS))
        message = f"{label} provider must be one of: {supported}"
        if required:
            raise ValueError(message)
        warnings.append(message)
        return None

    return ModelConfig(
        provider=provider,
        model=model,
        api_key=api_key,
        api_base=api_base.rstrip("/"),
        title=title,
    )


def find_repo_root(start: Path | None = None) -> Path:
    """Find a likely DocTology repo root without crawling above repo markers."""
    start_path = (start or Path.cwd()).resolve()
    if start_path.is_file():
        start_path = start_path.parent
    for candidate in [start_path, *start_path.parents]:
        if (
            (candidate / "AGENTS.md").exists()
            or (candidate / HELPER_CONFIG_FILENAME).exists()
            or (candidate / "scripts" / "llm_wiki.py").exists()
        ):
            return candidate
    return start_path


def config_path_for_root(root: Path, explicit_config: str | None = None) -> Path:
    if explicit_config:
        path = Path(explicit_config).expanduser().resolve()
        if not path.exists():
            raise FileNotFoundError(f"Helper config not found: {path}")
        return path
    return root / HELPER_CONFIG_FILENAME


def load_helper_config(root: Path, explicit_config: str | None = None) -> HelperLLMConfig:
    root = root.resolve()
    path = config_path_for_root(root, explicit_config)
    source_path = _display_path(root, path)
    if not path.exists():
        return HelperLLMConfig(
            source_path=source_path,
            enabled=False,
            chat_model=None,
            embeddings_provider=None,
            reranker_provider=None,
            warnings=(f"{HELPER_CONFIG_FILENAME} was not found",),
        )

    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"{path.name} is not valid JSON: {exc}") from exc

    if not isinstance(raw, dict):
        raise ValueError(f"{path.name} must contain a top-level object")

    enabled = True
    llm_wiki = raw.get("llmWiki")
    if llm_wiki is not None:
        llm_wiki_data = _require_mapping(llm_wiki, "llmWiki")
        enabled_value = llm_wiki_data.get("enabled", True)
        if not isinstance(enabled_value, bool):
            raise ValueError("llmWiki.enabled must be a boolean")
        enabled = enabled_value

    if not enabled:
        return HelperLLMConfig(
            source_path=source_path,
            enabled=False,
            chat_model=None,
            embeddings_provider=None,
            reranker_provider=None,
            warnings=("llmWiki.enabled is false",),
        )

    warnings: list[str] = []
    models = raw.get("models")
    if not isinstance(models, list) or not models:
        raise ValueError(f"{path.name} must contain a non-empty models list")

    chat_model = _normalize_provider(models[0], "models[0]", required=True, warnings=warnings)
    embeddings_provider = _normalize_provider(
        raw.get("embeddingsProvider"),
        "embeddingsProvider",
        required=False,
        warnings=warnings,
    )
    reranker_provider = _normalize_provider(
        raw.get("rerankerProvider"),
        "rerankerProvider",
        required=False,
        warnings=warnings,
    )

    return HelperLLMConfig(
        source_path=source_path,
        enabled=True,
        chat_model=chat_model,
        embeddings_provider=embeddings_provider,
        reranker_provider=reranker_provider,
        warnings=tuple(warnings),
    )


def endpoint(api_base: str, suffix: str) -> str:
    """Join an OpenAI-compatible base URL and suffix without duplicating it."""
    base = api_base.rstrip("/")
    normalized_suffix = suffix.strip("/")
    if base.endswith(normalized_suffix):
        return base
    return f"{base}/{normalized_suffix}"


def _mask_secret(value: str) -> str:
    if not value:
        return "missing"
    if len(value) <= 8:
        return "***"
    return value[:3] + "..." + value[-4:]


def _is_retryable_http_status(status_code: int) -> bool:
    return status_code == 429 or 500 <= status_code < 600


def _http_post_json(
    url: str,
    payload: dict[str, Any],
    api_key: str,
    *,
    timeout: float = 60.0,
    retries: int = 3,
    backoff_seconds: float = 2.0,
) -> dict[str, Any]:
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    last_error: Exception | None = None
    for attempt in range(retries + 1):
        try:
            if httpx is not None:
                with httpx.Client(timeout=timeout) as client:  # type: ignore[union-attr]
                    response = client.post(url, json=payload, headers=headers)
                if _is_retryable_http_status(response.status_code) and attempt < retries:
                    time.sleep(backoff_seconds * (2**attempt))
                    continue
                if response.status_code >= 400:
                    body = response.text[:500]
                    raise RuntimeError(f"HTTP {response.status_code}: {body}")
                data = response.json()
            else:
                encoded = json.dumps(payload).encode("utf-8")
                req = urlrequest.Request(url, data=encoded, headers=headers, method="POST")
                with urlrequest.urlopen(req, timeout=timeout) as response:
                    data = json.loads(response.read().decode("utf-8"))
            if not isinstance(data, dict):
                raise RuntimeError("Response JSON was not an object")
            return data
        except urlerror.HTTPError as exc:  # urllib fallback
            body = exc.read().decode("utf-8", errors="replace")[:500]
            last_error = RuntimeError(f"HTTP {exc.code}: {body}")
            if _is_retryable_http_status(exc.code) and attempt < retries:
                time.sleep(backoff_seconds * (2**attempt))
                continue
            break
        except Exception as exc:
            last_error = exc
            if attempt < retries:
                time.sleep(backoff_seconds * (2**attempt))
                continue

    safe_url = url.replace(api_key, _mask_secret(api_key))
    raise RuntimeError(f"Helper LLM request failed for {safe_url}: {last_error}") from last_error


def chat_completion(
    config: HelperLLMConfig,
    *,
    system_prompt: str,
    user_prompt: str,
    temperature: float = 0.2,
    max_tokens: int | None = None,
    timeout: float = 60.0,
) -> str:
    if not config.enabled:
        raise ValueError("configured LLM is disabled")
    if config.chat_model is None:
        raise ValueError("chat model is not configured")

    model = config.chat_model
    payload: dict[str, Any] = {
        "model": model.model,
        "temperature": temperature,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    }
    if max_tokens is not None:
        payload["max_tokens"] = max_tokens

    raw = _http_post_json(
        endpoint(model.api_base, "chat/completions"),
        payload,
        model.api_key,
        timeout=timeout,
    )

    choices = raw.get("choices")
    if not isinstance(choices, list) or not choices:
        raise RuntimeError("configured LLM response did not include choices")
    first = choices[0]
    if not isinstance(first, dict):
        raise RuntimeError("configured LLM choice was not an object")
    message = first.get("message")
    if not isinstance(message, dict):
        raise RuntimeError("configured LLM response did not include a message")

    content = message.get("content")
    if isinstance(content, str) and content.strip():
        return content.strip()
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, dict):
                if item.get("type") == "text":
                    parts.append(str(item.get("text") or "").strip())
                elif "text" in item:
                    parts.append(str(item.get("text") or "").strip())
        joined = "\n".join(part for part in parts if part)
        if joined:
            return joined.strip()
    raise RuntimeError("configured LLM response did not include text content")


def embed_texts(
    config: HelperLLMConfig,
    texts: str | Iterable[str],
    *,
    timeout: float = 60.0,
) -> list[list[float]]:
    if not config.enabled:
        raise ValueError("configured LLM is disabled")
    if config.embeddings_provider is None:
        raise ValueError("embeddingsProvider is not configured")

    text_list = [texts] if isinstance(texts, str) else list(texts)
    model = config.embeddings_provider
    raw = _http_post_json(
        endpoint(model.api_base, "embeddings"),
        {"model": model.model, "input": text_list},
        model.api_key,
        timeout=timeout,
    )

    data = raw.get("data")
    if not isinstance(data, list):
        raise RuntimeError("embedding response did not include data list")
    if data and all(isinstance(item, dict) and "index" in item for item in data):
        data = sorted(data, key=lambda item: int(item["index"]))

    vectors: list[list[float]] = []
    for item in data:
        if not isinstance(item, dict) or not isinstance(item.get("embedding"), list):
            raise RuntimeError("embedding response item did not include embedding list")
        vectors.append([float(value) for value in item["embedding"]])
    if len(vectors) != len(text_list):
        raise RuntimeError(f"embedding count mismatch: expected {len(text_list)}, got {len(vectors)}")
    return vectors


def rerank(
    config: HelperLLMConfig,
    *,
    query: str,
    documents: list[str],
    timeout: float = 60.0,
) -> list[dict[str, Any]]:
    if not config.enabled:
        raise ValueError("configured LLM is disabled")
    if config.reranker_provider is None:
        raise ValueError("rerankerProvider is not configured")

    model = config.reranker_provider
    raw = _http_post_json(
        endpoint(model.api_base, "rerank"),
        {"model": model.model, "query": query, "documents": documents},
        model.api_key,
        timeout=timeout,
    )
    results = raw.get("results")
    if isinstance(results, list):
        return [item for item in results if isinstance(item, dict)]
    data = raw.get("data")
    if isinstance(data, list):
        return [item for item in data if isinstance(item, dict)]
    raise RuntimeError("reranker response did not include results or data list")


def _probe_chat(config: HelperLLMConfig) -> dict[str, Any]:
    text = chat_completion(
        config,
        system_prompt="You are a configuration probe. Return exactly OK.",
        user_prompt="Return exactly OK.",
        temperature=0,
        max_tokens=16,
        timeout=45,
    )
    return {"ok": text.strip().upper().startswith("OK"), "response": text[:80]}


def _probe_embedding(config: HelperLLMConfig) -> dict[str, Any]:
    vectors = embed_texts(config, ["DocTology helper embedding probe"], timeout=45)
    dimension = len(vectors[0]) if vectors else 0
    return {"ok": bool(vectors and dimension > 0), "dimension": dimension}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="DocTology configured LLM config loader and probe.")
    parser.add_argument("--root", default=".", help="DocTology repo root. Defaults to current directory.")
    parser.add_argument("--config", help="Optional explicit wikiconfig.json path.")
    parser.add_argument("--check-config", action="store_true", help="Validate config without making API calls.")
    parser.add_argument("--probe-chat", action="store_true", help="Call chat/completions with a tiny probe prompt.")
    parser.add_argument("--probe-embedding", action="store_true", help="Call embeddings with a tiny probe input.")
    parser.add_argument("--json", action="store_true", help="Print JSON output. Default output is JSON.")
    args = parser.parse_args(argv)

    root = find_repo_root(Path(args.root))
    try:
        config = load_helper_config(root, args.config)
        result: dict[str, Any] = {
            "root": str(root),
            "config": config.public_dict(),
        }

        if args.probe_chat:
            result["chat_probe"] = _probe_chat(config)
        if args.probe_embedding:
            result["embedding_probe"] = _probe_embedding(config)

        print(json.dumps(result, ensure_ascii=False, indent=2))

        if args.check_config and (not config.enabled or config.chat_model is None):
            return 1
        if (args.probe_chat or args.probe_embedding) and (not config.enabled or config.chat_model is None):
            return 1
        return 0
    except Exception as exc:
        payload = {
            "root": str(root),
            "error": str(exc),
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
