# 関西電力様向けデモアプリ実装計画

> **For Hermes / Codex:** この計画は `DESIGN.md` と `docs/design/kepco-demo-app-mockup.png` を正とし、TDDで小さく実装する。営業デモで見せる画面には内部メモ、開発都合、ミラ口調、安い比較訴求を出さない。

**Goal:** 複数シートExcel設計書をアップロードし、Markdown / JSON / HTML Preview / 評価レポート / warnings を確認・ダウンロードできる、関西電力様向けの最小デモアプリを作る。

**Architecture:** 既存のPython変換CLIをドメイン中核として維持し、最初はローカル実行のWeb UIを薄く載せる。UIは `DESIGN.md` のトークンを使い、変換成果物は既存converterの出力をそのまま参照する。外部LLM/API送信は初期デモでは行わない。

**Tech Stack:** Python 3.10+, openpyxl, pytest, 標準ライブラリHTTP or 最小FastAPI系Web層（導入する場合は別PRで依存追加を明示）, Playwright screenshot smoke.

---

## Acceptance Criteria

1. `.xlsx` を1ファイル指定して変換できる。
2. ブック全体成果物として `book_specification.md` を表示できる。
3. シート一覧、選択シートプレビュー、成果物一覧、warnings一覧が1画面で確認できる。
4. `book_specification.md` / `extracted.json` / `preview.html` / `evaluation.md` / ZIP の導線を表示できる。
5. UIは `docs/design/kepco-demo-app-mockup.png` の方向性に沿う。
6. 顧客向け表示に以下を出さない。
   - 内部メモ
   - 開発都合
   - ミラ口調
   - 「Excelの代替」「Excelではできない」等の安い比較訴求
   - 未確認を成功扱いする文言
7. 初期デモでは外部LLM/APIへ文書内容を送信しない。
8. 変換できない/不確実な要素は warnings として明示する。

## Source of Truth

- 要件: `docs/2026-06-15-demo-app-requirements.md`
- デザインシステム: `DESIGN.md`
- 画像イメージ: `docs/design/kepco-demo-app-mockup.png`
- HTMLモック: `docs/design/kepco-demo-app-mockup.html`
- 既存変換中核: `src/jtc_excel_md/converter.py`
- CLI: `src/jtc_excel_md/cli.py`
- 既存テスト: `tests/test_jtc_excel_converter.py`

## Task 1: converter出力契約を固定する

**Objective:** Web UIが参照する成果物名とwarnings契約をテストで固定する。

**Files:**
- Modify: `tests/test_jtc_excel_converter.py`
- Modify if needed: `src/jtc_excel_md/converter.py`

**Step 1: Write failing test**

既存テストに、出力ディレクトリへ最低限以下が生成されることを確認するテストを追加する。

```python
def test_converter_outputs_demo_artifact_contract(tmp_path):
    # sample workbookを作成または既存fixtureを利用
    # convert/write_outputsを実行
    expected = {
        "book_specification.md",
        "extracted.json",
        "preview.html",
        "evaluation.md",
        "warnings.md",
    }
    assert expected <= {p.name for p in output_dir.iterdir()}
```

**Step 2: Run RED**

```bash
python -m pytest tests/test_jtc_excel_converter.py::test_converter_outputs_demo_artifact_contract -q
```

Expected: まだ契約が足りなければFAIL。

**Step 3: Implement minimal GREEN**

不足している成果物だけを `converter.py` に追加する。既存出力がある場合は名前と内容をUI契約に合わせる。

**Step 4: Verify**

```bash
python -m pytest tests/test_jtc_excel_converter.py -q
```

## Task 2: 顧客向けコピー監査を追加する

**Objective:** 営業デモ画面・成果物に不要な内部表現が混ざらないようにする。

**Files:**
- Create: `tests/test_customer_facing_copy.py`
- Read: `DESIGN.md`
- Read: `docs/design/kepco-demo-app-mockup.html`

**Step 1: Write failing/guard test**

```python
from pathlib import Path

CUSTOMER_FACING_FILES = [
    Path("DESIGN.md"),
    Path("docs/design/kepco-demo-app-mockup.html"),
]

BANNED_PHRASES = [
    "ミラ口調",
    "開発都合",
    "内部メモ",
    "Excelの代替",
    "Excelではできない",
    "安い",
]


def test_customer_facing_copy_has_no_banned_phrases():
    for path in CUSTOMER_FACING_FILES:
        text = path.read_text(encoding="utf-8")
        for phrase in BANNED_PHRASES:
            assert phrase not in text, f"{path}: {phrase}"
```

