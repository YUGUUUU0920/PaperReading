import { escapeHtml } from "../utils/dom.js";
import { buildLineageUrl, buildPaperUrl, buildSearchUrl } from "../utils/url.js";
import { getTagTone, getThemeMeta, toTagId } from "../utils/tags.js";

const NODE_WIDTH = 248;
const NODE_HEIGHT = 236;
const STAGE_PADDING_X = 92;
const YEAR_GAP = 252;
const LANE_GAP = 276;
const VERTICAL_PADDING = 92;

function toneOf(theme) {
  return getThemeMeta(theme).tone;
}

function renderTagPill(tag) {
  return `<span class="pill pill--tag" data-tone="${getTagTone(tag)}">${escapeHtml(tag)}</span>`;
}

function renderSignals(signals = []) {
  if (!signals.length) return "";
  return `<div class="signal-row">${signals.map((item) => `<span class="signal">${escapeHtml(item)}</span>`).join("")}</div>`;
}

function buildStageLayout(lineage) {
  const maxLane = Math.max(1, ...lineage.nodes.map((node) => Math.abs(node.lane || 0)));
  const centerY = VERTICAL_PADDING + maxLane * LANE_GAP;
  const width = STAGE_PADDING_X * 2 + Math.max(0, lineage.years.length - 1) * YEAR_GAP + NODE_WIDTH;
  const height = centerY + maxLane * LANE_GAP + NODE_HEIGHT + VERTICAL_PADDING;
  const positions = {};
  for (const node of lineage.nodes) {
    positions[node.id] = {
      x: STAGE_PADDING_X + (node.year_index || 0) * YEAR_GAP,
      y: centerY + (node.lane || 0) * LANE_GAP,
    };
  }
  return {
    width,
    height,
    centerLine: centerY + NODE_HEIGHT / 2,
    positions,
  };
}

function linkPath(from, to) {
  const sameColumn = Math.abs(to.x - from.x) < 12;
  if (sameColumn) {
    const startX = from.x + NODE_WIDTH * 0.62;
    const startY = from.y + NODE_HEIGHT * 0.18;
    const endX = to.x + NODE_WIDTH * 0.62;
    const endY = to.y + NODE_HEIGHT * 0.82;
    const controlX = startX + 58;
    const controlY = (startY + endY) / 2;
    return `M ${startX} ${startY} C ${controlX} ${startY}, ${controlX} ${endY}, ${endX} ${endY}`;
  }

  const startX = from.x + NODE_WIDTH - 12;
  const startY = from.y + NODE_HEIGHT * 0.52;
  const endX = to.x + 12;
  const endY = to.y + NODE_HEIGHT * 0.52;
  const bend = Math.max(72, Math.abs(endX - startX) * 0.34);
  return `M ${startX} ${startY} C ${startX + bend} ${startY}, ${endX - bend} ${endY}, ${endX} ${endY}`;
}

function renderYearBands(lineage, layout) {
  return lineage.years
    .map((year, index) => {
      const left = STAGE_PADDING_X + index * YEAR_GAP;
      return `
        <div class="lineage-year-band" style="left:${left}px;">
          <strong>${escapeHtml(year)}</strong>
        </div>
      `;
    })
    .join("");
}

function renderLinks(lineage, layout) {
  return lineage.links
    .map((link, index) => {
      const from = layout.positions[link.from];
      const to = layout.positions[link.to];
      if (!from || !to) return "";
      return `
        <path
          class="lineage-link lineage-link--${escapeHtml(link.kind || "branch")}"
          style="animation-delay:${120 + index * 70}ms;"
          d="${linkPath(from, to)}"
        ></path>
      `;
    })
    .join("");
}

function renderNode(node, layout) {
  const position = layout.positions[node.id];
  if (!position) return "";
  const themeTone = toneOf(node.theme);
  const href = buildPaperUrl(node.paper_id, {
    conference: node.conference,
    year: node.year,
  });
  const delay = 160 + (node.year_index || 0) * 120 + Math.abs(node.lane || 0) * 50;
  const signals = (node.signals || []).slice(0, 2);
  const tags = (node.tags || []).slice(0, 2);
  return `
    <a
      class="lineage-node lineage-node--${escapeHtml(node.kind)}"
      data-tone="${themeTone}"
      href="${href}"
      style="left:${position.x}px; top:${position.y}px; animation-delay:${delay}ms;"
    >
      <div class="lineage-node__head">
        <span class="pill pill--tag" data-tone="${themeTone}">${escapeHtml(node.phase)}</span>
        <span class="lineage-node__year">${escapeHtml(node.conference_label)} ${escapeHtml(node.year)}</span>
      </div>
      <strong>${escapeHtml(node.title_display || node.title)}</strong>
      <p class="lineage-node__authors">${escapeHtml(node.authors_text || "")}</p>
      ${renderSignals(signals)}
      <div class="tag-row">
        ${tags.map((tag) => renderTagPill(tag)).join("")}
      </div>
      <p class="lineage-node__preview summary-preview">${escapeHtml(node.summary_preview || "打开查看这篇论文的中文导读与原文链接。")}</p>
      <span class="lineage-node__cta">打开论文导读</span>
    </a>
  `;
}

