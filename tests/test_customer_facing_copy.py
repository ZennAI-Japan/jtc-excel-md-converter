from __future__ import annotations

from pathlib import Path

CUSTOMER_FACING_FILES = [
    Path("docs/design/kepco-demo-app-mockup.html"),
]

BANNED_PHRASES = [
    "ミラ口調",
    "開発都合",
    "内部メモ",
    "Excelの代替",
    "Excelではできない",
    "安い比較",
    "DEMO-",
    "テスト用",
]

REQUIRED_PHRASES = [
    "関西電力様向け",
    "ローカル解析",
    "要確認",
]


def test_customer_facing_static_mockup_has_required_enterprise_copy():
    for path in CUSTOMER_FACING_FILES:
        text = path.read_text(encoding="utf-8")
        for phrase in REQUIRED_PHRASES:
            assert phrase in text, f"{path}: missing {phrase}"


def test_customer_facing_static_mockup_has_no_banned_phrases():
    for path in CUSTOMER_FACING_FILES:
        text = path.read_text(encoding="utf-8")
        for phrase in BANNED_PHRASES:
            assert phrase not in text, f"{path}: {phrase}"


def test_runtime_demo_copy_has_no_banned_phrases(tmp_path):
    from tests.test_jtc_excel_converter import build_jtc_workbook
    from jtc_excel_md.converter import convert_workbook, write_outputs
    from jtc_excel_md.demo_server import render_demo_html

    source = tmp_path / "jtc.xlsx"
    output_dir = tmp_path / "out"
    build_jtc_workbook(source)
    result = convert_workbook(source)
    write_outputs(result, output_dir)

    text = render_demo_html(result, output_dir=output_dir)
    for phrase in BANNED_PHRASES:
        assert phrase not in text, phrase
