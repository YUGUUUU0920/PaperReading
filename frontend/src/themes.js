import { apiClient } from "./api/client.js";
import { renderTopNav } from "./components/top-nav.js";
import { escapeHtml } from "./utils/dom.js";
import { FEATURED_THEMES, THEME_GROUPS, getThemeMeta } from "./utils/tags.js";
import { buildSearchUrl } from "./utils/url.js";

const state = {
  bootstrap: {
    conferences: [],
    defaults: { conference: "icml", year: 2025 },
  },
  message: "从你关心的研究方向开始，快速找到相关论文。",
};

function renderThemeCard(theme, defaults) {
  const meta = getThemeMeta(theme);
  const href = buildSearchUrl({
    conference: defaults.conference,
    year: defaults.year,
    query: "",
    tags: [theme],
    sort: "default",
    page: 1,
  });
  return `
    <a class="atlas-feature-card" href="${href}" data-tone="${meta.tone}">
      <div class="atlas-feature-card__head">
        <span class="pill pill--tag" data-tone="${meta.tone}">${escapeHtml(theme)}</span>
        <span class="atlas-feature-card__arrow">打开合集</span>
      </div>
      <strong>${escapeHtml(theme)}</strong>
      <p>${escapeHtml(meta.description)}</p>
    </a>
  `;
}

function renderThemeGroups() {
  const defaults = state.bootstrap.defaults || { conference: "icml", year: 2025 };
  return THEME_GROUPS.map(
    (group) => `
      <section class="panel theme-cluster">
        <div class="section-head">
          <div>
            <p class="eyebrow">Collection Cluster</p>
            <h2>${escapeHtml(group.title)}</h2>
            <p>${escapeHtml(group.description)}</p>
          </div>
        </div>
        <div class="atlas-feature-grid">
          ${group.themes.map((theme) => renderThemeCard(theme, defaults)).join("")}
        </div>
      </section>
    `,
  ).join("");
}

function renderConferenceTracks() {
  const defaults = state.bootstrap.defaults || { conference: "icml", year: 2025 };
  const picks = (state.bootstrap.conferences || [])
    .map((conference) => {
      const years = Array.isArray(conference.years) ? [...conference.years].sort((left, right) => right - left) : [];
      return {
        code: conference.code,
        label: conference.label,
        year: years[0] || defaults.year,
      };
    })
    .slice(0, 4);

  return `
    <section class="panel home-section">
      <div class="section-head">
          <div>
            <p class="eyebrow">Archive Slices</p>
            <h2>按会议切入</h2>
            <p>如果你已经知道要看的会议批次，可以从这里直接进入对应榜单。</p>
          </div>
        </div>
      <div class="conference-grid">
        ${picks
          .map((item) => {
            const href = buildSearchUrl({
              conference: item.code,
              year: item.year,
              query: "",
              tags: [],
              sort: "default",
              page: 1,
            });
            return `
              <a class="conference-card" href="${href}">
                <div class="paper-card__meta">
                  <span class="pill">${escapeHtml(item.label)}</span>
                  <span class="pill">${escapeHtml(item.year)}</span>
                </div>
                <strong>${escapeHtml(item.label)} ${escapeHtml(item.year)}</strong>
                <p>查看这一会议在该年份的新品榜单，再继续筛选关键词和标签。</p>
              </a>
            `;
          })
          .join("")}
      </div>
    </section>
  `;
}

function render() {
  const defaults = state.bootstrap.defaults || { conference: "icml", year: 2025 };
  document.getElementById("app").innerHTML = `
    <main class="app-shell">
      ${renderTopNav("themes")}
      <section class="toolbar panel toolbar--compact toolbar--browse">
        <div class="toolbar-copy toolbar-copy--compact">
          <p class="eyebrow">Collections</p>
          <h1>按专题合集开始浏览</h1>
          <p class="toolbar-text">${escapeHtml(state.message)}</p>
          <div class="hero-pill-row">
            ${FEATURED_THEMES.slice(0, 6)
              .map((theme) => {
                const meta = getThemeMeta(theme);
                const href = buildSearchUrl({
                  conference: defaults.conference,
                  year: defaults.year,
                  query: "",
                  tags: [theme],
                  sort: "default",
                  page: 1,
                });
                return `<a class="pill pill--tag" data-tone="${meta.tone}" href="${href}">${escapeHtml(theme)}</a>`;
              })
              .join("")}
          </div>
        </div>
      </section>
      ${renderThemeGroups()}
      ${renderConferenceTracks()}
    </main>
  `;
}

apiClient
  .getBootstrap()
  .then((bootstrap) => {
    state.bootstrap = bootstrap;
    state.message = "每个合集都会直接带你看到对应方向的上榜论文、中文标签和导读入口。";
    render();
  })
  .catch((error) => {
    state.message = error.message;
    render();
  });

render();
