# 公開リリースチェックリスト

リポジトリを private から public へ変更する前に使うチェックリストです。

## リポジトリ安全確認

- [ ] `gh repo view --json visibility` を確認し、保守者が公開を承認している。
- [ ] 顧客の Word / Excel ファイル、スクリーンショット、生成済み成果物、非公開デモ素材をコミットしていない。
- [ ] `.env`、`.env.*`、APIキー、トークン、ローカル認証情報をコミットしていない。
- [ ] `.env.example` はプレースホルダだけで構成されている。
- [ ] `LICENSE` が存在し、採用ライセンスを保守者が承認している。
- [ ] `README.md`、`CONTRIBUTING.md`、`SECURITY.md` がローカルファーストとBYOK AIの挙動を説明している。

## 検証ゲート

```bash
python -m compileall -q src tests scripts
python -m pytest -q
python scripts/smoke_demo_ui.py
scripts/docker_smoke.sh
git diff --check
```

- [ ] ずんだもんデモ動画は `docs/assets/demo-zundamon.mp4` にあり、2MB以下で、h264 1280x720映像とAAC音声を含む。

## AI / プライバシー確認

- [ ] AI認証情報なしで変換器が動く。
- [ ] ローカルプロバイダ設定は、必要な場合にAPIキーなしで動く。
- [ ] プロバイダ別キーは概要やログ風出力で漏れない。
- [ ] 文書内容を外部APIへ送る機能は、明示的なオプトインになっている。
- [ ] 生のAPIキーはUIや成果物に表示されない。

## GitHub設定

- [ ] GitHubの非公開脆弱性報告を有効化する。
- [ ] Actions / workflow がforkへsecretを露出しないことを確認する。
- [ ] 既定ブランチ保護または保守者のマージ方針を確認する。
- [ ] 初期ラベルを作成する: `bug`, `documentation`, `good first issue`, `help wanted`, `security`, `provider-adapter`。

## リリースノート

- [ ] alpha / MVPソフトウェアであることを書く。
- [ ] 決定論的変換はオフラインで動くことを書く。
- [ ] AIプロバイダ対応はBYOKかつ任意であることを書く。
- [ ] 企業文書には機密情報が含まれ得るため、外部プロバイダへ送信する前に利用者が確認すべきことを書く。
