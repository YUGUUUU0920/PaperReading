import { apiClient } from "./api/client.js";
import { renderPageHero } from "./components/page-hero.js";
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
        <span class="atlas-feature-card__arrow">进入主题</span>
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
      <section class="panel home-section">
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
    .slice(0, 6);

  return `
    <section class="panel home-section">
      <div class="section-head">
        <div>
          <p class="eyebrow">Conference Entry</p>
          <h2>也可以直接从会议批次切入</h2>
          <p>如果你已经确定要看的会议和年份，可以从这里直接进入结果页，再继续按主题和关键词细分。</p>
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
                <p>直接查看这一会议年份下的论文，再继续做更细的筛选。</p>
              </a>
            `;
          })
          .join("")}
      </div>
    </section>
  `;
}

function renderHero() {
  const defaults = state.bootstrap.defaults || { conference: "icml", year: 2025 };
  const chips = FEATURED_THEMES.slice(0, 6)
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
    .join("");

  return renderPageHero({
    eyebrow: "Browse Themes",
    title: "先从研究主题建立方向感。",
    description:
      "当你还不想直接面对一整页论文结果时，先从中文主题进入会更轻松。每个主题都对应一组更相关的论文与阅读线索。",
    stats: [
      { value: FEATURED_THEMES.length, label: "高频主题" },
      { value: (state.bootstrap.conferences || []).length, label: "会议来源" },
      { value: defaults.year, label: "默认年份" },
    ],
    actions: [
      { href: "/explore", label: "去搜索页", className: "button-primary" },
      { href: "/lineage", label: "看研究脉络", className: "button-secondary" },
    ],
    note: "如果你已经知道方向，直接点进主题会比从空白搜索开始更快。",
    asideHtml: `
      <div class="hero-spotlight">
        <article class="hero-feature-card">
          <div class="section-label-row">
            <span class="section-label">热门主题</span>
            <span class="signal">${FEATURED_THEMES.length} 个</span>
          </div>
          <div class="tag-row tag-row--wrap">
            ${chips}
          </div>
        </article>
      </div>
    `,
  });
}

function render() {
  document.getElementById("app").innerHTML = `
    <main class="app-shell">
      ${renderTopNav("themes")}
      ${renderHero()}
      <div class="section-stack">
        ${renderThemeGroups()}
        ${renderConferenceTracks()}
      </div>
    </main>
  `;
}

apiClient
  .getBootstrap()
  .then((bootstrap) => {
    state.bootstrap = bootstrap;
    state.message = "每个主题都会带你进入一组更相关的论文结果，适合先建立方向感。";
    render();
  })
  .catch((error) => {
    state.message = error.message;
    render();
  });

render();
