# JTC Excel MD Converter

Prototype CLI for converting Japanese enterprise “Excel方眼紙” design documents into Markdown and structured JSON.

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
