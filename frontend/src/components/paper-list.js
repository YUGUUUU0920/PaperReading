import { escapeHtml } from "../utils/dom.js";
import { buildPaperUrl } from "../utils/url.js";

function renderTagRow(tags = [], { activeTags = [], clickable = false } = {}) {
  if (!tags.length) return "";
  return `
    <div class="tag-row">
      ${tags
        .slice(0, 6)
        .map((tag) =>
          clickable
            ? `<button class="pill pill--tag ${activeTags.includes(tag) ? "pill--active" : ""}" type="button" data-filter-tag="${escapeHtml(tag)}">${escapeHtml(tag)}</button>`
            : `<span class="pill pill--tag">${escapeHtml(tag)}</span>`,
        )
        .join("")}
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

function renderQuickStart(state) {
  const picks = (state.bootstrap.conferences || [])
    .map((conference) => {
      const years = Array.isArray(conference.years) ? [...conference.years].sort((a, b) => b - a) : [];
      return {
        code: conference.code,
        label: conference.label,
        year: years[0],
      };
    })
    .filter((item) => item.year)
    .slice(0, 4);

  return `
    <div class="welcome-grid">
      <article class="empty-card empty-card--large">
        <h3>从一个会议入口开始</h3>
        <p>可以直接输入关键词，也可以先进入某个会议年份，浏览该场会议的论文、标签和导读摘要。</p>
      </article>
      ${picks
        .map(
          (item) => `
            <article class="paper-card">
              <div class="paper-card__meta">
                <span class="pill">${escapeHtml(item.label)}</span>
                <span class="pill">${escapeHtml(item.year)}</span>
              </div>
              <h3>${escapeHtml(item.label)} ${escapeHtml(item.year)}</h3>
              <p class="preview">查看这一年的热门研究方向、代表论文与中文导读。</p>
              <div class="card-actions">
                <a class="button button-primary" href="/?conference=${escapeHtml(item.code)}&year=${escapeHtml(item.year)}">进入这个会场</a>
              </div>
            </article>
          `,
        )
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
            <h2>开始检索</h2>
            <p>选择会议、年份和关键词，快速定位值得精读的论文。</p>
          </div>
        </div>
        ${renderQuickStart(state)}
      </section>
    `;
  }

  const items = papers.length
    ? papers
        .map((paper) => {
          const preview = paper.summary_preview || "查看摘要、导读与相关资源。";
          const href = buildPaperUrl(paper.id, filters);
          return `
            <article class="paper-card">
              <div class="paper-card__meta">
                <span class="pill">${escapeHtml(paper.conference.toUpperCase())}</span>
                <span class="pill">${escapeHtml(paper.year)}</span>
                <span class="pill">${escapeHtml(paper.track || "未分类")}</span>
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
        })
        .join("")
    : `<div class="empty-card">
         <h3>当前没有论文</h3>
         <p>没有找到符合当前条件的结果。你可以换一个关键词，或者切换会议与年份继续探索。</p>
       </div>`;

  return `
    <section class="list-panel panel">
      <div class="section-head">
        <div>
          <h2>论文列表</h2>
          <p>${loading ? "正在整理检索结果..." : `共找到 ${total} 篇，当前页展示 ${count} 篇`}</p>
          ${
            resultTags?.length
              ? `<div class="quick-filter-row">
                   <span class="quick-filter-label">热门标签</span>
                   ${resultTags
                     .map(
                       (tag) =>
                         `<button class="pill pill--tag ${selectedTags.includes(tag) ? "pill--active" : ""}" type="button" data-filter-tag="${escapeHtml(tag)}">${escapeHtml(tag)}</button>`,
                     )
                     .join("")}
                 </div>`
              : ""
          }
        </div>
        <span class="counter">${count}</span>
      </div>
      <div class="paper-list">${items}</div>
      ${
        totalPages > 1
          ? `
            <div class="list-footer">
              <p class="pagination-note">第 ${currentPage} / ${totalPages} 页</p>
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
