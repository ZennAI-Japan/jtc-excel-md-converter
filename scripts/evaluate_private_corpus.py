from __future__ import annotations

import csv
import json
import re
from pathlib import Path

from jtc_excel_md.cli import convert_input_document
from jtc_excel_md.converter import write_outputs

SUPPORTED_SUFFIXES = {".xlsx", ".xlsm", ".xltx", ".xltm", ".docx", ".pdf"}
MIN_REQUIRED_DOCUMENTS = 10
MAX_RECOMMENDED_DOCUMENTS = 30
FORMULA_PREFIXES = ("=", "+", "-", "@")


def evaluate_corpus(
    input_dir: Path,
    output_dir: Path,
    *,
    summary_title: str = "実顧客文書評価サマリー",
    bar_label: str = "10〜30本評価対象・失敗0件の基準",
) -> dict[str, object]:
    documents = sorted(path for path in input_dir.rglob("*") if path.is_file() and path.suffix.lower() in SUPPORTED_SUFFIXES)
    output_dir.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, object]] = []
    for index, document in enumerate(documents[:MAX_RECOMMENDED_DOCUMENTS], start=1):
        case_id = f"case-{index:03d}"
        case_dir = output_dir / case_id
        try:
            result = convert_input_document(document)
            write_outputs(result, case_dir)
            result_warnings = result.get("warnings", [])
            warning_count = len(result_warnings) if isinstance(result_warnings, list) else 0
            rows.append(
                {
                    "case_id": case_id,
                    "file": _safe_cell(document.name),
                    "status": "ok",
                    "source_type": result.get("source_type", "excel_workbook"),
                    "warnings": warning_count,
                    "markdown_chars": len(str(result.get("markdown", ""))),
                    "output_dir": case_id,
                }
            )
        except Exception as exc:  # noqa: BLE001 - corpus runner must continue per file
            rows.append(
                {
                    "case_id": case_id,
                    "file": _safe_cell(document.name),
                    "status": "failed",
                    "source_type": "",
                    "warnings": 1,
                    "markdown_chars": 0,
                    "output_dir": case_id,
                    "error": _safe_cell(str(exc)),
                }
            )
    summary = _build_summary(rows, discovered_total=len(documents))
    _write_csv(output_dir / "evaluation_cases.csv", rows)
    (output_dir / "evaluation_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (output_dir / "evaluation_summary.md").write_text(
        _render_markdown(summary, rows, title=summary_title, bar_label=bar_label),
        encoding="utf-8",
    )
    return summary


def _build_summary(rows: list[dict[str, object]], *, discovered_total: int | None = None) -> dict[str, object]:
    total = len(rows)
    failed = sum(1 for row in rows if row["status"] != "ok")
    return {
        "discovered_documents": discovered_total if discovered_total is not None else total,
        "total_documents": total,
        "passed_documents": total - failed,
        "failed_documents": failed,
        "minimum_required_documents": MIN_REQUIRED_DOCUMENTS,
        "maximum_recommended_documents": MAX_RECOMMENDED_DOCUMENTS,
        "meets_private_corpus_bar": total >= MIN_REQUIRED_DOCUMENTS and failed == 0,
    }


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    fieldnames = ["case_id", "file", "status", "source_type", "warnings", "markdown_chars", "output_dir", "error"]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: _safe_cell(row.get(field, "")) for field in fieldnames})


def _safe_cell(value: object) -> str:
    text = str(value)
    text = re.sub(r"[\r\n\t]+", " ", text).strip()
    if text.startswith(FORMULA_PREFIXES):
        return f"'{text}"
    return text


def _render_markdown(
    summary: dict[str, object],
    rows: list[dict[str, object]],
    *,
    title: str = "実顧客文書評価サマリー",
    bar_label: str = "10〜30本評価対象・失敗0件の基準",
) -> str:
    lines = [
        f"# {title}",
        "",
        f"- 評価文書数: {summary['total_documents']}",
        f"- 検出文書数: {summary['discovered_documents']}",
        f"- 成功: {summary['passed_documents']}",
        f"- 失敗: {summary['failed_documents']}",
        f"- {bar_label}: {summary['meets_private_corpus_bar']}",
        "",
        "## ケース一覧",
        "",
        "| ケース | ファイル名 | 状態 | 種別 | 警告数 | Markdown文字数 |",
        "| --- | --- | --- | --- | ---: | ---: |",
    ]
    for row in rows:
        lines.append(
            f"| {_safe_cell(row.get('case_id', ''))} | {_safe_cell(row.get('file', ''))} | {row.get('status', '')} | {row.get('source_type', '')} | {row.get('warnings', 0)} | {row.get('markdown_chars', 0)} |"
        )
    return "\n".join(lines) + "\n"


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Evaluate 10-30 private customer Office/PDF documents locally.")
    parser.add_argument("input_dir", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    summary = evaluate_corpus(args.input_dir, args.out)
    print(json.dumps(summary, ensure_ascii=False))
    raise SystemExit(0 if summary["meets_private_corpus_bar"] else 1)


if __name__ == "__main__":
    main()
