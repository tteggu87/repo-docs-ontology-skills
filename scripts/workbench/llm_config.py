#!/usr/bin/env python3
"""Backend-only helper-model config loading and normalized chat calls."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from urllib import error, request

SUPPORTED_CHAT_PROVIDERS = {"openai"}
HELPER_CONFIG_FILENAME = "wikiconfig.json"


def continue_config_path(root: Path) -> Path:
    return root / HELPER_CONFIG_FILENAME


def _require_mapping(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be an object")
    return value


def _normalize_provider(value: Any, label: str) -> dict[str, str] | None:
    if value is None:
        return None
    data = _require_mapping(value, label)
    provider = str(data.get("provider") or "").strip()
    model = str(data.get("model") or "").strip()
    api_key = str(data.get("apiKey") or "").strip()
    api_base = str(data.get("apiBase") or "").strip()
    if not provider or not model or not api_key or not api_base:
        raise ValueError(f"{label} must include provider, model, apiKey, and apiBase")
    if provider not in SUPPORTED_CHAT_PROVIDERS:
        supported = ", ".join(sorted(SUPPORTED_CHAT_PROVIDERS))
        raise ValueError(f"{label} provider must be one of: {supported}")
    normalized = {
        "provider": provider,
        "model": model,
        "api_key": api_key,
        "api_base": api_base.rstrip("/"),
    }
    title = str(data.get("title") or "").strip()
    if title:
        normalized["title"] = title
    return normalized


def _load_llm_wiki_enabled(raw: dict[str, Any]) -> bool:
    llm_wiki = raw.get("llmWiki")
    if llm_wiki is None:
        return True
    data = _require_mapping(llm_wiki, "llmWiki")
    enabled = data.get("enabled", True)
    if not isinstance(enabled, bool):
        raise ValueError("llmWiki.enabled must be a boolean")
    return enabled


def load_continue_helper_config(root: Path) -> dict[str, Any] | None:
    path = continue_config_path(root)
    if not path.exists():
        return None
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"{HELPER_CONFIG_FILENAME} is not valid JSON") from exc
    if not isinstance(raw, dict):
        raise ValueError(f"{HELPER_CONFIG_FILENAME} must contain a top-level object")
    enabled = _load_llm_wiki_enabled(raw)
    if not enabled:
        return {
            "source_path": str(path.relative_to(root)),
            "enabled": False,
            "chat_model": None,
            "embeddings_provider": None,
            "reranker_provider": None,
        }

    models = raw.get("models")
    if not isinstance(models, list) or not models:
        raise ValueError(f"{HELPER_CONFIG_FILENAME} must contain a non-empty models list")

    chat_model = _normalize_provider(models[0], "models[0]")
    if chat_model is None:
        raise ValueError("models[0] is required")

    return {
        "source_path": str(path.relative_to(root)),
        "enabled": True,
        "chat_model": chat_model,
        "embeddings_provider": _normalize_provider(raw.get("embeddingsProvider"), "embeddingsProvider"),
        "reranker_provider": _normalize_provider(raw.get("rerankerProvider"), "rerankerProvider"),
    }


def helper_model_public_summary(config: dict[str, Any]) -> dict[str, Any]:
    if not config.get("enabled", True):
        return {
            "config_source": config["source_path"],
            "enabled": False,
        }
    chat_model = config["chat_model"]
    return {
        "config_source": config["source_path"],
        "enabled": True,
        "model_title": chat_model.get("title") or chat_model["model"],
        "provider": chat_model["provider"],
    }


def _chat_completions_url(api_base: str) -> str:
    return f"{api_base.rstrip('/')}/chat/completions"


def run_helper_chat_completion(
    config: dict[str, Any],
    *,
    system_prompt: str,
    user_prompt: str,
    temperature: float = 0.2,
) -> str:
    if not config.get("enabled", True):
        raise ValueError(f"helper model is disabled in {HELPER_CONFIG_FILENAME}")
    chat_model = config["chat_model"]
    payload = json.dumps(
        {
            "model": chat_model["model"],
            "temperature": temperature,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }
    ).encode("utf-8")
    req = request.Request(
        _chat_completions_url(chat_model["api_base"]),
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {chat_model['api_key']}",
        },
        method="POST",
    )
    try:
        with request.urlopen(req, timeout=45) as response:
            raw = json.loads(response.read().decode("utf-8"))
    except error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace").strip()
        detail = f": {body[:240]}" if body else ""
        raise ValueError(f"helper model request failed with HTTP {exc.code}{detail}") from exc
    except error.URLError as exc:
        raise ValueError(f"helper model request failed: {exc.reason}") from exc

    choices = raw.get("choices")
    if not isinstance(choices, list) or not choices:
        raise ValueError("helper model response did not include choices")
    message = choices[0].get("message") if isinstance(choices[0], dict) else None
    if not isinstance(message, dict):
        raise ValueError("helper model response did not include a message")
    content = message.get("content")
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        text_parts = [
            str(item.get("text") or "").strip()
            for item in content
            if isinstance(item, dict) and item.get("type") == "text"
        ]
        joined = "\n".join(part for part in text_parts if part)
        if joined:
            return joined.strip()
    raise ValueError("helper model response did not include text content")
