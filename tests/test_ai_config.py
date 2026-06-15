from __future__ import annotations

from pathlib import Path


def test_ai_config_defaults_to_deterministic_mode_without_keys():
    from jtc_excel_md.ai_config import load_ai_config

    config = load_ai_config(env={})

    assert config.enabled is False
    assert config.provider == "none"
    assert config.model is None
    assert config.base_url is None
    assert config.api_key is None
    assert config.safe_summary() == {
        "enabled": False,
        "provider": "none",
        "model": None,
        "base_url": None,
        "api_key": None,
    }


def test_ai_config_loads_generic_openai_compatible_environment():
    from jtc_excel_md.ai_config import load_ai_config

    config = load_ai_config(
        env={
            "JTC_AI_PROVIDER": "openai-compatible",
            "JTC_AI_API_KEY": "placeholder-key",
            "JTC_AI_BASE_URL": "http://127.0.0.1:11434/v1",
            "JTC_AI_MODEL": "qwen2.5-coder:7b",
        }
    )

    assert config.enabled is True
    assert config.provider == "openai-compatible"
    assert config.api_key == "placeholder-key"
    assert config.base_url == "http://127.0.0.1:11434/v1"
    assert config.model == "qwen2.5-coder:7b"
    assert config.safe_summary()["api_key"] == "pla...-key"
    assert "placeholder-key" not in repr(config)


def test_codex_provider_uses_openai_key_and_default_codex_model():
    from jtc_excel_md.ai_config import load_ai_config

    config = load_ai_config(
        env={
            "JTC_AI_PROVIDER": "codex",
            "OPENAI_API_KEY": "placeholder-openai-key",
        }
    )

    assert config.enabled is True
    assert config.provider == "codex"
    assert config.api_key == "placeholder-openai-key"
    assert config.base_url == "https://api.openai.com/v1"
    assert config.model == "codex-mini-latest"


def test_ai_config_supports_provider_specific_keys():
    from jtc_excel_md.ai_config import load_ai_config

    config = load_ai_config(
        env={
            "JTC_AI_PROVIDER": "anthropic",
            "ANTHROPIC_API_KEY": "placeholder-anthropic-key",
            "ANTHROPIC_MODEL": "claude-3-5-sonnet-latest",
        }
    )

    assert config.enabled is True
    assert config.provider == "anthropic"
    assert config.api_key == "placeholder-anthropic-key"
    assert config.model == "claude-3-5-sonnet-latest"


def test_ai_config_loads_env_file_without_overriding_process_env(tmp_path: Path):
    from jtc_excel_md.ai_config import load_ai_config

    env_file = tmp_path / ".env"
    env_file.write_text(
        "\n".join(
            [
                "JTC_AI_PROVIDER=openai-compatible",
                "JTC_AI_API_KEY=file-placeholder-key",
                "JTC_AI_BASE_URL=http://localhost:1234/v1",
                "JTC_AI_MODEL=file-model",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    config = load_ai_config(
        env={"JTC_AI_MODEL": "env-model"},
        env_file=env_file,
    )

    assert config.provider == "openai-compatible"
    assert config.api_key == "file-placeholder-key"
    assert config.base_url == "http://localhost:1234/v1"
    assert config.model == "env-model"


def test_local_provider_can_be_enabled_without_api_key():
    from jtc_excel_md.ai_config import load_ai_config

    config = load_ai_config(
        env={
            "JTC_AI_PROVIDER": "ollama",
            "JTC_AI_BASE_URL": "http://127.0.0.1:11434/v1",
            "JTC_AI_MODEL": "llama3.1",
        }
    )

    assert config.enabled is True
    assert config.provider == "ollama"
    assert config.api_key is None


def test_unknown_provider_is_not_enabled_even_with_generic_key():
    from jtc_excel_md.ai_config import load_ai_config

    config = load_ai_config(
        env={
            "JTC_AI_PROVIDER": "surprise-vendor",
            "JTC_AI_API_KEY": "placeholder-key",
            "JTC_AI_MODEL": "model",
        }
    )

    assert config.enabled is False
    assert config.provider == "surprise-vendor"
    assert config.api_key is None
    assert config.safe_summary()["api_key"] is None


def test_env_file_supports_export_prefix_and_inline_comments(tmp_path: Path):
    from jtc_excel_md.ai_config import load_ai_config

    env_file = tmp_path / ".env"
    env_file.write_text(
        "\n".join(
            [
                "export JTC_AI_PROVIDER=ollama # local runtime",
                "JTC_AI_MODEL='llama3.1' # quoted model",
            ]
        ),
        encoding="utf-8",
    )

    config = load_ai_config(env={}, env_file=env_file)

    assert config.enabled is True
    assert config.provider == "ollama"
    assert config.model == "llama3.1"
