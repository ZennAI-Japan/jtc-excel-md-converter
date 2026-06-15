from __future__ import annotations

from pathlib import Path
from typing import Any

try:  # pragma: no cover - import availability is covered through CLI tests
    import pymupdf
except Exception:  # pragma: no cover
    pymupdf = None  # type: ignore[assignment]

MAX_PDF_BYTES = 50_000_000
MAX_PAGES = 200


def convert_pdf_document(path: str | Path) -> dict[str, Any]:
    pdf_path = Path(path)
    if pymupdf is None:
        raise RuntimeError("PDF support requires PyMuPDF. Install with `pip install -e .` or `pip install PyMuPDF`.")
    if pdf_path.stat().st_size > MAX_PDF_BYTES:
        raise ValueError("PDF file is too large to parse safely")

    document = pymupdf.open(pdf_path)
    try:
        if document.page_count > MAX_PAGES:
            raise ValueError("PDF has too many pages to parse safely")
        pages: list[dict[str, Any]] = []
        images: list[dict[str, Any]] = []
        for index in range(1, document.page_count + 1):
            page = document.load_page(index - 1)
            text = str(page.get_text("text")).strip()
            page_images = page.get_images(full=True)
            pages.append({"index": index, "text": text, "image_count": len(page_images)})
            for image_index, image in enumerate(page_images, start=1):
                images.append({"page": index, "index": image_index, "xref": int(image[0])})
    finally:
        document.close()

    warnings = []
    if any(page["image_count"] for page in pages):
        warnings.append("PDF内の画像はプレースホルダーとして検出しました。必要に応じてOCRまたは人手確認を行ってください。")
    markdown = _render_pdf_markdown(pages, images)
    return {
        "source": str(pdf_path),
        "source_type": "pdf_document",
        "sheets": [],
        "document": {"pages": pages, "images": images},
        "markdown": markdown,
        "warnings": warnings,
    }


def _render_pdf_markdown(pages: list[dict[str, Any]], images: list[dict[str, Any]]) -> str:
    lines: list[str] = []
    first_text = next((str(page.get("text") or "").splitlines()[0].strip() for page in pages if page.get("text")), "PDF変換結果")
    lines.extend([f"# {first_text}", ""])
    for page in pages:
        lines.extend([f"## ページ {page['index']}", ""])
        text = str(page.get("text") or "").strip()
        lines.append(text if text else "（抽出できるテキストはありません）")
        lines.append("")
        if page.get("image_count"):
            lines.append(f"- 画像プレースホルダー: {page['image_count']}件")
            lines.append("")
    if images:
        lines.extend(["## 画像プレースホルダー", ""])
        for image in images:
            lines.append(f"- ページ{image['page']} / 画像{image['index']} / xref {image['xref']}")
    return "\n".join(lines).strip()
