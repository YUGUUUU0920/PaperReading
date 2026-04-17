import { escapeHtml } from "../utils/dom.js";
import { getTagTone } from "../utils/tags.js";

function renderStats(bootstrap, filters) {
  const conferenceCount = (bootstrap.conferences || []).length;
  const latestYear = Math.max(...((bootstrap.conferences || []).flatMap((item) => item.years || []).concat([filters.year || 2025])));
  const tagCount = Array.isArray(filters.tags) ? filters.tags.length : 0;
  return `
    <div class="page-hero__stats page-hero__stats--compact">
      <div class="hero-stat-card">
        <strong>${conferenceCount}</strong>
        <span>会议来源</span>
      </div>
      <div class="hero-stat-card">
        <strong>${latestYear}</strong>
        <span>最新年份</span>
      </div>
      <div class="hero-stat-card">
        <strong>${tagCount}</strong>
        <span>已选主题</span>
      </div>
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
    <section class="panel search-station">
      <div class="search-station__intro">
        <p class="eyebrow">Explore Papers</p>
        <h1>把一个研究问题收窄到能认真读的范围。</h1>
        <p class="page-hero__lead">
          先用会议、年份、关键词和中文主题把结果整理成一张更可读的图，再决定哪些论文值得打开详情继续深读。
        </p>
        ${renderStats(bootstrap, filters)}
      </div>
      <form id="search-form" class="search-form search-station__form">
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
            <span>当前筛选主题</span>
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
              : `<p class="tag-empty">先加一两个主题标签，通常会比只输关键词更快收窄结果。</p>`
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
