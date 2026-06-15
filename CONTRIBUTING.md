# Contributing

Thanks for helping improve JTC Excel MD Converter.

This project is intended to be usable as open source software by teams that need to convert enterprise Excel design documents into Markdown, JSON, and reviewable artifacts.

## Development setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
python -m pytest -q
```

## Local demo

```bash
jtc-md-demo examples/jtc_screen_design.xlsx --out outputs/demo-app --port 8765
```

Open `http://127.0.0.1:8765/`.

## AI provider configuration

The deterministic converter must keep working without AI credentials.
AI-assisted restructuring should read provider settings from environment variables or a local `.env` file.
Do not hardcode API keys in code, examples, tests, docs, screenshots, or issues.

Copy `.env.example` to `.env` and fill your provider:

```bash
cp .env.example .env
```

Supported provider values for the current configuration contract:

- `openai`
- `anthropic`
- `google`
- `openai-compatible`
- `ollama`
- `lmstudio`
- `local`

Generic settings:

```text
JTC_AI_PROVIDER=openai-compatible
JTC_AI_API_KEY=
JTC_AI_BASE_URL=http://127.0.0.1:11434/v1
JTC_AI_MODEL=qwen2.5-coder:7b
```

## Pull request checklist

Before opening or updating a PR, run:

```bash
python -m compileall -q src tests scripts
python -m pytest -q
python scripts/smoke_demo_ui.py
git diff --check
```

If the UI surface changes, verify customer-facing copy does not include internal notes, development-only language, or cheap tool-comparison framing.

## Security expectations

- Never commit `.env` or real credentials.
- Keep document contents local by default.
- Any future AI call must make provider, base URL, model, and network behavior explicit.
- Any future remote provider feature must have tests proving local/deterministic mode still works without credentials.
