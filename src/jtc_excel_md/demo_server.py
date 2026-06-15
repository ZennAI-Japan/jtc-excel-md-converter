from __future__ import annotations

import argparse
import json
import mimetypes
import tempfile
from html import escape
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlparse

from .converter import convert_workbook, write_outputs

ARTIFACTS = [
    ("book_specification.md", "統合Markdown仕様書"),
    ("extracted.json", "構造化データ"),
    ("preview.html", "セル座標付きレビュー画面"),
    ("evaluation.md", "変換評価レポート"),
    ("warnings.md", "要確認事項"),
    ("package.zip", "一括ダウンロード"),
]


def render_demo_html(result: dict[str, Any], *, output_dir: str | Path) -> str:
    """Render the local enterprise demo page from converter output."""
    output_path = Path(output_dir)
    sheets = result.get("sheets", [])
    warnings = result.get("warnings", [])
    metrics = _build_metrics(sheets, warnings, output_path)
    active_sheet = sheets[0] if sheets else {"name": "未選択", "blocks": [], "validations": [], "titles": []}
    active_block = active_sheet.get("blocks", [{}])[0] if active_sheet.get("blocks") else {}
    source_name = Path(str(result.get("source", "設計書.xlsx"))).name

    return f"""<!doctype html>
<html lang="ja">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>関西電力様向け 設計書ドキュメント化プラットフォーム</title>
  <style>{_styles()}</style>
</head>
<body>
  <main class="page">
    <header class="header">
      <div class="brand">
        <div class="brand-mark" aria-hidden="true"></div>
        <div>
          <h1>設計書ドキュメント化プラットフォーム</h1>
          <p>関西電力様向け 複数シートExcel解析</p>
        </div>
      </div>
      <nav class="header-actions" aria-label="主要操作">
        <span class="security-note">ローカル解析・外部送信なし</span>
        <a class="btn primary" href="/artifacts/preview.html">Preview</a>
        <a class="btn accent" href="/artifacts/package.zip">成果物をダウンロード</a>
      </nav>
    </header>

    <section class="hero">
      <div class="hero-card">
        <div class="eyebrow">DOCUMENT INTELLIGENCE</div>
        <h2>複数シートに分かれたExcel設計書を、<span class="nowrap">レビュー可能な統合仕様書</span>へ変換します。</h2>
        <p class="lead">罫線・結合セル・入力規則・コメント・セル座標を保持し、Markdown / JSON / HTML Preview / 評価レポートとして出力します。変換できない要素はwarningsとして明示します。</p>
      </div>
      <div class="upload-box">
        <div class="upload-title">変換対象ファイル</div>
        <div class="file-pill">
          <div class="file-icon">XLSX</div>
          <div>
            <div class="file-name">{escape(source_name)}</div>
            <div class="file-meta">{len(sheets)}シート・成果物 {metrics['artifact_count']}件・要確認 {len(warnings)}件</div>
          </div>
        </div>
        <a class="btn primary" href="/artifacts/book_specification.md">統合仕様書を開く</a>
      </div>
    </section>

    <section class="metrics" aria-label="変換評価サマリー">
      {_render_metric('認識シート', len(sheets), 'ブック全体')}
      {_render_metric('罫線ブロック', metrics['block_count'], '表・一覧')}
      {_render_metric('入力規則', metrics['validation_count'], 'プルダウン候補')}
      {_render_metric('要確認', len(warnings), 'warnings', warn=True)}
      {_render_metric('成果物', metrics['artifact_count'], 'Markdown / JSON 等')}
    </section>

    <section class="workspace">
      <aside class="panel">
        <div class="panel-header"><h3>シート構成</h3><span>{len(sheets)} SHEETS</span></div>
        <div class="sheet-list">{_render_sheet_list(sheets)}</div>
      </aside>

      <section class="panel">
        <div class="panel-header"><h3>変換プレビュー</h3><span>{escape(active_sheet.get('name', ''))}</span></div>
        <div class="preview-area">
          <div class="preview-toolbar"><span class="tab active">Preview</span><span class="panel-kicker">Source range: {escape(str(active_block.get('range', '未検出')))}</span></div>
          {_render_preview_table(active_block)}
          <div class="markdown-preview">
            <div class="md-title"># {escape(_first_title(active_sheet))}</div>
            <div>## {escape(active_sheet.get('name', ''))} / {escape(str(active_block.get('range', '')))}</div>
            <div class="md-accent">- 入力規則: {metrics['validation_count']}件</div>
            <div>- warnings: {len(warnings)}件</div>
            <div>- 出力: book_specification.md / extracted.json / preview.html / evaluation.md</div>
          </div>
        </div>
      </section>

      <aside class="panel">
        <div class="panel-header"><h3>成果物と確認事項</h3><span>READY</span></div>
        <div class="side-content">
          {_render_artifacts(output_path)}
          <div class="artifact warn"><strong>warnings.md</strong><span>変換時の要確認事項</span>{_render_warning_list(warnings)}</div>
        </div>
      </aside>
    </section>

    <div class="footer-note">
      <span>関西電力様向けの業務利用を想定した、監査可能なドキュメント化デモです。</span>
      <span>安全性: 初期デモでは外部LLM APIへ文書内容を送信しません。</span>
    </div>
  </main>
</body>
</html>
"""


