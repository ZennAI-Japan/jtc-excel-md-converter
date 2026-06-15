from __future__ import annotations

import zipfile
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET

W_NS = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
MAX_DOCUMENT_XML_BYTES = 5_000_000
MAX_COMPRESSION_RATIO = 100


def convert_word_document(path: str | Path) -> dict[str, Any]:
    """Convert a Word .docx document into structured JSON plus Markdown.

    This intentionally uses deterministic OOXML extraction first. AI/MarkItDown-style
    rewriting can be layered on top later, but the baseline keeps document content local
    and reviewable.
    """
    document_path = Path(path)
    root = _load_document_xml(document_path)
    body = root.find(f"{W_NS}body")
    if body is None:
        return _empty_result(document_path, ["Word document body was not found."])

    paragraphs: list[dict[str, str | int | None]] = []
    tables: list[dict[str, Any]] = []
    textboxes: list[dict[str, str | int]] = []
    images: list[dict[str, str | int]] = []
    ordered_blocks: list[dict[str, Any]] = []

    for child in list(body):
        if child.tag == f"{W_NS}p":
            for textbox_text in _paragraph_textboxes(child):
                textbox = {"index": len(textboxes) + 1, "text": textbox_text}
                textboxes.append(textbox)
                ordered_blocks.append({"type": "textbox", "textbox": textbox})
            for image_name in _paragraph_image_names(child):
                image = {"index": len(images) + 1, "name": image_name}
                images.append(image)
                ordered_blocks.append({"type": "image", "image": image})
            text = _paragraph_text(child)
            if not text:
                continue
            paragraph = {"index": len(paragraphs) + 1, "style": _paragraph_style(child), "text": text}
            paragraphs.append(paragraph)
            ordered_blocks.append({"type": "paragraph", "paragraph": paragraph})
        elif child.tag == f"{W_NS}tbl":
            for textbox_text in _element_textboxes(child):
                textbox = {"index": len(textboxes) + 1, "text": textbox_text}
                textboxes.append(textbox)
                ordered_blocks.append({"type": "textbox", "textbox": textbox})
            for image_name in _element_image_names(child):
                image = {"index": len(images) + 1, "name": image_name}
                images.append(image)
                ordered_blocks.append({"type": "image", "image": image})
            rows = _table_rows(child)
            if not rows:
                continue
            table = {"index": len(tables) + 1, "rows": rows}
            tables.append(table)
            ordered_blocks.append({"type": "table", "table": table})

    warnings = []
    if textboxes:
        warnings.append("Word内のテキストボックスを抽出しました。本文との順序や重なりは人手確認してください。")
    if images:
        warnings.append("Word内の画像プレースホルダーを検出しました。必要に応じて画像内容を人手確認してください。")
    markdown = _render_word_markdown(ordered_blocks)
    return {
        "source": str(document_path),
        "source_type": "word_document",
        "sheets": [],
        "document": {
            "paragraphs": paragraphs,
            "tables": tables,
            "textboxes": textboxes,
            "images": images,
        },
        "markdown": markdown,
        "warnings": warnings,
    }


def _load_document_xml(path: Path) -> ET.Element:
    with zipfile.ZipFile(path) as docx:
        try:
            info = docx.getinfo("word/document.xml")
        except KeyError as exc:
            raise ValueError("DOCX archive is missing word/document.xml") from exc
        if info.file_size > MAX_DOCUMENT_XML_BYTES:
            raise ValueError("word/document.xml is too large to parse safely")
        if info.compress_size and info.file_size / info.compress_size > MAX_COMPRESSION_RATIO:
            raise ValueError("word/document.xml compression ratio is too high to parse safely")
        xml_bytes = docx.read(info)
    return ET.fromstring(xml_bytes)


def _empty_result(path: Path, warnings: list[str]) -> dict[str, Any]:
    return {
        "source": str(path),
        "source_type": "word_document",
        "sheets": [],
        "document": {"paragraphs": [], "tables": [], "textboxes": [], "images": []},
        "markdown": "",
        "warnings": warnings,
    }


