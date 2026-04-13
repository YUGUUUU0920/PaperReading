from __future__ import annotations

from dataclasses import dataclass
from html import escape
from pathlib import Path
import argparse
import re
import shutil
import subprocess


SECTION_RE = re.compile(r"^##\s+(?P<title>.+)$")
DATE_RE = re.compile(r"(\d{4}-\d{2}-\d{2})")

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


def render_heatmap_svg(output_path: Path) -> None:
    cell_w = 112
    cell_h = 48
    left = 180
    top = 92
    width = left + cell_w * len(AXES) + 24
    height = top + cell_h * len(DEFAULT_SCORES) + 72
    rows = []
    for row_index, (name, values) in enumerate(DEFAULT_SCORES.items()):
        y = top + row_index * cell_h
        rows.append(
            f'<text x="{left - 16}" y="{y + 30}" text-anchor="end" font-size="16" fill="#1f1a14" font-family="Avenir Next, Segoe UI, sans-serif">{escape(name)}</text>'
        )
        for col_index, value in enumerate(values):
            x = left + col_index * cell_w
            rows.append(
                f'<rect x="{x}" y="{y}" rx="16" ry="16" width="{cell_w - 10}" height="{cell_h - 10}" fill="{COLORS[value]}" stroke="rgba(28,46,39,0.08)" />'
            )
            label_fill = "#ffffff" if value >= 4 else "#3c342b"
            rows.append(
                f'<text x="{x + (cell_w - 10)/2}" y="{y + 28}" text-anchor="middle" font-size="16" font-weight="700" fill="{label_fill}" font-family="Avenir Next, Segoe UI, sans-serif">{value}</text>'
            )
    header = []
    for index, axis in enumerate(AXES):
        x = left + index * cell_w + (cell_w - 10) / 2
        header.append(
            f'<text x="{x}" y="58" text-anchor="middle" font-size="15" fill="#5d5046" font-family="Avenir Next, Segoe UI, sans-serif">{escape(axis)}</text>'
        )
    legend = []
    for idx, value in enumerate(range(1, 6)):
        x = left + idx * 112
        legend.append(f'<rect x="{x}" y="{height - 42}" rx="10" ry="10" width="72" height="24" fill="{COLORS[value]}" />')
        legend.append(
            f'<text x="{x + 36}" y="{height - 25}" text-anchor="middle" font-size="12" font-weight="700" fill="{"#fff" if value >= 4 else "#3c342b"}" font-family="Avenir Next, Segoe UI, sans-serif">{value}</text>'
        )
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
  <rect width="100%" height="100%" rx="28" ry="28" fill="#fffdfa" />
  <text x="28" y="40" font-size="26" font-weight="700" fill="#1f1a14" font-family="Iowan Old Style, Palatino Linotype, serif">竞品能力热力图</text>
  <text x="28" y="68" font-size="14" fill="#6d5e51" font-family="Avenir Next, Segoe UI, sans-serif">5 = 很强，1 = 很弱。用于快速判断今天最值得借鉴的产品方向。</text>
  {''.join(header)}
  {''.join(rows)}
  {''.join(legend)}