def build_demo_response(result: dict[str, Any], *, output_dir: str | Path) -> tuple[int, dict[str, str], bytes]:
    body = render_demo_html(result, output_dir=output_dir).encode("utf-8")
    return 200, {"Content-Type": "text/html; charset=utf-8", "Content-Length": str(len(body))}, body


def build_artifact_response(output_dir: str | Path, request_path: str) -> tuple[int, dict[str, str], bytes]:
    parsed = urlparse(request_path)
    prefix = "/artifacts/"
    if not parsed.path.startswith(prefix):
        return _not_found()
    name = Path(unquote(parsed.path[len(prefix) :])).name
    allowed = {artifact for artifact, _label in ARTIFACTS} | {"specification.md"}
    if name not in allowed:
        return _not_found()
    path = Path(output_dir) / name
    if not path.exists() or not path.is_file():
        return _not_found()
    content_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    if path.suffix == ".md":
        content_type = "text/markdown; charset=utf-8"
    body = path.read_bytes()
    return 200, {"Content-Type": content_type, "Content-Length": str(len(body))}, body


def serve(workbook: str | Path, *, output_dir: str | Path | None = None, host: str = "127.0.0.1", port: int = 8765) -> None:
    workbook_path = Path(workbook)
    out = Path(output_dir) if output_dir else Path(tempfile.mkdtemp(prefix="jtc-md-demo-"))
    result = convert_workbook(workbook_path)
    write_outputs(result, out)

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802 - stdlib API
            if self.path == "/" or self.path.startswith("/?"):
                self._send(*build_demo_response(result, output_dir=out))
            elif self.path.startswith("/artifacts/"):
                self._send(*build_artifact_response(out, self.path))
            else:
                self._send(*_not_found())

        def log_message(self, format: str, *args: object) -> None:  # noqa: A002 - stdlib API
            return

        def _send(self, status: int, headers: dict[str, str], body: bytes) -> None:
            self.send_response(status)
            for key, value in headers.items():
                self.send_header(key, value)
            self.end_headers()
            self.wfile.write(body)

    server = ThreadingHTTPServer((host, port), Handler)
    print(f"serving: http://{host}:{server.server_port}")
    print(f"artifacts: {out}")
    server.serve_forever()


def main() -> None:
    parser = argparse.ArgumentParser(description="Serve the local KEPCO-style document conversion demo UI.")
    parser.add_argument("input", type=Path, help="Input .xlsx file")
    parser.add_argument("--out", type=Path, default=Path("outputs/demo-app"), help="Output directory")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    serve(args.input, output_dir=args.out, host=args.host, port=args.port)


def _not_found() -> tuple[int, dict[str, str], bytes]:
    body = b"not found"
    return 404, {"Content-Type": "text/plain; charset=utf-8", "Content-Length": str(len(body))}, body


def _build_metrics(sheets: list[dict[str, Any]], warnings: list[str], output_path: Path) -> dict[str, int]:
    del warnings
    return {
        "block_count": sum(len(sheet.get("blocks", [])) for sheet in sheets),
        "validation_count": sum(len(sheet.get("validations", [])) for sheet in sheets),
        "artifact_count": sum(1 for name, _ in ARTIFACTS if (output_path / name).exists()),
    }


def _render_metric(label: str, value: int, sub: str, *, warn: bool = False) -> str:
    warn_class = " warn" if warn else ""
    return f'<div class="metric{warn_class}"><div class="label">{escape(label)}</div><div class="value">{value}</div><div class="sub">{escape(sub)}</div></div>'


def _render_sheet_list(sheets: list[dict[str, Any]]) -> str:
    if not sheets:
        return '<div class="sheet-row active"><div class="sheet-name">シート未検出</div></div>'
    rows = []
    for index, sheet in enumerate(sheets):
        classes = "sheet-row active" if index == 0 else "sheet-row"
        rows.append(
            f'<div class="{classes}"><div class="sheet-top"><span class="sheet-name">{escape(sheet.get("name", ""))}</span>'
            f'<span class="sheet-type">{len(sheet.get("blocks", []))} blocks</span></div>'
            f'<div class="sheet-detail">入力規則 {len(sheet.get("validations", []))}・見出し {len(sheet.get("titles", []))}</div></div>'
        )
    return "".join(rows)


