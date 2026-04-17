import { escapeHtml } from "../utils/dom.js";
import { getTagTone } from "../utils/tags.js";

function renderStats(bootstrap, filters) {
  const conferenceCount = (bootstrap.conferences || []).length;
  const latestYear = Math.max(...((bootstrap.conferences || []).flatMap((item) => item.years || []).concat([filters.year || 2025])));
  const tagCount = Array.isArray(filters.tags) ? filters.tags.length : 0;
  return `
    <div class="hero-pill-row">
      <span class="signal">${conferenceCount} 个来源</span>
      <span class="signal">${latestYear} 最新年份</span>
      <span class="signal">${tagCount} 个已选主题</span>
    </div>
  `;
}

export function renderSearchToolbar(state) {
  const { bootstrap, filters, loading } = state;
  const selectedTags = Array.isArray(filters.tags) ? filters.tags : [];
  const conferenceOptions = (bootstrap.conferences || [])
    .map((item) => {
      const selected = item.code === filters.conference ? "selected" : "";
      return `<option value="${escapeHtml(item.code)}" ${selected}>${escapeHtml(item.label)}</option>`;
    })
    .join("");
  const tagOptions = [
    `<option value="">选择一个主题</option>`,
    ...((bootstrap.tagOptions || [])
      .filter((tag) => !selectedTags.includes(tag))
      .map((tag) => `<option value="${escapeHtml(tag)}">${escapeHtml(tag)}</option>`)),
  ].join("");
  const sortOptions = (bootstrap.sortOptions || [])
    .map((item) => {
      const selected = item.value === filters.sort ? "selected" : "";
      return `<option value="${escapeHtml(item.value)}" ${selected}>${escapeHtml(item.label)}</option>`;
    })
    .join("");

  return `
    <section class="toolbar panel toolbar--compact toolbar--workbench">
      <div class="toolbar-copy toolbar-copy--compact">
        <p class="eyebrow">Explore Papers</p>
        <h1>搜索论文</h1>
        <p class="toolbar-text">
          用会议、年份、关键词和中文主题缩小结果范围。
          如果你已经知道方向，可以先加主题标签，再进入论文详情继续阅读。
        </p>
        ${renderStats(bootstrap, filters)}
      </div>
      <form id="search-form" class="search-form">
        <label>
          <span>来源</span>
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
          <input name="query" type="search" value="${escapeHtml(filters.query)}" placeholder="标题、作者、摘要、方法名">
        </label>
        <label>
          <span>添加主题</span>
          <select id="tag-picker" name="tag_picker">
            ${tagOptions}
          </select>
        </label>
        <label>
          <span>排序</span>
          <select name="sort">
            ${sortOptions}
          </select>
        </label>
        <div class="query-field selected-tags-panel">
          <div class="selected-tags-head">
            <span>当前筛选</span>
            <button id="add-tag-button" class="button button-chip" type="button" ${loading ? "disabled" : ""}>加入主题</button>
          </div>
          ${
            selectedTags.length
              ? `<div class="tag-row">
                   ${selectedTags
                     .map(
                       (tag) =>
                         `<button class="pill pill--tag pill--active" data-tone="${getTagTone(tag)}" type="button" data-remove-tag="${escapeHtml(tag)}">${escapeHtml(tag)} ×</button>`,
                     )
                     .join("")}
                 </div>`
              : `<p class="tag-empty">先加一两个主题标签，通常能比只输关键词更快收窄结果。</p>`
          }
        </div>
        <div class="toolbar-actions">
          <button type="submit" class="button button-primary" ${loading ? "disabled" : ""}>开始搜索</button>
          <button id="refresh-button" type="button" class="button button-secondary" ${loading ? "disabled" : ""}>刷新数据</button>
        </div>
      </form>
    </section>
  `;
}
