from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
from dataclasses import dataclass
from html import escape
from pathlib import Path


SECTION_RE = re.compile(r"^##\s+(?P<title>.+)$")
DATE_RE = re.compile(r"(\d{4}-\d{2}-\d{2})")
DESKTOP_DIR_NAME = "Research Atlas 日报"
DESKTOP_PDF_TEMPLATE = "{date} Research Atlas 产品迭代日报.pdf"
DESKTOP_HTML_TEMPLATE = "{date} Research Atlas 产品迭代日报.html"
DESKTOP_MANIFEST_NAME = "reports.json"
CHROME_CANDIDATES = [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "google-chrome",
    "chromium",
]

AXES = ["发现路径", "持续跟踪", "阅读辅助", "结构化输出", "工作区组织"]
DEFAULT_SCORES = {
    "Litmaps": [5, 5, 2, 2, 3],
    "ResearchRabbit": [5, 4, 3, 2, 5],
    "Semantic Scholar": [4, 5, 3, 3, 4],
    "Elicit": [3, 4, 4, 5, 4],
    "SciSpace": [3, 3, 5, 4, 3],
    "Research Atlas": [4, 2, 4, 4, 4],
}
COLORS = {
    1: "#efe7dd",
    2: "#dfd7cb",
    3: "#c7dbc9",
    4: "#8fbca1",
    5: "#2d7a68",
}


@dataclass
class Report:
    title: str
    date: str
    sections: dict[str, list[str]]


def parse_report(path: Path) -> Report:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    title = lines[0].lstrip("# ").strip() if lines else path.stem
    date_match = DATE_RE.search(title) or DATE_RE.search(path.name)
    report_date = date_match.group(1) if date_match else path.stem
    sections: dict[str, list[str]] = {}
    current = ""
    for line in lines[1:]:
        match = SECTION_RE.match(line)
        if match:
            current = match.group("title").strip()
            sections[current] = []
            continue
        if current:
            sections[current].append(line)
    return Report(title=title, date=report_date, sections=sections)


def bullets(lines: list[str]) -> list[str]:
    return [line[2:].strip() for line in lines if line.startswith("- ")]


def paragraphs(lines: list[str]) -> list[str]:
    output: list[str] = []
    current: list[str] = []
    for line in lines:
        if not line.strip():
            if current:
                output.append(" ".join(current).strip())
                current = []
            continue
        if line.startswith("- "):
            continue
        current.append(line.strip())
    if current:
        output.append(" ".join(current).strip())
    return output


def inline_markdown(text: str) -> str:
    escaped = escape(text)
    return re.sub(r"`([^`]+)`", r"<strong>\1</strong>", escaped)


def desktop_output_dir() -> Path:
    root = Path.home() / "Desktop" / DESKTOP_DIR_NAME
    root.mkdir(parents=True, exist_ok=True)
    return root


def summary_text(report: Report) -> str:
    executive = bullets(report.sections.get("Executive summary", []))
    if executive:
        return executive[0]
    intro = paragraphs(report.sections.get("Executive summary", []))
    if intro:
        return intro[0]
    return "今天的日报聚焦竞品信号、可吸收能力和已经落地的产品改动。"


def next_action_text(report: Report) -> str:
    next_items = bullets(report.sections.get("Next candidate", []))
    return next_items[0] if next_items else "继续把主题浏览升级成持续研究流。"