def _render_preview_table(block: dict[str, Any]) -> str:
    headers = block.get("headers") or []
    rows = block.get("rows") or []
    if not headers or not rows:
        return '<div class="empty-state">表形式ブロックは検出されませんでした。</div>'
    header_html = "".join(f"<th>{escape(str(header))}</th>" for header in headers)
    row_html = []
    for row in rows[:5]:
        row_html.append("<tr>" + "".join(f"<td>{escape(str(row.get(header, '')))}</td>" for header in headers) + "</tr>")
    return f'<div class="excel-preview"><table><thead><tr>{header_html}</tr></thead><tbody>{"".join(row_html)}</tbody></table></div>'


def _render_artifacts(output_path: Path) -> str:
    cards = []
    for name, label in ARTIFACTS:
        exists_label = "生成済み" if (output_path / name).exists() else "未生成"
        cards.append(f'<a class="artifact ready" href="/artifacts/{escape(name)}"><strong>{escape(name)}</strong><span>{escape(label)}・{exists_label}</span></a>')
    return "".join(cards)


def _render_warning_list(warnings: list[str]) -> str:
    items = warnings or ["要確認項目は検出されませんでした。"]
    return '<div class="warning-list">' + "".join(f'<div class="warning-item">{escape(item)}</div>' for item in items[:6]) + "</div>"


def _first_title(sheet: dict[str, Any]) -> str:
    titles = sheet.get("titles") or []
    if titles:
        return str(titles[0].get("text", sheet.get("name", "")))
    return str(sheet.get("name", ""))


