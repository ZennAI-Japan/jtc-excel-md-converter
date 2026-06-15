from __future__ import annotations

import argparse
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


@dataclass(frozen=True)
class PublicSample:
    filename: str
    url: str
    source: str
    note: str


PUBLIC_SAMPLES: tuple[PublicSample, ...] = (
    PublicSample(
        "pandas-test1.xlsx",
        "https://raw.githubusercontent.com/pandas-dev/pandas/main/pandas/tests/io/data/excel/test1.xlsx",
        "pandas-dev/pandas",
        "Excel parser regression workbook used by pandas tests.",
    ),
    PublicSample(
        "pandas-test2.xlsx",
        "https://raw.githubusercontent.com/pandas-dev/pandas/main/pandas/tests/io/data/excel/test2.xlsx",
        "pandas-dev/pandas",
        "Excel parser regression workbook used by pandas tests.",
    ),
    PublicSample(
        "pandas-test3.xlsx",
        "https://raw.githubusercontent.com/pandas-dev/pandas/main/pandas/tests/io/data/excel/test3.xlsx",
        "pandas-dev/pandas",
        "Excel parser regression workbook used by pandas tests.",
    ),
    PublicSample(
        "pandas-test4.xlsx",
        "https://raw.githubusercontent.com/pandas-dev/pandas/main/pandas/tests/io/data/excel/test4.xlsx",
        "pandas-dev/pandas",
        "Excel parser regression workbook used by pandas tests.",
    ),
    PublicSample(
        "pandas-test5.xlsx",
        "https://raw.githubusercontent.com/pandas-dev/pandas/main/pandas/tests/io/data/excel/test5.xlsx",
        "pandas-dev/pandas",
        "Excel parser regression workbook used by pandas tests.",
    ),
    PublicSample(
        "pandas-multisheet.xlsx",
        "https://raw.githubusercontent.com/pandas-dev/pandas/main/pandas/tests/io/data/excel/test_multisheet.xlsx",
        "pandas-dev/pandas",
        "Multi-sheet Excel workbook.",
    ),
    PublicSample(
        "pandas-spaces.xlsx",
        "https://raw.githubusercontent.com/pandas-dev/pandas/main/pandas/tests/io/data/excel/test_spaces.xlsx",
        "pandas-dev/pandas",
        "Excel workbook with spacing edge cases.",
    ),
    PublicSample(
        "pandas-converters.xlsx",
        "https://raw.githubusercontent.com/pandas-dev/pandas/main/pandas/tests/io/data/excel/test_converters.xlsx",
        "pandas-dev/pandas",
        "Excel workbook with mixed cell values for converter tests.",
    ),
    PublicSample(
        "calibre-demo.docx",
        "https://calibre-ebook.com/downloads/demos/demo.docx",
        "calibre-ebook.com",
        "Public DOCX demo document.",
    ),
    PublicSample(
        "w3c-dummy.pdf",
        "https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf",
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
            status = "exists"
        else:
            _download(sample.url, destination)
            status = "downloaded"
        manifest.append(
            {
                "filename": sample.filename,
                "url": sample.url,
                "source": sample.source,
                "note": sample.note,
                "status": status,
            }
        )
    (corpus_dir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return manifest


def _download(url: str, destination: Path) -> None:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        raise ValueError(f"unsupported URL scheme: {url}")
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    tmp = destination.with_suffix(destination.suffix + ".tmp")
    with urllib.request.urlopen(request, timeout=60) as response, tmp.open("wb") as handle:  # noqa: S310 - fixed public manifest URLs
        shutil.copyfileobj(response, handle)
    if tmp.stat().st_size == 0:
        tmp.unlink(missing_ok=True)
        raise RuntimeError(f"downloaded empty file: {url}")
    tmp.replace(destination)


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