function rootAndLatest(lineage) {
  const trunk = (lineage.nodes || [])
    .filter((node) => node.kind === "trunk")
    .sort((left, right) => left.year - right.year || (left.year_index || 0) - (right.year_index || 0));
  return {
    root: trunk[0],
    latest: trunk[trunk.length - 1],
  };
}

export function renderLineagePreview(items = []) {
  const validItems = (items || []).filter((item) => item?.theme && item?.coverage && Array.isArray(item?.nodes));
  if (!validItems.length) {
    return `
      <section class="panel home-section">
        <div class="section-head">
          <div>
            <p class="eyebrow">Research Lineage</p>
            <h2>沿着研究演化去读论文</h2>
            <p>从主题主干、关键分支和代表工作出发，更快建立一个方向的整体感。</p>
          </div>
          <a class="button button-ghost" href="/lineage">打开研究脉络</a>
        </div>
        <div class="empty-card">
          <h3>研究脉络正在整理中</h3>
          <p>先从主题或搜索页开始浏览，后续这里会自动补全更多可视化脉络。</p>
        </div>
      </section>
    `;
  }

  return `
    <section class="panel home-section">
      <div class="section-head">
        <div>
          <p class="eyebrow">Research Lineage</p>
          <h2>沿着研究演化去读论文</h2>
          <p>从“起点论文”到“最新推进”，更快看清一个方向的主干和分支。</p>
        </div>
        <a class="button button-ghost" href="/lineage">打开完整脉络</a>
      </div>
      <div class="lineage-preview-grid">
        ${validItems
          .map((lineage) => {
            const meta = getThemeMeta(lineage.theme);
            const { root, latest } = rootAndLatest(lineage);
            const coverage = lineage.coverage || {};
            const yearCount = coverage.year_count || 0;
            const paperCount = coverage.paper_count || 0;
            const conferences = Array.isArray(coverage.conferences) ? coverage.conferences.join(" · ") : "";
            return `
              <a class="lineage-preview-card" data-tone="${meta.tone}" href="/lineage#theme-${toTagId(lineage.theme)}">
                <div class="atlas-feature-card__head">
                  <span class="pill pill--tag" data-tone="${meta.tone}">${escapeHtml(lineage.theme)}</span>
                  <span class="lineage-preview-card__meta">${escapeHtml(yearCount)} 年演化</span>
                </div>
                <strong>${escapeHtml(lineage.theme)}</strong>
                <p>${escapeHtml(lineage.story)}</p>
                <div class="signal-row">
                  <span class="signal">${escapeHtml(paperCount)} 篇相关论文</span>
                  ${lineage.focus_tag ? `<span class="signal">当前主干 · ${escapeHtml(lineage.focus_tag)}</span>` : ""}
                  ${conferences ? `<span class="signal">${escapeHtml(conferences)}</span>` : ""}
                </div>
                ${
                  root && latest
                    ? `
                      <div class="lineage-preview-card__track">
                        <span>${escapeHtml(root.year)} · ${escapeHtml(root.title_display || root.title)}</span>
                        <span>${escapeHtml(latest.year)} · ${escapeHtml(latest.title_display || latest.title)}</span>
                      </div>
                    `
                    : ""
                }
              </a>
            `;
          })
          .join("")}
      </div>
    </section>
  `;
}

function renderThemeNavigator(payload, activeTheme) {
  if (!payload.available_themes?.length) return "";
  return `
    <div class="lineage-chip-row">
      <a class="pill pill--tag ${!activeTheme ? "pill--active" : ""}" href="${buildLineageUrl()}">全部主题</a>
      ${payload.available_themes
        .slice(0, 10)
        .map((theme) => {
          const meta = getThemeMeta(theme);
          const active = theme === activeTheme ? "pill--active" : "";
          return `<a class="pill pill--tag ${active}" data-tone="${meta.tone}" href="${buildLineageUrl({ theme })}">${escapeHtml(theme)}</a>`;
        })
        .join("")}
    </div>
  `;
}

