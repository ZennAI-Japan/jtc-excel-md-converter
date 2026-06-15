from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

PROVIDER_ENV_PREFIXES = {
    "openai": "OPENAI",
    "anthropic": "ANTHROPIC",
    "google": "GOOGLE",
    "gemini": "GOOGLE",
    "openai-compatible": "OPENAI_COMPATIBLE",
    "ollama": "OLLAMA",
    "lmstudio": "LMSTUDIO",
    "local": "LOCAL_AI",
}

PROVIDERS_WITH_OPTIONAL_KEYS = {"ollama", "lmstudio", "local"}


@dataclass(frozen=True, repr=False)
class AIConfig:
    enabled: bool
    provider: str
    api_key: str | None = None
    base_url: str | None = None
    model: str | None = None

    def __repr__(self) -> str:
        return (
            "AIConfig("
            f"enabled={self.enabled!r}, "
            f"provider={self.provider!r}, "
            f"api_key={_mask_secret(self.api_key)!r}, "
            f"base_url={self.base_url!r}, "
            f"model={self.model!r})"
        )

    def safe_summary(self) -> dict[str, str | bool | None]:
        return {
            "enabled": self.enabled,
            "provider": self.provider,
            "model": self.model,
            "base_url": self.base_url,
            "api_key": _mask_secret(self.api_key),
        }


def load_ai_config(
    *,
    env: Mapping[str, str] | None = None,
    env_file: str | Path | None = None,
) -> AIConfig:
    """Load optional AI provider configuration without importing any vendor SDK.

    The converter is deterministic by default. AI features become available only when
    the caller explicitly configures a provider through environment variables or a
    local `.env` style file. Process/env values win over file values.
    """
    merged_env = _load_env_file(Path(env_file)) if env_file else {}
    merged_env.update({key: value for key, value in (env or os.environ).items() if value is not None})

    provider = _clean(merged_env.get("JTC_AI_PROVIDER"))
    if not provider:
        return AIConfig(enabled=False, provider="none")
    provider = provider.lower()
    if provider not in PROVIDER_ENV_PREFIXES:
        return AIConfig(enabled=False, provider=provider)

    prefix = PROVIDER_ENV_PREFIXES.get(provider, provider.upper().replace("-", "_"))
    api_key = _first_non_empty(
        merged_env.get("JTC_AI_API_KEY"),
        merged_env.get(f"{prefix}_API_KEY"),
        merged_env.get(f"{prefix}_TOKEN"),
    )
    base_url = _first_non_empty(
        merged_env.get("JTC_AI_BASE_URL"),
        merged_env.get(f"{prefix}_BASE_URL"),
        _default_base_url(provider),
    )
    model = _first_non_empty(
        merged_env.get("JTC_AI_MODEL"),
        merged_env.get(f"{prefix}_MODEL"),
        _default_model(provider),
    )

    enabled = bool(api_key or provider in PROVIDERS_WITH_OPTIONAL_KEYS)
    return AIConfig(
        enabled=enabled,
        provider=provider,
        api_key=api_key,
        base_url=base_url,
        model=model,
    )


def _load_env_file(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if line.startswith("export "):
            line = line[len("export ") :].strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = _strip_inline_comment(value).strip().strip('"').strip("'")
        if key:
            values[key] = value
    return values


def _strip_inline_comment(value: str) -> str:
    quote: str | None = None
    for index, char in enumerate(value):
        if char in {"'", '"'}:
            quote = None if quote == char else char if quote is None else quote
        if char == "#" and quote is None:
            return value[:index]
    return value


def _first_non_empty(*values: str | None) -> str | None:
    for value in values:
        cleaned = _clean(value)
        if cleaned:
            return cleaned
    return None


def _clean(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = str(value).strip()
    return cleaned or None


def _default_base_url(provider: str) -> str | None:
    if provider in {"ollama", "lmstudio", "local"}:
        return "http://127.0.0.1:11434/v1"
    return None


def _default_model(provider: str) -> str | None:
    defaults = {
        "openai": "gpt-4o-mini",
        "anthropic": "claude-3-5-haiku-latest",
        "google": "gemini-1.5-flash",
        "gemini": "gemini-1.5-flash",
    }
    return defaults.get(provider)


def _mask_secret(value: str | None) -> str | None:
    if not value:
        return None
    if len(value) <= 8:
        return "***"
    return f"{value[:3]}...{value[-4:]}"
