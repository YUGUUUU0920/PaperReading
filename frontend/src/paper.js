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
  viewer: null,
  viewerDraftName: "",
  comments: [],
  backUrl: "/",
  loadingDetail: false,
  loadingSummary: false,
  loadingComments: false,
  postingComment: false,
  updatingViewerName: false,
  message: "正在准备论文详情页...",
});

function render() {
  const state = store.getState();
  document.getElementById("app").innerHTML = `
    <main class="app-shell app-shell--detail">
      ${renderTopNav("explore")}
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
  if (summarizeButton) {
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

  document.querySelectorAll("[data-save-toggle]").forEach((button) => {
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
        store.setState({
          activePaper: data.item,
          message: enabled ? "已更新列表。" : "已移出列表。",
        });
      } catch (error) {
        store.setState({ message: error.message });
      } finally {
        render();
      }
    });
  });

  const viewerSaveButton = qs("#viewer-name-save");
  if (viewerSaveButton) {
    viewerSaveButton.addEventListener("click", async () => {
      const input = qs("#viewer-name-input");
      const displayName = String(input?.value || "").trim();
      if (!displayName) {
        store.setState({ message: "先给自己起个昵称。", viewerDraftName: "" });
        render();
        return;
      }
      store.setState({ updatingViewerName: true, message: "正在保存昵称..." });
      render();
      try {
        const data = await apiClient.updateViewer({ displayName });
        const comments = store
          .getState()
          .comments.map((item) => (item.profile_id === data.viewer.id ? { ...item, display_name: data.viewer.display_name } : item));
        store.setState({
          viewer: data.viewer,
          viewerDraftName: data.viewer.display_name,
          comments,
          message: "昵称已保存。",
        });
      } catch (error) {
        store.setState({ message: error.message });
      } finally {
        store.setState({ updatingViewerName: false });
        render();
      }
    });
  }

  const commentForm = qs("#comment-form");
  if (commentForm) {
    commentForm.addEventListener("submit", async (event) => {
      event.preventDefault();
      const paper = store.getState().activePaper;
      const textarea = qs("#comment-input");
      const content = String(textarea?.value || "").trim();
      if (!paper) return;
      let submitted = false;
      store.setState({ postingComment: true, message: "正在发布评论..." });
      render();
      try {
        const data = await apiClient.addComment(paper.id, { content });
        store.setState({
          viewer: data.viewer,
          viewerDraftName: data.viewer.display_name,
          comments: [...store.getState().comments, data.item],
          message: "评论已发布。",
        });
        submitted = true;
      } catch (error) {
        store.setState({ message: error.message });
      } finally {
        store.setState({ postingComment: false });
        render();
        if (submitted) {
          const refreshedTextarea = qs("#comment-input");
          if (refreshedTextarea) refreshedTextarea.value = "";
        }
      }
    });
  }

  const viewerInput = qs("#viewer-name-input");
  if (viewerInput) {
    viewerInput.addEventListener("input", (event) => {
      const target = event.target;
      store.setState({ viewerDraftName: String(target?.value || "") });
    });
  }
}

async function bootstrap() {
  const params = readSearchParams();
  const id = Number(params.get("id") || 0);
  if (!id) {
    store.setState({ message: "缺少论文 id，无法打开详情页。", backUrl: "/explore" });
    render();
    return;
  }

  const bootstrapData = await apiClient.getBootstrap();
  const filters = {
    conference: params.get("conference") || bootstrapData.defaults.conference,
    year: Number(params.get("year") || bootstrapData.defaults.year),
    query: params.get("query") || "",
    tags: params.getAll("tag").filter(Boolean).length ? params.getAll("tag").filter(Boolean) : bootstrapData.defaults.tags || [],
    sort: params.get("sort") || bootstrapData.defaults.sort || "default",
  };
  store.setState({
    bootstrap: bootstrapData,
    backUrl: buildSearchUrl(filters),
    loadingDetail: true,
    loadingComments: true,
    message: "正在整理论文详情、标签与相关资源...",
  });
  render();

  try {
    const [paperData, commentsData] = await Promise.all([apiClient.getPaper(id), apiClient.getComments(id)]);
    store.setState({
      activePaper: paperData.item,
      viewer: commentsData.viewer,
      viewerDraftName: commentsData.viewer?.display_name || "",
      comments: commentsData.items || [],
      message: "论文详情已加载。",
    });
  } catch (error) {
    store.setState({ message: error.message });
  } finally {
    store.setState({ loadingDetail: false, loadingComments: false });
    render();
  }
}

bootstrap().catch((error) => {
  store.setState({ message: error.message });
  render();
});
