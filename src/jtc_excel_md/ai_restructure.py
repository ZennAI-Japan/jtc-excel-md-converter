from __future__ import annotations

import json
import zipfile
from pathlib import Path
from typing import Any

from .ai_providers import AIProvider


def restructure_output_dir(output_dir: str | Path, *, provider: AIProvider) -> dict[str, Any]:
    """Create reviewable AI-restructured Markdown beside deterministic outputs.

    The deterministic `book_specification.md` remains unchanged. This keeps AI output
    explicitly opt-in and reviewable before downstream use.
    """
    out = Path(output_dir)
    deterministic_path = out / "book_specification.md"
    if not deterministic_path.exists():
        raise FileNotFoundError("book_specification.md is required before AI restructuring")
    deterministic_markdown = deterministic_path.read_text(encoding="utf-8")
    extracted = _read_optional_text(out / "extracted.json")
    prompt = _build_restructure_prompt(deterministic_markdown, extracted)
    response = provider.rewrite_specification(prompt)

    warnings = list(response.warnings)
    if not response.content.strip():
        warnings.append("AI整形結果が空だったため、ai_restructured_specification.md は作成しませんでした。")
    else:
        (out / "ai_restructured_specification.md").write_text(response.content.strip() + "\n", encoding="utf-8")
    (out / "ai_restructure_warnings.md").write_text(
        "# AI整形レビュー\n\n" + "\n".join(f"- {warning}" for warning in warnings or ["要確認項目はありません。"]) + "\n",
        encoding="utf-8",
    )
    metadata = {"provider": response.provider, "warnings": warnings, "wrote": bool(response.content.strip())}
    (out / "ai_restructure.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    _append_ai_artifacts_to_package(out)
    return metadata


def _append_ai_artifacts_to_package(output_dir: Path) -> None:
    package = output_dir / "package.zip"
    if not package.exists():
        return
    for name in ["ai_restructured_specification.md", "ai_restructure_warnings.md", "ai_restructure.json"]:
        path = output_dir / name
        if not path.exists():
            continue
        with zipfile.ZipFile(package, "a", compression=zipfile.ZIP_DEFLATED) as archive:
            archive.write(path, arcname=name)


def _build_restructure_prompt(markdown: str, extracted_json: str) -> str:
    return "\n\n".join(
        [
            "以下はOffice文書から決定的に抽出した仕様です。事実・座標・警告を保持し、日本語Markdownとして読みやすく再構成してください。未確認事項は推測せず『要確認』と書いてください。",
            "## 決定的Markdown",
            markdown,
            "## 抽出JSON",
            extracted_json[:20_000],
        ]
    )


def _read_optional_text(path: Path) -> str:
    if not path.exists():
        return "{}"
    return path.read_text(encoding="utf-8")
