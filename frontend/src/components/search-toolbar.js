import { escapeHtml } from "../utils/dom.js";
import { getTagTone } from "../utils/tags.js";

function renderWorkbenchStats(bootstrap, filters) {
  const conferenceCount = (bootstrap.conferences || []).length;
  const latestYear = Math.max(...((bootstrap.conferences || []).flatMap((item) => item.years || []).concat([filters.year || 2025])));
  const tagCount = Array.isArray(filters.tags) ? filters.tags.length : 0;

  return `
    <div class="workbench-stats">
      <article class="workbench-stat-card">
        <strong>${conferenceCount}</strong>
        <span>覆盖来源</span>
      </article>
      <article class="workbench-stat-card">
        <strong>${latestYear}</strong>
        <span>默认最新切片</span>
      </article>
      <article class="workbench-stat-card">
        <strong>${tagCount}</strong>
        <span>已选标签</span>
      </article>
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
    `<option value="">选择一个标签</option>`,
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
        <div class="toolbar-copy__row">
          <div>
            <p class="eyebrow">Research Explorer</p>
            <h1>论文发现</h1>
            <p class="toolbar-text">
              按会议、年份、关键词与标签筛选论文。如果你还没想好从哪里开始，可以先看看热门主题。
            </p>
          </div>
          <div class="toolbar-jump-row">
            <a class="button button-chip" href="/themes">热门主题</a>
            <a class="button button-chip" href="/lists">阅读清单</a>
            <a class="button button-chip" href="/datasets">论文库</a>
          </div>
        </div>
        <div class="hero-pill-row">
          <span class="signal">关键词检索</span>
          <span class="signal">中文标签</span>
          <span class="signal">引用排序</span>
          <span class="signal">独立导读页</span>
        </div>
        ${renderWorkbenchStats(bootstrap, filters)}
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
          <span>添加标签</span>
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
            <span>筛选中的主题</span>
            <button id="add-tag-button" class="button button-chip" type="button" ${loading ? "disabled" : ""}>加入标签</button>
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
              : `<p class="tag-empty">可以直接输入关键词，也可以先加一两个主题标签，让结果更聚焦。</p>`
          }
        </div>
        <div class="toolbar-actions">
          <button type="submit" class="button button-primary" ${loading ? "disabled" : ""}>开始探索</button>
          <button id="refresh-button" type="button" class="button button-secondary" ${loading ? "disabled" : ""}>刷新数据</button>
        </div>
      </form>
    </section>
  `;
}