def build_heatmap_svg() -> str:
    cell_w = 116
    cell_h = 50
    left = 170
    top = 118
    width = left + cell_w * len(AXES) + 20
    height = top + cell_h * len(DEFAULT_SCORES) + 70

    header = []
    rows = []
    for index, axis in enumerate(AXES):
        x = left + index * cell_w + (cell_w - 12) / 2
        header.append(
            f'<text x="{x}" y="88" text-anchor="middle" font-size="15" fill="#5d5046" font-family="Avenir Next, Segoe UI, sans-serif">{escape(axis)}</text>'
        )

    for row_index, (name, values) in enumerate(DEFAULT_SCORES.items()):
        y = top + row_index * cell_h
        rows.append(
            f'<text x="{left - 14}" y="{y + 31}" text-anchor="end" font-size="16" fill="#1f1a14" font-family="Avenir Next, Segoe UI, sans-serif">{escape(name)}</text>'
        )
        for col_index, value in enumerate(values):
            x = left + col_index * cell_w
            rows.append(
                f'<rect x="{x}" y="{y}" rx="16" ry="16" width="{cell_w - 12}" height="{cell_h - 12}" fill="{COLORS[value]}" stroke="rgba(28,46,39,0.08)" />'
            )
            label_fill = "#ffffff" if value >= 4 else "#3c342b"
            rows.append(
                f'<text x="{x + (cell_w - 12) / 2}" y="{y + 28}" text-anchor="middle" font-size="16" font-weight="700" fill="{label_fill}" font-family="Avenir Next, Segoe UI, sans-serif">{value}</text>'
            )

    legend = []
    legend_x = left + 8
    for idx, value in enumerate(range(1, 6)):
        x = legend_x + idx * 112
        legend.append(f'<rect x="{x}" y="{height - 40}" rx="10" ry="10" width="72" height="24" fill="{COLORS[value]}" />')
        legend.append(
            f'<text x="{x + 36}" y="{height - 23}" text-anchor="middle" font-size="12" font-weight="700" fill="{"#fff" if value >= 4 else "#3c342b"}" font-family="Avenir Next, Segoe UI, sans-serif">{value}</text>'
        )

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="竞品能力热力图">
  <rect width="100%" height="100%" rx="28" ry="28" fill="#fffdfa" />
  <text x="28" y="40" font-size="25" font-weight="700" fill="#1f1a14" font-family="Iowan Old Style, Palatino Linotype, serif">竞品能力热力图</text>
  <text x="28" y="66" font-size="14" fill="#6d5e51" font-family="Avenir Next, Segoe UI, sans-serif">5 = 很强，1 = 很弱。用于快速判断今天最值得借鉴的产品方向。</text>
  {''.join(header)}
  {''.join(rows)}
  {''.join(legend)}
