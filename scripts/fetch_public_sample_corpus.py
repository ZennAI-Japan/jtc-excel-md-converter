from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
for path in (REPO_ROOT, SRC_ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from scripts.evaluate_private_corpus import evaluate_corpus


PANDAS_COMMIT = "aee9241b414707c381277b4392d5f0ef06956ba9"
PANDAS_RAW_BASE = f"https://raw.githubusercontent.com/pandas-dev/pandas/{PANDAS_COMMIT}/pandas/tests/io/data/excel"


@dataclass(frozen=True)
class PublicSample:
    filename: str
    url: str
    sha256: str
    source: str
    note: str


PUBLIC_SAMPLES: tuple[PublicSample, ...] = (
    PublicSample(
        "pandas-test1.xlsx",
        f"{PANDAS_RAW_BASE}/test1.xlsx",
        "b6fe2d9ae5afd6d0bdfefbae9c0c1649d8bf883e183a153cb76f2a8a548cef11",
        "pandas-dev/pandas",
        "Excel parser regression workbook used by pandas tests.",
    ),
    PublicSample(
        "pandas-test2.xlsx",
        f"{PANDAS_RAW_BASE}/test2.xlsx",
        "1910a60747bd1a52bfd046973ff5df2a83bcbf57199920f29aac0606e9f21cef",
        "pandas-dev/pandas",
        "Excel parser regression workbook used by pandas tests.",
    ),
    PublicSample(
        "pandas-test3.xlsx",
        f"{PANDAS_RAW_BASE}/test3.xlsx",
        "b5683a998abe9573c825488837631842642ded0896f59213c806e2f4d878ca87",
        "pandas-dev/pandas",
        "Excel parser regression workbook used by pandas tests.",
    ),
    PublicSample(
        "pandas-test4.xlsx",
        f"{PANDAS_RAW_BASE}/test4.xlsx",
        "f6b631c1097ce10e64635e0f2d0a4f769b9ae505bc9dbd6598cb1776b8df8542",
        "pandas-dev/pandas",
        "Excel parser regression workbook used by pandas tests.",
    ),
    PublicSample(
        "pandas-test5.xlsx",
        f"{PANDAS_RAW_BASE}/test5.xlsx",
        "e36fbd1bd76d49254fc4626421b24efec49df1efccb322d18c08b95669c73251",
        "pandas-dev/pandas",
        "Excel parser regression workbook used by pandas tests.",
    ),
    PublicSample(
        "pandas-multisheet.xlsx",
        f"{PANDAS_RAW_BASE}/test_multisheet.xlsx",
        "2e2093238e2304bd6bce5db643db89cb6ff45774285701a43ad95c095359d496",
        "pandas-dev/pandas",
        "Multi-sheet Excel workbook.",
    ),
    PublicSample(
        "pandas-spaces.xlsx",
        f"{PANDAS_RAW_BASE}/test_spaces.xlsx",
        "8d909ca9a9d14086fd24d454ce63c7de9f1b6452c0faa109c5dd737c193ef121",
        "pandas-dev/pandas",
        "Excel workbook with spacing edge cases.",
    ),
    PublicSample(
        "pandas-converters.xlsx",
        f"{PANDAS_RAW_BASE}/test_converters.xlsx",
        "793f4c69aa2080d53793a85e6373c07905c5ce0f9203ce98675c7d9b5f69042f",
        "pandas-dev/pandas",
        "Excel workbook with mixed cell values for converter tests.",
    ),
    PublicSample(
        "calibre-demo.docx",
        "https://calibre-ebook.com/downloads/demos/demo.docx",
        "269329fc7ae54b3f289b3ac52efde387edc2e566ef9a48d637e841022c7e0eab",
        "calibre-ebook.com",
        "Public DOCX demo document.",
    ),
    PublicSample(
        "w3c-dummy.pdf",
        "https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf",
        "3df79d34abbca99308e79cb94461c1893582604d68329a41fd4bec1885e6adb4",
        "W3C WAI test files",
        "Small public text PDF fixture.",
    ),
)


USER_AGENT = "jtc-excel-md-converter-public-sample-fetcher/0.1"


def fetch_public_samples(corpus_dir: Path, *, overwrite: bool = False) -> list[dict[str, str]]:
    corpus_dir.mkdir(parents=True, exist_ok=True)
    manifest: list[dict[str, str]] = []
    for sample in PUBLIC_SAMPLES:
        destination = corpus_dir / sample.filename
        if destination.exists() and not overwrite:
            _verify_sha256(destination, sample.sha256)
            status = "exists"
        else:
            _download(sample.url, destination, expected_sha256=sample.sha256)
            status = "downloaded"
        manifest.append(
            {
                "filename": sample.filename,
                "url": sample.url,
                "sha256": sample.sha256,
                "source": sample.source,
                "note": sample.note,
                "status": status,
            }
        )
    (corpus_dir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return manifest


def _download(url: str, destination: Path, *, expected_sha256: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        raise ValueError(f"unsupported URL scheme: {url}")
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    tmp = destination.with_suffix(destination.suffix + ".tmp")
    try:
        with urllib.request.urlopen(request, timeout=60) as response, tmp.open("wb") as handle:  # noqa: S310 - fixed public manifest URLs
            shutil.copyfileobj(response, handle)
        if tmp.stat().st_size == 0:
            raise RuntimeError(f"downloaded empty file: {url}")
        _verify_sha256(tmp, expected_sha256)
        tmp.replace(destination)
    except Exception:
        tmp.unlink(missing_ok=True)
        raise


def _verify_sha256(path: Path, expected_sha256: str) -> None:
    actual = hashlib.sha256(path.read_bytes()).hexdigest()
    if actual != expected_sha256:
        raise RuntimeError(f"checksum mismatch for {path.name}: expected {expected_sha256}, got {actual}")


def run_public_sample_evaluation(corpus_dir: Path, output_dir: Path, *, overwrite: bool = False) -> dict[str, object]:
    fetch_public_samples(corpus_dir, overwrite=overwrite)
    return evaluate_corpus(
        corpus_dir,
        output_dir,
        summary_title="公開サンプル文書評価サマリー",
        bar_label="10〜30本公開サンプル評価・失敗0件の基準",
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Download public Office/PDF samples and run the local conversion evaluator.")
    parser.add_argument("--corpus", type=Path, default=Path("public-sample-corpus"))
    parser.add_argument("--out", type=Path, default=Path("public-sample-evaluation-output"))
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()

    summary = run_public_sample_evaluation(args.corpus, args.out, overwrite=args.overwrite)
    print(json.dumps(summary, ensure_ascii=False))
    raise SystemExit(0 if summary["meets_private_corpus_bar"] else 1)


if __name__ == "__main__":
    main()
