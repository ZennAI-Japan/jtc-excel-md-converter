from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Protocol
from urllib.parse import urlsplit, urlunsplit

from .ai_config import AIConfig


@dataclass(frozen=True)
class AIResponse:
    content: str
    provider: str
    warnings: list[str]


@dataclass(frozen=True, repr=False)
class AIRequest:
    method: str
    url: str
    headers: dict[str, str]
    body: str

    def __repr__(self) -> str:
        safe_headers = {
            key: "<redacted>" if key.lower() == "authorization" else value for key, value in self.headers.items()
        }
        return f"AIRequest(method={self.method!r}, url={self.url!r}, headers={safe_headers!r}, body=<json>)"


class AIProvider(Protocol):
    name: str

    def rewrite_specification(self, prompt: str) -> AIResponse:
        """Return a reviewable AI-assisted rewrite suggestion for a deterministic spec."""
        ...


HTTPPost = Callable[[AIRequest], dict[str, Any]]


class DisabledAIProvider:
    name = "disabled"

    def rewrite_specification(self, prompt: str) -> AIResponse:
        return AIResponse(
            content="",
            provider=self.name,
            warnings=["AI provider is disabled; deterministic output was preserved."],
        )


class OpenAICompatibleProvider:
    name = "openai-compatible"

    def __init__(self, config: AIConfig, *, http_post: HTTPPost | None = None) -> None:
        self._config = config
        self._http_post = http_post

    def build_rewrite_request(self, prompt: str) -> AIRequest:
        base_url = self._resolve_base_url()
        url = _join_chat_completions_url(base_url)
        headers = {"Content-Type": "application/json"}
        if self._config.api_key:
            headers["Authorization"] = f"Bearer {self._config.api_key}"
        body = json.dumps(
            {
                "model": self._config.model or "local-model",
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "Rewrite the provided deterministic spreadsheet-derived specification into clearer "
                            "Markdown. Preserve facts, coordinates, warnings, and uncertainty. Do not invent "
                            "requirements."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.2,
            },
            ensure_ascii=False,
        )
        return AIRequest(method="POST", url=url, headers=headers, body=body)

    def _resolve_base_url(self) -> str:
        if self._config.base_url is None:
            return "http://127.0.0.1:11434/v1"
        base_url = _safe_base_url(self._config.base_url)
        if base_url is None:
            raise ValueError("Invalid AI base URL")
        return base_url

    def rewrite_specification(self, prompt: str) -> AIResponse:
        try:
            request = self.build_rewrite_request(prompt)
        except ValueError:
            return AIResponse(
                content="",
                provider=self.name,
                warnings=["Invalid AI base URL; no external request was sent."],
            )
        if self._http_post is None:
            return AIResponse(
                content="",
                provider=self.name,
                warnings=["AI HTTP transport is not configured; no external request was sent."],
            )
        payload = self._http_post(request)
        content = _extract_openai_compatible_content(payload)
        warnings = payload.get("warnings") if isinstance(payload, dict) else None
        return AIResponse(
            content=content,
            provider=self.name,
            warnings=[str(item) for item in warnings] if isinstance(warnings, list) else [],
        )


def build_ai_provider(config: AIConfig, *, http_post: HTTPPost | None = None) -> AIProvider:
    if not config.enabled:
        return DisabledAIProvider()
    if config.provider in {"openai-compatible", "ollama", "lmstudio", "local"}:
        provider_config = config if config.provider == "openai-compatible" else _as_openai_compatible(config)
        return OpenAICompatibleProvider(provider_config, http_post=http_post)
    return DisabledAIProvider()


def _as_openai_compatible(config: AIConfig) -> AIConfig:
    return AIConfig(
        enabled=config.enabled,
        provider="openai-compatible",
        api_key=config.api_key,
        base_url=config.base_url,
        model=config.model,
    )


def _extract_openai_compatible_content(payload: dict[str, Any]) -> str:
    choices = payload.get("choices")
    if not isinstance(choices, list) or not choices:
        return ""
    first = choices[0]
    if not isinstance(first, dict):
        return ""
    message = first.get("message")
    if isinstance(message, dict) and isinstance(message.get("content"), str):
        return message["content"]
    if isinstance(first.get("text"), str):
        return first["text"]
    return ""


def _join_chat_completions_url(base_url: str) -> str:
    base = base_url.rstrip("/")
    if base.endswith("/chat/completions"):
        return base
    return f"{base}/chat/completions"


def _safe_base_url(base_url: str | None) -> str | None:
    if not base_url:
        return None
    candidate = base_url.strip()
    if candidate.startswith("//"):
        candidate = f"https:{candidate}"
    elif "://" not in candidate and not candidate.startswith("/"):
        candidate = f"http://{candidate}"
    try:
        parsed = urlsplit(candidate)
    except ValueError:
        return None
    if parsed.scheme not in {"http", "https"}:
        return None
    if not parsed.hostname:
        return None
    hostname = parsed.hostname
    if ":" in hostname and not hostname.startswith("["):
        hostname = f"[{hostname}]"
    try:
        port = parsed.port
    except ValueError:
        return None
    netloc = hostname if port is None else f"{hostname}:{port}"
    return urlunsplit((parsed.scheme, netloc, parsed.path, "", ""))
