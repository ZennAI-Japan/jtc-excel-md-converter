# Public release approval

このファイルは、リポジトリをpublic化する直前に保守者が確認して更新する承認記録です。

> 注意: このPRでは承認ゲートを整備するだけです。実顧客文書・秘密情報・ライセンスの最終確認が終わるまで、以下は未チェックのままにします。

- [ ] 保守者承認: public化してよいことをZennAI保守者が明示確認した。
- [ ] 実顧客文書評価: `scripts/evaluate_private_corpus.py <private-dir> --out <private-output-dir>` で10〜30本を評価し、失敗0件を確認した。
- [ ] 秘密情報確認: `.env`、実顧客名、個人情報、APIキー、社内URL、画面キャプチャの秘匿情報が含まれていないことを確認した。
- [ ] ライセンス確認: 依存関係・参考技術・同梱素材・デモ動画素材のライセンスを確認した。

## 実行コマンド

```bash
python scripts/public_release_gate.py
```

未承認の間は失敗します。public化直前に上記チェックを `[x]` に更新し、保守者レビュー付きPRで通してください。
