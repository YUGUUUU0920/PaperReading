import { apiClient } from "./api/client.js";
import { renderTopNav } from "./components/top-nav.js";
import { escapeHtml } from "./utils/dom.js";
import { FEATURED_THEMES, getThemeMeta } from "./utils/tags.js";
import { buildSearchUrl } from "./utils/url.js";

const state = {
  loading: true,
  message: "正在准备今日的研究入口...",
  bootstrap: {
    conferences: [],
    defaults: { conference: "icml", year: 2025 },
    tagOptions: [],
  },
};

function latestConferenceCards(bootstrap) {
  return (bootstrap.conferences || [])
    .map((conference) => {
      const years = Array.isArray(conference.years) ? [...conference.years].sort((left, right) => right - left) : [];
      return {
        code: conference.code,
        label: conference.label,
        year: years[0],
      };
    })
    .filter((item) => item.year)
    .slice(0, 4);
}

function renderCoverage(bootstrap) {
  const conferences = bootstrap.conferences || [];
  const years = conferences.flatMap((item) => item.years || []);
  const latestYear = years.length ? Math.max(...years) : bootstrap.defaults.year;
  return `
    <section class="home-grid home-grid--stats">
      <article class="home-stat-card panel">
        <strong>${conferences.length}</strong>
        <span>研究来源</span>
      </article>
      <article class="home-stat-card panel">
        <strong>${latestYear}</strong>
        <span>最新年份覆盖</span>
      </article>
      <article class="home-stat-card panel">
        <strong>${(bootstrap.tagOptions || []).length}+</strong>
        <span>中文主题标签</span>
      </article>
    </section>
  `;
}

function renderThemeCards(bootstrap) {
  const defaults = bootstrap.defaults || { conference: "icml", year: 2025 };
  return `
    <section class="panel home-section">
      <div class="section-head">
        <div>
          <p class="eyebrow">Featured Themes</p>
          <h2>常用研究入口</h2>
          <p>先选方向，再进入专题探索页继续收窄范围。</p>
        </div>
        <a class="button button-ghost" href="/themes">浏览全部主题</a>
      </div>
      <div class="atlas-feature-grid">
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
          })
          .join("")}
      </div>
    </section>
  `;
}

function renderHome() {
  const { bootstrap, message } = state;
  const defaults = bootstrap.defaults || { conference: "icml", year: 2025 };
  const exploreUrl = buildSearchUrl({
    conference: defaults.conference,
    year: defaults.year,
    query: "",
    tags: defaults.tags || [],
    sort: defaults.sort || "default",
    page: 1,
  });
  const conferenceCards = latestConferenceCards(bootstrap);

  document.getElementById("app").innerHTML = `
    <main class="app-shell app-shell--home">
      ${renderTopNav("home")}
      <section class="home-hero panel">
        <div class="home-hero__copy">
          <p class="eyebrow">Research Atlas</p>
          <h1>把研究入口收拢成几条清晰路径</h1>
          <p class="toolbar-text">
            先按主题判断方向，再进入专题探索页筛论文，最后把值得深读的工作沉淀进阅读清单。首页只保留真正高频的入口。
          </p>
          <div class="card-actions">
            <a class="button button-primary" href="${exploreUrl}">进入研究探索</a>
            <a class="button button-secondary" href="/themes">浏览主题路径</a>
            <a class="button button-ghost" href="/lists">打开阅读清单</a>
          </div>
        </div>
        <div class="home-hero__visual" aria-hidden="true">
          <div class="home-hero-orbit home-hero-orbit--outer"></div>
          <div class="home-hero-orbit home-hero-orbit--inner"></div>
          <div class="home-hero-card">
            <small>Today</small>
            <strong>${escapeHtml(defaults.conference.toUpperCase())} ${escapeHtml(defaults.year)}</strong>
            <span>${escapeHtml(message)}</span>
          </div>
          <span class="home-hero-node home-hero-node--one"></span>
          <span class="home-hero-node home-hero-node--two"></span>
          <span class="home-hero-node home-hero-node--three"></span>
        </div>
      </section>

      <section class="home-grid home-grid--routes">
        <a class="route-card panel" href="/themes">
          <p class="eyebrow">Path 01</p>
          <h2>主题浏览</h2>
          <p>适合先锁定研究方向，再进入具体论文。</p>
        </a>
        <a class="route-card panel" href="${exploreUrl}">
          <p class="eyebrow">Path 02</p>
          <h2>研究探索</h2>
          <p>按会议、年份、关键词与标签快速筛选。</p>
        </a>
        <a class="route-card panel" href="/lists">
          <p class="eyebrow">Path 03</p>
          <h2>阅读清单</h2>
          <p>收藏、待读、分组和备注都在这里沉淀。</p>
        </a>
        <a class="route-card panel" href="/datasets">
          <p class="eyebrow">Path 04</p>
          <h2>论文库状态</h2>
          <p>查看覆盖范围、年份切片与数据状态。</p>
        </a>
      </section>

      ${renderCoverage(bootstrap)}

      ${renderThemeCards(bootstrap)}

      <section class="panel home-section">
        <div class="section-head">
          <div>
            <p class="eyebrow">Conference Slices</p>
            <h2>从时间切片进入</h2>
            <p>如果你已经知道会议和年份，可以直接进入对应的研究流。</p>
          </div>
        </div>
        <div class="conference-grid">
          ${conferenceCards
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
                  <p>直接进入这一时间切片，查看主题分布与代表论文。</p>
                </a>
              `;
            })
            .join("")}
        </div>
      </section>
    </main>
  `;
}

apiClient
  .getBootstrap()
  .then((bootstrap) => {
    state.bootstrap = bootstrap;
    state.message = "按主题、按时间切片、按阅读任务进入，都已经准备好了。";
    state.loading = false;
    renderHome();
  })
  .catch((error) => {
    state.loading = false;
    state.message = error.message;
    renderHome();
  });

renderHome();
