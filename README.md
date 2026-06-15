# JTC Excel MD Converter

Word / Excel / PDF の業務文書を、Markdown・構造化JSON・レビュー用HTMLへ変換するローカルファーストのOSSです。

Excel方眼紙の罫線、結合セル、セル座標、入力規則、コメント、Word文書の見出し・段落・表、テキストPDFの本文を、AIが読みやすく人間が確認しやすい成果物として残します。

![JTC Excel MD Converter の概要](docs/assets/social-preview.png)

> GitHub social preview 用のPNGは `docs/assets/social-preview.png`、編集用SVGは `docs/assets/social-preview.svg` にあります。

## 特長

- Excel設計書をブック単位でMarkdown化
- Word `.docx` をMarkdown / JSON化
- テキストPDFをMarkdown / JSON化
- Excel / Word内の画像、図形、テキストボックスをプレースホルダーとして検出
- 変換結果の根拠を確認できる `preview.html` を生成
- 要確認箇所を `warnings.md` に分離
- `package.zip` で成果物を一括取得
- AI連携は任意。未設定でも決定論的な変換は動作
- DockerでPython環境を作らずに実行可能

## デモ動画

<video controls src="docs/assets/demo-zundamon.mp4" title="JTC Excel MD Converter デモ"></video>

動画が表示されない場合は、こちらを直接開いてください。

[デモ動画を開く](docs/assets/demo-zundamon.mp4)

## 変換例

入力側のExcel設計書では、罫線・結合セル・入力規則・セル座標に仕様情報が入っていることがあります。

```text
B2:H2  画面設計書：ログイン画面
B4:F7  項目 / 内容 / 必須 / 入力方式 / 備考
E5:E7  テキスト / パスワード / チェックボックス / ラジオ
```

変換後は、AIや検索システムに渡しやすいMarkdownと、レビュー可能なJSON/HTMLに分かれます。

```markdown
# 画面設計書：ログイン画面

| 項目 | 内容 | 必須 | 入力方式 | 備考 |
| --- | --- | --- | --- | --- |
| ユーザーID | 社員番号またはメール | ○ | テキスト | 半角英数 |
| パスワード | 8文字以上 | ○ | パスワード | マスク表示 |

### 入力規則
- E5:E7: テキスト / パスワード / チェックボックス / ラジオ
```

`preview.html` には元文書のセル範囲や抽出ブロックが残るため、人間が変換結果を確認しやすくなります。

## ローカル実行

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
jtc-md-convert examples/jtc_screen_design.xlsx --out outputs/jtc_screen_design
```

開発時にテストも実行する場合は、開発用extraを入れます。

```bash
pip install -e '.[dev]'
python -m pytest -q
```

Wordファイルも同じコマンドで実行できます。

```bash
jtc-md-convert path/to/design.docx --out outputs/word_design
```

PDF対応は `PyMuPDF` を使うため任意extraに分けています。PDFを変換する場合だけ、次のように入れてください。

```bash
pip install -e '.[pdf]'
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

## AI連携

AI支援は任意です。初期状態では外部APIへ文書内容を送りません。

設定する場合は `.env.example` をコピーします。

```bash
cp .env.example .env
```

OpenAI互換エンドポイントを利用する例です。

```text
JTC_AI_PROVIDER=openai-compatible
JTC_AI_API_KEY=your-api-key
JTC_AI_BASE_URL=http://127.0.0.1:11434/v1
JTC_AI_MODEL=qwen2.5-coder:7b
```

対応予定を含むプロバイダ値は以下です。

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

AIエンドポイントへ実際に整形を依頼する場合は、明示的に `--ai-restructure` を付けます。決定的に生成した `book_specification.md` は上書きせず、レビュー用の `ai_restructured_specification.md` と `ai_restructure_warnings.md` を別ファイルとして出力します。

`--ai-restructure` を付けた場合だけ、抽出済みMarkdownと `extracted.json` の内容を設定したAIエンドポイントへ送信します。機密文書を扱う場合は、利用組織で承認済みのローカル/専用エンドポイントを使うか、送信可能な文書だけで実行してください。`--ai-restructure` なしの通常変換は外部LLM/APIへ文書内容を送りません。

