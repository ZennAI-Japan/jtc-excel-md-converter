# Codex引き継ぎ: 関西電力様向けデモアプリ化

このブランチでは、複数シートExcel設計書を Markdown / JSON / HTMLプレビューへ変換するPoCに、関西電力様向けの営業デモUIを追加する。

## 必読資料

1. `docs/2026-06-15-demo-app-requirements.md`
2. `DESIGN.md`
3. `docs/design/kepco-demo-app-mockup.png`
4. `docs/2026-06-15-kepco-demo-app-implementation-plan.md`
5. `src/jtc_excel_md/converter.py`
6. `tests/test_jtc_excel_converter.py`

## プロダクト方針

- 顧客は関西電力様を想定する。
- 画面は派手なAI SaaSではなく、電力インフラ企業向けの堅実・安全・監査可能な業務アプリにする。
- 初期デモでは外部LLM/APIへ文書内容を送らない。
- 主成果物は `book_specification.md`。
- warningsを隠さない。
- 顧客向け画面に内部メモ、開発都合、ミラ口調、安い比較訴求を出さない。

## 最初に着手する作業

`docs/2026-06-15-kepco-demo-app-implementation-plan.md` の Task 1〜2 をTDDで実装する。

```bash
cd /Users/ryutarofurutani/repos/jtc-excel-md-converter
python -m pytest -q
npx -y @google/design.md lint DESIGN.md
```

## 確認済みベースライン

- `npx -y @google/design.md lint DESIGN.md`: errors 0, warnings 0
- `python -m pytest -q`: 4 passed
- PR: https://github.com/ZennAI-Japan/jtc-excel-md-converter/pull/1

## 禁止事項

- UIに「Excelの代替」「Excelではできない」などの比較訴求を入れない。
- 変換できない要素を成功扱いしない。
- converterロジックをWeb層へ複製しない。
- 実顧客ファイル送信、保存、外部API連携を勝手に追加しない。
