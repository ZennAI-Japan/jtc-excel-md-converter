# JTC Excel MD Converter

日本企業で長く使われてきた Word / Excel 設計書を、Markdown・構造化JSON・レビュー用HTMLへ変換するローカルファーストのOSSです。

汎用変換だけでは落ちやすい、Excel方眼紙の罫線、結合セル、セル座標、入力規則、コメント、Word文書の見出し・段落・表を、AIが読みやすく人間が確認しやすい成果物として残します。

## できること

- Excel設計書をブック単位でMarkdown化
- Word `.docx` をMarkdown / JSON化
- テキストPDFをMarkdown / JSON化
- Excel / Word内の画像、図形、テキストボックスをプレースホルダーとして検出
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

Word / PDFファイルも同じコマンドで実行できます。

```bash
jtc-md-convert path/to/design.docx --out outputs/word_design
jtc-md-convert path/to/design.pdf --out outputs/pdf_design
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
env UID="$(id -u)" GID="$(id -g)" docker compose run --rm jtc-md-converter
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

Codex / OpenAI互換エンドポイントへ実際に整形を依頼する場合は、明示的に `--ai-restructure` を付けます。決定的に生成した `book_specification.md` は上書きせず、レビュー用の `ai_restructured_specification.md` と `ai_restructure_warnings.md` を別ファイルとして出力します。

`--ai-restructure` を付けた場合だけ、抽出済みMarkdownと `extracted.json` の内容を設定したAIエンドポイントへ送信します。顧客文書を扱う場合は、社内承認済みのローカル/専用エンドポイントを使うか、送信可能な文書だけで実行してください。`--ai-restructure` なしの通常変換は外部LLM/APIへ文書内容を送りません。

```bash
jtc-md-convert examples/jtc_screen_design.xlsx \
  --out outputs/jtc_screen_design \
  --ai-env-file .env \
  --ai-restructure
```

## 実顧客文書10〜30本評価

実顧客文書はリポジトリに入れず、ローカルの非公開ディレクトリで評価します。

```bash
python scripts/evaluate_private_corpus.py private-corpus --out private-evaluation-output
```

`private-corpus/` と `private-evaluation-output/` は `.gitignore` 済みです。評価サマリーは `evaluation_summary.json`、`evaluation_summary.md`、`evaluation_cases.csv` に出ます。評価対象は最大30本に制限し、10本以上・失敗0件で基準達成です。CSV/Markdownにはフルパスを出さず、ケースIDとファイル名だけを残します。

## public化前承認ゲート

public化前は、保守者承認・実顧客文書評価・秘密情報確認・ライセンス確認を `docs/public-release-approval.md` で明示的にチェックします。

```bash
python scripts/public_release_gate.py
```

未承認の間は失敗します。これはpublic化を誤って進めないためのfail-closedゲートです。
GitHub Actionsでは手動実行の `Public Release Gate` workflow から同じチェックを実行できます。

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

現時点ではMVPです。Excel / Word / PDFの主要テキスト、表、罫線、入力規則、コメント、画像・図形・テキストボックスのプレースホルダー検出、実Codex整形の明示実行、private corpus評価ハーネス、public化前承認ゲートまで対応しています。画像そのもののOCR、スキャンPDFのOCR、図形の意味解釈、Office上の厳密な重なり順再現は対象外で、プレースホルダーとwarningsで人間確認へ回します。実顧客文書そのものの10〜30本評価は、秘密情報保護のためローカル非公開ディレクトリで実行してください。
