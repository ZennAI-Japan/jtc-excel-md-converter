from __future__ import annotations

from pathlib import Path
import io
import re
import tomllib


def test_public_sample_manifest_has_ten_supported_documents():
    from scripts.fetch_public_sample_corpus import PUBLIC_SAMPLES
    from scripts.evaluate_private_corpus import SUPPORTED_SUFFIXES

    assert len(PUBLIC_SAMPLES) >= 10
    filenames = [sample.filename for sample in PUBLIC_SAMPLES]
    assert len(filenames) == len(set(filenames))
    assert {Path(name).suffix for name in filenames} <= SUPPORTED_SUFFIXES
    assert {Path(name).suffix for name in filenames} >= {".xlsx", ".docx", ".pdf"}
    assert all(sample.url.startswith("https://") for sample in PUBLIC_SAMPLES)
    assert all(re.fullmatch(r"[0-9a-f]{64}", sample.sha256) for sample in PUBLIC_SAMPLES)
    assert all("pandas-dev/pandas/main" not in sample.url for sample in PUBLIC_SAMPLES)


def test_public_sample_fetcher_verifies_existing_file_checksum(tmp_path):
    from scripts.fetch_public_sample_corpus import _verify_sha256

    sample = tmp_path / "sample.txt"
    sample.write_text("hello", encoding="utf-8")
    _verify_sha256(sample, "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824")

    try:
        _verify_sha256(sample, "0" * 64)
    except RuntimeError as exc:
        assert "checksum mismatch" in str(exc)
    else:
        raise AssertionError("checksum mismatch must fail closed")


def test_public_sample_download_cleans_tmp_file_on_checksum_error(tmp_path, monkeypatch):
    import scripts.fetch_public_sample_corpus as fetcher

    destination = tmp_path / "downloaded.bin"

    def fake_urlopen(request, timeout):
        return io.BytesIO(b"not the expected file")

    monkeypatch.setattr(fetcher.urllib.request, "urlopen", fake_urlopen)

    try:
        fetcher._download("https://example.com/source.bin", destination, expected_sha256="0" * 64)
    except RuntimeError as exc:
        assert "checksum mismatch" in str(exc)
    else:
        raise AssertionError("checksum mismatch must fail closed")

    assert not destination.exists()
    assert not destination.with_suffix(".bin.tmp").exists()


def test_readme_is_public_oss_copy_without_internal_positioning():
    text = Path("README.md").read_text(encoding="utf-8")
    banned = [
        "関西電力",
        "実顧客",
        "public化",
        "Codex",
        "ご主人",
        "ミラ",
        "ZennAI",
        "社内承認済み",
        "初期デモ",
        "評価レポート",
        "文書セット評価",
    ]
    for phrase in banned:
        assert phrase not in text, phrase
    assert "公開サンプルで動作確認する" in text
    assert "scripts/fetch_public_sample_corpus.py" in text
    assert "ローカルファースト" in text
    assert "Word / Excelで作られた業務文書" in text
    assert "JTC企業でよく使われるWord / Excelの業務文書" in text
    assert "対応できること / まだ苦手なこと" in text
    assert "このツールは、そうした構造を読み取り、Markdown仕様書として出力します" in text
    assert "中心となる成果物は `book_specification.md`" in text
    assert "完璧な文書理解AIではありません" in text
    assert "テキストPDFにも対応しています" in text
    assert "docs/assets/social-preview.png" in text
    assert "PyMuPDF" in text
    assert "AGPL-3.0-or-later" in text
    assert "SHA-256" in text
    assert "pip install -e '.[pdf]'" in text
    assert "jtc-excel-md-converter[pdf]" in text


def test_pyproject_keeps_pymupdf_in_optional_pdf_extra():
    data = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))
    dependencies = data["project"]["dependencies"]
    optional = data["project"]["optional-dependencies"]

    assert not any("PyMuPDF" in item for item in dependencies)
    assert any("PyMuPDF" in item for item in optional["pdf"])
    assert any("PyMuPDF" in item for item in optional["dev"])


def test_docker_runtime_installs_pdf_extra_for_pdf_smoke():
    text = Path("Dockerfile").read_text(encoding="utf-8")
    assert "pip install --no-cache-dir '.[pdf]'" in text


def test_notice_documents_pdf_dependency_license_boundary():
    text = Path("NOTICE.md").read_text(encoding="utf-8")
    assert "PyMuPDF" in text
    assert "AGPL-3.0-or-later" in text
    assert "商用ライセンス" in text
    assert "サンプル文書" in text
    assert "SHA-256" in text


def test_social_preview_asset_exists():
    text = Path("docs/assets/social-preview.svg").read_text(encoding="utf-8")
    assert "JTC Excel MD Converter" in text
    assert "Office文書をAIが読める仕様書へ" in text
