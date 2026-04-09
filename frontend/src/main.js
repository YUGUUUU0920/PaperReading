import { apiClient } from "./api/client.js";
import { renderTopNav } from "./components/top-nav.js";
import { renderSearchToolbar } from "./components/search-toolbar.js";
import { renderStatusBanner } from "./components/status-banner.js";
import { renderPaperList } from "./components/paper-list.js";
import { createStore } from "./state/store.js";
import { qs } from "./utils/dom.js";
import { buildSearchUrl, readSearchParams } from "./utils/url.js";

const store = createStore({
  bootstrap: {
    conferences: [],
    defaults: { conference: "icml", year: 2024 },
    summaryEnabled: false,
  },
  filters: {
    conference: "icml",
    year: 2024,
    query: "",
  },
  message: "准备就绪。搜索时会自动获取官方论文列表。",
  dataset: null,
  papers: [],
  loading: false,
});

function render() {
  const state = store.getState();
  const app = document.getElementById("app");
  app.innerHTML = `
    <main class="app-shell">
      ${renderTopNav("papers")}
      ${renderSearchToolbar(state)}
      ${renderStatusBanner(state)}
      <section class="workspace workspace--single">
        ${renderPaperList(state)}
      </section>
    </main>
  `;
  bindEvents();
}

function bindEvents() {
  const searchForm = qs("#search-form");
  const refreshButton = qs("#refresh-button");

  if (searchForm) {
    searchForm.addEventListener("submit", async (event) => {
      event.preventDefault();
      const form = new FormData(searchForm);
      const filters = {
        conference: String(form.get("conference") || "").trim(),
        year: Number(form.get("year") || 0),
        query: String(form.get("query") || "").trim(),
      };
      window.history.replaceState({}, "", buildSearchUrl(filters));
      store.setState({ filters });
      await runSearch({ refresh: false });
    });
  }

  if (refreshButton) {
    refreshButton.addEventListener("click", async () => {
      const { filters } = store.getState();
      store.setState({
        loading: true,
        message: `正在强制刷新 ${filters.conference.toUpperCase()} ${filters.year} 的本地缓存...`,
      });
      render();
      try {
        const data = await apiClient.refreshDataset(filters);
        store.setState({
          dataset: data.dataset,
          message: `缓存已刷新：${data.dataset.conference.toUpperCase()} ${data.dataset.year} 共 ${data.dataset.item_count} 篇。`,
        });
      } catch (error) {
        store.setState({ message: error.message });
      } finally {
        store.setState({ loading: false });
        await runSearch({ refresh: false });
      }
    });
  }
}

async function bootstrap() {
  const data = await apiClient.getBootstrap();
  const params = readSearchParams();
  const filters = {
    conference: params.get("conference") || data.defaults.conference,
    year: Number(params.get("year") || data.defaults.year),
    query: params.get("query") || "",
  };
  store.setState({
    bootstrap: data,
    filters,
  });
  render();
  await runSearch({ refresh: false });
}

async function runSearch({ refresh }) {
  const { filters } = store.getState();
  store.setState({
    loading: true,
    message: refresh
      ? `正在刷新并查询 ${filters.conference.toUpperCase()} ${filters.year}...`
      : `正在查询 ${filters.conference.toUpperCase()} ${filters.year}，如果本地没有数据会自动从官方站点获取...`,
  });
  render();
  try {
    const data = await apiClient.searchPapers({
      conference: filters.conference,
      year: filters.year,
      query: filters.query,
      autoSync: true,
    });
    store.setState({
      papers: data.items,
      dataset: data.dataset,
      message: data.dataset
        ? `${data.dataset.conference.toUpperCase()} ${data.dataset.year} 已就绪，当前缓存 ${data.dataset.item_count} 篇论文。`
        : "查询完成。",
    });
  } catch (error) {
    store.setState({
      message: error.message,
      papers: [],
    });
  } finally {
    store.setState({ loading: false });
    render();
  }
}

store.subscribe(() => {});
bootstrap().catch((error) => {
  store.setState({ message: error.message });
  render();
});
