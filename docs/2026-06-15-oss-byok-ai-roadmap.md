# OSS / BYOK AI ロードマップ

> **Hermes / Codex向けメモ:** 文書プライバシーを弱めず、OSSとして使える状態を目指す。変換器は既定で決定論的に動作する。AI機能は任意・明示的・利用者自身のプロバイダ/APIキー設定に限定する。

## 目的

利用者が Excel / Word の企業文書をローカルで変換でき、必要な場合だけ自分のAIプロバイダを接続できる状態にする。対象はホスト型API、OpenAI互換エンドポイント、Ollama / LM Studio などのローカル実行環境を含む。

## アーキテクチャ

`converter.py` を決定論的な抽出中核として維持する。AIは別レイヤーに分離し、明示的な成果物を入力として、レビュー可能なMarkdown再構成案を返す。利用者が設定で選んでいない限り、中核変換器やローカルデモからAI呼び出しを行わない。

## 技術スタック

Python 3.10+、openpyxl、標準ライブラリのenv解析、将来の任意プロバイダアダプタ、pytest、画面スモーク。

## 原則

1. ローカルファースト: Word / Excel 文書は既定で利用者の端末内に留める。
2. BYOK AI: OpenAI、Anthropic、Google Gemini、OpenAI互換、Ollama、LM Studio、ローカルgatewayを利用者が設定する。
3. 認証情報を直書きしない: 例やテストに実キーを含めない。
4. 決定論的な基盤: AIプロバイダなしでも変換器が動く。
5. レビュー可能な出力: AI出力は警告・根拠つきの成果物として扱い、黙って既存成果物を書き換えない。
6. ベンダーニュートラル: プロバイダアダプタは小さな内部インターフェースを共有する。

## このPRで入った基盤

- `.env.example` にプロバイダ設定を記載し、初期推奨を `codex` にした。
- `src/jtc_excel_md/ai_config.py` が、SDKに依存せず設定を読み込み、安全化する。
- `src/jtc_excel_md/word_converter.py` が、`.docx` の見出し・段落・表を同じ成果物契約へ抽出する。
- `src/jtc_excel_md/ai_providers.py` が、任意AIプロバイダのインターフェースとOpenAI互換リクエスト生成を定義する。
- `tests/test_ai_config.py` が、汎用・プロバイダ別・Codex初期・ファイル読み込み・ローカルno-key設定を検証する。
- `tests/test_ai_providers.py` が、無効プロバイダ、secret-safeなリクエスト情報、注入HTTP境界を検証する。
- `tests/test_word_converter.py` が、`.docx` 抽出とCLI成果物生成を検証する。
- `Dockerfile`、`compose.yaml`、`scripts/docker_smoke.sh` が、Docker CLI実行環境を提供する。
- `.gitignore` が `.env` と `.env.*` を除外し、`.env.example` を追跡対象に残す。
- `CONTRIBUTING.md`、`SECURITY.md`、`LICENSE` がOSS公開に必要な最低限の衛生面を整える。
- READMEと主要ドキュメントを日本語化し、ずんだもん音声つきデモ動画を追加する。

## タスク1: プロバイダアダプタ

目的: 変換中核からネットワーク呼び出しを行わず、ベンダーニュートラルなアダプタを追加する。

対象:

- `src/jtc_excel_md/ai_providers.py`
- `tests/test_ai_providers.py`

受入条件:

- `rewrite_specification(prompt: str) -> AIResponse` 相当の小さなインターフェースを定義する。
- `AIConfig.enabled` がfalseの場合は無効プロバイダを返す。
- `openai-compatible` はリクエスト情報を準備し、テストではHTTP境界をmockする。

## タスク2: AI支援再構成コマンド

目的: すでに生成済みの成果物に対し、設定済みプロバイダを使える別コマンドを追加する。

対象:

- `src/jtc_excel_md/ai_restructure.py`
- `pyproject.toml`
- `tests/test_ai_restructure.py`

受入条件:

- 出力ディレクトリから `book_specification.md` と `extracted.json` を読む。
- プロバイダ未設定時は分かりやすく終了し、決定論的変換を壊さない。
- fake providerでは `ai_restructured_specification.md` と `ai_restructure_warnings.md` を生成する。

## タスク3: UIのオプトイン表示

目的: ローカルデモにAI設定状態を表示する。ただし自動送信しない。

対象:

- `src/jtc_excel_md/demo_server.py`
- `tests/test_demo_server.py`

受入条件:

- UIが `AI支援: 未設定 / ローカル / 外部プロバイダ` を安全化済み設定から表示する。
- 外部プロバイダ時はプライバシー注意を表示する。
- 生のAPIキーを表示しない。

## タスク4: 公開リリースチェックリスト

目的: リポジトリを安全にpublic化できる状態を作る。

対象:

- `docs/public-release-checklist.md`

受入条件:

- secret scan、生成物確認、顧客文書確認、license、脆弱性報告、パッケージメタデータ、README手順を含める。
- visibility変更は自動化せず、保守者の手動操作にする。

## タスク5: 配布

目的: OSS利用者が予測可能にインストールできる状態にする。

対象:

- `pyproject.toml`
- 必要に応じてGitHub Actions workflow

受入条件:

- project URLs、license metadata、authors、classifiersを整える。
- CIはローカル同等の compileall、pytest、可能ならsmokeを実行する。
- パッケージ公開は保守者が認証情報を承認するまで手動にする。
