from __future__ import annotations

import json
import zipfile
from pathlib import Path

import pymupdf


def test_ci_workflow_runs_python_docker_and_security_gates():
    workflow = Path(".github/workflows/ci.yml")
    assert workflow.exists()
    text = workflow.read_text(encoding="utf-8")
    assert "python -m compileall -q src tests scripts" in text
    assert "python -m pytest -q" in text
    assert "scripts/docker_smoke.sh" in text
    assert "docker compose config --quiet" in text
    assert 'env UID="$(id -u)" GID="$(id -g)" docker compose run' in text
    assert "secret assignment scan" in text
    assert "--exclude-dir='*.egg-info'" in text
    release_workflow = Path(".github/workflows/public-release-gate.yml")
    assert release_workflow.exists()
    assert "python scripts/public_release_gate.py" in release_workflow.read_text(encoding="utf-8")


def test_cli_accepts_text_pdf_and_writes_standard_artifacts(tmp_path: Path):
    from jtc_excel_md.cli import run

    pdf_path = tmp_path / "design.pdf"
    doc = pymupdf.open()
    page = doc.new_page()
    page.insert_text((72, 72), "請求管理システム PDF設計書", fontname="japan")
    page.insert_text((72, 100), "承認フローと入力チェックを確認する。", fontname="japan")
    doc.save(pdf_path)
    doc.close()

    out = tmp_path / "out"
    assert run([str(pdf_path), "--out", str(out)]) == 0
    payload = json.loads((out / "extracted.json").read_text(encoding="utf-8"))
    assert payload["source_type"] == "pdf_document"
    assert payload["document"]["pages"][0]["text"].startswith("請求管理システム")
    assert "# 請求管理システム PDF設計書" in (out / "book_specification.md").read_text(encoding="utf-8")


def test_ai_restructure_writes_reviewable_artifacts_without_mutating_base_outputs(tmp_path: Path):
    from jtc_excel_md.ai_providers import AIResponse
    from jtc_excel_md.ai_restructure import restructure_output_dir

    out = tmp_path / "converted"
    out.mkdir()
    original = "# 元仕様\n\n- A1: 申請者"
    (out / "book_specification.md").write_text(original, encoding="utf-8")
    (out / "extracted.json").write_text('{"source":"fixture.xlsx"}\n', encoding="utf-8")

    class FakeProvider:
        name = "fake-codex"

        def rewrite_specification(self, prompt: str) -> AIResponse:
            assert "# 元仕様" in prompt
            assert "fixture.xlsx" in prompt
            return AIResponse(content="# AI整形仕様\n\n- A1を保持", provider=self.name, warnings=["人手確認"])

    result = restructure_output_dir(out, provider=FakeProvider())

    assert result["provider"] == "fake-codex"
    assert (out / "book_specification.md").read_text(encoding="utf-8") == original
    assert (out / "ai_restructured_specification.md").read_text(encoding="utf-8").startswith("# AI整形仕様")
    assert "人手確認" in (out / "ai_restructure_warnings.md").read_text(encoding="utf-8")


def test_word_converter_extracts_textboxes_and_image_placeholders(tmp_path: Path):
    from jtc_excel_md.word_converter import convert_word_document

    docx = tmp_path / "rich.docx"
    xml = """<?xml version='1.0' encoding='UTF-8'?>
<w:document xmlns:w='http://schemas.openxmlformats.org/wordprocessingml/2006/main'
            xmlns:a='http://schemas.openxmlformats.org/drawingml/2006/main'
            xmlns:wp='http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing'>
  <w:body>
    <w:p><w:r><w:t>図形つき設計書</w:t></w:r></w:p>
    <w:p><w:r><w:drawing><wp:inline><a:graphic><a:graphicData><pic:pic xmlns:pic='http://schemas.openxmlformats.org/drawingml/2006/picture'><pic:nvPicPr><pic:cNvPr id='1' name='画面キャプチャ.png'/></pic:nvPicPr></pic:pic></a:graphicData></a:graphic></wp:inline></w:drawing></w:r></w:p>
    <w:p><w:r><w:pict><w:txbxContent><w:p><w:r><w:t>テキストボックス内の注意事項</w:t></w:r></w:p></w:txbxContent></w:pict></w:r></w:p>
  </w:body>
</w:document>
"""
    with zipfile.ZipFile(docx, "w") as zf:
        zf.writestr("word/document.xml", xml)

    result = convert_word_document(docx)
    assert result["document"]["textboxes"] == [{"index": 1, "text": "テキストボックス内の注意事項"}]
    assert result["document"]["paragraphs"] == [{"index": 1, "style": None, "text": "図形つき設計書"}]
    assert result["document"]["images"] == [{"index": 1, "name": "画面キャプチャ.png"}]
    assert any("画像プレースホルダー" in warning for warning in result["warnings"])


