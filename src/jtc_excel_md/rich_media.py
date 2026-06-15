from __future__ import annotations

import zipfile
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET

A_NS = "{http://schemas.openxmlformats.org/drawingml/2006/main}"
XDR_NS = "{http://schemas.openxmlformats.org/drawingml/2006/spreadsheetDrawing}"
PIC_NS = "{http://schemas.openxmlformats.org/drawingml/2006/picture}"
MAX_DRAWING_XML_BYTES = 2_000_000


def extract_xlsx_drawing_media(path: str | Path) -> dict[str, list[dict[str, str]]]:
    """Extract reviewable text/image placeholders from XLSX drawing XML.

    openpyxl intentionally focuses on cell/workbook structures. Enterprise design
    books often keep important notes in shapes/text boxes, so we inspect drawing XML
    directly and surface those items as warnings/review evidence.
    """
    workbook_path = Path(path)
    textboxes: list[dict[str, str]] = []
    images: list[dict[str, str]] = []
    shapes: list[dict[str, str]] = []
    try:
        archive = zipfile.ZipFile(workbook_path)
    except zipfile.BadZipFile:
        return {"textboxes": [], "images": [], "shapes": []}
    with archive:
        for name in sorted(archive.namelist()):
            if not name.startswith("xl/drawings/drawing") or not name.endswith(".xml"):
                continue
            info = archive.getinfo(name)
            if info.file_size > MAX_DRAWING_XML_BYTES:
                continue
            try:
                root = ET.fromstring(archive.read(info))
            except ET.ParseError:
                continue
            textboxes.extend(_extract_textboxes(root, name))
            images.extend(_extract_images(root, name))
            shapes.extend(_extract_shapes(root, name))
    return {"textboxes": textboxes, "images": images, "shapes": shapes}


def _extract_textboxes(root: ET.Element, drawing_name: str) -> list[dict[str, str]]:
    items: list[dict[str, str]] = []
    for shape in root.iter(f"{XDR_NS}sp"):
        text = "".join(node.text or "" for node in shape.iter(f"{A_NS}t")).strip()
        if not text:
            continue
        name = _named_child(shape, f"{XDR_NS}cNvPr") or "テキストボックス"
        items.append({"drawing": drawing_name, "name": name, "text": text})
    return items


def _extract_images(root: ET.Element, drawing_name: str) -> list[dict[str, str]]:
    items: list[dict[str, str]] = []
    for picture in list(root.iter(f"{XDR_NS}pic")) + list(root.iter(f"{PIC_NS}pic")):
        name = _named_child(picture, f"{XDR_NS}cNvPr") or _named_child(picture, f"{PIC_NS}cNvPr") or "画像"
        payload = {"drawing": drawing_name, "name": name}
        if payload not in items:
            items.append(payload)
    return items


def _extract_shapes(root: ET.Element, drawing_name: str) -> list[dict[str, str]]:
    items: list[dict[str, str]] = []
    for shape in list(root.iter(f"{XDR_NS}sp")) + list(root.iter(f"{XDR_NS}cxnSp")):
        text = "".join(node.text or "" for node in shape.iter(f"{A_NS}t")).strip()
        if text:
            continue
        name = _named_child(shape, f"{XDR_NS}cNvPr") or "図形"
        payload = {"drawing": drawing_name, "name": name}
        if payload not in items:
            items.append(payload)
    return items


def _named_child(element: ET.Element, tag: str) -> str | None:
    for child in element.iter(tag):
        value = child.attrib.get("name")
        if value:
            return value
    return None
