import { markdownToHtml } from "../utils/markdown.js";
import { escapeHtml } from "../utils/dom.js";
import { buildPaperUrl } from "../utils/url.js";

function renderTags(tags = []) {
  if (!tags.length) return "";
  return `
    <div class="tag-row">
      ${tags.map((tag) => `<span class="pill pill--tag">${escapeHtml(tag)}</span>`).join("")}
    </div>
  `;
}

function renderSaveActions(activePaper) {
  return `
    <div class="save-actions">
      <button class="button button-chip ${activePaper.saved?.favorite ? "active" : ""}" type="button" data-save-toggle="${activePaper.id}:favorite:${activePaper.saved?.favorite ? "0" : "1"}">
        ${activePaper.saved?.favorite ? "已收藏" : "收藏"}
      </button>
      <button class="button button-chip ${activePaper.saved?.reading ? "active" : ""}" type="button" data-save-toggle="${activePaper.id}:reading:${activePaper.saved?.reading ? "0" : "1"}">
        ${activePaper.saved?.reading ? "已在待读" : "加入待读"}
      </button>
    </div>
  `;
}

function renderSavedSummary(activePaper) {
  const items = [];
  if (activePaper.saved?.favorite) {
    const groupName = activePaper.saved.favorite.group_name?.trim();
    items.push(groupName ? `收藏分组：${groupName}` : "已加入收藏");
  }
  if (activePaper.saved?.reading) {
    const groupName = activePaper.saved.reading.group_name?.trim();
    items.push(activePaper.saved.reading.is_read ? "待读状态：已读" : "待读状态：未读");
    if (groupName) items.push(`待读分组：${groupName}`);
  }
  if (!items.length) return "";
  return `
    <div class="signal-row">
      ${items.map((item) => `<span class="signal">${escapeHtml(item)}</span>`).join("")}
    </div>
  `;
}

function renderSignals(activePaper) {
  const items = [];
  if (activePaper.citation_count) items.push(`被引 ${activePaper.citation_count}`);
  if (activePaper.top_10_percent_cited) items.push("高影响力");
  if (activePaper.open_access) items.push("开放获取");
  if (activePaper.code_url) items.push("附代码");
  if (!items.length) return "";
  return `
    <div class="signal-row">
      ${items.map((item) => `<span class="signal">${escapeHtml(item)}</span>`).join("")}
    </div>
  `;
}

function renderResources(activePaper) {
  const links = [...(activePaper.resource_links || [])];
  if (activePaper.code_url && !links.some((item) => item.url === activePaper.code_url)) {
    links.unshift({ kind: "github", url: activePaper.code_url, label: "代码仓库" });
  }
  if (!links.length) return "";
  return `
    <div class="resource-grid">
      ${links
        .slice(0, 8)
        .map(
          (item) => `
            <a class="resource-link" href="${escapeHtml(item.url)}" target="_blank" rel="noreferrer">
              <span>${escapeHtml(item.label || item.kind || "相关资源")}</span>
              <small>${escapeHtml((item.kind || "resource").toUpperCase())}</small>
            </a>
          `,
        )
        .join("")}
    </div>
  `;
}

function renderRelated(activePaper) {
  const related = activePaper.related_papers || [];
  if (!related.length) return "";
  return `
    <div class="detail-block">
      <h3>同主题推荐</h3>
      <div class="related-list">
        ${related
          .map((item) => {
            const href = buildPaperUrl(item.id, {
              conference: item.conference,
              year: item.year,
            });
            return `
              <a class="related-card" href="${href}">
                <div class="paper-card__meta">
                  <span class="pill">${escapeHtml(item.conference.toUpperCase())}</span>
                  <span class="pill">${escapeHtml(item.year)}</span>
                  <span class="pill">${escapeHtml(item.track || "论文")}</span>
                </div>
                <strong>${escapeHtml(item.title_display || item.title)}</strong>
                <p class="authors">${escapeHtml(item.authors_text || "")}</p>
                ${item.tags?.length ? `<div class="tag-row">${item.tags.slice(0, 4).map((tag) => `<span class="pill pill--tag">${escapeHtml(tag)}</span>`).join("")}</div>` : ""}
                <p class="preview">${escapeHtml(item.summary_preview || "进入详情页查看导读。")}</p>
              </a>
            `;
          })
          .join("")}
      </div>
    </div>
  `;
}

export function renderPaperDetail(state) {
  const { activePaper, loadingDetail, loadingSummary, backUrl } = state;
  if (!activePaper) {
    return `
      <section class="detail-panel panel">
        <div class="empty-card empty-card--large">
          <h2>论文详情</h2>
          <p>在这里查看摘要、中文导读、研究标签与相关论文。</p>
        </div>
      </section>
    `;
  }

  const actionLabel = loadingSummary ? "导读生成中..." : "更新中文导读";

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
        ${renderSignals(activePaper)}
        ${renderTags(activePaper.tags || [])}
      </div>

      <div class="detail-actions">
        <button id="summarize-paper-button" class="button button-primary" ${loadingSummary || loadingDetail ? "disabled" : ""}>${actionLabel}</button>
        ${activePaper.paper_url ? `<a class="button button-ghost" href="${escapeHtml(activePaper.paper_url)}" target="_blank" rel="noreferrer">官方详情</a>` : ""}
        ${activePaper.pdf_url ? `<a class="button button-secondary" href="${escapeHtml(activePaper.pdf_url)}" target="_blank" rel="noreferrer">打开 PDF</a>` : ""}
      </div>
      ${renderSaveActions(activePaper)}
      ${renderSavedSummary(activePaper)}

      ${renderResources(activePaper)}

      <div class="detail-block">
        <h3>摘要</h3>
        <p>${escapeHtml(activePaper.abstract || (loadingDetail ? "摘要加载中..." : "当前暂未展示摘要。"))}</p>
      </div>

      <div class="detail-block">
        <div class="detail-summary-head">
          <h3>中文总结</h3>
          <div class="paper-card__meta">
            ${activePaper.summary_source_label ? `<span class="pill pill--warm">${escapeHtml(activePaper.summary_source_label)}</span>` : ""}
            ${activePaper.summary_updated_at ? `<span class="pill">${escapeHtml(activePaper.summary_updated_at)}</span>` : ""}
          </div>
        </div>
        <div class="markdown">${markdownToHtml(activePaper.summary || "点击上方按钮即可生成中文总结。")}</div>
      </div>

      ${renderRelated(activePaper)}
    </section>
  `;
}
