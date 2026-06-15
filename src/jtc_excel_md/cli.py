from __future__ import annotations

import argparse
import json
import urllib.error
import urllib.request
from json import JSONDecodeError
from collections.abc import Sequence
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

from .ai_config import load_ai_config
from .ai_providers import AIRequest, build_ai_provider
from .ai_restructure import restructure_output_dir
from .converter import convert_workbook, write_outputs
from .pdf_converter import convert_pdf_document
from .word_converter import convert_word_document


def main() -> None:
    raise SystemExit(run())


def run(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Convert JTC-style Excel/Word design docs to Markdown/JSON.")
    parser.add_argument("input", type=Path, help="Input .xlsx/.xlsm/.docx file")
    parser.add_argument("--out", type=Path, required=True, help="Output directory")
    parser.add_argument("--ai-env-file", type=Path, help="Optional .env file for bring-your-own-AI settings")
    parser.add_argument("--show-ai-config", action="store_true", help="Print a secret-masked AI configuration summary")
    parser.add_argument(
        "--ai-restructure",
        action="store_true",
        help="Call the configured OpenAI-compatible/Codex endpoint and write reviewable AI-restructured Markdown",
    )
    args = parser.parse_args(argv)

    result = convert_input_document(args.input)
    ai_config = None
    if args.ai_env_file or args.show_ai_config or args.ai_restructure:
        ai_config = load_ai_config(env_file=args.ai_env_file)
        ai_summary = _public_ai_summary(ai_config.safe_summary())
        result["ai"] = ai_summary
        if args.show_ai_config:
            print(f"ai: {ai_summary}")
    write_outputs(result, args.out)
    if args.ai_restructure:
        assert ai_config is not None
        ai_result = restructure_output_dir(args.out, provider=build_ai_provider(ai_config, http_post=_http_post_json))
        print(f"wrote: {args.out / 'ai_restructure.json'}")
        if ai_result.get("wrote"):
            print(f"wrote: {args.out / 'ai_restructured_specification.md'}")
        print(f"wrote: {args.out / 'ai_restructure_warnings.md'}")
    print(f"wrote: {args.out / 'extracted.json'}")
    print(f"wrote: {args.out / 'book_specification.md'}")
    print(f"wrote: {args.out / 'specification.md'}")
    print(f"wrote: {args.out / 'warnings.md'}")
    print(f"wrote: {args.out / 'preview.html'}")
    print(f"wrote: {args.out / 'evaluation.md'}")
    print(f"wrote: {args.out / 'package.zip'}")
    return 0


def convert_input_document(path: Path) -> dict[str, object]:
    suffix = path.suffix.lower()
    if suffix in {".xlsx", ".xlsm", ".xltx", ".xltm"}:
        result = convert_workbook(path)
        result.setdefault("source_type", "excel_workbook")
        return result
    if suffix == ".docx":
        return convert_word_document(path)
    if suffix == ".pdf":
        return convert_pdf_document(path)
    raise ValueError(f"Unsupported input file type: {suffix or '<none>'}")


def _http_post_json(request: AIRequest) -> dict[str, object]:
    data = request.body.encode("utf-8")
    http_request = urllib.request.Request(
        request.url,
        data=data,
        method=request.method,
        headers=request.headers,
    )
    try:
        with urllib.request.urlopen(http_request, timeout=60) as response:  # noqa: S310 - user-configured BYOK endpoint
            payload = response.read(5_000_000).decode("utf-8")
        parsed = json.loads(payload)
    except urllib.error.URLError as exc:
        return {"choices": [], "warnings": [f"AI endpoint request failed: {exc.reason}"]}
    except (JSONDecodeError, UnicodeDecodeError) as exc:
        return {"choices": [], "warnings": [f"AI endpoint returned invalid JSON: {exc}"]}
    return parsed if isinstance(parsed, dict) else {"choices": [], "warnings": ["AI endpoint returned non-object JSON."]}


def _public_ai_summary(summary: dict[str, str | bool | None]) -> dict[str, str | bool | None]:
    """Return artifact-safe AI settings without raw or key-derived secret material."""
    return {
        "enabled": summary["enabled"],
        "provider": summary["provider"],
        "model": summary["model"],
        "base_url": _safe_base_url(summary["base_url"]),
        "api_key_configured": bool(summary["api_key"]),
    }


def _safe_base_url(base_url: str | bool | None) -> str | None:
    if not isinstance(base_url, str) or not base_url:
        return None
    candidate = base_url.strip()
    if candidate.startswith("//"):
        candidate = f"https:{candidate}"
    elif "://" not in candidate and "@" in candidate:
        candidate = f"https://{candidate}"
    try:
        parsed = urlsplit(candidate)
    except ValueError:
        return None
    if not parsed.scheme or not parsed.hostname:
        if "@" in parsed.netloc or "@" in candidate.split("/", 1)[0]:
            return None
        return candidate.split("?", 1)[0].split("#", 1)[0]
    hostname = parsed.hostname
    if ":" in hostname and not hostname.startswith("["):
        hostname = f"[{hostname}]"
    try:
        port = parsed.port
    except ValueError:
        port = None
    netloc = hostname if port is None else f"{hostname}:{port}"
    return urlunsplit((parsed.scheme, netloc, parsed.path, "", ""))


if __name__ == "__main__":
    main()
