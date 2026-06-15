from __future__ import annotations

import json


def test_factory_returns_disabled_provider_for_deterministic_config():
    from jtc_excel_md.ai_config import AIConfig
    from jtc_excel_md.ai_providers import DisabledAIProvider, build_ai_provider

    provider = build_ai_provider(AIConfig(enabled=False, provider="none"))

    assert isinstance(provider, DisabledAIProvider)
    assert provider.name == "disabled"
    assert provider.rewrite_specification("# spec").content == ""
    assert provider.rewrite_specification("# spec").warnings == ["AI provider is disabled; deterministic output was preserved."]


def test_openai_compatible_provider_prepares_secret_safe_request_metadata():
    from jtc_excel_md.ai_config import AIConfig
    from jtc_excel_md.ai_providers import OpenAICompatibleProvider, build_ai_provider

    raw_api_key = "-".join(["provider", "secret", "key"])
    provider = build_ai_provider(
        AIConfig(
            enabled=True,
            provider="openai-compatible",
            api_key=raw_api_key,
            base_url="https://user:pass@example.com/v1?token=url-secret",
            model="local-model",
        )
    )

    assert isinstance(provider, OpenAICompatibleProvider)
    request = provider.build_rewrite_request("# Original spec")

    assert request.method == "POST"
    assert request.url == "https://example.com/v1/chat/completions"
    assert request.headers["Content-Type"] == "application/json"
    assert request.headers["Authorization"] == f"Bearer {raw_api_key}"
    assert "provider-secret-key" not in repr(request)
    assert "user:pass" not in request.url
    assert "url-secret" not in request.url
    payload = json.loads(request.body)
    assert payload["model"] == "local-model"
    assert payload["messages"][0]["role"] == "system"
    assert "Markdown" in payload["messages"][0]["content"]
    assert payload["messages"][1] == {"role": "user", "content": "# Original spec"}


def test_openai_compatible_provider_uses_injected_http_transport_without_sdk_or_real_network():
    from jtc_excel_md.ai_config import AIConfig
    from jtc_excel_md.ai_providers import build_ai_provider

    calls = []

    def fake_post(request):
        calls.append(request)
        return {
            "choices": [
                {
                    "message": {
                        "content": "# AI restructured spec\n\n- preserved business section",
                    }
                }
            ],
            "warnings": ["review before use"],
        }

    raw_api_key = "-".join(["local", "test", "key"])
    provider = build_ai_provider(
        AIConfig(
            enabled=True,
            provider="openai-compatible",
            api_key=raw_api_key,
            base_url="http://127.0.0.1:11434/v1",
            model="qwen2.5-coder:7b",
        ),
        http_post=fake_post,
    )

    response = provider.rewrite_specification("# Existing deterministic spec")

    assert len(calls) == 1
    assert calls[0].url == "http://127.0.0.1:11434/v1/chat/completions"
    assert response.content.startswith("# AI restructured spec")
    assert response.warnings == ["review before use"]
    assert response.provider == "openai-compatible"


def test_openai_compatible_provider_rejects_unsafe_or_malformed_base_urls():
    from jtc_excel_md.ai_config import AIConfig
    from jtc_excel_md.ai_providers import OpenAICompatibleProvider, build_ai_provider

    unsafe_provider = build_ai_provider(
        AIConfig(enabled=True, provider="openai-compatible", base_url="file:///tmp/model.sock", model="local-model")
    )
    invalid_port_provider = build_ai_provider(
        AIConfig(enabled=True, provider="openai-compatible", base_url="https://example.com:bad/v1", model="local-model")
    )
    schemeless_provider = build_ai_provider(
        AIConfig(enabled=True, provider="openai-compatible", base_url="localhost:11434/v1?token=url-secret", model="local-model")
    )

    assert isinstance(unsafe_provider, OpenAICompatibleProvider)
    assert isinstance(invalid_port_provider, OpenAICompatibleProvider)
    assert isinstance(schemeless_provider, OpenAICompatibleProvider)
    try:
        unsafe_provider.build_rewrite_request("# spec")
    except ValueError as exc:
        assert "Invalid AI base URL" in str(exc)
    else:
        raise AssertionError("unsafe explicit base URL must fail closed")
    try:
        invalid_port_provider.build_rewrite_request("# spec")
    except ValueError as exc:
        assert "Invalid AI base URL" in str(exc)
    else:
        raise AssertionError("malformed explicit base URL must fail closed")
    assert schemeless_provider.build_rewrite_request("# spec").url == "http://localhost:11434/v1/chat/completions"


def test_invalid_explicit_base_url_does_not_call_http_transport():
    from jtc_excel_md.ai_config import AIConfig
    from jtc_excel_md.ai_providers import build_ai_provider

    calls = []

    def fake_post(request):
        calls.append(request)
        return {"choices": [{"message": {"content": "should not run"}}]}

    provider = build_ai_provider(
        AIConfig(
            enabled=True,
            provider="openai-compatible",
            api_key="-".join(["local", "test", "key"]),
            base_url="file:///tmp/model.sock",
            model="local-model",
        ),
        http_post=fake_post,
    )

    response = provider.rewrite_specification("# spec")

    assert calls == []
    assert response.content == ""
    assert response.warnings == ["Invalid AI base URL; no external request was sent."]
