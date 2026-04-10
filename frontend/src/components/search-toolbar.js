import { escapeHtml } from "../utils/dom.js";

export function renderSearchToolbar(state) {
  const { bootstrap, filters, loading } = state;
  const conferenceOptions = (bootstrap.conferences || [])
    .map((item) => {
      const selected = item.code === filters.conference ? "selected" : "";
      return `<option value="${escapeHtml(item.code)}" ${selected}>${escapeHtml(item.label)}</option>`;
    })
    .join("");

  return `
    <section class="toolbar panel">
      <div class="toolbar-copy">
        <p class="eyebrow">Paper Reading</p>
        <h1>顶会论文检索与中文导读</h1>
        <p class="toolbar-text">
          面向 ACL、NeurIPS、ICML、ICLR 的论文浏览空间，支持中文标签、导读摘要、引用与资源信号，适合快速筛选值得细读的工作。
        </p>
      </div>
      <form id="search-form" class="search-form">
        <label>
          <span>会议</span>
          <select name="conference">
            ${conferenceOptions}
          </select>
        </label>
        <label>
          <span>年份</span>
          <input name="year" type="number" min="2021" max="2030" value="${escapeHtml(filters.year)}">
        </label>
        <label class="query-field">
          <span>关键词</span>
          <input name="query" type="search" value="${escapeHtml(filters.query)}" placeholder="标题、作者、摘要">
        </label>
        <div class="toolbar-actions">
          <button type="submit" class="button button-primary" ${loading ? "disabled" : ""}>搜索论文</button>
          <button id="refresh-button" type="button" class="button button-secondary" ${loading ? "disabled" : ""}>更新数据</button>
        </div>
      </form>
    </section>
  `;
}
