from __future__ import annotations

import json
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape


def _write_docx(path: Path) -> None:
    document_xml = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:body>
    <w:p>
      <w:pPr><w:pStyle w:val="Heading1"/></w:pPr>
      <w:r><w:t>{escape("請求管理システム 基本設計書")}</w:t></w:r>
    </w:p>
    <w:p><w:r><w:t>{escape("この文書はWordで作成された画面仕様です。")}</w:t></w:r></w:p>
    <w:p><w:r><w:t>項目A</w:t><w:tab/><w:t>項目B</w:t><w:br/><w:t>補足</w:t></w:r></w:p>
    <w:tbl>
      <w:tr>
        <w:tc><w:p><w:r><w:t>項目</w:t></w:r></w:p></w:tc>
        <w:tc><w:p><w:r><w:t>内容</w:t></w:r></w:p></w:tc>
      </w:tr>
      <w:tr>
        <w:tc><w:p><w:r><w:t>承認者</w:t></w:r></w:p></w:tc>
        <w:tc><w:p><w:r><w:t>経理部長</w:t></w:r></w:p></w:tc>
      </w:tr>
    </w:tbl>
  </w:body>
</w:document>
"""
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as docx:
        docx.writestr("[Content_Types].xml", "")
        docx.writestr("word/document.xml", document_xml)


def test_convert_word_document_extracts_paragraphs_tables_and_markdown(tmp_path: Path):
    from jtc_excel_md.word_converter import convert_word_document

    docx_path = tmp_path / "design.docx"
    _write_docx(docx_path)

    result = convert_word_document(docx_path)

    assert result["source_type"] == "word_document"
    assert result["document"]["paragraphs"] == [
        {"index": 1, "style": "Heading1", "text": "請求管理システム 基本設計書"},
        {"index": 2, "style": None, "text": "この文書はWordで作成された画面仕様です。"},
        {"index": 3, "style": None, "text": "項目A\t項目B\n補足"},
    ]
    assert result["document"]["tables"] == [
        {
            "index": 1,
            "rows": [["項目", "内容"], ["承認者", "経理部長"]],
        }
    ]
    assert "# 請求管理システム 基本設計書" in result["markdown"]
    assert "この文書はWordで作成された画面仕様です。" in result["markdown"]
    assert "項目A\t項目B\n補足" in result["markdown"]
    assert "| 項目 | 内容 |" in result["markdown"]
    assert "| 承認者 | 経理部長 |" in result["markdown"]


def test_cli_accepts_docx_and_writes_standard_artifacts(tmp_path: Path):
    from jtc_excel_md.cli import run

    docx_path = tmp_path / "design.docx"
    output_dir = tmp_path / "out"
    _write_docx(docx_path)

    exit_code = run([str(docx_path), "--out", str(output_dir)])

    assert exit_code == 0
    payload = json.loads((output_dir / "extracted.json").read_text(encoding="utf-8"))
    assert payload["source_type"] == "word_document"
    assert payload["document"]["paragraphs"][0]["text"] == "請求管理システム 基本設計書"
    assert (output_dir / "book_specification.md").read_text(encoding="utf-8").startswith("# 請求管理システム")
    assert "請求管理システム 基本設計書" in (output_dir / "preview.html").read_text(encoding="utf-8")
    assert (output_dir / "package.zip").exists()


def test_convert_word_document_rejects_missing_or_oversized_document_xml(tmp_path: Path):
    from jtc_excel_md.word_converter import convert_word_document

    missing_xml = tmp_path / "missing.docx"
    with zipfile.ZipFile(missing_xml, "w", compression=zipfile.ZIP_DEFLATED) as docx:
        docx.writestr("[Content_Types].xml", "")

    try:
        convert_word_document(missing_xml)
    except ValueError as exc:
        assert "word/document.xml" in str(exc)
    else:
        raise AssertionError("missing document.xml must fail closed")

    oversized_xml = tmp_path / "oversized.docx"
    with zipfile.ZipFile(oversized_xml, "w", compression=zipfile.ZIP_DEFLATED) as docx:
        docx.writestr("word/document.xml", b"x" * (5_000_001))

    try:
        convert_word_document(oversized_xml)
    except ValueError as exc:
        assert "too large" in str(exc)
    else:
        raise AssertionError("oversized document.xml must fail closed")
