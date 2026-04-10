import { apiClient } from "./api/client.js";
import { renderTopNav } from "./components/top-nav.js";
import { createStore } from "./state/store.js";
import { escapeHtml } from "./utils/dom.js";
import { buildPaperUrl } from "./utils/url.js";

const store = createStore({
  loading: false,
  message: "这里汇总你标记为收藏与待读的论文。",
  counts: {
    favorite: 0,
    reading: 0,
  },
  favorite: [],
  reading: [],
});

function renderTagRow(tags = []) {
  if (!tags.length) return "";
  return `
    <div class="tag-row">
      ${tags.slice(0, 5).map((tag) => `<span class="pill pill--tag">${escapeHtml(tag)}</span>`).join("")}
    </div>
  `;
}

function renderSavedSection(title, listType, items) {
  if (!items.length) {
    return `
      <section class="list-panel panel">
        <div class="section-head">
          <div>
            <h2>${escapeHtml(title)}</h2>
          </div>
        </div>
        <div class="empty-card">
          <h3>这里还没有论文</h3>
          <p>回到检索页或论文详情页，把感兴趣的论文加入这个列表。</p>
        </div>
      </section>
    `;
  }

  return `
    <section class="list-panel panel">
      <div class="section-head">
        <div>
          <h2>${escapeHtml(title)}</h2>
          <p>共 ${items.length} 篇</p>
        </div>
      </div>
      <div class="paper-list">
        ${items
          .map((paper) => {
            const href = buildPaperUrl(paper.id, {
              conference: paper.conference,
              year: paper.year,
            });
            return `
              <article class="paper-card">
                <div class="paper-card__meta">
                  <span class="pill">${escapeHtml(paper.conference.toUpperCase())}</span>
                  <span class="pill">${escapeHtml(paper.year)}</span>
                  <span class="pill">${escapeHtml(paper.track || "未分类")}</span>
                </div>
                <h3>${escapeHtml(paper.title_display || paper.title)}</h3>
                <p class="authors">${escapeHtml(paper.authors_text || "")}</p>
                ${renderTagRow(paper.tags || [])}
                <p class="preview summary-preview">${escapeHtml(paper.summary_preview || "进入详情页查看导读。")}</p>
                <div class="card-actions">
                  <a class="button button-primary" href="${href}">查看详情</a>
                  ${paper.pdf_url ? `<a class="button button-ghost" href="${escapeHtml(paper.pdf_url)}" target="_blank" rel="noreferrer">打开 PDF</a>` : ""}
                  <button class="button button-chip active" type="button" data-save-toggle="${paper.id}:${escapeHtml(listType)}:0">移出列表</button>
                </div>
              </article>
            `;
          })
          .join("")}
      </div>
    </section>
  `;
}

function render() {
  const state = store.getState();
  document.getElementById("app").innerHTML = `
    <main class="app-shell">
      ${renderTopNav("lists")}
      <section class="toolbar panel toolbar--compact">
        <div class="toolbar-copy">
          <p class="eyebrow">Reading Lists</p>
          <h1>收藏与待读</h1>
          <p class="toolbar-text">${escapeHtml(state.message)}</p>
          <div class="status-pills">
            <span class="pill">收藏 ${escapeHtml(state.counts.favorite)}</span>
            <span class="pill">待读 ${escapeHtml(state.counts.reading)}</span>
          </div>
        </div>
      </section>
      <section class="workspace workspace--single">
        ${renderSavedSection("收藏夹", "favorite", state.favorite)}
        ${renderSavedSection("待读列表", "reading", state.reading)}
      </section>
    </main>
  `;
  bindEvents();
}

function bindEvents() {
  document.querySelectorAll("[data-save-toggle]").forEach((button) => {
    button.addEventListener("click", async () => {
      const raw = String(button.getAttribute("data-save-toggle") || "");
      const [paperIdText, listType, enabledText] = raw.split(":");
      const paperId = Number(paperIdText || 0);
      const enabled = enabledText === "1";
      if (!paperId || !listType) return;
      store.setState({
        loading: true,
        message: enabled ? "正在加入列表..." : "正在移出列表...",
      });
      render();
      try {
        await apiClient.toggleSavedPaper({ paperId, listType, enabled });
        await loadAll();
        store.setState({
          message: enabled ? "已更新列表。" : "已移出列表。",
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
  const payload = await apiClient.getSavedLists();
  store.setState({
    favorite: payload.favorite || [],
    reading: payload.reading || [],
    counts: payload.counts || { favorite: 0, reading: 0 },
  });
}

loadAll()
  .then(render)
  .catch((error) => {
    store.setState({ message: error.message });
    render();
  });

render();
