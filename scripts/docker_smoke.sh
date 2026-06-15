#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")/.."

IMAGE="${IMAGE:-jtc-excel-md-converter:local}"
OUT_DIR="outputs/docker-smoke"

mkdir -p outputs
rm -rf "${OUT_DIR}"

docker build -t "${IMAGE}" .

docker run --rm \
  --user "$(id -u):$(id -g)" \
  --workdir /work \
  -v "${PWD}/examples:/work/examples:ro" \
  -v "${PWD}/outputs:/work/outputs" \
  --entrypoint jtc-md-convert \
  "${IMAGE}" \
  examples/jtc_screen_design.xlsx --out "${OUT_DIR}"

test -s outputs/docker-smoke/extracted.json
test -s outputs/docker-smoke/book_specification.md
test -s outputs/docker-smoke/preview.html
test -s outputs/docker-smoke/evaluation.md
test -s outputs/docker-smoke/package.zip

printf 'docker_smoke=ok image=%s out=%s\n' "${IMAGE}" "${OUT_DIR}"
