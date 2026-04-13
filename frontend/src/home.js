import { apiClient } from "./api/client.js";
import { renderTopNav } from "./components/top-nav.js";
import { escapeHtml } from "./utils/dom.js";
import { FEATURED_THEMES, getThemeMeta } from "./utils/tags.js";
import { buildSearchUrl } from "./utils/url.js";

const state = {
  loading: true,
  message: "正在准备今日值得关注的论文方向...",
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
          <h2>热门研究方向</h2>
          <p>从你关心的方向开始，快速看到相关论文与中文导读。</p>
        </div>
        <a class="button button-ghost" href="/themes">查看全部主题</a>
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
                  <span class="atlas-feature-card__arrow">查看论文</span>
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
          <h1>更快找到今天值得读的论文</h1>
          <p class="toolbar-text">
            用主题、导读和研究信号重新组织论文发现过程，帮助你更快判断哪些工作值得细读、比较和收藏。
          </p>
          <div class="card-actions">
            <a class="button button-primary" href="${exploreUrl}">开始发现论文</a>
            <a class="button button-secondary" href="/themes">查看热门主题</a>
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
          <p class="eyebrow">Themes</p>
          <h2>热门主题</h2>
          <p>从高频研究方向开始，快速进入相关论文集合。</p>
        </a>
        <a class="route-card panel" href="${exploreUrl}">
          <p class="eyebrow">Search</p>
          <h2>论文发现</h2>
          <p>按会议、年份、关键词与标签做更细的筛选。</p>
        </a>
        <a class="route-card panel" href="/lists">
          <p class="eyebrow">Reading List</p>
          <h2>阅读清单</h2>
          <p>把收藏、待读、分组和备注都沉淀下来。</p>
        </a>
        <a class="route-card panel" href="/datasets">
          <p class="eyebrow">Library</p>
          <h2>论文库</h2>
          <p>查看覆盖范围、年份分布与数据更新情况。</p>
        </a>
      </section>

      ${renderCoverage(bootstrap)}

      ${renderThemeCards(bootstrap)}

      <section class="panel home-section">
        <div class="section-head">
          <div>
            <p class="eyebrow">Conference Slices</p>
            <h2>按会议与年份浏览</h2>
            <p>如果你已经知道想看的会议和年份，可以直接从这里开始。</p>
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
                  <p>查看这一场会议在该年份的论文、主题和代表工作。</p>
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
    state.message = "从主题、会议或阅读清单开始，都能很快进入今天最值得看的论文。";
    state.loading = false;
    renderHome();
  })
  .catch((error) => {
    state.loading = false;
    state.message = error.message;
    renderHome();
  });

renderHome();