def _paragraph_text(paragraph: ET.Element) -> str:
    parts: list[str] = []
    _append_visible_text(paragraph, parts, in_textbox=False)
    return "".join(parts).strip()


def _append_visible_text(element: ET.Element, parts: list[str], *, in_textbox: bool) -> None:
    now_in_textbox = in_textbox or element.tag == f"{W_NS}txbxContent"
    if now_in_textbox:
        for child in list(element):
            _append_visible_text(child, parts, in_textbox=True)
        return
    if element.tag == f"{W_NS}t":
        parts.append(element.text or "")
    elif element.tag == f"{W_NS}tab":
        parts.append("\t")
    elif element.tag in {f"{W_NS}br", f"{W_NS}cr"}:
        parts.append("\n")
    for child in list(element):
        _append_visible_text(child, parts, in_textbox=False)


def _paragraph_textboxes(paragraph: ET.Element) -> list[str]:
    return _element_textboxes(paragraph)


def _element_textboxes(element: ET.Element) -> list[str]:
    boxes: list[str] = []
    for content in element.iter(f"{W_NS}txbxContent"):
        text = "".join(node.text or "" for node in content.iter(f"{W_NS}t")).strip()
        if text:
            boxes.append(text)
    return boxes


def _paragraph_image_names(paragraph: ET.Element) -> list[str]:
    return _element_image_names(paragraph)


def _element_image_names(element: ET.Element) -> list[str]:
    if not any(_local_name(child.tag) in {"drawing", "pict"} for child in element.iter()):
        return []
    names: list[str] = []
    for child in element.iter():
        if _local_name(child.tag) == "cNvPr":
            name = child.attrib.get("name")
            if name and name not in names:
                names.append(name)
    return names or (["画像"] if any(_local_name(child.tag) == "drawing" for child in element.iter()) else [])


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _paragraph_style(paragraph: ET.Element) -> str | None:
    style = paragraph.find(f"{W_NS}pPr/{W_NS}pStyle")
    if style is None:
        return None
    return style.attrib.get(f"{W_NS}val")


def _table_rows(table: ET.Element) -> list[list[str]]:
    rows: list[list[str]] = []
    for row in table.findall(f"{W_NS}tr"):
        cells = [_cell_text(cell) for cell in row.findall(f"{W_NS}tc")]
        if any(cells):
            rows.append(cells)
    return rows


def _cell_text(cell: ET.Element) -> str:
    paragraphs = [_paragraph_text(paragraph) for paragraph in cell.findall(f"{W_NS}p")]
    return "\n".join(paragraph for paragraph in paragraphs if paragraph).strip()


def _render_word_markdown(blocks: list[dict[str, Any]]) -> str:
    lines: list[str] = []
    for block in blocks:
        if block["type"] == "paragraph":
            paragraph = block["paragraph"]
            text = str(paragraph["text"])
            style = paragraph.get("style")
            if isinstance(style, str) and style.lower().startswith("heading"):
                level_text = "".join(ch for ch in style if ch.isdigit())
                level = min(max(int(level_text or "1"), 1), 6)
                lines.append(f"{'#' * level} {text}")
            else:
                lines.append(text)
            lines.append("")
        elif block["type"] == "table":
            rows = block["table"]["rows"]
            lines.extend(_render_table(rows))
            lines.append("")
        elif block["type"] == "textbox":
            textbox = block["textbox"]
            lines.append(f"> テキストボックス: {textbox['text']}")
            lines.append("")
        elif block["type"] == "image":
            image = block["image"]
            lines.append(f"![画像プレースホルダー: {image['name']}](#)")
            lines.append("")
    return "\n".join(lines).strip()


def _render_table(rows: list[list[str]]) -> list[str]:
    if not rows:
        return []
    width = max(len(row) for row in rows)
    normalized = [row + [""] * (width - len(row)) for row in rows]
    header = normalized[0]
    lines = [
        "| " + " | ".join(_escape_md(cell) for cell in header) + " |",
        "| " + " | ".join("---" for _ in header) + " |",
    ]
    for row in normalized[1:]:
        lines.append("| " + " | ".join(_escape_md(cell) for cell in row) + " |")
    return lines


def _escape_md(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", "<br>")
