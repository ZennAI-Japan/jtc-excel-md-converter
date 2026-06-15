from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

DOCS_TO_KEEP_JAPANESE = [
    Path("README.md"),
    Path("CONTRIBUTING.md"),
    Path("SECURITY.md"),
    Path("DESIGN.md"),
    *Path("docs").glob("*.md"),
]

ENGLISH_DOC_PHRASES = [
    "Quick start",
    "Docker quick start",
    "AI provider configuration",
    "Local demo UI",
    "Security Policy",
    "Supported versions",
    "Reporting a vulnerability",
    "Public Release Checklist",
    "OSS + Bring-Your-Own-AI Roadmap",
    "Current foundation in this PR",
    "Acceptance Criteria",
    "Source of Truth",
    "Final Verification Gate",
    "Must Read",
    "Product Direction",
    "Suggested First Goal",
    "Current Verified Baseline",
    "Do Not",
    "Overview",
    "Colors",
    "Typography",
    "Layout",
    "Do's and Don'ts",
]


def test_user_facing_documentation_is_japanese_first():
    for path in DOCS_TO_KEEP_JAPANESE:
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        for phrase in ENGLISH_DOC_PHRASES:
            assert phrase not in text, f"{path} still contains English docs phrase: {phrase}"


def test_readme_embeds_zundamon_demo_video():
    text = Path("README.md").read_text(encoding="utf-8")
    assert "docs/assets/demo-zundamon.mp4" in text
    assert "ずんだもん" in text
    assert Path("docs/assets/demo-zundamon.mp4").exists()


def test_zundamon_demo_video_is_small_and_has_audio_video_streams():
    if shutil.which("ffprobe") is None:
        pytest.skip("ffprobe is required to inspect the embedded demo video")
    video = Path("docs/assets/demo-zundamon.mp4")
    assert video.stat().st_size <= 2_000_000
    probe = subprocess.check_output(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_streams",
            "-of",
            "json",
            str(video),
        ],
        text=True,
    )
    streams = json.loads(probe)["streams"]
    assert any(s.get("codec_type") == "video" and s.get("width") == 1280 and s.get("height") == 720 for s in streams)
    assert any(s.get("codec_type") == "audio" and s.get("codec_name") == "aac" for s in streams)
