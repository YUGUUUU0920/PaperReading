import { escapeHtml } from "../utils/dom.js";
import { buildPaperUrl } from "../utils/url.js";

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
        <h3>先选一个会议年份再开始搜索</h3>
        <p>为了让公网版更快打开，首页不再默认抓取整场会议。你可以直接检索关键词，或者从下面的快捷入口进入。</p>
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
              <p class="preview">点击后会进入对应会议年份，并自动开始抓取与分页展示论文。</p>
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
  const { papers, filters, loading, total, pageSize, hasSearched, hasNext } = state;
  const count = papers.length;
  const currentPage = Number(filters.page || 1);
  const totalPages = total ? Math.max(1, Math.ceil(total / pageSize)) : 0;

  if (!hasSearched && !loading) {
    return `
      <section class="list-panel panel">
        <div class="section-head">
          <div>
            <h2>开始检索</h2>
            <p>选择会议、年份和关键词后再发起查询，避免首页一打开就加载很长的论文列表。</p>
          </div>
        </div>
        ${renderQuickStart(state)}
      </section>
    `;
  }

  const items = papers.length
    ? papers
        .map((paper) => {
          const preview = paper.summary_preview || "打开详情页后会自动补全摘要，并生成中文总结。";
          const href = buildPaperUrl(paper.id, filters);
          return `
            <article class="paper-card">
              <div class="paper-card__meta">
                <span class="pill">${escapeHtml(paper.conference.toUpperCase())}</span>
                <span class="pill">${escapeHtml(paper.year)}</span>
                <span class="pill">${escapeHtml(paper.track || "未分类")}</span>
              </div>
              <h3>${escapeHtml(paper.title_display || paper.title)}</h3>
              <p class="authors">${escapeHtml(paper.authors_text)}</p>
              <p class="preview summary-preview">${escapeHtml(preview)}</p>
              <div class="card-actions">
                <a class="button button-primary" href="${href}">查看详情</a>
                ${paper.pdf_url ? `<a class="button button-ghost" href="${escapeHtml(paper.pdf_url)}" target="_blank" rel="noreferrer">打开 PDF</a>` : ""}
              </div>
            </article>
          `;
        })
        .join("")
    : `<div class="empty-card">
         <h3>当前没有论文</h3>
         <p>这通常意味着当前会议年份还没缓存，或者这个关键词没有命中。现在搜索会自动拉取官方数据，不需要先做手动同步。</p>
       </div>`;

  return `
    <section class="list-panel panel">
      <div class="section-head">
        <div>
          <h2>论文列表</h2>
          <p>${loading ? "正在加载官方数据或本地缓存..." : `共找到 ${total} 篇，当前页展示 ${count} 篇`}</p>
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
