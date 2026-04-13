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
  message: "先选主题，再进入更具体的论文流。",
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
        <span class="atlas-feature-card__arrow">进入专题</span>
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
            <p class="eyebrow">Theme Cluster</p>
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
          <p class="eyebrow">Shortcuts</p>
          <h2>按会议切入</h2>
          <p>如果你已经知道想看的会议，就从这里直接跳到专题探索页。</p>
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
                <p>进入这一会议切片，再按主题、关键词和信号继续筛选。</p>
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
          <p class="eyebrow">Theme Browser</p>
          <h1>先决定方向，再进入论文</h1>
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
    state.message = "每个主题都会把你带到更具体的专题探索页，而不是把所有信息堆在首页。";
    render();
  })
  .catch((error) => {
    state.message = error.message;
    render();
  });

render();
