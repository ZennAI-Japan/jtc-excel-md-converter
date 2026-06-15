# 公開サンプル文書での評価

このリポジトリには、公開URLから取得できるOffice/PDFサンプルを使った評価スクリプトがあります。

```bash
python scripts/fetch_public_sample_corpus.py \
  --corpus public-sample-corpus \
  --out public-sample-evaluation-output
```

スクリプトは以下を行います。

1. 公開URLから `.xlsx` / `.docx` / `.pdf` のサンプルを取得
2. 取得元URLとファイル名を `manifest.json` に保存
3. 変換処理を実行
4. `evaluation_summary.json`、`evaluation_summary.md`、`evaluation_cases.csv` を出力

`public-sample-corpus/` と `public-sample-evaluation-output/` はGit管理対象外です。取得したファイルの利用条件は、各配布元のライセンス・利用規約を確認してください。

## 収録元

現在の既定リストは次の公開サンプルです。

- `pandas-dev/pandas` のExcelテスト用 `.xlsx` ファイル
- calibreの公開DOCXデモファイル
- W3C WAIの公開PDFテストファイル

公開サンプルは動作確認用です。企業固有フォーマットへの適合性確認には、自社で利用可能な社内文書または公開可能な模擬文書で追加評価してください。
