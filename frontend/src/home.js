import { apiClient } from "./api/client.js";
import { renderLineagePreview } from "./components/lineage-sections.js";
import { renderTopNav } from "./components/top-nav.js";
import { escapeHtml, qsa } from "./utils/dom.js";
import { FEATURED_THEMES, getThemeMeta, getTagTone } from "./utils/tags.js";
import { buildPaperUrl, buildSearchUrl } from "./utils/url.js";

const state = {
  loading: true,
  message: "正在整理中文研究新品榜...",
  bootstrap: {
    conferences: [],
    defaults: { conference: "icml", year: 2025 },
    tagOptions: [],
  },
  showcase: {
    overview: {
      total_papers: 0,
      conference_count: 0,
      latest_year: 2025,
      theme_count: 0,
      favorite_count: 0,
      reading_count: 0,
    },
    ranked_launches: [],
    latest_launches: [],
    collections: [],
    makers: [],
    tracks: [],
  },
  lineage: {
    items: [],
    available_themes: [],
    coverage: {
      paper_count: 0,
      dataset_count: 0,
    },
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

function getLatestYear() {
  return state.showcase.overview?.latest_year || state.bootstrap.defaults?.year || 2025;
}

function buildTodayBoardUrl() {
  return buildSearchUrl({
    year: getLatestYear(),
    sort: "citations_desc",
    page: 1,
  });
}

function buildThemeUrl(theme) {
  return buildSearchUrl({
    year: getLatestYear(),
    tags: [theme],
    sort: "citations_desc",
    page: 1,
  });
}

function renderThemePill(tag) {
  const tone = getTagTone(tag);
  return `<span class="pill pill--tag" data-tone="${tone}">${escapeHtml(tag)}</span>`;
}

function renderSignalRow(paper) {
  const signals = [];
  if (paper.launch_score) signals.push(`热度 ${paper.launch_score}`);
  if (paper.citation_count) signals.push(`被引 ${paper.citation_count}`);
  if (paper.code_url) signals.push("附代码");
  if (paper.open_access) signals.push("开放获取");
  if (paper.top_10_percent_cited) signals.push("高影响力");
  if (!signals.length) return "";
  return `
    <div class="signal-row">
      ${signals.map((item) => `<span class="signal">${escapeHtml(item)}</span>`).join("")}
    </div>
  `;
}

function renderSaveActions(paper) {
  return `
    <div class="save-actions">
      <button class="button button-chip ${paper.saved?.favorite ? "active" : ""}" type="button" data-save-toggle="${paper.id}:favorite:${paper.saved?.favorite ? "0" : "1"}">
        ${paper.saved?.favorite ? "已收藏" : "收藏"}
      </button>
      <button class="button button-chip ${paper.saved?.reading ? "active" : ""}" type="button" data-save-toggle="${paper.id}:reading:${paper.saved?.reading ? "0" : "1"}">
        ${paper.saved?.reading ? "已在待读" : "加入待读"}
      </button>
    </div>
  `;
}

function renderHero() {
  const heroPaper = state.showcase.ranked_launches[0];
  const latestPapers = state.showcase.latest_launches.slice(0, 3);
  const latestYear = getLatestYear();
  const latestTheme = state.showcase.collections[0]?.theme || heroPaper?.primary_theme || "人工智能";
  const heroUrl = heroPaper ? buildPaperUrl(heroPaper.id, { conference: heroPaper.conference, year: heroPaper.year }) : buildTodayBoardUrl();

  return `
    <section class="home-hero panel home-hero--launchpad">
      <div class="home-hero__copy">
        <p class="eyebrow">Launchboard</p>
        <h1>像逛 Product Hunt 一样，发现今天最值得追的中文研究新品。</h1>
        <p class="toolbar-text">
          我们把榜单、专题合集、作者热度、中文导读和阅读清单放到同一个入口里，
          让研究发现不只是“搜到论文”，而是快速判断哪些工作值得立刻跟进。
        </p>
        <div class="hero-pill-row">
          <span class="pill">${latestYear} 最新批次</span>
          <span class="pill">${state.showcase.overview.total_papers} 条研究条目</span>
          <span class="pill">${state.showcase.overview.theme_count} 个中文主题</span>
          ${renderThemePill(latestTheme)}
        </div>
        <div class="card-actions">
          <a class="button button-primary" href="${buildTodayBoardUrl()}">打开今日主榜</a>
          <a class="button button-secondary" href="/lineage">查看研究脉络</a>
          <a class="button button-ghost" href="/themes">浏览专题合集</a>
        </div>
      </div>
      <div class="home-hero__visual home-hero__visual--launch">
        ${
          heroPaper
            ? `
              <a class="hero-launch-card" href="${heroUrl}">
                <div class="hero-launch-card__head">
                  <span class="pill">No.1 今日主榜</span>
                  <span class="hero-rank-score">${heroPaper.launch_score}</span>
                </div>
                <strong>${escapeHtml(heroPaper.title_display || heroPaper.title)}</strong>
                <p>${escapeHtml(heroPaper.summary_preview || "查看中文导读、研究信号和相关推荐。")}</p>
                <div class="hero-launch-meta">
                  <span>${escapeHtml(heroPaper.conference.toUpperCase())} ${escapeHtml(heroPaper.year)}</span>
                  <span>${escapeHtml(heroPaper.track_label || "主会场")}</span>
                  <span>${escapeHtml(heroPaper.primary_theme || "人工智能")}</span>
                </div>
              </a>
            `
            : `
              <div class="hero-launch-card">
                <div class="hero-launch-card__head">
                  <span class="pill">Launchboard</span>
                </div>
                <strong>正在等待研究条目</strong>
                <p>${escapeHtml(state.message)}</p>
              </div>
            `
        }
        <div class="hero-mini-stream">
          ${latestPapers
            .map((paper, index) => {
              const href = buildPaperUrl(paper.id, { conference: paper.conference, year: paper.year });
              return `
                <a class="hero-mini-item" href="${href}">
                  <span class="hero-mini-item__rank">${index + 1}</span>
                  <div>
                    <strong>${escapeHtml(paper.title_display || paper.title)}</strong>
                    <span>${escapeHtml(paper.primary_theme || "人工智能")} · ${escapeHtml(paper.conference.toUpperCase())} ${escapeHtml(paper.year)}</span>
                  </div>
                </a>
              `;
            })
            .join("")}
        </div>
      </div>
    </section>
  `;
}

function renderCoverage() {
  const overview = state.showcase.overview;
  return `
    <section class="home-grid home-grid--stats home-grid--stats-wide">
      <article class="home-stat-card panel">
        <strong>${overview.total_papers}</strong>
        <span>已收录研究新品</span>
      </article>
      <article class="home-stat-card panel">
        <strong>${overview.conference_count}</strong>
        <span>官方会议源</span>
      </article>
      <article class="home-stat-card panel">
        <strong>${overview.theme_count}</strong>
        <span>中文专题合集</span>
      </article>
      <article class="home-stat-card panel">
        <strong>${overview.reading_count + overview.favorite_count}</strong>
        <span>你的已沉淀条目</span>
      </article>
    </section>
  `;
}

function renderLaunchCard(paper, index) {
  const detailUrl = buildPaperUrl(paper.id, { conference: paper.conference, year: paper.year });
  return `
    <article class="paper-card paper-card--lift launch-card">
      <div class="launch-card__head">
        <div class="launch-rank-badge">
          <span class="launch-rank-badge__index">#{index + 1}</span>
          <span class="launch-rank-badge__label">今日热榜</span>
        </div>
        <div class="paper-card__meta">
          <span class="pill">${escapeHtml(paper.conference.toUpperCase())}</span>
          <span class="pill">${escapeHtml(paper.year)}</span>
          <span class="pill">${escapeHtml(paper.track_label || "主会场")}</span>
          ${paper.primary_theme ? renderThemePill(paper.primary_theme) : ""}
        </div>
      </div>
      <h3>${escapeHtml(paper.title_display || paper.title)}</h3>
      <p class="authors">${escapeHtml(paper.authors_text)}</p>
      ${renderSignalRow(paper)}
      <p class="preview summary-preview">${escapeHtml(paper.summary_preview || "查看摘要、导读与资源链接。")}</p>
      <div class="card-actions">
        <a class="button button-primary" href="${detailUrl}">查看详情</a>
        <a class="button button-secondary" href="${buildThemeUrl(paper.primary_theme || "人工智能")}">相似主题</a>
        ${paper.pdf_url ? `<a class="button button-ghost" href="${escapeHtml(paper.pdf_url)}" target="_blank" rel="noreferrer">打开 PDF</a>` : ""}
      </div>
      ${renderSaveActions(paper)}
    </article>
  `;
}

function renderLatestItem(paper) {
  const href = buildPaperUrl(paper.id, { conference: paper.conference, year: paper.year });
  return `
    <a class="mini-launch-card" href="${href}">
      <div class="mini-launch-card__head">
        <strong>${escapeHtml(paper.title_display || paper.title)}</strong>
        <span class="mini-launch-card__score">${escapeHtml(paper.launch_score)}</span>
      </div>
      <p>${escapeHtml(paper.primary_theme || "人工智能")} · ${escapeHtml(paper.conference.toUpperCase())} ${escapeHtml(paper.year)}</p>
    </a>
  `;
}

function renderDiscussionCards() {
  const firstTheme = state.showcase.collections[0]?.theme || FEATURED_THEMES[0];
  const secondTheme = state.showcase.collections[1]?.theme || FEATURED_THEMES[1];
  const topPaper = state.showcase.ranked_launches[0];
  const compareHref = topPaper
    ? buildPaperUrl(topPaper.id, { conference: topPaper.conference, year: topPaper.year })
    : buildTodayBoardUrl();
  const items = [
    {
      eyebrow: "讨论题 01",
      title: `${firstTheme} 里哪三篇最值得本周精读？`,
      description: "从一个专题合集切入，把“看什么”先固定下来，再决定读法和对比维度。",
      href: buildThemeUrl(firstTheme),
    },
    {
      eyebrow: "讨论题 02",
      title: "如何比较今日榜首和现有方案的真实差距？",
      description: "直接进入榜首条目，看摘要结构、实验设置和资源信号，减少只看标题的误判。",
      href: compareHref,
    },
    {
      eyebrow: "讨论题 03",
      title: `${secondTheme} 值不值得建一个长期跟踪清单？`,
      description: "把专题发现和待读清单串起来，形成更接近 Product Hunt 复访节奏的使用路径。",
      href: "/lists",
    },
  ];

  return `
    <section class="panel home-section side-panel">
      <div class="section-head">
        <div>
          <p class="eyebrow">Community Prompts</p>
          <h2>社区讨论入口</h2>
          <p>先把值得聊的问题摆出来，让发现流程天然带着比较和判断。</p>
        </div>
      </div>
      <div class="discussion-grid">
        ${items
          .map(
            (item) => `
              <a class="discussion-card" href="${item.href}">
                <p class="eyebrow">${escapeHtml(item.eyebrow)}</p>
                <strong>${escapeHtml(item.title)}</strong>
                <p>${escapeHtml(item.description)}</p>
              </a>
            `
          )
          .join("")}
      </div>
    </section>
  `;
}

function renderBoardSection() {
  return `
    <section class="launch-layout">
      <div class="panel home-section">
        <div class="section-head">
          <div>
            <p class="eyebrow">Today Board</p>
            <h2>今日主榜</h2>
            <p>综合引用、资源信号、会场级别与新近热度整理出最值得先看的研究条目。</p>
          </div>
          <a class="button button-ghost" href="${buildTodayBoardUrl()}">进入完整榜单</a>
        </div>
        <div class="launch-feed">
          ${state.showcase.ranked_launches.map((paper, index) => renderLaunchCard(paper, index)).join("")}
        </div>
      </div>
      <aside class="launch-sidebar">
        <section class="panel home-section side-panel">
          <div class="section-head">
            <div>
              <p class="eyebrow">Latest</p>
              <h2>最新上新</h2>
              <p>用更轻的浏览密度快速扫过最近进入视野的论文条目。</p>
            </div>
          </div>
          <div class="mini-launch-list">
            ${state.showcase.latest_launches.map((paper) => renderLatestItem(paper)).join("")}
          </div>
        </section>
        ${renderDiscussionCards()}
      </aside>
    </section>
  `;
}

function renderCollections() {
  return `
    <section class="panel home-section">
      <div class="section-head">
        <div>
          <p class="eyebrow">Collections</p>
          <h2>专题合集</h2>
          <p>把 Product Hunt 的合集机制翻译成中文研究主题，让发现不再只围绕单篇论文展开。</p>
        </div>
        <a class="button button-ghost" href="/themes">查看全部合集</a>
      </div>
      <div class="collection-grid">
        ${state.showcase.collections
          .map((collection) => {
            const meta = getThemeMeta(collection.theme);
            return `
              <article class="collection-card" data-tone="${meta.tone}">
                <div class="collection-card__head">
                  ${renderThemePill(collection.theme)}
                  <span class="counter">${collection.count}</span>
                </div>
                <h3>${escapeHtml(collection.theme)}</h3>
                <p>${escapeHtml(meta.description)}</p>
                <div class="collection-card__list">
                  ${collection.items
                    .map((paper) => {
                      const href = buildPaperUrl(paper.id, { conference: paper.conference, year: paper.year });
                      return `
                        <a class="collection-paper-link" href="${href}">
                          <strong>${escapeHtml(paper.title_display || paper.title)}</strong>
                          <span>${escapeHtml(paper.conference.toUpperCase())} ${escapeHtml(paper.year)} · 热度 ${escapeHtml(paper.launch_score)}</span>
                        </a>
                      `;
                    })
                    .join("")}
                </div>
                <a class="button button-secondary" href="${buildThemeUrl(collection.theme)}">进入这个合集</a>
              </article>
            `;
          })
          .join("")}
      </div>
    </section>
  `;
}

function renderPathGrid() {
  return `
    <section class="home-grid home-grid--routes">
      <a class="route-card panel" href="/lineage">
        <p class="eyebrow">Path</p>
        <h2>研究脉络</h2>
        <p>沿着主题主干和关键分支去读，先建立一个方向的整体地图。</p>
      </a>
      <a class="route-card panel" href="/explore">
        <p class="eyebrow">Board</p>
        <h2>今日主榜</h2>
        <p>从热度更高、信号更强的论文开始，再决定哪些值得深入精读。</p>
      </a>
      <a class="route-card panel" href="/themes">
        <p class="eyebrow">Collections</p>
        <h2>专题合集</h2>
        <p>按中文主题进入同方向论文集合，更适合系统性扫一条研究线。</p>
      </a>
      <a class="route-card panel" href="/lists">
        <p class="eyebrow">Reading List</p>
        <h2>阅读清单</h2>
        <p>把收藏、待读、分组和备注沉淀下来，形成自己的长期阅读节奏。</p>
      </a>
    </section>
  `;
}

function renderMakerSection() {
  return `
    <section class="panel home-section">
      <div class="section-head">
        <div>
          <p class="eyebrow">Maker Board</p>
          <h2>作者热榜</h2>
          <p>把 Product Hunt 的 maker 视角迁移到研究场景，帮助你看到谁在持续产出值得跟进的工作。</p>
        </div>
      </div>
      <div class="maker-grid">
        ${state.showcase.makers
          .map(
            (maker, index) => `
              <article class="maker-card">
                <div class="maker-card__head">
                  <span class="maker-card__rank">#${index + 1}</span>
                  ${renderThemePill(maker.top_theme)}
                </div>
                <strong>${escapeHtml(maker.name)}</strong>
                <p>${maker.paper_count} 篇上榜条目 · 覆盖 ${maker.conference_count} 个会议 · 热度 ${maker.heat_score}</p>
              </article>
            `
          )
          .join("")}
      </div>
    </section>
  `;
}

function renderConferenceSection() {
  const conferenceCards = latestConferenceCards(state.bootstrap);
  return `
    <section class="panel home-section">
      <div class="section-head">
        <div>
          <p class="eyebrow">Archive Slices</p>
          <h2>按会议与年份回看</h2>
          <p>如果你已经知道想观察的会议批次，可以直接从档案切片进入。</p>
        </div>
      </div>
      <div class="conference-grid">
        ${conferenceCards
          .map((item) => {
            const href = buildSearchUrl({
              conference: item.code,
              year: item.year,
              sort: "citations_desc",
              page: 1,
            });
            return `
              <a class="conference-card" href="${href}">
                <div class="paper-card__meta">
                  <span class="pill">${escapeHtml(item.label)}</span>
                  <span class="pill">${escapeHtml(item.year)}</span>
                </div>
                <strong>${escapeHtml(item.label)} ${escapeHtml(item.year)}</strong>
                <p>从这个会议批次进入榜单、标签和论文详情页。</p>
              </a>
            `;
          })
          .join("")}
      </div>
    </section>
  `;
}

function renderEmptyState() {
  return `
    <section class="panel home-section">
      <div class="empty-card empty-card--large atlas-note">
        <h3>研究新品榜正在准备中</h3>
        <p>${escapeHtml(state.message)}</p>
        <div class="card-actions">
          <a class="button button-primary" href="/explore">打开论文发现</a>
          <a class="button button-secondary" href="/datasets">查看数据档案</a>
        </div>
      </div>
    </section>
  `;
}

function renderHome() {
  const hasContent = state.showcase.ranked_launches.length || state.showcase.collections.length;
  document.getElementById("app").innerHTML = `
    <main class="app-shell app-shell--home app-shell--launchpad">
      ${renderTopNav("home")}
      ${renderHero()}
      ${renderCoverage()}
      ${hasContent ? renderBoardSection() : renderEmptyState()}
      ${hasContent ? renderCollections() : ""}
      ${renderPathGrid()}
      ${renderLineagePreview(state.lineage.items || [])}
      ${state.showcase.makers.length ? renderMakerSection() : ""}
      ${renderConferenceSection()}
    </main>
  `;
  bindEvents();
}

function replacePaperInCollection(items, updatedPaper) {
  return items.map((item) => (item.id === updatedPaper.id ? updatedPaper : item));
}

function replacePaperAcrossShowcase(updatedPaper) {
  state.showcase = {
    ...state.showcase,
    ranked_launches: replacePaperInCollection(state.showcase.ranked_launches, updatedPaper),
    latest_launches: replacePaperInCollection(state.showcase.latest_launches, updatedPaper),
    collections: (state.showcase.collections || []).map((collection) => ({
      ...collection,
      items: replacePaperInCollection(collection.items || [], updatedPaper),
    })),
  };
}

function bindEvents() {
  qsa("[data-save-toggle]").forEach((button) => {
    button.addEventListener("click", async () => {
      const raw = String(button.getAttribute("data-save-toggle") || "");
      const [paperIdText, listType, enabledText] = raw.split(":");
      const paperId = Number(paperIdText || 0);
      const enabled = enabledText === "1";
      if (!paperId || !listType) return;
      try {
        const data = await apiClient.toggleSavedPaper({ paperId, listType, enabled });
        replacePaperAcrossShowcase(data.item);
        renderHome();
      } catch (error) {
        state.message = error.message;
        renderHome();
      }
    });
  });
}

Promise.all([
  apiClient.getBootstrap(),
  apiClient.getShowcase(),
  apiClient.getLineage({ limit: 3 }).catch(() => ({
    items: [],
    available_themes: [],
    coverage: {
      paper_count: 0,
      dataset_count: 0,
    },
  })),
])
  .then(([bootstrap, showcase, lineage]) => {
    state.bootstrap = bootstrap;
    state.showcase = showcase;
    state.lineage = lineage;
    state.message = "今日榜单已准备好，可以从主榜、合集或作者热榜任一入口开始。";
    state.loading = false;
    renderHome();
  })
  .catch((error) => {
    state.loading = false;
    state.message = error.message;
    renderHome();
  });

renderHome();