function renderHighlights(lineage) {
  const highlights = lineage.highlights || [];
  if (!highlights.length) return "";
  return `
    <div class="lineage-highlight-grid">
      ${highlights
        .map((item) => {
          const href = buildPaperUrl(item.paper_id, {
            conference: item.conference,
            year: item.year,
          });
          return `
            <a class="lineage-highlight-card" href="${href}">
              <span class="signal">${escapeHtml(item.label)}</span>
              <strong>${escapeHtml(item.title_display || item.title)}</strong>
              <p>${escapeHtml(item.summary_preview || "打开查看完整导读。")}</p>
              <div class="tag-row">
                ${(item.tags || []).map((tag) => renderTagPill(tag)).join("")}
              </div>
            </a>
          `;
        })
        .join("")}
    </div>
  `;
}

function renderLineageSection(lineage) {
  const meta = getThemeMeta(lineage.theme);
  const layout = buildStageLayout(lineage);
  const exploreHref = buildSearchUrl({
    query: "",
    tags: [lineage.theme],
    sort: "default",
    page: 1,
  });

  return `
    <section class="panel lineage-section" id="theme-${toTagId(lineage.theme)}" data-tone="${meta.tone}">
      <div class="section-head">
        <div>
          <p class="eyebrow">Theme Lineage</p>
          <h2>${escapeHtml(lineage.theme)}</h2>
          <p>${escapeHtml(lineage.story)}</p>
        </div>
        <div class="card-actions">
          <a class="button button-secondary" href="${exploreHref}">浏览该主题论文</a>
        </div>
      </div>
      <div class="lineage-summary-bar">
        <div class="signal-row">
          <span class="signal">${escapeHtml(lineage.coverage.paper_count)} 篇相关论文</span>
          <span class="signal">${escapeHtml(lineage.coverage.milestone_count)} 个关键节点</span>
          ${lineage.focus_tag ? `<span class="signal">当前主干 · ${escapeHtml(lineage.focus_tag)}</span>` : ""}
          <span class="signal">${escapeHtml(lineage.coverage.conferences.join(" · "))}</span>
        </div>
        <p class="toolbar-text">${escapeHtml(lineage.summary)}</p>
      </div>
      ${renderHighlights(lineage)}
      <div class="lineage-stage-shell">
        <div class="lineage-stage" style="width:${layout.width}px; height:${layout.height}px;">
          <div class="lineage-axis" style="top:${layout.centerLine}px;"></div>
          ${renderYearBands(lineage, layout)}
          <svg class="lineage-links" viewBox="0 0 ${layout.width} ${layout.height}" preserveAspectRatio="none" aria-hidden="true">
            ${renderLinks(lineage, layout)}
          </svg>
          ${lineage.nodes.map((node) => renderNode(node, layout)).join("")}
        </div>
      </div>
    </section>
  `;
}

export function renderLineageExplorer(payload, { activeTheme = "" } = {}) {
  const items = payload.items || [];
  if (!items.length) {
    return `
      <section class="panel lineage-section">
        <div class="section-head">
          <div>
            <p class="eyebrow">Research Lineage</p>
            <h2>研究脉络</h2>
            <p>这里会把一个主题的代表论文串成主干与分支，帮助你按演化去读，而不是逐篇散看。</p>
          </div>
        </div>
        ${renderThemeNavigator(payload, activeTheme)}
        <div class="empty-card empty-card--large">
          <h3>还没有整理出可展示的脉络</h3>
          <p>先从其它主题开始，或等待更多相关论文进入这条研究线。</p>
        </div>
      </section>
    `;
  }

  return `
    <section class="panel lineage-intro">
      <div class="section-head">
        <div>
          <p class="eyebrow">Research Lineage</p>
          <h2>顺着主干，看清一个领域怎么长出来</h2>
          <p>我们把同一主题下的代表论文串成主干与分支，让你可以从起点工作一路看到最新进展。</p>
        </div>
        <div class="signal-row">
          <span class="signal">${escapeHtml(payload.coverage?.paper_count || 0)} 篇已收录论文</span>
          <span class="signal">${escapeHtml(payload.coverage?.dataset_count || 0)} 个已追踪数据源</span>
        </div>
      </div>
      ${renderThemeNavigator(payload, activeTheme)}
    </section>
    <div class="lineage-stack">
      ${items.map((lineage) => renderLineageSection(lineage)).join("")}
    </div>
  `;
}
