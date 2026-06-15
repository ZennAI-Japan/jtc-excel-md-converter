# Before / After サンプル

このページは、`examples/jtc_screen_design.xlsx` を実際に変換したBefore/Afterです。

## 実行コマンド

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
jtc-md-convert examples/jtc_screen_design.xlsx --out outputs/jtc_screen_design
```

## Before: Excel設計書の中身

入力ファイル:

```text
examples/jtc_screen_design.xlsx
```

Excel上では、結合セル・罫線・入力規則・コメントに仕様情報が入っています。

```text
Sheet: 画面設計書
Size: 7 rows x 8 columns

B2:H2  画面設計書：ログイン画面

B4:F7  罫線で囲まれた項目定義表

| セル範囲 | 内容 |
| --- | --- |
| B4:F4 | 項目 / 内容 / 必須 / 入力方式 / 備考 |
| B5:F5 | ユーザーID / 社員番号またはメール / ○ / テキスト / 半角英数 |
| B6:F6 | パスワード / 8文字以上 / ○ / パスワード / マスク表示 |
| B7:F7 | ログイン保持 / 次回から自動ログイン /  / チェックボックス / 任意 |
| E5:E7 | 入力規則: テキスト / パスワード / チェックボックス / ラジオ |
| F5 | コメント: DB項目 user_id に対応 |
```

## After: Markdown仕様書

生成ファイル:

```text
outputs/jtc_screen_design/specification.md
```

```markdown
# 画面設計書：ログイン画面

## 抽出した見出し

- B2:H2: 画面設計書：ログイン画面

## 画面設計書 / B4:F7

| 項目 | 内容 | 必須 | 入力方式 | 備考 |
| --- | --- | --- | --- | --- |
| ユーザーID | 社員番号またはメール | ○ | テキスト | 半角英数 |
| パスワード | 8文字以上 | ○ | パスワード | マスク表示 |
| ログイン保持 | 次回から自動ログイン |  | チェックボックス | 任意 |

### 入力規則

- E5:E7: テキスト / パスワード / チェックボックス / ラジオ
```

## After: 構造化JSON

生成ファイル:

```text
outputs/jtc_screen_design/extracted.json
```

抜粋:

```json
{
  "source": "examples/jtc_screen_design.xlsx",
  "sheets": [
    {
      "name": "画面設計書",
      "titles": [
        {
          "range": "B2:H2",
          "text": "画面設計書：ログイン画面",
          "start_cell": "B2"
        }
      ],
      "blocks": [
        {
          "type": "bordered_table",
          "range": "B4:F7",
          "headers": ["項目", "内容", "必須", "入力方式", "備考"],
          "rows": [
            {
              "項目": "ユーザーID",
              "内容": "社員番号またはメール",
              "必須": "○",
              "入力方式": "テキスト",
              "備考": "半角英数"
            }
          ]
        }
      ]
    }
  ]
}
```

## After: レビュー用HTML / 評価 / 警告

変換後はMarkdownだけでなく、人間がレビューしやすい補助ファイルも出力します。

```text
outputs/jtc_screen_design/preview.html
outputs/jtc_screen_design/evaluation.md
outputs/jtc_screen_design/warnings.md
outputs/jtc_screen_design/package.zip
```

`evaluation.md` の例:

```text
- Sheets: 1
- Bordered blocks: 1
- Merged titles: 1
- Input validations: 1
- Warnings: 2
```

`warnings.md` の例:

```text
- 画面設計書: 結合セル B2:H2 を見出しとして解釈しました。
- 画面設計書: コメント付きセル F5 は人手確認してください。
```

## 何が嬉しいか

- Excel方眼紙の罫線ブロックを、Markdown表として取り出せる
- 結合セルのタイトルを、見出しとして残せる
- 入力規則やコメントを、AI/RAGに渡せる情報として落とせる
- `warnings.md` に要確認事項を分けるため、変換結果を過信しにくい
- `preview.html` とセル座標で、元文書との対応を人間が確認できる

## 想定ユースケース

- 大手企業のWord/Excel設計書をAI検索・RAG用ナレッジへ変換
- 既存システムの設計書棚卸し
- Markdown化された仕様書から、要件整理・テスト観点・移行計画を作成
- 顧客文書を外部SaaSへ送らず、ローカルで一次変換
