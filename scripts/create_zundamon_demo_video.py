from __future__ import annotations

import json
import subprocess
import tempfile
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, cast

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "assets" / "demo-zundamon.mp4"
VOICEVOX_URL = "http://127.0.0.1:50021"
SPEAKER_ID = 3  # ずんだもん ノーマル。生成前に /speakers で確認する。
WIDTH = 1280
HEIGHT = 720
FPS = 30

SCRIPT = [
    {
        "title": "WordとExcel設計書を、Markdownへ。",
        "body": "JTC Excel MD Converterは、企業に残る設計書をローカルで変換するツールなのだ。",
        "voice": "JTC Excel MD Converterは、企業に残るワードとエクセル設計書を、ローカルでMarkdownへ変換するツールなのだ。",
    },
    {
        "title": "罫線・結合セル・表をそのまま確認。",
        "body": "Markdown、JSON、レビュー用HTML、warningsをまとめて出力します。",
        "voice": "Markdown、JSON、レビュー用HTML、ワーニングをまとめて出力するのだ。",
    },
    {
        "title": "AI連携は任意。既定はローカル処理。",
        "body": "CodexやローカルLLMは、利用者が明示的に設定した場合だけ使います。",
        "voice": "AI連携は任意なのだ。CodexやローカルLLMは、利用者が明示的に設定した場合だけ使うのだ。",
    },
    {
        "title": "Dockerで、どこでも同じ変換体験。",
        "body": "Docker runとComposeの両方で、成果物生成まで確認できます。",
        "voice": "Dockerで、どこでも同じ変換体験なのだ。Docker runとComposeの両方で、成果物生成まで確認できるのだ。",
    },
]


def _request_json(path: str, *, method: str = "GET", data: bytes | None = None) -> Any:
    req = urllib.request.Request(VOICEVOX_URL + path, data=data, method=method)
    if data is not None:
        req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req, timeout=60) as res:
        return json.loads(res.read().decode("utf-8"))


def verify_zundamon() -> None:
    speakers = _request_json("/speakers")
    for speaker in speakers:
        if speaker.get("name") == "ずんだもん":
            ids = {style["id"] for style in speaker.get("styles", [])}
            if SPEAKER_ID in ids:
                return
    raise RuntimeError("VOICEVOXでずんだもん speaker id=3 を確認できませんでした")


def synthesize(text: str, wav_path: Path) -> None:
    query_path = f"/audio_query?text={urllib.parse.quote(text)}&speaker={SPEAKER_ID}"
    query = cast(dict[str, Any], _request_json(query_path, method="POST", data=b""))
    query["speedScale"] = 1.08
    query["prePhonemeLength"] = 0.08
    query["postPhonemeLength"] = 0.08
    synth_path = f"/synthesis?speaker={SPEAKER_ID}"
    req = urllib.request.Request(
        VOICEVOX_URL + synth_path,
        data=json.dumps(query).encode("utf-8"),
        method="POST",
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=120) as res:
        wav_path.write_bytes(res.read())


def font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        "/System/Library/Fonts/ヒラギノ角ゴシック W6.ttc",
        "/System/Library/Fonts/ヒラギノ角ゴシック W4.ttc",
        "/Library/Fonts/Arial Unicode.ttf",
    ]
    for candidate in candidates:
        p = Path(candidate)
        if p.exists():
            return ImageFont.truetype(str(p), size=size)
    return ImageFont.load_default()


def wrap(draw: ImageDraw.ImageDraw, text: str, font_obj: ImageFont.ImageFont, max_width: int) -> list[str]:
    lines: list[str] = []
    current = ""
    for ch in text:
        candidate = current + ch
        if draw.textbbox((0, 0), candidate, font=font_obj)[2] <= max_width:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = ch
    if current:
        lines.append(current)
    return lines


def make_slide(index: int, title: str, body: str, path: Path) -> None:
    img = Image.new("RGB", (WIDTH, HEIGHT), "#F5F8FB")
    draw = ImageDraw.Draw(img)
    title_font = font(58)
    body_font = font(34)
    label_font = font(24)
    draw.rectangle((0, 0, WIDTH, 88), fill="#0051A2")
    draw.text((56, 28), "JTC Excel MD Converter", fill="white", font=label_font)
    draw.rounded_rectangle((56, 150, WIDTH - 56, HEIGHT - 90), radius=28, fill="white", outline="#D8E0EA", width=3)
    draw.text((100, 205), title, fill="#172033", font=title_font)
    y = 330
    for line in wrap(draw, body, body_font, WIDTH - 220):
        draw.text((105, y), line, fill="#344054", font=body_font)
        y += 54
    draw.rounded_rectangle((100, 555, 310, 610), radius=16, fill="#FFF4EB")
    draw.text((124, 568), f"{index + 1}/4 ローカル実行", fill="#8F3900", font=label_font)
    draw.text((WIDTH - 310, HEIGHT - 58), "ずんだもん音声デモ", fill="#5E6B7A", font=label_font)
    img.save(path)


def duration(path: Path) -> float:
    out = subprocess.check_output([
        "ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", str(path)
    ], text=True)
    return float(out.strip())


def main() -> None:
    verify_zundamon()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        parts: list[Path] = []
        for index, item in enumerate(SCRIPT):
            png = tmp / f"slide_{index}.png"
            wav = tmp / f"voice_{index}.wav"
            mp4 = tmp / f"part_{index}.mp4"
            make_slide(index, item["title"], item["body"], png)
            synthesize(item["voice"], wav)
            subprocess.run([
                "ffmpeg", "-y", "-loop", "1", "-i", str(png), "-i", str(wav),
                "-t", f"{duration(wav) + 0.4:.2f}", "-vf", f"scale={WIDTH}:{HEIGHT},format=yuv420p",
                "-c:v", "libx264", "-preset", "veryfast", "-r", str(FPS),
                "-c:a", "aac", "-b:a", "128k", "-shortest", str(mp4)
            ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            parts.append(mp4)
        concat = tmp / "concat.txt"
        concat.write_text("".join(f"file '{p}'\n" for p in parts), encoding="utf-8")
        subprocess.run([
            "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat),
            "-c", "copy", str(OUT)
        ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print(f"wrote={OUT}")


if __name__ == "__main__":
    main()