def test_word_converter_extracts_table_nested_textboxes_and_images(tmp_path: Path):
    from jtc_excel_md.word_converter import convert_word_document

    docx = tmp_path / "table-rich.docx"
    xml = """<?xml version='1.0' encoding='UTF-8'?>
<w:document xmlns:w='http://schemas.openxmlformats.org/wordprocessingml/2006/main'
            xmlns:a='http://schemas.openxmlformats.org/drawingml/2006/main'
            xmlns:wp='http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing'>
  <w:body>
    <w:tbl><w:tr><w:tc>
      <w:p><w:r><w:t>セル本文</w:t></w:r></w:p>
      <w:p><w:r><w:pict><w:txbxContent><w:p><w:r><w:t>表内注記</w:t></w:r></w:p></w:txbxContent></w:pict></w:r></w:p>
      <w:p><w:r><w:drawing><wp:inline><a:graphic><a:graphicData><pic:pic xmlns:pic='http://schemas.openxmlformats.org/drawingml/2006/picture'><pic:nvPicPr><pic:cNvPr id='2' name='表内画像.png'/></pic:nvPicPr></pic:pic></a:graphicData></a:graphic></wp:inline></w:drawing></w:r></w:p>
    </w:tc></w:tr></w:tbl>
  </w:body>
</w:document>
"""
    with zipfile.ZipFile(docx, "w") as zf:
        zf.writestr("word/document.xml", xml)

    result = convert_word_document(docx)

    assert result["document"]["tables"] == [{"index": 1, "rows": [["セル本文"]]}]
    assert result["document"]["textboxes"] == [{"index": 1, "text": "表内注記"}]
    assert result["document"]["images"] == [{"index": 1, "name": "表内画像.png"}]


def test_excel_drawing_xml_text_and_picture_are_reported(tmp_path: Path):
    from jtc_excel_md.rich_media import extract_xlsx_drawing_media

    xlsx = tmp_path / "drawing.xlsx"
    drawing = """<xdr:wsDr xmlns:xdr='http://schemas.openxmlformats.org/drawingml/2006/spreadsheetDrawing' xmlns:a='http://schemas.openxmlformats.org/drawingml/2006/main'>
      <xdr:twoCellAnchor><xdr:sp><xdr:nvSpPr><xdr:cNvPr id='2' name='吹き出し 1'/></xdr:nvSpPr><xdr:txBody><a:p><a:r><a:t>図形内メモ</a:t></a:r></a:p></xdr:txBody></xdr:sp></xdr:twoCellAnchor>
      <xdr:twoCellAnchor><xdr:pic><xdr:nvPicPr><xdr:cNvPr id='3' name='構成図.png'/></xdr:nvPicPr></xdr:pic></xdr:twoCellAnchor>
    </xdr:wsDr>"""
    with zipfile.ZipFile(xlsx, "w") as zf:
        zf.writestr("xl/drawings/drawing1.xml", drawing)

    media = extract_xlsx_drawing_media(xlsx)
    assert media["textboxes"] == [{"drawing": "xl/drawings/drawing1.xml", "name": "吹き出し 1", "text": "図形内メモ"}]
    assert media["images"] == [{"drawing": "xl/drawings/drawing1.xml", "name": "構成図.png"}]


def test_excel_non_text_shapes_are_reported_as_shape_placeholders(tmp_path: Path):
    from jtc_excel_md.rich_media import extract_xlsx_drawing_media

    xlsx = tmp_path / "shape.xlsx"
    drawing = """<xdr:wsDr xmlns:xdr='http://schemas.openxmlformats.org/drawingml/2006/spreadsheetDrawing' xmlns:a='http://schemas.openxmlformats.org/drawingml/2006/main'>
      <xdr:twoCellAnchor><xdr:sp><xdr:nvSpPr><xdr:cNvPr id='4' name='四角形 1'/></xdr:nvSpPr><xdr:spPr/></xdr:sp></xdr:twoCellAnchor>
      <xdr:twoCellAnchor><xdr:cxnSp><xdr:nvCxnSpPr><xdr:cNvPr id='5' name='コネクタ 1'/></xdr:nvCxnSpPr><xdr:spPr/></xdr:cxnSp></xdr:twoCellAnchor>
    </xdr:wsDr>"""
    with zipfile.ZipFile(xlsx, "w") as zf:
        zf.writestr("xl/drawings/drawing1.xml", drawing)

    media = extract_xlsx_drawing_media(xlsx)

    assert media["shapes"] == [
        {"drawing": "xl/drawings/drawing1.xml", "name": "四角形 1"},
        {"drawing": "xl/drawings/drawing1.xml", "name": "コネクタ 1"},
    ]
