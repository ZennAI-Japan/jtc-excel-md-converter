# JTC Excel MD Converter

Local-first open source toolkit for converting Japanese enterprise “Excel方眼紙” design documents into Markdown, structured JSON, and reviewable artifacts.

The deterministic converter works without AI credentials. Optional AI-assisted restructuring is designed as bring-your-own-AI: users can configure their own hosted API, OpenAI-compatible gateway, or local model runtime without committing keys to the repository.

This MVP focuses on preserving information that generic spreadsheet-to-Markdown tools often lose:

- bordered regions as semantic blocks
- merged-cell titles and section labels
- cell coordinates
- data validation / dropdown options
- comments and warning output for human review

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
python -m pytest -q
jtc-md-convert examples/jtc_screen_design.xlsx --out outputs/jtc_screen_design
```

Generated files:

- `extracted.json` — structured sheet/block/cell data
- `book_specification.md` — workbook-level Markdown specification
- `specification.md` — backward-compatible Markdown filename
- `warnings.md` — items requiring review
- `preview.html` — cell-coordinate review preview
- `evaluation.md` — conversion summary
- `package.zip` — downloadable artifact bundle

## AI provider configuration

Copy the template and fill only the provider you want to use:

```bash
cp .env.example .env
```

The current configuration contract supports:

- `openai`
- `anthropic`
- `google`
- `openai-compatible`
- `ollama`
- `lmstudio`
- `local`

Generic OpenAI-compatible or local gateway example:

```text
JTC_AI_PROVIDER=openai-compatible
JTC_AI_API_KEY=
JTC_AI_BASE_URL=http://127.0.0.1:11434/v1
JTC_AI_MODEL=qwen2.5-coder:7b
```

Provider-specific alternatives such as `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, and `GOOGLE_API_KEY` are also supported by the config loader. The repository ignores `.env` and `.env.*`; keep real API keys local.

To include a secret-masked AI configuration summary in the conversion artifacts:

```bash
jtc-md-convert examples/jtc_screen_design.xlsx \
  --out outputs/jtc_screen_design \
  --ai-env-file .env \
  --show-ai-config
```

The CLI records provider/model, a sanitized base URL (scheme + host + path only), and whether an API key is configured, but it does not write raw or key-derived API key text to `extracted.json`, `evaluation.md`, stdout, or the artifact ZIP. Raw API keys stay local.

## Local demo UI

Run the KEPCO-oriented local demo UI:

```bash
jtc-md-demo examples/jtc_screen_design.xlsx --out outputs/demo-app --port 8765
```

Open:

```text
http://127.0.0.1:8765/
```

The initial demo runs locally and does not send document content to external LLM/API services.
It shows the sheet list, extracted preview, workbook-level Markdown artifact, structured JSON,
review HTML, evaluation report, warnings, and ZIP download route.

Smoke-test the rendered UI and capture a screenshot:

```bash
python scripts/smoke_demo_ui.py
```

## Scope

This is not a generic Excel renderer. It is a PoC baseline for reverse-engineering JTC-style system design documents that use Excel as a layout canvas.
