from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path
from urllib.request import urlopen

BANNED_VISIBLE_PHRASES = [
    "ミラ口調",
    "開発都合",
    "内部メモ",
    "Excelの代替",
    "Excelではできない",
    "安い比較",
    "DEMO-",
    "テスト用",
]
REQUIRED_VISIBLE_PHRASES = [
    "設計書ドキュメント化プラットフォーム",
    "関西電力様向け",
    "ローカル解析",
    "book_specification.md",
    "warnings.md",
]


def main() -> None:
    parser = argparse.ArgumentParser(description="Smoke-test the local demo UI and capture a screenshot.")
    parser.add_argument("--input", default="examples/jtc_screen_design.xlsx")
    parser.add_argument("--out", default="outputs/demo-ui-smoke")
    parser.add_argument("--port", type=int, default=8766)
    parser.add_argument("--screenshot", default="outputs/demo-ui-smoke.png")
    args = parser.parse_args()

    root = Path.cwd()
    screenshot = root / args.screenshot
    screenshot.parent.mkdir(parents=True, exist_ok=True)
    url = f"http://127.0.0.1:{args.port}/"

    process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "jtc_excel_md.demo_server",
            args.input,
            "--out",
            args.out,
            "--host",
            "127.0.0.1",
            "--port",
            str(args.port),
        ],
        cwd=root,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        env={**dict(__import__("os").environ), "PYTHONPATH": str(root / "src")},
    )
    try:
        body = _wait_for_body(url, process)
        for phrase in REQUIRED_VISIBLE_PHRASES:
            assert phrase in body, f"missing visible phrase: {phrase}"
        for phrase in BANNED_VISIBLE_PHRASES:
            assert phrase not in body, f"banned visible phrase: {phrase}"

        subprocess.run(
            [
                "npx",
                "-y",
                "playwright",
                "screenshot",
                "--viewport-size=1440,1100",
                url,
                str(screenshot),
            ],
            check=True,
            cwd=root,
        )
        assert screenshot.exists() and screenshot.stat().st_size > 100_000, screenshot
        print(f"demo_ui_smoke=ok url={url} screenshot={screenshot} bytes={screenshot.stat().st_size}")
    finally:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()


def _wait_for_body(url: str, process: subprocess.Popen[str]) -> str:
    last_error: Exception | None = None
    for _ in range(40):
        if process.poll() is not None:
            output = process.stdout.read() if process.stdout else ""
            raise RuntimeError(f"demo server exited early with {process.returncode}: {output}")
        try:
            with urlopen(url, timeout=2) as response:
                return response.read().decode("utf-8")
        except Exception as exc:  # noqa: BLE001 - retry startup race
            last_error = exc
            time.sleep(0.25)
    raise RuntimeError(f"demo server did not become ready: {last_error}")


if __name__ == "__main__":
    main()
