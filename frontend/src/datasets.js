import { apiClient } from "./api/client.js";
import { renderTopNav } from "./components/top-nav.js";
import { createStore } from "./state/store.js";
import { escapeHtml } from "./utils/dom.js";

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
                <a class="button button-ghost" href="/?conference=${escapeHtml(dataset.conference)}&year=${escapeHtml(dataset.year)}">查看论文</a>
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
            <article class="empty-card">
              <h3>${escapeHtml(item.label)} ${escapeHtml(item.year)}</h3>
              <p>想先整理某个会议年份的论文，可以从这里直接开始。</p>
              <div class="card-actions">
                <a class="button button-ghost" href="/?conference=${escapeHtml(item.code)}&year=${escapeHtml(item.year)}">浏览论文</a>
                <button class="button button-secondary" data-refresh="${escapeHtml(item.code)}:${escapeHtml(item.year)}">更新数据</button>
              </div>
            </article>
          `,
        )
        .join("")}
    </div>
  `;
}

function render() {
  const state = store.getState();
  document.getElementById("app").innerHTML = `
    <main class="app-shell">
      ${renderTopNav("datasets")}
      <section class="toolbar panel toolbar--compact">
        <div class="toolbar-copy">
          <p class="eyebrow">Paper Library</p>
          <h1>论文库总览</h1>
          <p class="toolbar-text">${escapeHtml(state.message)}</p>
        </div>
      </section>
      <section class="workspace workspace--single">
        <section class="list-panel panel">
          <div class="section-head">
            <div>
              <h2>已收录年份</h2>
              <p>查看每个会议年份的论文规模与最近更新时间。</p>
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
