import { apiClient } from "./api/client.js";
import { renderTopNav } from "./components/top-nav.js";
import { renderPaperDetail } from "./components/paper-detail.js";
import { createStore } from "./state/store.js";
import { qs } from "./utils/dom.js";
import { buildSearchUrl, readSearchParams } from "./utils/url.js";

const store = createStore({
  bootstrap: {
    conferences: [],
    defaults: { conference: "icml", year: 2025 },
    summaryEnabled: false,
  },
  activePaper: null,
  backUrl: "/",
  loadingDetail: false,
  loadingSummary: false,
  message: "正在准备论文详情页...",
});

function render() {
  const state = store.getState();
  document.getElementById("app").innerHTML = `
    <main class="app-shell app-shell--detail">
      ${renderTopNav("papers")}
      <section class="status-banner panel">
        <div>
          <h2>论文导读</h2>
          <p>${state.message}</p>
        </div>
      </section>
      ${renderPaperDetail(state)}
    </main>
  `;
  bindEvents();
}

function bindEvents() {
  const summarizeButton = qs("#summarize-paper-button");
  if (!summarizeButton) return;
  summarizeButton.addEventListener("click", async () => {
    const paper = store.getState().activePaper;
    if (!paper) return;
    store.setState({
      loadingSummary: true,
      message: "正在生成中文导读...",
    });
    render();
    try {
      const data = await apiClient.summarizePaper(paper.id);
      store.setState({
        activePaper: data.item,
        message: "中文导读已更新。",
      });
    } catch (error) {
      store.setState({ message: error.message });
    } finally {
      store.setState({ loadingSummary: false });
      render();
    }
  });
}

async function bootstrap() {
  const params = readSearchParams();
  const id = Number(params.get("id") || 0);
  if (!id) {
    store.setState({ message: "缺少论文 id，无法打开详情页。", backUrl: "/" });
    render();
    return;
  }

  const bootstrapData = await apiClient.getBootstrap();
  const filters = {
    conference: params.get("conference") || bootstrapData.defaults.conference,
    year: Number(params.get("year") || bootstrapData.defaults.year),
    query: params.get("query") || "",
  };
  store.setState({
    bootstrap: bootstrapData,
    backUrl: buildSearchUrl(filters),
    loadingDetail: true,
    message: "正在整理论文详情、标签与相关资源...",
  });
  render();

  try {
    const data = await apiClient.getPaper(id);
    store.setState({
      activePaper: data.item,
      message: "论文详情已加载。",
    });
  } catch (error) {
    store.setState({ message: error.message });
  } finally {
    store.setState({ loadingDetail: false });
    render();
  }
}

bootstrap().catch((error) => {
  store.setState({ message: error.message });
  render();
});
