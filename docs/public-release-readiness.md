# Public release readiness

最終更新: 2026-06-15

このメモは、リポジトリをpublic化する直前の判断材料をまとめるためのものです。

## 現在の状態

- GitHub visibility: public化承認済み（公開操作後に `gh repo view ... --json visibility` で再確認する）
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

## Public release approval gate

`docs/public-release-approval.md` は、保守者 Ryutaro Furutani / りゅう社長 の明示承認により全項目を承認済みです。

承認根拠:

- Discord threadで「全て僕で承認します」と明示承認。

承認済み項目:

- 保守者承認
- 実顧客文書評価（保守者判断で公開可否を承認。実顧客文書はrepoへ同梱せず、実行済み評価は公開サンプル10本・失敗0件）
- 秘密情報確認
- ライセンス確認

`python scripts/public_release_gate.py` が `public_release_approval=ok` を返す状態であることを公開前に確認します。

## GitHub social preview設定について

GitHub GraphQL `UpdateRepositoryInput` には social preview image を更新する公開フィールドがありません。CLI/APIで安全に設定できる経路は確認できていないため、現時点では `docs/assets/social-preview.png` をGitHub Settings画面から手動アップロードする想定です。

推奨手順:

1. `docs/assets/social-preview.png` をローカルに保存する。
2. GitHub repository settingsを開く。
3. Social preview欄にPNGをアップロードする。
4. 公開後にGitHubのリポジトリページで見え方を確認する。

## 公開後に確認すること

1. `gh repo view ZennAI-Japan/jtc-excel-md-converter --json visibility,url` が `PUBLIC` を返す。
2. GitHub Actionsの最新CIが成功している。
3. READMEの画像・デモ動画・ライセンス表記がpublic画面で見える。
4. 必要に応じてGitHub Settingsから social preview PNG を手動アップロードする。
