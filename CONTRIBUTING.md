# コントリビューションガイド

JTC Excel MD Converter の改善に協力いただきありがとうございます。

このプロジェクトは、企業の Word / Excel 設計書を Markdown、構造化JSON、レビュー可能な成果物へ変換するためのOSSです。既定ではローカル処理を維持し、AI連携は利用者が明示的に設定した場合だけ有効にします。

## 開発環境

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
python -m pytest -q
```

動画検証や動画再生成を行う場合は `ffmpeg` / `ffprobe` も必要です。

## Dockerでの確認

```bash
scripts/docker_smoke.sh
```

## ローカルデモ

```bash
jtc-md-demo examples/jtc_screen_design.xlsx --out outputs/demo-app --port 8765
```

ブラウザで `http://127.0.0.1:8765/` を開きます。

## AIプロバイダ設定

決定論的な変換は、AI認証情報なしで必ず動く必要があります。

AI支援を追加する場合は、環境変数またはローカル `.env` から設定を読み込みます。APIキーをコード、例、テスト、ドキュメント、スクリーンショット、Issueへ直接書かないでください。

```bash
cp .env.example .env
```

推奨初期設定はCodexです。

```text
JTC_AI_PROVIDER=codex
OPENAI_API_KEY=your-local-key
JTC_AI_BASE_URL=https://api.openai.com/v1
JTC_AI_MODEL=codex-mini-latest
```

ローカル互換APIの例です。

```text
JTC_AI_PROVIDER=openai-compatible
JTC_AI_API_KEY=
JTC_AI_BASE_URL=http://127.0.0.1:11434/v1
JTC_AI_MODEL=qwen2.5-coder:7b
```

## PR前チェック

PR作成または更新前に、少なくとも以下を実行してください。

```bash
python -m compileall -q src tests scripts
python -m pytest -q
python scripts/smoke_demo_ui.py
scripts/docker_smoke.sh
git diff --check
```

UIや顧客向け表示を変更した場合は、内部メモ、開発都合、安い比較訴求、未確認を成功扱いする文言が混ざっていないことを確認してください。

## セキュリティ方針

- `.env` や実認証情報をコミットしない。
- 企業文書の内容は既定でローカルに保持する。
- 将来のAI呼び出しは、プロバイダ、ベースURL、モデル、ネットワーク挙動を明示する。
- 外部AIプロバイダ機能を追加する場合も、認証情報なしのローカル変換が壊れないことをテストで保証する。
