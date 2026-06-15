from __future__ import annotations

from pathlib import Path

from tests.test_jtc_excel_converter import build_jtc_workbook


def test_converter_outputs_demo_artifact_contract(tmp_path: Path):
    from jtc_excel_md.converter import convert_workbook, write_outputs

    source = tmp_path / "jtc.xlsx"
    output_dir = tmp_path / "out"
    build_jtc_workbook(source)

    result = convert_workbook(source)
    write_outputs(result, output_dir)

    expected = {
        "book_specification.md",
        "extracted.json",
        "preview.html",
        "evaluation.md",
        "warnings.md",
        "package.zip",
    }
    assert expected <= {path.name for path in output_dir.iterdir()}


def test_demo_home_contains_kepco_demo_copy_and_converter_output(tmp_path: Path):
    from jtc_excel_md.converter import convert_workbook, write_outputs
    from jtc_excel_md.demo_server import render_demo_html

    source = tmp_path / "jtc.xlsx"
    output_dir = tmp_path / "out"
    build_jtc_workbook(source)
    result = convert_workbook(source)
    write_outputs(result, output_dir)

    html = render_demo_html(result, output_dir=output_dir)

    assert "設計書ドキュメント化プラットフォーム" in html
    assert "関西電力様向け" in html
    assert "ローカル解析" in html
    assert "book_specification.md" in html
    assert "extracted.json" in html
    assert "preview.html" in html
    assert "evaluation.md" not in html
    assert "評価レポート" not in html
    assert "warnings.md" in html
    assert "package.zip" in html
    assert "画面設計書" in html
    assert "B4:F7" in html
    assert "コメント付きセル F5" in html


def test_demo_request_handler_serves_home_and_artifacts(tmp_path: Path):
    from jtc_excel_md.converter import convert_workbook, write_outputs
    from jtc_excel_md.demo_server import build_demo_response, build_artifact_response

    source = tmp_path / "jtc.xlsx"
    output_dir = tmp_path / "out"
    build_jtc_workbook(source)
    result = convert_workbook(source)
    write_outputs(result, output_dir)

    status, headers, body = build_demo_response(result, output_dir=output_dir)
    assert status == 200
    assert headers["Content-Type"].startswith("text/html")
    assert "設計書ドキュメント化プラットフォーム" in body.decode("utf-8")

    artifact_status, artifact_headers, artifact_body = build_artifact_response(output_dir, "/artifacts/book_specification.md")
    assert artifact_status == 200
    assert artifact_headers["Content-Type"].startswith("text/markdown")
    assert "画面設計書：ログイン画面" in artifact_body.decode("utf-8")
