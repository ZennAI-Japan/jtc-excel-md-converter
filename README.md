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
jtc-md-convert examples/jtc_screen_design.xlsx --out outputs/jtc_screen_design
```

Generated files:

- `extracted.json` — structured sheet/block/cell data
- `specification.md` — human/AI-readable Markdown
- `warnings.md` — items requiring review

## Scope

This is not a generic Excel renderer. It is a PoC baseline for reverse-engineering JTC-style system design documents that use Excel as a layout canvas.