</svg>
"""


def render_source_links(items: list[str]) -> str:
    rows = []
    for item in items:
        if ": " in item:
            label, url = item.split(": ", 1)
            rows.append(f'<li><a href="{escape(url)}" target="_blank" rel="noreferrer">{escape(label)}</a></li>')
        else:
            rows.append(f"<li>{inline_markdown(item)}</li>")
    return "".join(rows)


def render_list(items: list[str]) -> str:
    return "".join(f"<li>{inline_markdown(item)}</li>" for item in items)


def render_html(report: Report, heatmap_svg: str) -> str:
    executive = bullets(report.sections.get("Executive summary", []))
    signals = bullets(report.sections.get("Competitor signals", []))
    adopt = bullets(report.sections.get("What we can adopt", []))
    changed = bullets(report.sections.get("What changed today", []))
    regression = bullets(report.sections.get("Regression", []))
    next_items = bullets(report.sections.get("Next candidate", []))
    sources = bullets(report.sections.get("Sources", []))
    intro = paragraphs(report.sections.get("Executive summary", []))
    hero_text = intro[0] if intro else summary_text(report)

    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escape(report.title)}</title>
  <style>
    :root {{
      --line: rgba(39, 31, 24, 0.12);
      --text: #1f1a14;
      --muted: #6d5e51;
      --accent: #156f63;
      --accent-soft: rgba(21, 111, 99, 0.1);
      --shadow: 0 24px 70px rgba(57, 38, 18, 0.08);
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      background:
        radial-gradient(circle at top left, rgba(255,210,145,0.32), transparent 30%),
        radial-gradient(circle at top right, rgba(49,130,110,0.18), transparent 24%),
        linear-gradient(180deg, #f7f2ea 0%, #efe8df 100%);
      color: var(--text);
      font-family: "Avenir Next", "Segoe UI", sans-serif;
    }}
    main {{
      width: min(1120px, calc(100% - 32px));
      margin: 0 auto;
      padding: 28px 0 52px;
      display: grid;
      gap: 18px;
    }}
    .panel {{
      background: rgba(255,253,250,0.95);
      border: 1px solid var(--line);
      border-radius: 28px;
      box-shadow: var(--shadow);
      padding: 22px;
    }}
    .hero {{
      display: grid;
      gap: 18px;
    }}
    .hero-top {{
      display: grid;
      grid-template-columns: minmax(0, 1.35fr) minmax(290px, 0.65fr);
      gap: 18px;
      align-items: start;
    }}
    .hero-copy {{
      display: grid;
      gap: 14px;
      min-width: 0;
    }}
    .hero-side {{
      display: grid;
      gap: 12px;
    }}
    h1, h2, h3 {{
      margin: 0;
      font-family: "Iowan Old Style", "Palatino Linotype", serif;
    }}
    h1 {{
      font-size: clamp(28px, 3.6vw, 40px);
      line-height: 1.08;
      max-width: 16ch;
      overflow-wrap: anywhere;
    }}
    h2 {{
      font-size: 24px;
      margin-bottom: 10px;
    }}
    h3 {{
      font-size: 20px;
      margin-bottom: 6px;
    }}
    p, li {{
      line-height: 1.78;
      color: var(--muted);
      margin: 0;
    }}
    ul {{
      margin: 0;
      padding-left: 18px;
      display: grid;
      gap: 8px;
    }}
    .eyebrow {{
      text-transform: uppercase;
      letter-spacing: .14em;
      font-size: 12px;
      color: var(--accent);
      font-weight: 700;
    }}
    .chip-row, .meta-row {{
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
    }}
    .chip {{
      display: inline-flex;
      min-height: 32px;
      padding: 0 12px;
      align-items: center;
      justify-content: center;
      border-radius: 999px;
      background: var(--accent-soft);
      color: var(--accent);
      font-weight: 700;
      font-size: 13px;
    }}
    .kpi-grid {{
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 10px;
    }}
    .kpi {{
      border-radius: 20px;
      padding: 16px;
      background: linear-gradient(180deg, rgba(255,255,255,0.88), rgba(247,242,236,0.98));
      border: 1px solid rgba(21,111,99,0.08);
    }}
    .kpi strong {{
      display: block;
      font-size: 28px;
      margin-bottom: 4px;
      color: var(--text);
    }}
    .kpi span {{
      color: var(--muted);
      font-size: 13px;
    }}
    .chart-shell {{
      display: grid;
      gap: 12px;
    }}
    .chart-frame {{
      overflow-x: auto;
      border-radius: 24px;
      background: linear-gradient(180deg, rgba(255,255,255,0.75), rgba(247,242,236,0.96));
      border: 1px solid rgba(21,111,99,0.08);
      padding: 14px;
    }}
    .chart-frame svg {{
      width: 100%;
      min-width: 740px;
      height: auto;
      display: block;
    }}
    .grid-two {{
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 18px;
    }}
    .grid-three {{
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 18px;
    }}
    .source-list a {{
      color: var(--accent);
      text-decoration: none;
    }}
    strong {{
      color: var(--text);
    }}
    .today-call {{
      padding: 18px;
      border-radius: 22px;
      background: linear-gradient(180deg, rgba(21,111,99,0.08), rgba(255,255,255,0.92));
      border: 1px solid rgba(21,111,99,0.12);
    }}
    @media (max-width: 900px) {{
      .hero-top, .grid-two, .grid-three {{
        grid-template-columns: 1fr;
      }}

      .kpi-grid {{
        grid-template-columns: repeat(3, minmax(0, 1fr));
      }}

      h1 {{
        max-width: none;
      }}
    }}
    @media (max-width: 680px) {{
      main {{
        width: min(100% - 16px, 1120px);
        padding-top: 16px;
      }}

      .panel {{
        padding: 18px;
        border-radius: 22px;
      }}

      .kpi-grid {{
        grid-template-columns: 1fr;
      }}
    }}
    @media print {{
      @page {{
        size: A4;
        margin: 12mm;
      }}

      body {{
        background: #fff;
      }}

      main {{
        width: 100%;
        padding: 0;
      }}

      .panel {{
        box-shadow: none;
        break-inside: avoid;
      }}

      .chart-shell {{
        break-before: page;
      }}

      .grid-two {{
        break-inside: avoid;
      }}
    }}
  </style>
</head>
<body>
  <main>
    <section class="panel hero">
      <div class="hero-top">
        <div class="hero-copy">
          <p class="eyebrow">Daily Product Brief</p>
          <h1>{escape(report.title)}</h1>
          <p>{inline_markdown(hero_text)}</p>
          <div class="chip-row">
            <span class="chip">竞品扫描</span>
            <span class="chip">结构化日报</span>
            <span class="chip">小步迭代</span>
          </div>
        </div>
        <aside class="hero-side">
          <div class="today-call">
            <h3>今日建议</h3>
            <p>{inline_markdown(next_items[0] if next_items else "继续把主题浏览升级成持续研究流。")}</p>
          </div>
        </aside>
      </div>
      <div class="kpi-grid">
        <article class="kpi"><strong>5</strong><span>观察产品</span></article>
        <article class="kpi"><strong>{len(adopt)}</strong><span>可借鉴方向</span></article>
        <article class="kpi"><strong>{len(changed)}</strong><span>今日动作</span></article>
      </div>
    </section>

    <section class="panel chart-shell">
      <div class="meta-row">
        <span class="chip">竞品能力热力图</span>
        <span class="chip">可打印</span>
        <span class="chip">日报归档</span>
      </div>
      <div class="chart-frame">
        {heatmap_svg}
      </div>
      <p>这份日报已经做成自包含 HTML 文件，直接双击即可阅读，也可以在浏览器里打印为 PDF。</p>
    </section>

    <section class="grid-two">
      <article class="panel">
        <h2>竞品信号</h2>
        <ul>{render_list(signals)}</ul>
      </article>
      <article class="panel">
        <h2>我们该吸收什么</h2>
        <ul>{render_list(adopt)}</ul>
      </article>
    </section>

    <section class="grid-two">
      <article class="panel">
        <h2>今天已经做了什么</h2>
        <ul>{render_list(changed)}</ul>
      </article>
      <article class="panel">
        <h2>回归结果</h2>
        <ul>{render_list(regression)}</ul>
      </article>
    </section>

    <section class="grid-two">
      <article class="panel">
        <h2>下一步最值得做</h2>
        <ul>{render_list(next_items)}</ul>
      </article>
      <article class="panel source-list">
        <h2>官方来源</h2>
        <ul>{render_source_links(sources)}</ul>
      </article>
    </section>
  </main>
</body>
</html>
"""


