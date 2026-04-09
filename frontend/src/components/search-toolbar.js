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
        <p class="eyebrow">Research Console</p>
        <h1>搜索页只保留检索，详情拆到独立页面</h1>
        <p class="toolbar-text">
          现在搜索时会自动从官方站点拉取并缓存当前会议年份的数据。
          点开论文会跳到单独详情页，不再把摘要和总结挤在右下角长栏里。
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
          <button id="refresh-button" type="button" class="button button-secondary" ${loading ? "disabled" : ""}>刷新缓存</button>
        </div>
      </form>
    </section>
  `;
}
