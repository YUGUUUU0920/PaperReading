import { escapeHtml } from "../utils/dom.js";
import { buildPaperUrl, buildSearchUrl } from "../utils/url.js";
import { FEATURED_THEMES, getTagTone, getThemeMeta, pickPrimaryTheme, toTagId } from "../utils/tags.js";

function renderTagPill(tag, { activeTags = [], clickable = false } = {}) {
  const tone = getTagTone(tag);
  const active = activeTags.includes(tag) ? "pill--active" : "";
  if (clickable) {
    return `<button class="pill pill--tag ${active}" data-tone="${tone}" type="button" data-filter-tag="${escapeHtml(tag)}">${escapeHtml(tag)}</button>`;
  }
  return `<span class="pill pill--tag" data-tone="${tone}">${escapeHtml(tag)}</span>`;
}

function renderTagRow(tags = [], options = {}) {
  if (!tags.length) return "";
  return `
    <div class="tag-row">
      ${tags.slice(0, 6).map((tag) => renderTagPill(tag, options)).join("")}
    </div>
  `;
}

function renderSignalRow(paper) {
  const signals = [];
  if (paper.citation_count) signals.push(`被引 ${paper.citation_count}`);
  if (paper.code_url) signals.push("附代码");
  if (paper.open_access) signals.push("开放获取");
  if (paper.top_10_percent_cited) signals.push("高影响力");
  if (!signals.length) return "";
  return `
    <div class="signal-row">
      ${signals.map((item) => `<span class="signal">${escapeHtml(item)}</span>`).join("")}
    </div>
  `;
}

function renderSaveActions(paper) {
  return `
    <div class="save-actions">
      <button class="button button-chip ${paper.saved?.favorite ? "active" : ""}" type="button" data-save-toggle="${paper.id}:favorite:${paper.saved?.favorite ? "0" : "1"}">
        ${paper.saved?.favorite ? "已收藏" : "收藏"}
      </button>
      <button class="button button-chip ${paper.saved?.reading ? "active" : ""}" type="button" data-save-toggle="${paper.id}:reading:${paper.saved?.reading ? "0" : "1"}">
        ${paper.saved?.reading ? "已在待读" : "加入待读"}
      </button>
    </div>
  `;
}

function buildThemeGroups(papers = []) {
  const groups = new Map();
  for (const paper of papers) {
    const theme = paper.primary_theme || pickPrimaryTheme(paper.tags || []);
    const bucket = groups.get(theme) || [];
    bucket.push(paper);
    groups.set(theme, bucket);
  }
  return Array.from(groups.entries()).sort((left, right) => {
    if (right[1].length !== left[1].length) return right[1].length - left[1].length;
    return left[0].localeCompare(right[0], "zh-CN");
  });
}

function renderPaperCard(paper, filters, selectedTags) {
  const preview = paper.summary_preview || "查看摘要、导读与相关资源。";
  const href = buildPaperUrl(paper.id, filters);
  return `
    <article class="paper-card paper-card--lift">
      <div class="paper-card__meta">
        <span class="pill">${escapeHtml(paper.conference.toUpperCase())}</span>
        <span class="pill">${escapeHtml(paper.year)}</span>
        <span class="pill">${escapeHtml(paper.track_label || paper.track || "未分类")}</span>
        ${paper.summary_source_label ? `<span class="pill pill--warm">${escapeHtml(paper.summary_source_label)}</span>` : ""}
      </div>
      <h3>${escapeHtml(paper.title_display || paper.title)}</h3>
      <p class="authors">${escapeHtml(paper.authors_text)}</p>
      ${renderSignalRow(paper)}
      ${renderTagRow(paper.tags || [], { activeTags: selectedTags, clickable: true })}
      <p class="preview summary-preview">${escapeHtml(preview)}</p>
      <div class="card-actions">
        <a class="button button-primary" href="${href}">查看详情</a>
        ${paper.pdf_url ? `<a class="button button-ghost" href="${escapeHtml(paper.pdf_url)}" target="_blank" rel="noreferrer">打开 PDF</a>` : ""}
        ${paper.code_url ? `<a class="button button-ghost" href="${escapeHtml(paper.code_url)}" target="_blank" rel="noreferrer">代码</a>` : ""}
      </div>
      ${renderSaveActions(paper)}
    </article>
  `;
}