def load_archive_entries(output_dir: Path) -> list[dict[str, str]]:
    manifest_path = output_dir / DESKTOP_MANIFEST_NAME
    if not manifest_path.exists():
        return []
    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []
    if not isinstance(payload, list):
        return []
    entries: list[dict[str, str]] = []
    for item in payload:
        if not isinstance(item, dict):
            continue
        required = {"date", "title", "summary", "next_action", "filename", "kind"}
        if not required.issubset(item):
            continue
        entries.append({key: str(item[key]) for key in required})
    return entries


def save_archive_entries(output_dir: Path, entries: list[dict[str, str]]) -> None:
    manifest_path = output_dir / DESKTOP_MANIFEST_NAME
    manifest_path.write_text(
        json.dumps(entries, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def upsert_archive_entry(output_dir: Path, entry: dict[str, str]) -> list[dict[str, str]]:
    entries = [item for item in load_archive_entries(output_dir) if item.get("date") != entry["date"]]
    entries.append(entry)
    entries.sort(key=lambda item: item["date"], reverse=True)
    save_archive_entries(output_dir, entries)
    return entries


def render_archive_index(output_dir: Path, entries: list[dict[str, str]]) -> Path:
    cards = []
    for item in entries:
        action_label = "打开 PDF" if item["kind"] == "pdf" else "打开 HTML"
        cards.append(
            f"""
            <article class="card">
              <div class="card-top">
                <div>
                  <p class="eyebrow">{escape(item["date"])}</p>
                  <h3>{escape(item["title"])}</h3>
                </div>
                <span class="chip">{'每日 PDF' if item["kind"] == "pdf" else '自包含 HTML'}</span>
              </div>
              <p>{inline_markdown(item["summary"])}</p>
              <div class="hint">
                <strong>下一步</strong>
                <span>{inline_markdown(item["next_action"])}</span>
              </div>
              <a class="button" href="{escape(item["filename"])}">{action_label}</a>
            </article>
            """
        )
    html = f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Research Atlas 日报归档</title>
  <style>
    body {{
      margin: 0;
      font-family: "Avenir Next", "Segoe UI", sans-serif;
      background: linear-gradient(180deg, #f7f2ea 0%, #efe8df 100%);
      color: #1f1a14;
    }}
    main {{
      width: min(860px, calc(100% - 32px));
      margin: 0 auto;
      padding: 32px 0 56px;
      display: grid;
      gap: 18px;
    }}
    .panel {{
      background: rgba(255,253,250,0.95);
      border: 1px solid rgba(39,31,24,0.12);
      border-radius: 24px;
      padding: 22px;
      box-shadow: 0 18px 48px rgba(57, 38, 18, 0.08);
    }}
    h1, h2, h3 {{
      margin: 0 0 10px;
      font-family: "Iowan Old Style", "Palatino Linotype", serif;
    }}
    p, li {{
      line-height: 1.7;
      color: #6d5e51;
    }}
    .eyebrow {{
      margin: 0 0 6px;
      color: #156f63;
      text-transform: uppercase;
      letter-spacing: .12em;
      font-size: 12px;
      font-weight: 700;
    }}
    .grid {{
      display: grid;
      gap: 16px;
    }}
    .card-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
      gap: 16px;
    }}
    .card {{
      border-radius: 22px;
      padding: 18px;
      border: 1px solid rgba(21,111,99,0.08);
      background: linear-gradient(180deg, rgba(255,255,255,0.92), rgba(247,242,236,0.98));
      display: grid;
      gap: 12px;
    }}
    .card-top {{
      display: flex;
      align-items: start;
      justify-content: space-between;
      gap: 12px;
    }}
    .chip {{
      display: inline-flex;
      align-items: center;
      justify-content: center;
      min-height: 28px;
      padding: 0 10px;
      border-radius: 999px;
      background: rgba(21,111,99,0.1);
      color: #156f63;
      font-size: 12px;
      font-weight: 700;
      white-space: nowrap;
    }}
    .hint {{
      display: grid;
      gap: 4px;
      padding: 12px 14px;
      border-radius: 18px;
      background: rgba(21,111,99,0.06);
      border: 1px solid rgba(21,111,99,0.08);
    }}
    .hint strong {{
      font-size: 13px;
      color: #1f1a14;
    }}
    .button {{
      display: inline-flex;
      width: fit-content;
      min-height: 38px;
      padding: 0 14px;
      align-items: center;
      justify-content: center;
      border-radius: 999px;
      background: #156f63;
      color: #fff;
      text-decoration: none;
      font-weight: 700;
    }}
    .meta {{
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
    }}
    .meta span {{
      display: inline-flex;
      min-height: 30px;
      align-items: center;
      padding: 0 12px;
      border-radius: 999px;
      background: rgba(21,111,99,0.08);
      color: #156f63;
      font-size: 13px;
      font-weight: 700;
    }}
    ul {{
      margin: 0;
      padding-left: 18px;
      display: grid;
      gap: 10px;
    }}
    a {{
      color: #156f63;
      text-decoration: none;
      font-weight: 700;
    }}
  </style>
</head>
<body>
  <main>
    <section class="panel">
      <h1>Research Atlas 日报归档</h1>
      <p>这里会保存每天生成的阅读版日报。主交付优先是 PDF，仓库里继续保留 HTML 与图表源文件，方便追溯和继续加工。</p>
      <div class="meta">
        <span>桌面归档</span>
        <span>每日阅读</span>
        <span>结构化简报</span>
      </div>
    </section>
    <section class="panel">
      <h2>日报列表</h2>
      <div class="grid">{''.join(cards) if cards else '<p>还没有日报</p>'}</div>
    </section>
  </main>
</body>
</html>
"""
    index_path = output_dir / "index.html"
    index_path.write_text(html, encoding="utf-8")
    return index_path


def find_chrome_binary() -> str | None:
    for candidate in CHROME_CANDIDATES:
        if "/" in candidate:
            if Path(candidate).exists():
                return candidate
            continue
        resolved = shutil.which(candidate)
        if resolved:
            return resolved
    return None


def export_pdf(source_html: Path, output_pdf: Path) -> bool:
    chrome = find_chrome_binary()
    if chrome is None:
        return False

    output_pdf.parent.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(
        [
            chrome,
            "--headless",
            "--disable-gpu",
            "--no-first-run",
            "--no-default-browser-check",
            "--no-pdf-header-footer",
            "--print-to-pdf-no-header",
            f"--print-to-pdf={output_pdf}",
            source_html.resolve().as_uri(),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    return result.returncode == 0 and output_pdf.exists() and output_pdf.stat().st_size > 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Render a product iteration report into visual HTML and desktop archive files.")
    parser.add_argument("--date", required=True)
    args = parser.parse_args()

    project_root = Path(__file__).resolve().parents[1]
    report_path = project_root / "reports" / "product-iterations" / f"{args.date}.md"
    report = parse_report(report_path)

    heatmap_svg = build_heatmap_svg()
    repo_svg_path = report_path.with_name(f"{args.date}-heatmap.svg")
    repo_png_path = report_path.with_name(f"{args.date}-heatmap.png")
    repo_html_path = report_path.with_suffix(".html")

    repo_svg_path.write_text(heatmap_svg, encoding="utf-8")
    if shutil.which("sips"):
        subprocess.run(
            ["sips", "-s", "format", "png", str(repo_svg_path), "--out", str(repo_png_path)],
            check=False,
            capture_output=True,
        )

    repo_html_path.write_text(render_html(report, heatmap_svg), encoding="utf-8")

    desktop_dir = desktop_output_dir()
    desktop_pdf_path = desktop_dir / DESKTOP_PDF_TEMPLATE.format(date=report.date)
    desktop_html_path = desktop_dir / DESKTOP_HTML_TEMPLATE.format(date=report.date)

    if export_pdf(repo_html_path, desktop_pdf_path):
        desktop_primary_path = desktop_pdf_path
        if desktop_html_path.exists():
            desktop_html_path.unlink()
        output_kind = "pdf"
    else:
        desktop_html_path.write_text(render_html(report, heatmap_svg), encoding="utf-8")
        if desktop_pdf_path.exists():
            desktop_pdf_path.unlink()
        desktop_primary_path = desktop_html_path
        output_kind = "html"

    archive_entries = upsert_archive_entry(
        desktop_dir,
        {
            "date": report.date,
            "title": report.title,
            "summary": summary_text(report),
            "next_action": next_action_text(report),
            "filename": desktop_primary_path.name,
            "kind": output_kind,
        },
    )
    archive_index_path = render_archive_index(desktop_dir, archive_entries)

    print(repo_html_path)
    print(repo_svg_path)
    if repo_png_path.exists():
        print(repo_png_path)
    print(desktop_primary_path)
    print(archive_index_path)


if __name__ == "__main__":
    main()
