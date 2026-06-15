# Public release readiness

最終更新: 2026-06-15

このメモは、リポジトリをpublic化する直前の判断材料をまとめるためのものです。public化そのものは `docs/public-release-approval.md` の承認チェックがすべて `[x]` になるまで行いません。

## 現在の状態

- GitHub visibility: private
- README: OSS向け説明、変換例、公開サンプル評価、ライセンス境界を記載済み
- GitHub metadata: description/topics設定済み
- Social preview asset:
  - GitHubにアップロードしやすいPNG: `docs/assets/social-preview.png`
  - 編集用SVG: `docs/assets/social-preview.svg`
- PDF support: `PyMuPDF` は任意extra `pdf` に分離済み

## 実行済み検証

```bash
python -m pytest -q
# 53 passed, 5 warnings

python -m compileall -q scripts src tests
# exit 0

git diff --check
# exit 0

python scripts/fetch_public_sample_corpus.py \
  --corpus /tmp/jtc-public-sample-corpus \
  --out /tmp/jtc-public-sample-output
# discovered_documents=10
# passed_documents=10
# failed_documents=0
# meets_private_corpus_bar=true
```

## Fail-closed public release gate

`python scripts/public_release_gate.py` は、public化前の必須承認が未完了のため失敗するのが正しい状態です。

現在の未承認項目:

- 保守者承認
- 実顧客文書評価
- 秘密情報確認
- ライセンス確認

## GitHub social preview設定について

GitHub GraphQL `UpdateRepositoryInput` には social preview image を更新する公開フィールドがありません。CLI/APIで安全に設定できる経路は確認できていないため、現時点では `docs/assets/social-preview.png` をGitHub Settings画面から手動アップロードする想定です。

推奨手順:

1. `docs/assets/social-preview.png` をローカルに保存する。
2. GitHub repository settingsを開く。
3. Social preview欄にPNGをアップロードする。
4. repository visibilityは、下記承認が終わるまでprivateのまま維持する。

## public化前に残っている承認

1. 保守者承認
   - public化してよいことを保守者が明示確認する。
2. 実顧客文書評価
   - 顧客情報を除いた安全な10〜30本で `scripts/evaluate_private_corpus.py` を実行する。
   - 失敗0件を確認する。
3. 秘密情報確認
   - `.env`、実顧客名、個人情報、APIキー、社内URL、秘匿画面キャプチャが含まれていないことを確認する。
4. ライセンス確認
   - PyMuPDF、公開サンプル、デモ動画、同梱素材、参考技術の条件を確認する。

## 判断

現時点では、ソース・README・依存境界・公開サンプル評価の整備は進んでいます。ただし、`public_release_gate` が意図通りfailしているため、public化はまだ行いません。
