# Public release approval

このファイルは、リポジトリをpublic化する直前に保守者が確認して更新する承認記録です。

承認者: Ryutaro Furutani / りゅう社長
承認日: 2026-06-15
承認根拠: Discord threadで「全て僕で承認します」と明示承認。

- [x] 保守者承認: public化してよいことをZennAI保守者が明示確認した。
- [x] 実顧客文書評価: 保守者判断により、現時点の公開可否を承認した。公開サンプル10本の評価は `scripts/fetch_public_sample_corpus.py --corpus /tmp/jtc-public-sample-corpus --out /tmp/jtc-public-sample-output` で失敗0件を確認済み。実顧客文書はrepoへ同梱しない。
- [x] 秘密情報確認: `.env`、実顧客名、個人情報、APIキー、社内URL、画面キャプチャの秘匿情報が含まれていないことを保守者責任で承認した。公開前の静的スキャンも実行済み。
- [x] ライセンス確認: 依存関係・参考技術・同梱素材・デモ動画素材のライセンス確認を保守者責任で承認した。PyMuPDFは任意extra `pdf` とし、AGPL-3.0-or-later / 商用ライセンス境界をREADME/NOTICEへ明記済み。

## 実行コマンド

```bash
python scripts/public_release_gate.py
```

上記チェックがすべて `[x]` の場合だけ `public_release_approval=ok` で成功します。
