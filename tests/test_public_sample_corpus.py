from __future__ import annotations

from pathlib import Path


def test_public_sample_manifest_has_ten_supported_documents():
    from scripts.fetch_public_sample_corpus import PUBLIC_SAMPLES
    from scripts.evaluate_private_corpus import SUPPORTED_SUFFIXES

    assert len(PUBLIC_SAMPLES) >= 10
    filenames = [sample.filename for sample in PUBLIC_SAMPLES]
    assert len(filenames) == len(set(filenames))
    assert {Path(name).suffix for name in filenames} <= SUPPORTED_SUFFIXES
    assert {Path(name).suffix for name in filenames} >= {".xlsx", ".docx", ".pdf"}
    assert all(sample.url.startswith("https://") for sample in PUBLIC_SAMPLES)


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
    ]
    for phrase in banned:
        assert phrase not in text, phrase
    assert "公開サンプル文書で評価する" in text
    assert "scripts/fetch_public_sample_corpus.py" in text
    assert "ローカルファーストのOSS" in text
