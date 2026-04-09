import { escapeHtml } from "../utils/dom.js";
import { buildPaperUrl } from "../utils/url.js";

export function renderPaperList(state) {
  const { papers, filters, loading } = state;
  const count = papers.length;
  const items = papers.length
    ? papers
        .map((paper) => {
          const preview = paper.has_summary
            ? "已生成中文总结，点击详情即可查看。"
            : paper.has_abstract
              ? "已获取摘要，点击详情可自动生成中文总结。"
              : "摘要会在打开详情时自动补全，并生成中文总结。";
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
              <p class="preview">${escapeHtml(preview)}</p>
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
          <p>${loading ? "正在加载官方数据或本地缓存..." : `当前结果 ${count} 篇`}</p>
        </div>
        <span class="counter">${count}</span>
      </div>
      <div class="paper-list">${items}</div>
    </section>
  `;
}
