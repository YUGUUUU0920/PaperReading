import { escapeHtml } from "../utils/dom.js";
import { getTagTone } from "../utils/tags.js";

function renderHeroStats(bootstrap) {
  const conferenceCount = (bootstrap.conferences || []).length;
  const years = (bootstrap.conferences || []).flatMap((item) => item.years || []);
  const minYear = years.length ? Math.min(...years) : 2024;
  const maxYear = years.length ? Math.max(...years) : 2025;
  const tagCount = (bootstrap.tagOptions || []).length;

  return `
    <div class="hero-stats">
      <article class="hero-stat-card">
        <strong>${conferenceCount}</strong>
        <span>研究来源</span>
      </article>
      <article class="hero-stat-card">
        <strong>${minYear}-${maxYear}</strong>
        <span>时间切片</span>
      </article>
      <article class="hero-stat-card">
        <strong>${tagCount}+</strong>
        <span>中文主题标签</span>
      </article>
    </div>
  `;
}

function renderHeroMotion() {
  return `
    <div class="hero-motion" aria-hidden="true">
      <div class="hero-orbit hero-orbit--outer"></div>
      <div class="hero-orbit hero-orbit--mid"></div>
      <div class="hero-orbit hero-orbit--inner"></div>
      <span class="hero-node hero-node--one"></span>
      <span class="hero-node hero-node--two"></span>
      <span class="hero-node hero-node--three"></span>
      <div class="hero-panel">
        <small>Research Atlas</small>
        <strong>Theme · Signal · Brief</strong>
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
    <section class="toolbar panel">
      <div class="toolbar-copy">
        <p class="eyebrow">Research Atlas</p>
        <h1>把论文流变成可阅读的研究图谱</h1>
        <p class="toolbar-text">
          用主题、信号和中文导读重新组织论文发现过程，让你先看清方向，再决定哪些工作值得深入阅读。
        </p>
        <div class="hero-pill-row">
          <span class="signal">主题导览</span>
          <span class="signal">中文标签</span>
          <span class="signal">导读摘要</span>
          <span class="signal">资源线索</span>
        </div>
        ${renderHeroStats(bootstrap)}
        ${renderHeroMotion()}
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
              : `<p class="tag-empty">先定义你关心的研究主题，系统会把结果压缩成更清晰的主题视图。</p>`
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