function renderLanding(state) {
  const { filters } = state;
  return `
    <div class="landing-stack landing-stack--compact">
      <div class="empty-card empty-card--large atlas-note">
        <h3>先定义方向，再开始筛选</h3>
        <p>研究探索页只负责检索和收窄结果。若你还没确定方向，先跳到主题页会更轻松。</p>
        <div class="card-actions">
          <a class="button button-primary" href="/themes">浏览主题</a>
          <a class="button button-secondary" href="/lists">查看阅读清单</a>
        </div>
      </div>
      <div class="atlas-feature-grid atlas-feature-grid--compact">
        ${FEATURED_THEMES.slice(0, 6)
          .map((theme) => {
            const meta = getThemeMeta(theme);
            const href = buildSearchUrl({ ...filters, tags: [theme], page: 1, query: "" });
            return `
              <a class="atlas-feature-card" href="${href}" data-tone="${meta.tone}">
                <div class="atlas-feature-card__head">
                  <span class="pill pill--tag" data-tone="${meta.tone}">${escapeHtml(theme)}</span>
                  <span class="atlas-feature-card__arrow">探索</span>
                </div>
                <strong>${escapeHtml(theme)}</strong>
                <p>${escapeHtml(meta.description)}</p>
              </a>
            `;
          })
          .join("")}
      </div>
    </div>
  `;
}

function renderThemeNavigator(groups) {
  if (groups.length <= 1) return "";
  return `
    <div class="theme-brief-grid">
      ${groups
        .map(([theme, papers]) => {
          const meta = getThemeMeta(theme);
          return `
            <a class="theme-brief-card" href="#theme-${toTagId(theme)}" data-tone="${meta.tone}">
              <div class="theme-brief-card__head">
                <span class="pill pill--tag" data-tone="${meta.tone}">${escapeHtml(theme)}</span>
                <span class="counter">${papers.length}</span>
              </div>
              <p>${escapeHtml(meta.description)}</p>
            </a>
          `;
        })
        .join("")}
    </div>
  `;
}

export function renderPaperList(state) {
  const { papers, filters, loading, total, pageSize, hasSearched, hasNext, resultTags } = state;
  const count = papers.length;
  const currentPage = Number(filters.page || 1);
  const totalPages = total ? Math.max(1, Math.ceil(total / pageSize)) : 0;
  const selectedTags = Array.isArray(filters.tags) ? filters.tags : [];

  if (!hasSearched && !loading) {
    return `
      <section class="list-panel panel">
        <div class="section-head">
          <div>
            <h2>开始一次新的探索</h2>
            <p>输入关键词，或直接从下面的主题入口跳转。</p>
          </div>
        </div>
        ${renderLanding(state)}
      </section>
    `;
  }

  if (!papers.length) {
    return `
      <section class="list-panel panel">
        <div class="section-head">
          <div>
            <h2>研究主题图谱</h2>
            <p>${loading ? "正在整理检索结果..." : "暂时没有符合当前条件的结果。"}</p>
          </div>
        </div>
        <div class="empty-card">
          <h3>还没有匹配到论文</h3>
          <p>可以换一个关键词，或者调整会议、年份与标签组合，重新定义你要观察的主题范围。</p>
        </div>
      </section>
    `;
  }

  const groups = buildThemeGroups(papers);

  return `
    <section class="list-panel panel">
      <div class="section-head">
        <div>
          <h2>研究主题图谱</h2>
          <p>${loading ? "正在整理检索结果..." : `本页展示 ${count} 篇论文，归纳为 ${groups.length} 个主题切片。`}</p>
          ${
            resultTags?.length
              ? `<div class="quick-filter-row">
                   <span class="quick-filter-label">相关标签</span>
                   ${resultTags.map((tag) => renderTagPill(tag, { activeTags: selectedTags, clickable: true })).join("")}
                 </div>`
              : ""
          }
        </div>
        <span class="counter">${count}</span>
      </div>
      ${renderThemeNavigator(groups)}
      <div class="theme-group-stack">
        ${groups
          .map(([theme, items]) => {
            const meta = getThemeMeta(theme);
            return `
              <section class="theme-group" id="theme-${toTagId(theme)}" data-tone="${meta.tone}">
                <div class="theme-group__head">
                  <div class="theme-group__copy">
                    <p class="eyebrow">Theme</p>
                    <h3>${escapeHtml(theme)}</h3>
                    <p>${escapeHtml(meta.description)}</p>
                  </div>
                  <div class="paper-card__meta">
                    <span class="pill pill--tag" data-tone="${meta.tone}">${escapeHtml(theme)}</span>
                    <span class="pill">${items.length} 篇</span>
                  </div>
                </div>
                <div class="theme-paper-grid">
                  ${items.map((paper) => renderPaperCard(paper, filters, selectedTags)).join("")}
                </div>
              </section>
            `;
          })
          .join("")}
      </div>
      ${
        totalPages > 1
          ? `
            <div class="list-footer">
              <p class="pagination-note">第 ${currentPage} / ${totalPages} 页，累计命中 ${total} 篇论文</p>
              <div class="card-actions">
                <button class="button button-ghost" data-page="${currentPage - 1}" ${currentPage <= 1 || loading ? "disabled" : ""}>上一页</button>
                <button class="button button-secondary" data-page="${currentPage + 1}" ${!hasNext || loading ? "disabled" : ""}>下一页</button>
              </div>
            </div>
          `
          : ""
      }
    </section>
  `;
}