```bash
jtc-md-convert examples/jtc_screen_design.xlsx \
  --out outputs/jtc_screen_design \
  --ai-env-file .env \
  --ai-restructure
```

## 公開サンプル文書で評価する

公開URLから取得できるサンプル文書で、変換処理をまとめて確認できます。

```bash
python scripts/fetch_public_sample_corpus.py \
  --corpus public-sample-corpus \
  --out public-sample-evaluation-output
```

取得元URL、ファイル名、SHA-256は `public-sample-corpus/manifest.json` に保存されます。評価結果は `public-sample-evaluation-output/evaluation_summary.json`、`evaluation_summary.md`、`evaluation_cases.csv` に出ます。

既定の公開サンプルは、pandasのExcelテスト用ファイル、calibreのDOCXデモ、W3C WAIのPDFテストファイルです。pandas由来のURLは特定commitに固定し、取得済みファイルもSHA-256で検証します。

公開サンプルでの評価は、変換パイプラインの動作確認と品質の簡易確認です。特定組織の文書品質を保証するものではありません。導入判断では、利用可能な模擬文書や利用許可済み文書で追加評価してください。

詳しくは [公開サンプル文書での評価](docs/public-sample-corpus.md) を参照してください。

## 手元の文書セットで評価する

手元のOffice/PDF文書は、リポジトリ外またはGit管理対象外のディレクトリで評価します。

```bash
python scripts/evaluate_private_corpus.py private-corpus --out private-evaluation-output
```

`private-corpus/` と `private-evaluation-output/` は `.gitignore` 済みです。評価サマリーは `evaluation_summary.json`、`evaluation_summary.md`、`evaluation_cases.csv` に出ます。評価対象は最大30本に制限し、10本以上・失敗0件で基準達成です。CSV/Markdownにはフルパスを出さず、ケースIDとファイル名だけを残します。

## リリース前チェック

リリース前に、承認、文書評価、秘密情報確認、ライセンス確認を `docs/public-release-approval.md` で明示的にチェックします。

```bash
python scripts/public_release_gate.py
```

未承認の間は失敗します。GitHub Actionsでは手動実行の `Public Release Gate` workflow から同じチェックを実行できます。

## ローカルデモUI

ローカルデモUIを起動します。

```bash
jtc-md-demo examples/jtc_screen_design.xlsx --out outputs/demo-app --port 8765
```

ブラウザで以下を開きます。

```text
http://127.0.0.1:8765/
```

このデモはローカル処理のみで、外部LLM/APIへ文書内容を送信しません。シート一覧、抽出プレビュー、統合Markdown、構造化JSON、レビューHTML、評価レポート、warnings、ZIPダウンロード導線を確認できます。

画面スモークテストは以下です。

```bash
python scripts/smoke_demo_ui.py
```

## 対象範囲

このツールは汎用Excelレンダラーではありません。Excelをレイアウトキャンバスとして使った業務設計書を、レビュー可能な仕様書・AI投入用データへ変換するためのPoC基盤です。

現時点ではMVPです。Excel / Word / PDFの主要テキスト、表、罫線、入力規則、コメント、画像・図形・テキストボックスのプレースホルダー検出、AI整形の明示実行、文書セット評価ハーネス、リリース前チェックまで対応しています。画像そのもののOCR、スキャンPDFのOCR、図形の意味解釈、Office上の厳密な重なり順再現は対象外で、プレースホルダーとwarningsで人間確認へ回します。

## ライセンスと依存関係

このリポジトリ本体は MIT License です。

主な依存関係は `openpyxl` です。PDF対応は任意extraの `pdf` に分けており、`pip install -e '.[pdf]'` または `pip install 'jtc-excel-md-converter[pdf]'` を実行した場合だけ `PyMuPDF` が入ります。

`openpyxl` は MIT License、`PyMuPDF` は AGPL-3.0-or-later または商用ライセンスのデュアルライセンスです。配布・組み込み・商用利用の条件は利用形態により変わるため、PDF対応を含めて再配布する場合は `NOTICE.md` と各プロジェクトのライセンスを確認してください。
