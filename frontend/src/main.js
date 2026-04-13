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
    tags: [],
    sort: "default",
    page: 1,
  },
  message: "准备就绪。先定义一个研究主题，再开始探索论文。",
  dataset: null,
  papers: [],
  resultTags: [],
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
  const addTagButton = qs("#add-tag-button");
  const tagPicker = qs("#tag-picker");

  if (searchForm) {
    searchForm.addEventListener("submit", async (event) => {
      event.preventDefault();
      const form = new FormData(searchForm);
      const current = store.getState().filters;
      const filters = {
        conference: String(form.get("conference") || "").trim(),
        year: Number(form.get("year") || 0),
        query: String(form.get("query") || "").trim(),
        tags: current.tags || [],
        sort: String(form.get("sort") || "default").trim() || "default",
        page: 1,
      };
      store.setState({ filters });
      await runSearch({ refresh: false });
    });
  }

  if (addTagButton && tagPicker) {
    addTagButton.addEventListener("click", async () => {
      const picked = String(tagPicker.value || "").trim();
      if (!picked) return;
      const { filters, hasSearched, loading } = store.getState();
      if (loading) return;
      const nextTags = filters.tags.includes(picked) ? filters.tags : [...filters.tags, picked];
      store.setState({
        filters: {
          ...filters,
          tags: nextTags,
          page: 1,
        },
      });
      if (hasSearched) {
        await runSearch({ refresh: false });
      } else {
        render();
      }
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

  qsa("[data-filter-tag]").forEach((button) => {
    button.addEventListener("click", async () => {
      const tag = String(button.getAttribute("data-filter-tag") || "").trim();
      const { filters, loading } = store.getState();
      if (loading) return;
      store.setState({
        filters: {
          ...filters,
          tags: filters.tags.includes(tag) ? filters.tags.filter((item) => item !== tag) : [...filters.tags, tag],
          page: 1,
        },
      });
      await runSearch({ refresh: false });
    });
  });

  qsa("[data-remove-tag]").forEach((button) => {
    button.addEventListener("click", async () => {
      const tag = String(button.getAttribute("data-remove-tag") || "").trim();
      const { filters, hasSearched, loading } = store.getState();
      if (loading) return;
      const nextTags = filters.tags.filter((item) => item !== tag);
      store.setState({
        filters: {
          ...filters,
          tags: nextTags,
          page: 1,
        },
      });
      if (hasSearched) {
        await runSearch({ refresh: false });
      } else {
        render();
      }
    });
  });

  qsa("[data-save-toggle]").forEach((button) => {
    button.addEventListener("click", async () => {
      const raw = String(button.getAttribute("data-save-toggle") || "");
      const [paperIdText, listType, enabledText] = raw.split(":");
      const paperId = Number(paperIdText || 0);
      const enabled = enabledText === "1";
      if (!paperId || !listType) return;
      store.setState({ message: enabled ? "正在加入列表..." : "正在移出列表..." });
      render();
      try {
        const data = await apiClient.toggleSavedPaper({ paperId, listType, enabled });
        const papers = store.getState().papers.map((paper) => (paper.id === paperId ? data.item : paper));
        store.setState({
          papers,
          message: enabled ? "已更新列表。" : "已移出列表。",
        });
      } catch (error) {
        store.setState({ message: error.message });
      } finally {
        render();
      }
    });
  });
}

async function bootstrap() {
  const data = await apiClient.getBootstrap();
  const params = readSearchParams();
  const hasExplicitSearch = ["conference", "year", "query", "tag", "sort", "page"].some((key) => params.has(key));
  const year = Number(params.get("year") || data.defaults.year) || data.defaults.year;
  const page = Math.max(1, Number(params.get("page") || 1) || 1);
  const tags = params.getAll("tag").filter(Boolean);
  const filters = {
    conference: params.get("conference") || data.defaults.conference,
    year,
    query: params.get("query") || "",
    tags: tags.length ? tags : data.defaults.tags || [],
    sort: params.get("sort") || data.defaults.sort || "default",
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
      : `正在整理 ${filters.conference.toUpperCase()} ${filters.year} 第 ${filters.page} 页的主题结果...`,
  });
  render();
  try {
    const data = await apiClient.searchPapers({
      conference: filters.conference,
      year: filters.year,
      query: filters.query,
      tags: filters.tags,
      sort: filters.sort,
      page: filters.page,
      limit: store.getState().pageSize,
      autoSync: true,
    });
    store.setState({
      papers: data.items,
      dataset: data.dataset,
      resultTags: data.result_tags || [],
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
      resultTags: [],
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
