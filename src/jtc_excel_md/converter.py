from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from openpyxl import load_workbook
from openpyxl.cell.cell import Cell
from openpyxl.utils import get_column_letter, range_boundaries
from openpyxl.worksheet.worksheet import Worksheet


def convert_workbook(path: str | Path) -> dict[str, Any]:
    """Convert a JTC-style Excel workbook into structured JSON plus Markdown."""
    workbook_path = Path(path)
    workbook = load_workbook(workbook_path, data_only=False)
    sheets = [_extract_sheet(sheet) for sheet in workbook.worksheets]
    warnings = _collect_warnings(sheets)
    markdown = _render_markdown(sheets)
    return {
        "source": str(workbook_path),
        "sheets": sheets,
        "markdown": markdown,
        "warnings": warnings,
    }


def write_outputs(result: dict[str, Any], output_dir: str | Path) -> None:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "extracted.json").write_text(
        json.dumps(_json_payload(result), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (out / "specification.md").write_text(result["markdown"] + "\n", encoding="utf-8")
    warnings = result.get("warnings") or ["要確認項目は検出されませんでした。"]
    (out / "warnings.md").write_text(
        "# Warnings\n\n" + "\n".join(f"- {warning}" for warning in warnings) + "\n",
        encoding="utf-8",
    )


def _json_payload(result: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in result.items() if key != "markdown"}


def _extract_sheet(sheet: Worksheet) -> dict[str, Any]:
    titles = _extract_titles(sheet)
    blocks = _extract_bordered_tables(sheet)
    validations = _extract_validations(sheet)
    return {
        "name": sheet.title,
        "titles": titles,
        "blocks": blocks,
        "validations": validations,
    }


def _extract_titles(sheet: Worksheet) -> list[dict[str, str]]:
    titles: list[dict[str, str]] = []
    for merged in sheet.merged_cells.ranges:
        min_col, min_row, _max_col, _max_row = range_boundaries(str(merged))
        start_cell = f"{get_column_letter(min_col)}{min_row}"
        value = sheet.cell(min_row, min_col).value
        if value is None or str(value).strip() == "":
            continue
        titles.append({"range": str(merged), "text": str(value).strip(), "start_cell": start_cell})
    return titles


def _extract_bordered_tables(sheet: Worksheet) -> list[dict[str, Any]]:
    bordered = {
        (cell.row, cell.column)
        for row in sheet.iter_rows()
        for cell in row
        if _has_border(cell) and _not_empty_region_candidate(cell)
    }
    components = _connected_components(bordered)
    tables: list[dict[str, Any]] = []
    for component in components:
        min_row = min(row for row, _col in component)
        max_row = max(row for row, _col in component)
        min_col = min(col for _row, col in component)
        max_col = max(col for _row, col in component)
        if (max_row - min_row + 1) < 2 or (max_col - min_col + 1) < 2:
            continue
        headers = [_cell_text(sheet.cell(min_row, col)) for col in range(min_col, max_col + 1)]
        if not any(headers):
            continue
        rows: list[dict[str, str]] = []
        cells: dict[str, dict[str, str]] = {}
        for row_index in range(min_row + 1, max_row + 1):
            values = [_cell_text(sheet.cell(row_index, col)) for col in range(min_col, max_col + 1)]
            if not any(values):
                continue
            rows.append({header or f"列{idx + 1}": value for idx, (header, value) in enumerate(zip(headers, values))})
        for row_index, col_index in sorted(component):
            cell = sheet.cell(row_index, col_index)
            coordinate = cell.coordinate
            cell_payload: dict[str, str] = {}
            text = _cell_text(cell)
            if text:
                cell_payload["value"] = text
            if cell.comment:
                cell_payload["comment"] = str(cell.comment.text).strip()
            if cell.fill and cell.fill.fill_type:
                color = getattr(cell.fill.fgColor, "rgb", None)
                if color:
                    cell_payload["fill"] = str(color)
            if cell_payload:
                cells[coordinate] = cell_payload
        range_name = f"{get_column_letter(min_col)}{min_row}:{get_column_letter(max_col)}{max_row}"
        tables.append(
            {
                "type": "bordered_table",
                "range": range_name,
                "headers": headers,
                "rows": rows,
                "cells": cells,
            }
        )
    return sorted(tables, key=lambda block: range_boundaries(block["range"])[1:3])


def _has_border(cell: Cell) -> bool:
    border = cell.border
    return any(getattr(side, "style", None) for side in [border.left, border.right, border.top, border.bottom])


def _not_empty_region_candidate(cell: Cell) -> bool:
    # Empty bordered cells are often part of JTC layout. Keep them only when the row/column is not completely blank.
    return True


def _connected_components(cells: set[tuple[int, int]]) -> list[set[tuple[int, int]]]:
    remaining = set(cells)
    components: list[set[tuple[int, int]]] = []
    while remaining:
        start = remaining.pop()
        stack = [start]
        component = {start}
        while stack:
            row, col = stack.pop()
            for neighbor in [(row - 1, col), (row + 1, col), (row, col - 1), (row, col + 1)]:
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    component.add(neighbor)
                    stack.append(neighbor)
        components.append(component)
    return components


def _extract_validations(sheet: Worksheet) -> list[dict[str, Any]]:
    validations: list[dict[str, Any]] = []
    for validation in sheet.data_validations.dataValidation:
        options = _parse_validation_options(validation.formula1)
        for sqref in str(validation.sqref).split():
            validations.append({"range": sqref, "type": validation.type, "options": options})
    return validations


def _parse_validation_options(formula: str | None) -> list[str]:
    if not formula:
        return []
    stripped = str(formula).strip()
    if stripped.startswith('"') and stripped.endswith('"'):
        stripped = stripped[1:-1]
    if not stripped or stripped.startswith("="):
        return [stripped] if stripped else []
    return [part.strip() for part in stripped.split(",") if part.strip()]


def _cell_text(cell: Cell) -> str:
    value = cell.value
    if value is None:
        return ""
    text = str(value).strip()
    return text


def _collect_warnings(sheets: list[dict[str, Any]]) -> list[str]:
    warnings: list[str] = []
    for sheet in sheets:
        for title in sheet["titles"]:
            warnings.append(f"{sheet['name']}: 結合セル {title['range']} を見出しとして解釈しました。")
        for block in sheet["blocks"]:
            for coordinate, payload in block["cells"].items():
                if "comment" in payload:
                    warnings.append(f"{sheet['name']}: コメント付きセル {coordinate} は人手確認してください。")
        for validation in sheet["validations"]:
            if validation["type"] == "list" and not validation["options"]:
                warnings.append(f"{sheet['name']}: 入力規則 {validation['range']} は外部範囲参照の可能性があります。")
    return warnings


def _render_markdown(sheets: list[dict[str, Any]]) -> str:
    lines: list[str] = []
    for sheet in sheets:
        title = sheet["titles"][0]["text"] if sheet["titles"] else sheet["name"]
        lines.append(f"# {title}")
        lines.append("")
        if sheet["titles"]:
            lines.append("## 抽出した見出し")
            lines.append("")
            for title_info in sheet["titles"]:
                lines.append(f"- {title_info['range']}: {title_info['text']}")
            lines.append("")
        for block in sheet["blocks"]:
            lines.append(f"## {sheet['name']} / {block['range']}")
            lines.append("")
            headers = block["headers"]
            lines.append("| " + " | ".join(_escape_md(header or " ") for header in headers) + " |")
            lines.append("| " + " | ".join("---" for _ in headers) + " |")
            for row in block["rows"]:
                lines.append("| " + " | ".join(_escape_md(row.get(header or f"列{idx + 1}", "")) for idx, header in enumerate(headers)) + " |")
            lines.append("")
        if sheet["validations"]:
            lines.append("### 入力規則")
            lines.append("")
            for validation in sheet["validations"]:
                option_text = " / ".join(validation["options"]) if validation["options"] else "外部参照または未解析"
                lines.append(f"- {validation['range']}: {option_text}")
            lines.append("")
    return "\n".join(lines).strip()


def _escape_md(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", "<br>")
