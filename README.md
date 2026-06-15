# JTC Excel MD Converter

日本企業で長く使われてきた Word / Excel 設計書を、Markdown・構造化JSON・レビュー用HTMLへ変換するローカルファーストのOSSです。

汎用変換だけでは落ちやすい、Excel方眼紙の罫線、結合セル、セル座標、入力規則、コメント、Word文書の見出し・段落・表を、AIが読みやすく人間が確認しやすい成果物として残します。

## できること

- Excel設計書をブック単位でMarkdown化
- Word `.docx` をMarkdown / JSON化
- 変換結果の根拠を確認できる `preview.html` を生成
- 要確認箇所を `warnings.md` に分離
- `package.zip` で成果物を一括取得
- AI連携は任意。未設定でも決定論的な変換は動作
- DockerでPython環境を作らずに実行可能

## ずんだもん音声つきデモ動画

<video controls src="docs/assets/demo-zundamon.mp4" title="JTC Excel MD Converter ずんだもんデモ"></video>

動画が表示されない場合は、こちらを直接開いてください。

[ずんだもんデモ動画を開く](docs/assets/demo-zundamon.mp4)

再生成する場合は、VOICEVOX Engineを `http://127.0.0.1:50021` で起動し、`ffmpeg` / `ffprobe` と `pillow` を使える状態で次を実行します。

```bash
pip install -e '.[video]'
python scripts/create_zundamon_demo_video.py
```

## ローカル実行

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
python -m pytest -q
jtc-md-convert examples/jtc_screen_design.xlsx --out outputs/jtc_screen_design
```

Wordファイルも同じコマンドで実行できます。

```bash
jtc-md-convert path/to/design.docx --out outputs/word_design
```

生成される主なファイルは以下です。

- `extracted.json`: 抽出した構造化データ
- `book_specification.md`: 統合Markdown仕様書
- `specification.md`: 互換用のMarkdownファイル名
- `warnings.md`: 人間レビューが必要な項目
- `preview.html`: 元文書との対応を確認するHTML
- `evaluation.md`: 変換結果の概要
- `package.zip`: 成果物一式

## Docker実行

Python環境を作らずに試す場合はDockerを使います。

```bash
docker build -t jtc-excel-md-converter:local .
mkdir -p outputs
docker run --rm \
  --user "$(id -u):$(id -g)" \
  --workdir /work \
  -v "$PWD/examples:/work/examples:ro" \
  -v "$PWD/outputs:/work/outputs" \
  jtc-excel-md-converter:local \
  examples/jtc_screen_design.xlsx --out outputs/docker-smoke
```

Composeでも実行できます。

```bash
docker compose run --rm jtc-md-converter
```

LinuxでUID/GIDが `1000:1000` ではない場合は、次のように指定してください。

```bash
UID=$(id -u) GID=$(id -g) docker compose run --rm jtc-md-converter
```

WindowsではWSLまたはGit Bashでの実行を推奨します。必要に応じて `docker run --user` の指定を利用環境に合わせてください。

Dockerの実行確認スクリプトもあります。

```bash
scripts/docker_smoke.sh
```

## AIプロバイダ設定

AI支援は任意です。初期状態では外部APIへ文書内容を送りません。

設定する場合は `.env.example` をコピーします。

```bash
cp .env.example .env
```

現在の推奨初期設定はCodexです。

```text
JTC_AI_PROVIDER=codex
OPENAI_API_KEY=your-local-key
JTC_AI_BASE_URL=https://api.openai.com/v1
JTC_AI_MODEL=codex-mini-latest
```

ローカルまたはOpenAI互換エンドポイントも利用できます。

```text
JTC_AI_PROVIDER=openai-compatible
JTC_AI_API_KEY=
JTC_AI_BASE_URL=http://127.0.0.1:11434/v1
JTC_AI_MODEL=qwen2.5-coder:7b
```

対応予定を含むプロバイダ値は以下です。

- `codex`
- `openai`
- `anthropic`
- `google`
- `openai-compatible`
- `ollama`
- `lmstudio`
- `local`

変換成果物にAI設定の安全な概要を含める場合は、次のように実行します。

```bash
jtc-md-convert examples/jtc_screen_design.xlsx \
  --out outputs/jtc_screen_design \
  --ai-env-file .env \
  --show-ai-config
```

出力にはプロバイダ名、モデル名、安全化したベースURL、APIキー設定有無だけを記録します。生のAPIキーやキーの一部は `extracted.json`、`evaluation.md`、標準出力、ZIPへ書き込みません。

## ローカルデモUI

関西電力様向けのローカルデモUIを起動します。

```bash
jtc-md-demo examples/jtc_screen_design.xlsx --out outputs/demo-app --port 8765
```

ブラウザで以下を開きます。

```text
http://127.0.0.1:8765/
```

初期デモはローカル処理のみで、外部LLM/APIへ文書内容を送信しません。シート一覧、抽出プレビュー、統合Markdown、構造化JSON、レビューHTML、評価レポート、warnings、ZIPダウンロード導線を確認できます。

画面スモークテストは以下です。

```bash
python scripts/smoke_demo_ui.py
```

## 対象範囲

このツールは汎用Excelレンダラーではありません。Excelをレイアウトキャンバスとして使ったJTC式システム設計書を、レビュー可能な仕様書・AI投入用データへ変換するためのPoC基盤です。

現時点ではMVPです。画像、図形、テキストボックス、PDF、実Codex整形実行、大量実文書評価は次フェーズです。
