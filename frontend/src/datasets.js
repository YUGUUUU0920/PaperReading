import { apiClient } from "./api/client.js";
import { renderPageHero } from "./components/page-hero.js";
import { renderTopNav } from "./components/top-nav.js";
import { createStore } from "./state/store.js";
import { escapeHtml } from "./utils/dom.js";
import { buildSearchUrl } from "./utils/url.js";

const store = createStore({
  bootstrap: {
    conferences: [],
    defaults: { conference: "icml", year: 2025 },
  },
  datasets: [],
  loading: false,
  message: "这里汇总已经收录的会议年份与论文规模。",
});

function renderDatasetCards(state) {
  if (!state.datasets.length) {
    return `
      <div class="empty-card">
        <h3>还没有收录记录</h3>
        <p>先去论文检索页浏览一个会议年份，这里就会出现对应的论文库概览。</p>
      </div>
    `;
  }

  return `
    <div class="dataset-grid">
      ${state.datasets
        .map(
          (dataset) => `
            <article class="paper-card">
              <div class="paper-card__meta">
                <span class="pill">${escapeHtml(dataset.conference.toUpperCase())}</span>
                <span class="pill">${escapeHtml(dataset.year)}</span>
                <span class="pill">${escapeHtml(dataset.status)}</span>
              </div>
              <h3>${escapeHtml(dataset.item_count)} 篇论文</h3>
              <p class="preview">最近更新：${escapeHtml(dataset.last_synced_at || "暂无")}</p>
              ${dataset.last_error ? `<p class="error-text">${escapeHtml(dataset.last_error)}</p>` : ""}
              <div class="card-actions">
                <a class="button button-ghost" href="${buildSearchUrl({ conference: dataset.conference, year: dataset.year })}">查看论文</a>
                <button class="button button-primary" data-refresh="${escapeHtml(dataset.conference)}:${escapeHtml(dataset.year)}">更新论文库</button>
              </div>
            </article>
          `,
        )
        .join("")}
    </div>
  `;
}

function renderQuickActions(state) {
  const items = [];
  for (const conference of state.bootstrap.conferences || []) {
    for (const year of conference.years || []) {
      items.push({ code: conference.code, label: conference.label, year });
    }
  }

  return `
    <div class="dataset-grid">
      ${items
        .map(
          (item) => `
            <article class="conference-card">
              <div class="paper-card__meta">
                <span class="pill">${escapeHtml(item.label)}</span>
                <span class="pill">${escapeHtml(item.year)}</span>
              </div>
              <strong>${escapeHtml(item.label)} ${escapeHtml(item.year)}</strong>
              <p>从这里直接进入该会议年份，开始浏览与整理论文。</p>
              <div class="card-actions">
                <a class="button button-ghost" href="${buildSearchUrl({ conference: item.code, year: item.year })}">浏览论文</a>
                <button class="button button-secondary" data-refresh="${escapeHtml(item.code)}:${escapeHtml(item.year)}">更新数据</button>
              </div>
            </article>
          `,
        )
        .join("")}
    </div>
  `;
}

function renderHero(state) {
  return renderPageHero({
    eyebrow: "Research Coverage",
    title: "先知道你手上这套论文库覆盖到哪里。",
    description:
      "这里集中展示已收录的会议年份、论文规模和更新时间。你可以先确认覆盖范围，再决定从哪个会议批次开始继续读。",
    stats: [
      { value: state.datasets.length || 0, label: "已同步批次" },
      { value: (state.bootstrap.conferences || []).length, label: "会议来源" },
      { value: state.bootstrap.defaults?.year || 2025, label: "默认年份" },
    ],
    actions: [
      { href: "/explore", label: "打开搜索", className: "button-primary" },
      { href: "/themes", label: "浏览主题", className: "button-secondary" },
    ],
    note: state.message,
  });
}

function render() {
  const state = store.getState();
  document.getElementById("app").innerHTML = `
    <main class="app-shell">
      ${renderTopNav("datasets")}
      ${renderHero(state)}
      <section class="workspace workspace--single">
        <section class="list-panel panel">
          <div class="section-head">
            <div>
              <h2>已收录年份</h2>
              <p>查看每个会议年份的论文规模、同步状态与最近更新时间。</p>
            </div>
          </div>
          ${renderDatasetCards(state)}
        </section>
        <section class="list-panel panel">
          <div class="section-head">
            <div>
              <h2>快速入口</h2>
              <p>从这里直接进入任意会议年份，开始浏览与整理论文。</p>
            </div>
          </div>
          ${renderQuickActions(state)}
        </section>
      </section>
    </main>
  `;
  bindEvents();
}

function bindEvents() {
  document.querySelectorAll("[data-refresh]").forEach((button) => {
    button.addEventListener("click", async () => {
      const [conference, yearText] = String(button.getAttribute("data-refresh")).split(":");
      store.setState({
        loading: true,
        message: `正在更新 ${conference.toUpperCase()} ${yearText}...`,
      });
      render();
      try {
        await apiClient.refreshDataset({ conference, year: Number(yearText) });
        await loadAll();
        store.setState({
          message: `${conference.toUpperCase()} ${yearText} 已更新。`,
        });
      } catch (error) {
        store.setState({ message: error.message });
      } finally {
        store.setState({ loading: false });
        render();
      }
    });
  });
}

async function loadAll() {
  const [bootstrap, datasets] = await Promise.all([apiClient.getBootstrap(), apiClient.getDatasets()]);
  store.setState({
    bootstrap,
    datasets: datasets.items || [],
  });
}

loadAll()
  .then(render)
  .catch((error) => {
    store.setState({ message: error.message });
    render();
  });

render();