**Important:** `DESIGN.md` のDon'tsには禁止語を説明目的で含むため、実装時は「画面HTML・将来のappテンプレート・出力HTML」を対象にするなど、監査対象を顧客表示ファイルへ限定する。

**Step 2: Run RED/GREEN**

```bash
python -m pytest tests/test_customer_facing_copy.py -q
```

## Task 3: Web UIの最小ルートを作る

**Objective:** ローカルブラウザでデモ画面を開けるようにする。

**Files:**
- Create: `src/jtc_excel_md/web_app.py` or `src/jtc_excel_md/demo_server.py`
- Create: `src/jtc_excel_md/web_assets/` if needed
- Modify: `pyproject.toml`
- Test: `tests/test_demo_server.py`

**Step 1: Write failing test**

標準ライブラリまたは選定したWeb frameworkのテストクライアントで `/` が200を返し、主要文言を含むことを確認する。

```python
def test_demo_home_contains_kepco_demo_copy():
    response = client.get("/")
    assert response.status_code == 200
    body = response.text
    assert "設計書ドキュメント化プラットフォーム" in body
    assert "関西電力様向け" in body
    assert "ローカル解析" in body
```

**Step 2: Run RED**

```bash
python -m pytest tests/test_demo_server.py -q
```

**Step 3: Implement minimal GREEN**

`docs/design/kepco-demo-app-mockup.html` をベースに、アプリテンプレートへ移す。最初はサンプルデータ固定でよい。ただし画面内には「サンプル」という目立つデモ都合表現を出しすぎない。

**Step 4: Verify**

```bash
python -m pytest tests/test_demo_server.py tests/test_customer_facing_copy.py -q
```

## Task 4: サンプルExcelの変換結果を画面へ接続する

**Objective:** 固定UIではなく、既存converterの実出力を画面表示へつなぐ。

**Files:**
- Modify: `src/jtc_excel_md/web_app.py` or `src/jtc_excel_md/demo_server.py`
- Modify: `tests/test_demo_server.py`
- Use: `examples/jtc_screen_design.xlsx`

**Step 1: Write failing test**

`examples/jtc_screen_design.xlsx` を変換し、画面本文に実際の成果物名・warnings件数・シート名が出ることを確認する。

```python
def test_demo_home_uses_converter_output(tmp_path):
    # sample workbookを変換
    # demo serverにoutput_dirを渡す
    body = client.get("/").text
    assert "book_specification.md" in body
    assert "warnings" in body
    assert "画面" in body
```

**Step 2: Run RED**

```bash
python -m pytest tests/test_demo_server.py::test_demo_home_uses_converter_output -q
```

**Step 3: Implement minimal GREEN**

Web層はconverterの結果を読むだけにする。変換ロジックをWeb層へ複製しない。

**Step 4: Verify**

```bash
python -m pytest -q
```

## Task 5: Playwright screenshot smokeを追加する

**Objective:** 画面崩れと禁止文言を画像・レンダリングで検出する。

**Files:**
- Create: `scripts/render_demo_screenshot.py` or `scripts/smoke_demo_ui.py`
- Modify: `pyproject.toml` scripts if needed
- Output: `outputs/demo-ui-smoke.png` or `docs/design/kepco-demo-app-runtime.png`

**Step 1: Create smoke script**

PlaywrightでローカルURLを開き、以下を確認する。

- viewport 1440x1100でスクリーンショット生成
- `document.documentElement.scrollWidth <= document.documentElement.clientWidth + 1`
- 主要見出しが表示される
- 禁止文言が表示されない

**Step 2: Verify**

```bash
python scripts/smoke_demo_ui.py
```

Expected: screenshot path and layout metricsを出力し、exit 0。

## Task 6: READMEにローカル試用手順を追加する

**Objective:** ご主人や営業メンバーが同じデモを再現できるようにする。

**Files:**
- Modify: `README.md`

**Content requirements:**

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
python -m pytest -q
jtc-md-convert examples/jtc_screen_design.xlsx --output outputs/demo
# Web UI起動コマンドは実装後に記載
```

**Verify:**

```bash
python -m pytest -q
```

## Final Verification Gate

実装完了を報告する前に必ず実行する。

```bash
npx -y @google/design.md lint DESIGN.md
python -m pytest -q
python scripts/smoke_demo_ui.py
```

PR報告には以下を含める。

- PR URL
- 最新commit SHA
- 起動コマンド
- 生成スクリーンショット
- 変換に使ったサンプルExcel
- まだ本番対応していない範囲
  - 認証
  - 権限管理
  - 実顧客ファイルの保存/削除ポリシー
  - 大容量ファイル
  - マクロ/画像/図形/OLE
  - 外部LLM/API連携
