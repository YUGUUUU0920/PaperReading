import { apiClient } from "./api/client.js";
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

function renderHero() {
  const defaults = currentDefaults();
  const heroPaper = state.showcase.ranked_launches[0];
  const leadingTheme = preferredTheme();
  const leadingMeta = getThemeMeta(leadingTheme);
  const heroUrl = heroPaper
    ? buildPaperUrl(heroPaper.id, { conference: heroPaper.conference, year: heroPaper.year })
    : buildSearchUrl({
        conference: defaults.conference,
        year: defaults.year,
        sort: "default",
        page: 1,
      });

  return `
    <section class="home-hero panel">
      <div class="home-hero__copy home-hero__copy--atlas">
        <p class="eyebrow">Research Atlas</p>
        <h1>先找到真正值得读的论文。</h1>
        <p class="toolbar-text">
          用关键词、中文主题和研究脉络组织论文发现流程。
          先快速判断方向，再决定哪些工作值得投入时间深读。
        </p>
        <div class="hero-pill-row">
          <span class="pill">${state.showcase.overview.latest_year} 最新论文</span>
          <span class="pill">${state.showcase.overview.total_papers} 篇已收录</span>
          <span class="pill">${state.showcase.overview.theme_count} 个中文主题</span>
        </div>
        <div class="card-actions">
          <a class="button button-primary" href="/explore">开始搜索</a>
          <a class="button button-secondary" href="/themes">浏览主题</a>
          <a class="button button-ghost" href="/lineage">研究脉络</a>
        </div>
        <p class="tag-empty home-note">${escapeHtml(renderIdentityHint())}</p>
      </div>
      <div class="home-hero__visual home-hero__visual--atlas">
        <div class="atlas-glow atlas-glow--one"></div>
        <div class="atlas-glow atlas-glow--two"></div>
        <div class="atlas-glass-card">
          <div class="paper-card__meta">
            <span class="pill pill--tag" data-tone="${leadingMeta.tone}">${escapeHtml(leadingTheme)}</span>
            ${
              heroPaper
                ? `
                  <span class="pill">${escapeHtml(heroPaper.conference.toUpperCase())}</span>
                  <span class="pill">${escapeHtml(heroPaper.year)}</span>
                `
                : `<span class="pill">${escapeHtml(defaults.year)}</span>`
            }
          </div>
          ${
            heroPaper
              ? `
                <a class="atlas-featured-link" href="${heroUrl}">
                  <strong>${escapeHtml(heroPaper.title_display || heroPaper.title)}</strong>
                  <p>${escapeHtml(heroPaper.summary_preview || "打开论文详情，查看摘要、导读与相关资源。")}</p>
                  ${renderSignalRow(heroPaper)}
                </a>
              `
              : `
                <div class="atlas-featured-link">
                  <strong>正在准备推荐论文</strong>
                  <p>${escapeHtml(state.message)}</p>
                </div>
              `
          }
        </div>
      </div>
    </section>
  `;
}

function renderPathGrid() {
  const defaults = currentDefaults();
  const firstTheme = preferredTheme();
  return `
    <section class="home-grid home-grid--routes home-grid--routes-compact">
      <a class="route-card panel" href="/explore">
        <p class="eyebrow">Search</p>
        <h2>按关键词搜索</h2>
        <p>从会议、年份、关键词开始，迅速缩小到真正相关的一小批论文。</p>
      </a>
      <a class="route-card panel" href="${buildSearchUrl({ conference: defaults.conference, year: defaults.year, tags: [firstTheme], sort: "default", page: 1 })}">
        <p class="eyebrow">Themes</p>
        <h2>按主题浏览</h2>
        <p>如果你已经知道方向，可以直接进入中文主题，把相关工作放在一起看。</p>
      </a>
      <a class="route-card panel" href="/lineage">
        <p class="eyebrow">Lineage</p>
        <h2>沿脉络阅读</h2>
        <p>从起点论文到最新推进，快速补齐一个方向的整体地图。</p>
      </a>
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
        ${(paper.tags || []).slice(0, 3).map((tag) => renderTagPill(tag)).join("")}
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
          <h2>先从这几篇开始</h2>
          <p>这里不是排名，而是当前更适合先打开的代表论文。</p>
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
  const collections = (state.showcase.collections || []).slice(0, 3);
  if (!collections.length) return "";
  return `
    <section class="panel home-section">
      <div class="section-head">
        <div>
          <p class="eyebrow">Themes</p>
          <h2>先看这几个方向</h2>
          <p>每个方向都收拢了一组相关论文，适合快速判断是否值得继续深读。</p>
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
                <a class="button button-secondary" href="${buildSearchUrl({ conference: defaults.conference, year: defaults.year, tags: [collection.theme], sort: "default", page: 1 })}">进入主题</a>
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
      <div class="empty-card empty-card--large atlas-note">
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
      ${renderPathGrid()}
      ${hasContent ? renderFeaturedSection() : renderEmptyState()}
      ${hasContent ? renderCollections() : ""}
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

Promise.all([apiClient.getBootstrap(), apiClient.getShowcase()])
  .then(([bootstrap, showcase]) => {
    state.bootstrap = bootstrap;
    state.showcase = showcase;
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
