from __future__ import annotations

import argparse
from collections.abc import Sequence
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

from .ai_config import load_ai_config
from .converter import convert_workbook, write_outputs


def main() -> None:
    raise SystemExit(run())


def run(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Convert JTC-style Excel design docs to Markdown/JSON.")
    parser.add_argument("input", type=Path, help="Input .xlsx file")
    parser.add_argument("--out", type=Path, required=True, help="Output directory")
    parser.add_argument("--ai-env-file", type=Path, help="Optional .env file for bring-your-own-AI settings")
    parser.add_argument("--show-ai-config", action="store_true", help="Print a secret-masked AI configuration summary")
    args = parser.parse_args(argv)

    result = convert_workbook(args.input)
    if args.ai_env_file or args.show_ai_config:
        ai_config = load_ai_config(env_file=args.ai_env_file)
        ai_summary = _public_ai_summary(ai_config.safe_summary())
        result["ai"] = ai_summary
        if args.show_ai_config:
            print(f"ai: {ai_summary}")
    write_outputs(result, args.out)
    print(f"wrote: {args.out / 'extracted.json'}")
    print(f"wrote: {args.out / 'book_specification.md'}")
    print(f"wrote: {args.out / 'specification.md'}")
    print(f"wrote: {args.out / 'warnings.md'}")
    print(f"wrote: {args.out / 'preview.html'}")
    print(f"wrote: {args.out / 'evaluation.md'}")
    print(f"wrote: {args.out / 'package.zip'}")
    return 0


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
