import { apiClient } from "./api/client.js";
import { renderTopNav } from "./components/top-nav.js";
import { renderSearchToolbar } from "./components/search-toolbar.js";
import { renderStatusBanner } from "./components/status-banner.js";
import { renderPaperList } from "./components/paper-list.js";
import { createStore } from "./state/store.js";
import { qs, qsa } from "./utils/dom.js";
import { buildSearchUrl, readSearchParams } from "./utils/url.js";

const store = createStore({
  bootstrap: {
    conferences: [],
    defaults: { conference: "icml", year: 2025 },
    summaryEnabled: false,
  },
  filters: {
    conference: "icml",
    year: 2025,
    query: "",
    page: 1,
  },
  message: "准备就绪。选择会议、年份和关键词后开始检索。",
  dataset: null,
  papers: [],
  total: 0,
  pageSize: 24,
  hasNext: false,
  hasSearched: false,
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
        page: 1,
      };
      store.setState({ filters });
      await runSearch({ refresh: false });
    });
  }

  if (refreshButton) {
    refreshButton.addEventListener("click", async () => {
      const { filters } = store.getState();
      store.setState({
        loading: true,
        message: `正在更新 ${filters.conference.toUpperCase()} ${filters.year} 的论文数据...`,
      });
      render();
      try {
        const data = await apiClient.refreshDataset(filters);
        store.setState({
          dataset: data.dataset,
          message: `${data.dataset.conference.toUpperCase()} ${data.dataset.year} 已更新，共收录 ${data.dataset.item_count} 篇论文。`,
        });
      } catch (error) {
        store.setState({ message: error.message });
      } finally {
        store.setState({ loading: false });
        await runSearch({ refresh: false });
      }
    });
  }

  qsa("[data-page]").forEach((button) => {
    button.addEventListener("click", async () => {
      const nextPage = Number(button.getAttribute("data-page") || 0);
      if (!nextPage || nextPage < 1) return;
      const { filters, loading } = store.getState();
      if (loading || nextPage === Number(filters.page || 1)) return;
      store.setState({
        filters: { ...filters, page: nextPage },
      });
      window.scrollTo({ top: 0, behavior: "smooth" });
      await runSearch({ refresh: false });
    });
  });
}

async function bootstrap() {
  const data = await apiClient.getBootstrap();
  const params = readSearchParams();
  const hasExplicitSearch = ["conference", "year", "query", "page"].some((key) => params.has(key));
  const year = Number(params.get("year") || data.defaults.year) || data.defaults.year;
  const page = Math.max(1, Number(params.get("page") || 1) || 1);
  const filters = {
    conference: params.get("conference") || data.defaults.conference,
    year,
    query: params.get("query") || "",
    page,
  };
  store.setState({
    bootstrap: data,
    filters,
  });
  render();
  if (hasExplicitSearch) {
    await runSearch({ refresh: false });
  }
}

async function runSearch({ refresh }) {
  const { filters } = store.getState();
  window.history.replaceState({}, "", buildSearchUrl(filters));
  store.setState({
    loading: true,
    hasSearched: true,
    message: refresh
      ? `正在更新并整理 ${filters.conference.toUpperCase()} ${filters.year} 的结果...`
      : `正在整理 ${filters.conference.toUpperCase()} ${filters.year} 第 ${filters.page} 页的检索结果...`,
  });
  render();
  try {
    const data = await apiClient.searchPapers({
      conference: filters.conference,
      year: filters.year,
      query: filters.query,
      page: filters.page,
      limit: store.getState().pageSize,
      autoSync: true,
    });
    store.setState({
      papers: data.items,
      dataset: data.dataset,
      total: data.total || 0,
      pageSize: data.page_size || store.getState().pageSize,
      hasNext: Boolean(data.has_next),
      message: data.dataset
        ? `${data.dataset.conference.toUpperCase()} ${data.dataset.year} 当前共收录 ${data.dataset.item_count} 篇论文，本次命中 ${data.total || data.count} 篇。`
        : "检索完成。",
    });
  } catch (error) {
    store.setState({
      message: error.message,
      papers: [],
      total: 0,
      hasNext: false,
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
