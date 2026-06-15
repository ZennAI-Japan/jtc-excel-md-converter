from __future__ import annotations

import json
import zipfile
from pathlib import Path


def _write_minimal_docx(path: Path, text: str) -> None:
    xml = f"""<?xml version='1.0' encoding='UTF-8'?>
<w:document xmlns:w='http://schemas.openxmlformats.org/wordprocessingml/2006/main'>
  <w:body><w:p><w:r><w:t>{text}</w:t></w:r></w:p></w:body>
</w:document>
"""
    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr("word/document.xml", xml)


def test_private_corpus_evaluator_writes_summary_and_requires_10_documents(tmp_path: Path):
    from scripts.evaluate_private_corpus import evaluate_corpus

    input_dir = tmp_path / "private"
    input_dir.mkdir()
    for index in range(10):
        _write_minimal_docx(input_dir / f"case-{index}.docx", f"顧客文書{index}")

    summary = evaluate_corpus(input_dir, tmp_path / "out")

    assert summary["total_documents"] == 10
    assert summary["failed_documents"] == 0
    assert summary["meets_private_corpus_bar"] is True
    saved = json.loads((tmp_path / "out" / "evaluation_summary.json").read_text(encoding="utf-8"))
    assert saved == summary
    assert (tmp_path / "out" / "evaluation_cases.csv").exists()
    csv_text = (tmp_path / "out" / "evaluation_cases.csv").read_text(encoding="utf-8")
    assert str(input_dir) not in csv_text
    assert "case-001" in csv_text


def test_private_corpus_evaluator_fails_bar_when_document_count_is_low(tmp_path: Path):
    from scripts.evaluate_private_corpus import evaluate_corpus

    input_dir = tmp_path / "private"
    input_dir.mkdir()
    _write_minimal_docx(input_dir / "case.docx", "顧客文書")

    summary = evaluate_corpus(input_dir, tmp_path / "out")

    assert summary["total_documents"] == 1
    assert summary["meets_private_corpus_bar"] is False


def test_private_corpus_evaluator_caps_at_30_and_escapes_csv_formula_names(tmp_path: Path):
    from scripts.evaluate_private_corpus import evaluate_corpus

    input_dir = tmp_path / "private"
    input_dir.mkdir()
    _write_minimal_docx(input_dir / "=HYPERLINK evil.docx", "危険な名前")
    for index in range(35):
        _write_minimal_docx(input_dir / f"case-{index}.docx", f"顧客文書{index}")

    summary = evaluate_corpus(input_dir, tmp_path / "out")

    assert summary["discovered_documents"] == 36
    assert summary["total_documents"] == 30
    csv_text = (tmp_path / "out" / "evaluation_cases.csv").read_text(encoding="utf-8")
    assert "'=HYPERLINK evil.docx" in csv_text


def test_public_release_gate_fails_closed_until_all_approvals_are_checked(tmp_path: Path):
    from scripts.public_release_gate import check_public_release_approval

    approval = tmp_path / "approval.md"
    approval.write_text(
        "- [x] 保守者承認\n"
        "- [ ] 実顧客文書評価\n"
        "- [x] 秘密情報確認\n"
        "- [x] ライセンス確認\n",
        encoding="utf-8",
    )
    ok, issues = check_public_release_approval(approval)
    assert ok is False
    assert issues == ["未承認: 実顧客文書評価"]

    approval.write_text(
        "- [x] 保守者承認\n"
        "- [x] 実顧客文書評価\n"
        "- [x] 秘密情報確認\n"
        "- [x] ライセンス確認\n",
        encoding="utf-8",
    )
    assert check_public_release_approval(approval) == (True, [])
