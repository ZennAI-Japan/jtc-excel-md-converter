---
version: alpha
name: 関西電力様向けドキュメントインテリジェンスデモ
description: 関西電力様向けに、複数シートExcel設計書をAI活用可能な統合ドキュメントへ変換するデモアプリのデザインシステム。
colors:
  primary: "#0051A2"
  primary-dark: "#054385"
  accent: "#B94A00"
  accent-decorative: "#EB6100"
  accent-dark: "#8F3900"
  success: "#0C7A43"
  warning: "#8A5200"
  danger: "#C52223"
  ink: "#172033"
  muted: "#5E6B7A"
  border: "#D8E0EA"
  surface: "#FFFFFF"
  surface-soft: "#F5F8FB"
  surface-blue: "#EAF4FF"
  surface-orange: "#FFF4EB"
typography:
  h1:
    fontFamily: Inter, "Noto Sans JP", system-ui, sans-serif
    fontSize: 2.25rem
    fontWeight: 700
    lineHeight: 1.18
    letterSpacing: "-0.02em"
  h2:
    fontFamily: Inter, "Noto Sans JP", system-ui, sans-serif
    fontSize: 1.5rem
    fontWeight: 700
    lineHeight: 1.28
    letterSpacing: "-0.01em"
  body:
    fontFamily: Inter, "Noto Sans JP", system-ui, sans-serif
    fontSize: 1rem
    fontWeight: 400
    lineHeight: 1.7
  label:
    fontFamily: Inter, "Noto Sans JP", system-ui, sans-serif
    fontSize: 0.78rem
    fontWeight: 700
    lineHeight: 1.4
    letterSpacing: "0.08em"
  mono:
    fontFamily: "SFMono-Regular, Roboto Mono, monospace"
    fontSize: 0.86rem
    fontWeight: 500
    lineHeight: 1.55
rounded:
  sm: 6px
  md: 12px
  lg: 20px
  xl: 28px
spacing:
  xs: 6px
  sm: 10px
  md: 16px
  lg: 24px
  xl: 36px
  xxl: 56px
components:
  button-primary:
    backgroundColor: "{colors.primary}"
    textColor: "#FFFFFF"
    rounded: "{rounded.md}"
    padding: 14px
  button-primary-hover:
    backgroundColor: "{colors.primary-dark}"
    textColor: "#FFFFFF"
    rounded: "{rounded.md}"
    padding: 14px
  button-accent:
    backgroundColor: "{colors.accent}"
    textColor: "#FFFFFF"
    rounded: "{rounded.md}"
    padding: 14px
  button-accent-hover:
    backgroundColor: "{colors.accent-dark}"
    textColor: "#FFFFFF"
    rounded: "{rounded.md}"
    padding: 14px
  app-shell:
    backgroundColor: "{colors.surface-soft}"
    textColor: "{colors.ink}"
    rounded: "{rounded.xl}"
    padding: 24px
  card:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    rounded: "{rounded.lg}"
    padding: 20px
  selected-row:
    backgroundColor: "{colors.surface-blue}"
    textColor: "{colors.primary-dark}"
    rounded: "{rounded.md}"
    padding: 12px
  warning-chip:
    backgroundColor: "{colors.surface-orange}"
    textColor: "{colors.warning}"
    rounded: "{rounded.sm}"
    padding: 8px
  muted-label:
    backgroundColor: "{colors.surface-soft}"
    textColor: "{colors.muted}"
    rounded: "{rounded.sm}"
    padding: 8px
  divider-chip:
    backgroundColor: "{colors.border}"
    textColor: "{colors.ink}"
    rounded: "{rounded.sm}"
    padding: 8px
  decorative-accent-mark:
    backgroundColor: "{colors.accent-decorative}"
    textColor: "#000000"
    rounded: "{rounded.sm}"
    padding: 6px
  danger-chip:
    backgroundColor: "#FFF0F0"
    textColor: "{colors.danger}"
    rounded: "{rounded.sm}"
    padding: 8px
  success-chip:
    backgroundColor: "#EAF8F0"
    textColor: "{colors.success}"
    rounded: "{rounded.sm}"
    padding: 8px
