import { markdownToHtml } from "../utils/markdown.js";
import { escapeHtml } from "../utils/dom.js";

export function renderPaperDetail(state) {
  const { activePaper, loadingDetail, loadingSummary, bootstrap, backUrl } = state;
  if (!activePaper) {
    return `
      <section class="detail-panel panel">
        <div class="empty-card empty-card--large">
          <h2>论文详情</h2>
          <p>从左侧选一篇论文后，这里会显示摘要、官方链接和中文总结。</p>
          <p>${bootstrap.summaryEnabled ? "已配置模型总结能力。" : "当前未配置模型接口，会先使用启发式总结。"}</p>
        </div>
      </section>
    `;
  }

  const actionLabel = loadingSummary ? "总结生成中..." : "生成中文总结";

  return `
    <section class="detail-panel panel">
      <div class="detail-topline">
        <a class="button button-ghost" href="${escapeHtml(backUrl || "/")}">返回论文列表</a>
      </div>
      <div class="detail-head">
        <div class="paper-card__meta">
          <span class="pill">${escapeHtml(activePaper.conference.toUpperCase())}</span>
          <span class="pill">${escapeHtml(activePaper.year)}</span>
          <span class="pill">${escapeHtml(activePaper.track || "未分类")}</span>
        </div>
        <h2>${escapeHtml(activePaper.title_display || activePaper.title)}</h2>
        <p class="authors">${escapeHtml(activePaper.authors_text)}</p>
      </div>

      <div class="detail-actions">
        <button id="summarize-paper-button" class="button button-primary" ${loadingSummary || loadingDetail ? "disabled" : ""}>${actionLabel}</button>
        ${activePaper.paper_url ? `<a class="button button-ghost" href="${escapeHtml(activePaper.paper_url)}" target="_blank" rel="noreferrer">官方详情</a>` : ""}
        ${activePaper.pdf_url ? `<a class="button button-secondary" href="${escapeHtml(activePaper.pdf_url)}" target="_blank" rel="noreferrer">打开 PDF</a>` : ""}
      </div>

      <div class="detail-block">
        <h3>摘要</h3>
        <p>${escapeHtml(activePaper.abstract || (loadingDetail ? "摘要加载中..." : "当前还没有拿到摘要。"))}</p>
      </div>

      <div class="detail-block">
        <h3>中文总结</h3>
        <div class="markdown">${markdownToHtml(activePaper.summary || "点击上方按钮即可生成中文总结。")}</div>
      </div>
    </section>
  `;
}
