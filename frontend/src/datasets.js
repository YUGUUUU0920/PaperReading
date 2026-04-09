import { apiClient } from "./api/client.js";
import { renderTopNav } from "./components/top-nav.js";
import { createStore } from "./state/store.js";
import { escapeHtml } from "./utils/dom.js";

const store = createStore({
  bootstrap: {
    conferences: [],
    defaults: { conference: "icml", year: 2024 },
  },
  datasets: [],
  loading: false,
  message: "这里展示当前已缓存的数据集，以及你可以主动刷新的会议年份。",
});

function renderDatasetCards(state) {
  if (!state.datasets.length) {
    return `
      <div class="empty-card">
        <h3>还没有已追踪的数据集</h3>
        <p>回到论文检索页执行一次搜索后，这里的缓存状态就会自动出现。</p>
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
              <h3>${escapeHtml(dataset.item_count)} 篇缓存论文</h3>
              <p class="preview">最近同步：${escapeHtml(dataset.last_synced_at || "暂无")}</p>
              ${dataset.last_error ? `<p class="error-text">${escapeHtml(dataset.last_error)}</p>` : ""}
              <div class="card-actions">
                <a class="button button-ghost" href="/?conference=${escapeHtml(dataset.conference)}&year=${escapeHtml(dataset.year)}">查看论文</a>
                <button class="button button-primary" data-refresh="${escapeHtml(dataset.conference)}:${escapeHtml(dataset.year)}">刷新这个数据集</button>
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
              <p>如果你想提前预热某个会议年份的缓存，可以在这里直接刷新。</p>
              <div class="card-actions">
                <a class="button button-ghost" href="/?conference=${escapeHtml(item.code)}&year=${escapeHtml(item.year)}">去检索</a>
                <button class="button button-secondary" data-refresh="${escapeHtml(item.code)}:${escapeHtml(item.year)}">刷新缓存</button>
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
          <p class="eyebrow">Dataset Operations</p>
          <h1>缓存状态和刷新操作拆成独立页面</h1>
          <p class="toolbar-text">${escapeHtml(state.message)}</p>
        </div>
      </section>
      <section class="workspace workspace--single">
        <section class="list-panel panel">
          <div class="section-head">
            <div>
              <h2>已追踪数据集</h2>
              <p>这些是已经被搜索过或手动刷新过的会议年份。</p>
            </div>
          </div>
          ${renderDatasetCards(state)}
        </section>
        <section class="list-panel panel">
          <div class="section-head">
            <div>
              <h2>快速刷新入口</h2>
              <p>如果你要预热缓存，可以直接在这里触发。</p>
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
        message: `正在刷新 ${conference.toUpperCase()} ${yearText}...`,
      });
      render();
      try {
        await apiClient.refreshDataset({ conference, year: Number(yearText) });
        await loadAll();
        store.setState({
          message: `${conference.toUpperCase()} ${yearText} 已刷新。`,
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
