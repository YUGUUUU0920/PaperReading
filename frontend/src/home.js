import { apiClient } from "./api/client.js";
import { renderLineagePreview } from "./components/lineage-sections.js";
import { renderPageHero } from "./components/page-hero.js";
import { renderTopNav } from "./components/top-nav.js";
import { escapeHtml, qsa } from "./utils/dom.js";
import { getTagTone, getThemeMeta } from "./utils/tags.js";
import { buildPaperUrl, buildSearchUrl } from "./utils/url.js";

const DEFAULTS = { conference: "icml", year: 2025 };

const state = {
  loading: true,
  message: "正在整理研究入口...",
  bootstrap: {
    conferences: [],
    defaults: DEFAULTS,
    tagOptions: [],
    auth: {},
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
  },
};

function currentDefaults() {
  return state.bootstrap.defaults || DEFAULTS;
}

function preferredTheme() {
  return state.showcase.collections[0]?.theme || state.bootstrap.tagOptions?.[0] || "大模型";
}

function renderTagPill(tag) {
  return `<span class="pill pill--tag" data-tone="${getTagTone(tag)}">${escapeHtml(tag)}</span>`;
}

function renderSignalRow(paper) {
  const signals = [];
  if (paper.citation_count) signals.push(`被引 ${paper.citation_count}`);
  if (paper.code_url) signals.push("附代码");
  if (paper.open_access) signals.push("开放获取");
  if (paper.top_10_percent_cited) signals.push("高影响力");
  if (!signals.length) return "";
  return `<div class="signal-row">${signals.map((item) => `<span class="signal">${escapeHtml(item)}</span>`).join("")}</div>`;
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

function renderIdentityHint() {
  if (state.bootstrap.auth?.githubEnabled) {
    return "论文详情页支持收藏、待读与评论，也可以用 GitHub 身份参与讨论。";
  }
  return "论文详情页支持收藏、待读与评论，昵称会保存在当前浏览器里。";
}

function renderHeroAside() {
  const defaults = currentDefaults();
  const heroPaper = state.showcase.ranked_launches[0];
  const leadingTheme = preferredTheme();
  const leadingMeta = getThemeMeta(leadingTheme);
  const paperUrl = heroPaper
    ? buildPaperUrl(heroPaper.id, { conference: heroPaper.conference, year: heroPaper.year })
    : buildSearchUrl({
        conference: defaults.conference,
        year: defaults.year,
        sort: "default",
        page: 1,
      });

  return `
    <div class="hero-spotlight">
      <article class="hero-feature-card">
        <div class="section-label-row">
          <span class="section-label">当前焦点</span>
          ${heroPaper ? `<span class="signal">${escapeHtml(heroPaper.conference.toUpperCase())} ${escapeHtml(heroPaper.year)}</span>` : ""}
        </div>
        ${
          heroPaper
            ? `
              <a class="hero-feature-card__link" href="${paperUrl}">
                <strong>${escapeHtml(heroPaper.title_display || heroPaper.title)}</strong>
                <p>${escapeHtml(heroPaper.summary_preview || "打开论文详情，查看摘要、导读与相关资源。")}</p>
                ${renderSignalRow(heroPaper)}
              </a>
              <div class="tag-row">
                ${(heroPaper.tags || []).slice(0, 4).map((tag) => renderTagPill(tag)).join("")}
              </div>
            `
            : `
              <div class="hero-feature-card__link">
                <strong>正在准备推荐论文</strong>
                <p>${escapeHtml(state.message)}</p>
              </div>
            `
        }
      </article>
      <article class="hero-feature-card hero-feature-card--theme" data-tone="${leadingMeta.tone}">
        <div class="section-label-row">
          <span class="section-label">建议切入主题</span>
          ${renderTagPill(leadingTheme)}
        </div>
        <strong>${escapeHtml(leadingTheme)}</strong>
        <p>${escapeHtml(leadingMeta.description)}</p>
        <div class="card-actions">
          <a
            class="button button-secondary"
            href="${buildSearchUrl({
              conference: defaults.conference,
              year: defaults.year,
              tags: [leadingTheme],
              sort: "default",
              page: 1,
            })}"
          >
            进入这个主题
          </a>
        </div>
      </article>
    </div>
  `;
}

function renderHero() {
  const overview = state.showcase.overview || {};
  return renderPageHero({
    eyebrow: "Research Atlas",
    title: "先把今天真正值得读的论文筛出来。",
    description:
      "用搜索、中文主题、研究脉络和阅读清单，把论文发现流程重新排整齐。先建立方向感，再决定哪些工作值得投入时间深读。",
    stats: [
      { value: overview.latest_year || 2025, label: "最新年份" },
      { value: overview.total_papers || 0, label: "已收录论文" },
      { value: overview.theme_count || 0, label: "中文主题" },
      { value: overview.reading_count || 0, label: "待读条目" },
    ],
    actions: [
      { href: "/explore", label: "开始搜索", className: "button-primary" },
      { href: "/themes", label: "浏览主题", className: "button-secondary" },
      { href: "/lineage", label: "查看脉络", className: "button-ghost" },
    ],
    note: renderIdentityHint(),
    asideHtml: renderHeroAside(),
    className: "page-hero--home",
  });
}

function renderRouteGrid() {
  const defaults = currentDefaults();
  const firstTheme = preferredTheme();
  const items = [
    {
      eyebrow: "Search",
      title: "先用问题和关键词收窄范围",
      body: "从会议、年份、关键词开始，把一个方向迅速缩到能认真阅读的一小批论文。",
      href: "/explore",
      cta: "进入搜索",
    },
    {
      eyebrow: "Themes",
      title: "按中文主题建立方向感",
      body: "如果你已经知道大方向，直接进入中文主题，把相关论文放在一起看。",
      href: buildSearchUrl({ conference: defaults.conference, year: defaults.year, tags: [firstTheme], sort: "default", page: 1 }),
      cta: "进入主题",
    },
    {
      eyebrow: "Lineage",
      title: "顺着主干理解研究演化",
      body: "从起点工作到最新推进，把一个主题的关键论文串成可读的主线。",
      href: "/lineage",
      cta: "查看脉络",
    },
  ];

  return `
    <section class="panel home-section">
      <div class="section-head">
        <div>
          <p class="eyebrow">Reading Flow</p>
          <h2>按这条阅读流进入会更清楚</h2>
          <p>这个首页不再堆信息，而是把论文发现分成三个更自然的入口。</p>
        </div>
      </div>
      <div class="route-grid">
        ${items
          .map(
            (item) => `
              <a class="route-card" href="${item.href}">
                <p class="eyebrow">${escapeHtml(item.eyebrow)}</p>
                <h3>${escapeHtml(item.title)}</h3>
                <p>${escapeHtml(item.body)}</p>
                <span class="route-card__cta">${escapeHtml(item.cta)}</span>
              </a>
            `,
          )
          .join("")}
      </div>
    </section>
  `;
}

function renderFeaturedPaper(paper) {
  const href = buildPaperUrl(paper.id, { conference: paper.conference, year: paper.year });
  return `
    <article class="paper-card paper-card--lift">
      <div class="paper-card__meta">
        <span class="pill">${escapeHtml(paper.conference.toUpperCase())}</span>
        <span class="pill">${escapeHtml(paper.year)}</span>
        <span class="pill">${escapeHtml(paper.track_label || paper.track || "论文")}</span>
      </div>
      <h3>${escapeHtml(paper.title_display || paper.title)}</h3>
      <p class="authors">${escapeHtml(paper.authors_text)}</p>
      ${renderSignalRow(paper)}
      <div class="tag-row">
        ${(paper.tags || []).slice(0, 4).map((tag) => renderTagPill(tag)).join("")}
      </div>
      <p class="preview summary-preview">${escapeHtml(paper.summary_preview || "查看摘要、导读与资源信号。")}</p>
      <div class="card-actions">
        <a class="button button-primary" href="${href}">查看详情</a>
        ${paper.pdf_url ? `<a class="button button-ghost" href="${escapeHtml(paper.pdf_url)}" target="_blank" rel="noreferrer">打开 PDF</a>` : ""}
      </div>
      ${renderSaveActions(paper)}
    </article>
  `;
}

function renderFeaturedSection() {
  const papers = (state.showcase.ranked_launches || []).slice(0, 3);
  if (!papers.length) return "";
  return `
    <section class="panel home-section">
      <div class="section-head">
        <div>
          <p class="eyebrow">Featured Papers</p>
          <h2>适合先打开的代表论文</h2>
          <p>这里不是排行榜，而是当前更适合先建立方向感的几篇工作。</p>
        </div>
        <a class="button button-ghost" href="/explore">查看完整结果</a>
      </div>
      <div class="theme-paper-grid">
        ${papers.map((paper) => renderFeaturedPaper(paper)).join("")}
      </div>
    </section>
  `;
}

function renderCollections() {
  const defaults = currentDefaults();
  const collections = (state.showcase.collections || []).slice(0, 4);
  if (!collections.length) return "";
  return `
    <section class="panel home-section">
      <div class="section-head">
        <div>
          <p class="eyebrow">Themes</p>
          <h2>先从这几个研究方向判断值不值得追</h2>
          <p>每个方向都收拢了一组相关论文，适合快速判断你接下来该读哪一条线。</p>
        </div>
        <a class="button button-ghost" href="/themes">查看全部主题</a>
      </div>
      <div class="collection-grid">
        ${collections
          .map((collection) => {
            const meta = getThemeMeta(collection.theme);
            return `
              <article class="collection-card" data-tone="${meta.tone}">
                <div class="collection-card__head">
                  ${renderTagPill(collection.theme)}
                  <span class="counter">${collection.count}</span>
                </div>
                <h3>${escapeHtml(collection.theme)}</h3>
                <p>${escapeHtml(meta.description)}</p>
                <div class="collection-card__list">
                  ${(collection.items || [])
                    .slice(0, 3)
                    .map((paper) => {
                      const href = buildPaperUrl(paper.id, { conference: paper.conference, year: paper.year });
                      return `
                        <a class="collection-paper-link" href="${href}">
                          <strong>${escapeHtml(paper.title_display || paper.title)}</strong>
                          <span>${escapeHtml(paper.conference.toUpperCase())} ${escapeHtml(paper.year)}</span>
                        </a>
                      `;
                    })
                    .join("")}
                </div>
                <a
                  class="button button-secondary"
                  href="${buildSearchUrl({ conference: defaults.conference, year: defaults.year, tags: [collection.theme], sort: "default", page: 1 })}"
                >
                  进入主题
                </a>
              </article>
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
      <div class="empty-card empty-card--large">
        <h3>正在准备论文入口</h3>
        <p>${escapeHtml(state.message)}</p>
        <div class="card-actions">
          <a class="button button-primary" href="/explore">打开论文搜索</a>
          <a class="button button-secondary" href="/themes">浏览主题</a>
        </div>
      </div>
    </section>
  `;
}

function renderHome() {
  const hasContent = state.showcase.ranked_launches.length || state.showcase.collections.length;
  document.getElementById("app").innerHTML = `
    <main class="app-shell app-shell--home">
      ${renderTopNav("home")}
      ${renderHero()}
      <div class="section-stack">
        ${renderRouteGrid()}
        ${hasContent ? renderFeaturedSection() : renderEmptyState()}
        ${hasContent ? renderCollections() : ""}
        ${renderLineagePreview(state.lineage.items || [])}
      </div>
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

Promise.all([apiClient.getBootstrap(), apiClient.getShowcase(), apiClient.getLineage({ limit: 3 })])
  .then(([bootstrap, showcase, lineage]) => {
    state.bootstrap = bootstrap;
    state.showcase = showcase;
    state.lineage = lineage;
    state.message = "从搜索、主题或研究脉络开始，先找到值得投入时间的论文。";
    state.loading = false;
    renderHome();
  })
  .catch((error) => {
    state.loading = false;
    state.message = error.message;
    renderHome();
  });

renderHome();
