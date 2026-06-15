# NOTICE

このリポジトリ本体は MIT License で提供されます。

## 主な依存関係

| 依存関係 | 用途 | ライセンス上の注意 |
| --- | --- | --- |
| openpyxl | Excel `.xlsx` の読み取り | MIT License |
| PyMuPDF | テキストPDFの読み取り | AGPL-3.0-or-later または商用ライセンス |
| pytest | 開発時テスト | MIT License |

## PyMuPDF について

PDF対応は PyMuPDF に依存しています。PyMuPDF は AGPL-3.0-or-later と商用ライセンスのデュアルライセンスです。

このため、PDF対応を含めた配布、組み込み、SaaS提供、社内外への再配布を行う場合は、利用形態が PyMuPDF のライセンス条件に合うか確認してください。必要に応じて商用ライセンスの利用、PDF機能の分離、または別PDFバックエンドへの差し替えを検討してください。

## サンプル文書について

`scripts/fetch_public_sample_corpus.py` は公開URLからサンプル文書を取得します。サンプル文書そのものはこのリポジトリに同梱せず、取得元URL、ファイル名、SHA-256を `manifest.json` に記録します。

取得したファイルの利用条件は各配布元のライセンス・利用規約に従ってください。
