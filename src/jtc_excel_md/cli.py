from __future__ import annotations

import argparse
from pathlib import Path

from .converter import convert_workbook, write_outputs


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert JTC-style Excel design docs to Markdown/JSON.")
    parser.add_argument("input", type=Path, help="Input .xlsx file")
    parser.add_argument("--out", type=Path, required=True, help="Output directory")
    args = parser.parse_args()

    result = convert_workbook(args.input)
    write_outputs(result, args.out)
    print(f"wrote: {args.out / 'extracted.json'}")
    print(f"wrote: {args.out / 'specification.md'}")
    print(f"wrote: {args.out / 'warnings.md'}")