def _styles() -> str:
    return """
:root{--primary:#0051A2;--primary-dark:#054385;--accent:#B94A00;--accent-decorative:#EB6100;--success:#0C7A43;--warning:#8A5200;--ink:#172033;--muted:#5E6B7A;--border:#D8E0EA;--surface:#FFFFFF;--surface-soft:#F5F8FB;--surface-blue:#EAF4FF;--surface-orange:#FFF4EB;--shadow:0 18px 60px rgba(23,32,51,.10)}*{box-sizing:border-box}body{margin:0;min-height:100vh;background:linear-gradient(180deg,#F7FAFD 0%,#EFF5FB 100%);color:var(--ink);font-family:Inter,"Noto Sans JP",-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;line-height:1.65}.page{max-width:1440px;min-height:900px;margin:0 auto;padding:28px;background:radial-gradient(circle at 88% 8%,rgba(0,81,162,.13),transparent 28%),linear-gradient(180deg,rgba(255,255,255,.7),rgba(245,248,251,.9))}.header{display:flex;align-items:center;justify-content:space-between;padding:18px 22px;background:rgba(255,255,255,.90);border:1px solid var(--border);border-radius:24px;box-shadow:0 12px 36px rgba(23,32,51,.06)}.brand{display:flex;align-items:center;gap:14px}.brand-mark{width:42px;height:42px;border-radius:12px;background:linear-gradient(135deg,var(--primary),var(--primary-dark));position:relative}.brand-mark:after{content:"";position:absolute;right:-4px;bottom:7px;width:20px;height:6px;border-radius:999px;background:var(--accent-decorative);transform:rotate(-28deg)}h1{margin:0;font-size:20px;line-height:1.25;letter-spacing:-.02em}.brand p{margin:2px 0 0;font-size:12px;color:var(--muted)}.header-actions{display:flex;gap:10px;align-items:center}.security-note{padding:9px 12px;color:var(--primary-dark);background:var(--surface-blue);border-radius:999px;font-size:12px;font-weight:700}.btn{display:inline-block;text-decoration:none;border-radius:12px;padding:12px 16px;font-weight:700;font-size:13px}.btn.primary{background:var(--primary);color:#fff}.btn.accent{background:var(--accent);color:#fff}.hero{display:grid;grid-template-columns:1.05fr .95fr;gap:22px;margin:22px 0}.hero-card,.upload-box,.panel,.metric{background:var(--surface);border:1px solid var(--border);box-shadow:var(--shadow)}.hero-card{border-radius:28px;padding:28px}.eyebrow{display:inline-flex;gap:8px;align-items:center;margin-bottom:14px;color:var(--primary-dark);font-size:12px;font-weight:800;letter-spacing:.08em}.eyebrow:before{content:"";width:22px;height:4px;border-radius:99px;background:var(--accent-decorative)}h2{margin:0;max-width:760px;font-size:34px;line-height:1.22;letter-spacing:-.025em}.nowrap{white-space:nowrap}.lead{margin:14px 0 0;color:var(--muted);font-size:15px;max-width:780px}.upload-box{display:grid;grid-template-rows:auto 1fr auto;gap:15px;border-style:dashed;border-radius:24px;padding:22px;background:linear-gradient(180deg,#fff,#F8FBFF)}.upload-title{font-weight:800;font-size:16px}.file-pill{align-self:center;display:flex;align-items:center;gap:12px;padding:18px;border:1px solid var(--border);border-radius:18px;background:white}.file-icon{width:42px;height:52px;border-radius:8px;background:linear-gradient(180deg,#EAF4FF,#D7E9FB);border:1px solid #BFD7F0;display:grid;place-items:center;font-size:13px;font-weight:900;color:var(--primary-dark)}.file-name{font-weight:800}.file-meta{font-size:12px;color:var(--muted)}.metrics{display:grid;grid-template-columns:repeat(5,1fr);gap:12px;margin-bottom:22px}.metric{border-radius:20px;padding:16px;min-height:104px}.metric .label{color:var(--muted);font-size:12px;font-weight:700}.metric .value{margin-top:7px;font-size:30px;line-height:1;font-weight:800;letter-spacing:-.03em;color:var(--primary-dark)}.metric .sub{margin-top:8px;color:var(--muted);font-size:12px}.metric.warn .value{color:var(--warning)}.workspace{display:grid;grid-template-columns:290px 1fr 330px;gap:18px;align-items:stretch}.panel{border-radius:24px;overflow:hidden}.panel-header{display:flex;justify-content:space-between;align-items:center;padding:16px 18px;border-bottom:1px solid var(--border);background:#FBFDFF}.panel-header h3{margin:0;font-size:14px;font-weight:800}.panel-header span,.panel-kicker{font-size:11px;color:var(--muted);font-weight:700}.sheet-list{padding:10px;display:grid;gap:8px}.sheet-row{padding:12px;border-radius:14px;border:1px solid transparent;display:grid;gap:4px;background:#fff}.sheet-row.active{background:var(--surface-blue);border-color:#BBD8F4}.sheet-top{display:flex;justify-content:space-between;align-items:center;gap:10px}.sheet-name{font-weight:800;font-size:13px}.sheet-type{font-size:11px;color:var(--primary-dark);font-weight:800}.sheet-detail{color:var(--muted);font-size:11px}.preview-area{padding:18px}.preview-toolbar{display:flex;justify-content:space-between;align-items:center;margin-bottom:14px}.tab{padding:8px 12px;border-radius:999px;font-size:12px;font-weight:800;color:#fff;background:var(--primary)}.excel-preview{border:1px solid #BAC9D8;border-radius:18px;overflow:hidden;background:#fff}table{width:100%;border-collapse:collapse;table-layout:fixed}th,td{border:1px solid #C9D5E2;padding:10px 8px;vertical-align:top;font-size:12px}th{background:#F1F6FB;color:var(--primary-dark);font-weight:800}.markdown-preview{margin-top:14px;border-radius:18px;background:#101C2D;color:#EAF4FF;padding:16px;font-family:"SFMono-Regular","Roboto Mono",monospace;font-size:12px;line-height:1.65;min-height:150px}.md-title{color:#fff;font-weight:900}.md-accent{color:#FFBE91}.side-content{padding:16px;display:grid;gap:14px}.artifact{display:block;text-decoration:none;color:var(--ink);border:1px solid var(--border);border-radius:16px;padding:14px;background:#fff}.artifact strong{display:block;font-size:13px;margin-bottom:3px}.artifact span{color:var(--muted);font-size:12px}.artifact.ready{border-color:#BFE2CE;background:#F3FBF6}.artifact.warn{border-color:#F1D8AB;background:var(--surface-orange)}.warning-list{display:grid;gap:8px;margin-top:10px}.warning-item{padding:10px;border-radius:12px;background:#fff;color:var(--warning);font-size:12px;font-weight:700}.footer-note{margin-top:18px;display:flex;justify-content:space-between;align-items:center;color:var(--muted);font-size:12px;padding:0 6px}.empty-state{border:1px dashed var(--border);border-radius:18px;padding:28px;color:var(--muted);background:#fff}@media(max-width:1000px){.page{padding:16px}.header,.hero,.workspace{display:block}.header-actions{margin-top:14px;flex-wrap:wrap}.hero-card,.upload-box,.panel{margin-bottom:16px}.metrics{grid-template-columns:repeat(2,1fr)}}
"""


if __name__ == "__main__":
    main()