</svg>
"""
    output_path.write_text(svg, encoding="utf-8")


def render_html(report: Report, chart_name: str) -> str:
    executive = bullets(report.sections.get("Executive summary", []))
    signals = bullets(report.sections.get("Competitor signals", []))
    adopt = bullets(report.sections.get("What we can adopt", []))
    changed = bullets(report.sections.get("What changed today", []))
    regression = bullets(report.sections.get("Regression", []))
    next_items = bullets(report.sections.get("Next candidate", []))
    sources = bullets(report.sections.get("Sources", []))
    intro = paragraphs(report.sections.get("Executive summary", []))

    def inline_markdown(text: str) -> str:
        escaped = escape(text)
        return re.sub(r"`([^`]+)`", r"<strong>\1</strong>", escaped)

    def render_list(items: list[str]) -> str:
        return "".join(f"<li>{inline_markdown(item)}</li>" for item in items)

    def render_source_links(items: list[str]) -> str:
        rows = []
        for item in items:
            if ": " in item:
                label, url = item.split(": ", 1)
                rows.append(f'<li><a href="{escape(url)}" target="_blank" rel="noreferrer">{escape(label)}</a></li>')
            else:
                rows.append(f"<li>{inline_markdown(item)}</li>")
        return "".join(rows)

    hero_text = intro[0] if intro else (executive[0] if executive else "今天的日报聚焦竞品信号、可吸收能力和已经落地的产品改动。")

    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escape(report.title)}</title>
  <style>
    :root {{
      --bg: #f5efe8;
      --panel: #fffdfa;
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
        radial-gradient(circle at top left, rgba(255,210,145,0.35), transparent 32%),
        radial-gradient(circle at top right, rgba(49,130,110,0.18), transparent 28%),
        linear-gradient(180deg, #f7f2ea 0%, #efe8df 100%);
      color: var(--text);
      font-family: "Avenir Next", "Segoe UI", sans-serif;
    }}
    main {{
      width: min(1180px, calc(100% - 32px));
      margin: 0 auto;
      padding: 32px 0 56px;
      display: grid;
      gap: 18px;
    }}
    .panel {{
      background: rgba(255,253,250,0.94);
      border: 1px solid var(--line);
      border-radius: 28px;
      box-shadow: var(--shadow);
      padding: 24px;
    }}
    .hero {{
      display: grid;
      grid-template-columns: 1.15fr 0.85fr;
      gap: 18px;
    }}
    h1, h2, h3 {{
      margin: 0;
      font-family: "Iowan Old Style", "Palatino Linotype", serif;
    }}
    h1 {{ font-size: clamp(36px, 5vw, 58px); line-height: 1.02; max-width: 11ch; }}
    h2 {{ font-size: 24px; margin-bottom: 10px; }}
    p, li {{ line-height: 1.75; color: var(--muted); }}
    ul {{ margin: 0; padding-left: 18px; display: grid; gap: 8px; }}
    .eyebrow {{
      text-transform: uppercase;
      letter-spacing: .14em;
      font-size: 12px;
      color: var(--accent);
      font-weight: 700;
      margin-bottom: 10px;
    }}
    .hero-kpis, .grid-two, .grid-three {{
      display: grid;
      gap: 14px;
    }}
    .hero-kpis {{
      grid-template-columns: repeat(3, minmax(0, 1fr));
      margin-top: 20px;
    }}
    .kpi {{
      border-radius: 20px;
      padding: 16px;
      background: linear-gradient(180deg, rgba(255,255,255,0.84), rgba(247,242,236,0.96));
      border: 1px solid rgba(21,111,99,0.08);
    }}
    .kpi strong {{ display: block; font-size: 28px; margin-bottom: 4px; }}
    .kpi span {{ color: var(--muted); font-size: 13px; }}
    .grid-two {{
      grid-template-columns: 1.05fr 0.95fr;
    }}
    .grid-three {{
      grid-template-columns: repeat(3, minmax(0, 1fr));
    }}
    .chip-row {{
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin-top: 14px;
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
    .source-list a {{ color: var(--accent); text-decoration: none; }}
    .chart img {{ width: 100%; height: auto; display: block; }}
    .print-note {{
      display: inline-flex;
      align-items: center;
      gap: 8px;
      color: var(--muted);
      font-size: 13px;
      margin-top: 18px;
    }}
    @media (max-width: 900px) {{
      .hero, .grid-two, .grid-three {{ grid-template-columns: 1fr; }}
      .hero-kpis {{ grid-template-columns: 1fr 1fr; }}
    }}
    @media print {{
      body {{ background: #fff; }}
      main {{ width: 100%; padding: 0; }}
      .panel {{ box-shadow: none; break-inside: avoid; }}
    }}
  </style>
</head>
<body>
  <main>
    <section class="panel hero">
      <div>
        <p class="eyebrow">Daily Product Brief</p>
        <h1>{escape(report.title)}</h1>
        <p>{inline_markdown(hero_text)}</p>
        <div class="chip-row">
          <span class="chip">竞品扫描</span>
          <span class="chip">结构化日报</span>
          <span class="chip">小步迭代</span>
        </div>
        <div class="hero-kpis">
          <article class="kpi"><strong>5</strong><span>观察产品</span></article>
          <article class="kpi"><strong>{len(adopt)}</strong><span>可借鉴方向</span></article>
          <article class="kpi"><strong>{len(changed)}</strong><span>今日动作</span></article>
        </div>
      </div>
      <div class="panel chart">
        <h2>竞品能力热力图</h2>
        <img src="{escape(chart_name)}" alt="竞品能力热力图">
        <p class="print-note">这份 HTML 可直接在浏览器里另存为 PDF。</p>
      </div>
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
        <h2>下一步最值得做</h2>
        <ul>{render_list(next_items)}</ul>
      </article>
    </section>

    <section class="grid-two">
      <article class="panel">
        <h2>回归结果</h2>
        <ul>{render_list(regression)}</ul>
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


def main() -> None:
    parser = argparse.ArgumentParser(description="Render a product iteration report into visual HTML and SVG.")
    parser.add_argument("--date", required=True)
    args = parser.parse_args()

    project_root = Path(__file__).resolve().parents[1]
    report_path = project_root / "reports" / "product-iterations" / f"{args.date}.md"
    report = parse_report(report_path)
    chart_path = report_path.with_name(f"{args.date}-heatmap.svg")
    png_path = report_path.with_name(f"{args.date}-heatmap.png")
    html_path = report_path.with_suffix(".html")

    render_heatmap_svg(chart_path)
    if shutil.which("sips"):
        subprocess.run(
            ["sips", "-s", "format", "png", str(chart_path), "--out", str(png_path)],
            check=False,
            capture_output=True,
        )
    html_path.write_text(render_html(report, chart_path.name), encoding="utf-8")

    print(html_path)
    print(chart_path)
    if png_path.exists():
        print(png_path)


if __name__ == "__main__":
    main()
