from __future__ import annotations

from pathlib import Path


def test_docker_assets_define_reproducible_cli_runtime():
    root = Path(__file__).resolve().parents[1]
    dockerfile = root / "Dockerfile"
    compose = root / "compose.yaml"
    smoke = root / "scripts" / "docker_smoke.sh"

    assert dockerfile.exists()
    dockerfile_text = dockerfile.read_text(encoding="utf-8")
    assert "python:3.12-slim" in dockerfile_text
    assert "pip install --no-cache-dir '.[pdf]'" in dockerfile_text
    assert "USER app" in dockerfile_text
    assert 'ENTRYPOINT ["jtc-md-convert"]' in dockerfile_text

    assert compose.exists()
    compose_text = compose.read_text(encoding="utf-8")
    assert "jtc-md-converter:" in compose_text
    assert 'user: "${UID:-1000}:${GID:-1000}"' in compose_text
    assert "./examples:/work/examples:ro" in compose_text
    assert "./outputs:/work/outputs" in compose_text

    assert smoke.exists()
    smoke_text = smoke.read_text(encoding="utf-8")
    assert "docker build" in smoke_text
    assert "jtc-md-convert" in smoke_text
    assert "examples/jtc_screen_design.xlsx" in smoke_text
    assert "test -s outputs/docker-smoke/extracted.json" in smoke_text