---

## 概要

関西電力様向けのデモアプリは、エネルギーインフラ企業にふさわしい信頼性、堅実さ、監査可能性を前面に出す。見た目は派手なAI SaaSではなく、既存設計書を安全に読み解き、レビュー可能な統合仕様書へ変換する業務アプリとして設計する。

画面の主役は「AIらしさ」ではなく、アップロードされたExcelブック、複数シートの構造、抽出できた仕様、確認が必要なwarnings、出力されるMarkdownである。ユーザーが短時間で「このExcel設計書が、どの程度AI活用可能な文書になったか」を判断できることを最優先にする。

## 色

- **Primary `#0051A2`:** 関西電力様の公開サイトCSSで確認できる青系統をベースにした主色。信頼、堅牢、電力インフラの印象を担う。
- **Accent `#B94A00`:** 公開サイトCSSで確認できるオレンジ系統を、白文字でも読める濃度へ調整した補助色。主要CTA、変換進捗、選択中の導線だけに限定して使う。`#EB6100` は装飾線や小さなアクセントに限定する。
- **Surface colors:** 白と淡い青灰で、業務画面としての可読性を確保する。
- **Warning / danger:** warningsや未対応要素を隠さず示すため、落ち着いた黄・赤を使う。警告は目立たせるが不安を煽らない。

## タイポグラフィ

日本語の業務文書を読みやすくするため、`Noto Sans JP` 相当の角ゴシックを前提にする。英数字・件数・セル座標はInterまたはsystem-uiで高密度に見せ、セル座標やファイル名はmonoを補助的に使う。

見出しは大きくしすぎず、業務アプリとして情報量を確保する。営業デモ中にプロジェクター投影しても読めるよう、主要数値とアクションは強いコントラストで表示する。

## レイアウト

デモ画面は3カラムを基本にする。

1. 左: アップロード済みファイルとシート一覧
2. 中央: 選択シートのプレビューと抽出結果
3. 右: 統合Markdown、評価レポート、warnings、ダウンロード導線

アップロード直後の状態では、ブック全体の変換状況と成果物一覧を上部に表示する。ユーザーが「何ができたか」を先に理解できる構造にする。

## 奥行きと階層

影は薄く、境界線と余白で階層を作る。インフラ企業向けのため、過度なグラデーション、ガラス表現、浮遊感は避ける。カードはレビュー単位を明確に分けるために使う。

## 形状

角丸は中程度に抑える。過度に丸いSaaS表現は避け、`12px`〜`20px`を中心にした落ち着いた印象にする。表やプレビュー領域は角丸よりも罫線・セル座標の可読性を優先する。

## コンポーネント

- **Upload panel:** `.xlsx` 1ファイルを明確に受け付ける。機密文書を扱うため、ローカル処理・一時保存方針を短く添える。
- **Sheet list:** シート名、推定カテゴリ、warnings数を1行で表示する。選択中シートは淡い青背景にする。
- **Preview table:** Excel由来のセル座標を小さく表示し、元ファイルへの追跡性を示す。
- **Evaluation cards:** シート数、罫線ブロック数、入力規則数、warnings数を並べる。
- **Warnings panel:** 未対応・要確認を成功扱いしないための信頼コンポーネント。黄色系で表示し、件数と内容を短く見せる。
- **Download actions:** `book_specification.md`、`extracted.json`、`preview.html`、`evaluation.md`、ZIPを明確に分ける。

## 推奨事項と禁止事項

**推奨**

- 顧客向け画面では正式な事業文体を使う。
- 「既存設計書をAI活用可能な資産にする」と表現する。
- warningsと未対応要素を明示し、信頼性を高める。
- 関西電力様向けに、堅実・安全・監査可能な印象を優先する。

**禁止**

- 「Excelの代替」「Excelではできない」などの安い比較訴求を使わない。
- 内部メモ、開発都合、デモ用注釈、ミラ口調をUIに出さない。
- 派手なグラデーションやAI風の抽象装飾で業務価値を薄めない。
- 変換できない要素を成功扱いしない。
