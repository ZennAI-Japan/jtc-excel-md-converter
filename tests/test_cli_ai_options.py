from __future__ import annotations

import json
import zipfile
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Border, Side


def _write_minimal_workbook(path: Path) -> None:
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "画面設計"
    sheet["A1"] = "項目"
    sheet["B1"] = "内容"
    sheet["A2"] = "画面名"
    sheet["B2"] = "ログイン"
    thin = Side(style="thin")
    border = Border(left=thin, right=thin, top=thin, bottom=thin)
    for row in sheet["A1:B2"]:
        for cell in row:
            cell.border = border
    workbook.save(path)


def test_cli_can_load_ai_env_file_and_write_safe_ai_summary(tmp_path: Path, capsys):
    from jtc_excel_md.cli import run

    workbook_path = tmp_path / "screen.xlsx"
    output_dir = tmp_path / "out"
    env_file = tmp_path / ".env"
    _write_minimal_workbook(workbook_path)
    raw_api_key = "-".join(["super", "secret", "test", "key"])
    masked_api_key = "sup" + "...-" + "key"
    env_file.write_text(
        "\n".join(
            [
                "JTC_AI_PROVIDER=openai-compatible",
                f"JTC_AI_API_KEY={raw_api_key}",
                "JTC_AI_BASE_URL=https://user:pass@example.com/v1?api_key=url-secret&debug=true",
                "JTC_AI_MODEL=qwen2.5-coder:7b",
            ]
        ),
        encoding="utf-8",
    )

    exit_code = run([str(workbook_path), "--out", str(output_dir), "--ai-env-file", str(env_file), "--show-ai-config"])

    captured = capsys.readouterr().out
    payload = json.loads((output_dir / "extracted.json").read_text(encoding="utf-8"))
    evaluation = (output_dir / "evaluation.md").read_text(encoding="utf-8")
    with zipfile.ZipFile(output_dir / "package.zip") as package:
        packaged_text = "\n".join(
            package.read(name).decode("utf-8")
            for name in package.namelist()
            if name.endswith((".json", ".md"))
        )

    assert exit_code == 0
    assert "openai-compatible" in captured
    assert "api_key_configured" in captured
    assert masked_api_key not in captured
    assert raw_api_key not in captured
    assert "user:pass" not in captured
    assert "url-secret" not in captured
    assert payload["ai"] == {
        "enabled": True,
        "provider": "openai-compatible",
        "model": "qwen2.5-coder:7b",
        "base_url": "https://example.com/v1",
        "api_key_configured": True,
    }
    assert "## AI Configuration" in evaluation
    assert "openai-compatible" in evaluation
    extracted_text = (output_dir / "extracted.json").read_text(encoding="utf-8")
    assert raw_api_key not in extracted_text
    assert masked_api_key not in extracted_text
    assert "user:pass" not in (output_dir / "extracted.json").read_text(encoding="utf-8")
    assert "url-secret" not in (output_dir / "extracted.json").read_text(encoding="utf-8")
    assert raw_api_key not in evaluation
    assert masked_api_key not in evaluation
    assert "user:pass" not in evaluation
    assert "url-secret" not in evaluation
    assert raw_api_key not in packaged_text
    assert masked_api_key not in packaged_text
    assert "user:pass" not in packaged_text
    assert "url-secret" not in packaged_text


def test_cli_stays_deterministic_without_ai_env_file(tmp_path: Path):
    from jtc_excel_md.cli import run

    workbook_path = tmp_path / "screen.xlsx"
    output_dir = tmp_path / "out"
    _write_minimal_workbook(workbook_path)

    exit_code = run([str(workbook_path), "--out", str(output_dir)])

    payload = json.loads((output_dir / "extracted.json").read_text(encoding="utf-8"))
    evaluation = (output_dir / "evaluation.md").read_text(encoding="utf-8")

    assert exit_code == 0
    assert "ai" not in payload
    assert "## AI Configuration" not in evaluation


def test_safe_base_url_removes_userinfo_queries_and_invalid_ports():
    from jtc_excel_md.cli import _safe_base_url

    assert _safe_base_url("//user:pass@example.com/v1?api_key=url-secret") == "https://example.com/v1"
    assert _safe_base_url("user:pass@example.com/v1?api_key=url-secret") == "https://example.com/v1"
    assert _safe_base_url("https://example.com:abc/v1?token=url-secret") == "https://example.com/v1"
    assert _safe_base_url("https://user:pass@/v1?api_key=url-secret") is None
    assert _safe_base_url("user:pass@/v1?api_key=url-secret") is None
    assert _safe_base_url("https://[::1]:11434/v1?token=url-secret") == "https://[::1]:11434/v1"
    assert _safe_base_url("https://[::1:11434/v1?token=url-secret") is None
