import { markdownToHtml } from "../utils/markdown.js";
import { escapeHtml } from "../utils/dom.js";
import { buildPaperUrl } from "../utils/url.js";
import { getTagTone } from "../utils/tags.js";

function formatTimestamp(value) {
  if (!value) return "";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat("zh-CN", {
    month: "numeric",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(date);
}

function renderTags(tags = []) {
  if (!tags.length) return "";
  return `
    <div class="tag-row">
      ${tags.map((tag) => `<span class="pill pill--tag" data-tone="${getTagTone(tag)}">${escapeHtml(tag)}</span>`).join("")}
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
                  <span class="pill">${escapeHtml(item.track_label || item.track || "论文")}</span>
                </div>
                <strong>${escapeHtml(item.title_display || item.title)}</strong>
                <p class="authors">${escapeHtml(item.authors_text || "")}</p>
                ${item.tags?.length ? `<div class="tag-row">${item.tags.slice(0, 4).map((tag) => `<span class="pill pill--tag" data-tone="${getTagTone(tag)}">${escapeHtml(tag)}</span>`).join("")}</div>` : ""}
                <p class="preview">${escapeHtml(item.summary_preview || "进入详情页查看导读。")}</p>
              </a>
            `;
          })
          .join("")}
      </div>
    </div>
  `;
}

function renderViewerPanel(state) {
  const { viewer, viewerDraftName = "", updatingViewerName, postingComment } = state;
  const displayName = viewer?.display_name || "访客";
  return `
    <div class="community-panel">
      <div class="community-panel__head">
        <div>
          <h3>评论区</h3>
          <p>留下你的判断、质疑或补充观点，也可以先看看开场观点再决定怎么读这篇论文。</p>
        </div>
        <div class="signal-row">
          <span class="signal">${escapeHtml(viewer?.is_guest ? "访客身份" : "个人身份")}</span>
          <span class="signal">${escapeHtml(displayName)}</span>
        </div>
      </div>
      <div class="viewer-card">
        <label class="field-grid--wide">
          <span>你的昵称</span>
          <input id="viewer-name-input" type="text" maxlength="20" value="${escapeHtml(viewerDraftName || displayName)}" placeholder="给自己起个名字" />
        </label>
        <div class="card-actions">
          <button id="viewer-name-save" class="button button-secondary" type="button" ${updatingViewerName ? "disabled" : ""}>
            ${updatingViewerName ? "保存中..." : "保存昵称"}
          </button>
          <span class="tag-empty">不注册也能评论，昵称会保存在当前浏览器里。</span>
        </div>
      </div>
      <form id="comment-form" class="editor-form">
        <label class="field-grid--wide">
          <span>写下你的看法</span>
          <textarea id="comment-input" placeholder="比如：这篇方法哪里最值得看？实验哪里还想追问？"></textarea>
        </label>
        <div class="card-actions">
          <button class="button button-primary" type="submit" ${postingComment ? "disabled" : ""}>
            ${postingComment ? "发表中..." : "发布评论"}
          </button>
        </div>
      </form>
    </div>
  `;
}

function renderCommentItem(item) {
  return `
    <article class="comment-card ${item.is_seed ? "comment-card--seed" : ""}">
      <div class="comment-card__head">
        <div class="comment-card__identity">
            <strong>${escapeHtml(item.display_name)}</strong>
            <div class="paper-card__meta">
            ${item.is_seed ? '<span class="pill pill--warm">开场观点</span>' : '<span class="pill">读者评论</span>'}
            ${item.created_at ? `<span class="signal">${escapeHtml(formatTimestamp(item.created_at))}</span>` : ""}
          </div>
        </div>
      </div>
      <p class="comment-card__content">${escapeHtml(item.content)}</p>
    </article>
  `;
}

function renderComments(state) {
  const { comments = [], loadingComments } = state;
  if (loadingComments) {
    return `
      <div class="detail-block">
        <h3>正在加载评论区...</h3>
      </div>
    `;
  }
  if (!comments.length) {
    return `
      <div class="empty-card">
        <h3>还没有评论</h3>
        <p>你可以先留下第一条看法，也可以等系统整理出更多开场观点。</p>
      </div>
    `;
  }
  const seedComments = comments.filter((item) => item.is_seed);
  const userComments = comments.filter((item) => !item.is_seed);
  return `
    <div class="comment-stack">
      ${
        seedComments.length
          ? `
            <div class="detail-block">
              <div class="detail-summary-head">
                <h3>开场观点</h3>
                <span class="signal">${seedComments.length} 条</span>
              </div>
              <div class="comment-list">
                ${seedComments.map((item) => renderCommentItem(item)).join("")}
              </div>
            </div>
          `
          : ""
      }
      <div class="detail-block">
        <div class="detail-summary-head">
          <h3>读者评论</h3>
          <span class="signal">${userComments.length} 条</span>
        </div>
        ${
          userComments.length
            ? `<div class="comment-list">${userComments.map((item) => renderCommentItem(item)).join("")}</div>`
            : `<div class="empty-card"><p>还没有读者评论，你可以先留下第一条。</p></div>`
        }
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
          <span class="pill">${escapeHtml(activePaper.track_label || activePaper.track || "未分类")}</span>
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

      <div class="detail-block">
        ${renderViewerPanel(state)}
        ${renderComments(state)}
      </div>
    </section>
  `;
}
