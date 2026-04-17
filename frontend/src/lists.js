import { apiClient } from "./api/client.js";
import { renderPageHero } from "./components/page-hero.js";
import { renderTopNav } from "./components/top-nav.js";
import { createStore } from "./state/store.js";
import { escapeHtml } from "./utils/dom.js";
import { getTagTone } from "./utils/tags.js";
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
      ${tags.slice(0, 5).map((tag) => `<span class="pill pill--tag" data-tone="${getTagTone(tag)}">${escapeHtml(tag)}</span>`).join("")}
    </div>
  `;
}

function renderSavedSignals(entry, paper) {
  const items = [];
  if (entry.group_name) items.push(`分组：${entry.group_name}`);
  if (entry.is_read) items.push("已读");
  else items.push("未读");
  if (paper.citation_count) items.push(`被引 ${paper.citation_count}`);
  return `
    <div class="signal-row">
      ${items.map((item) => `<span class="signal">${escapeHtml(item)}</span>`).join("")}
    </div>
  `;
}

function renderEditor(paper, listType, entry) {
  return `
    <details class="saved-editor">
      <summary>编辑分组、备注与阅读状态</summary>
      <form class="editor-form" data-update-entry="${paper.id}:${escapeHtml(listType)}">
        <div class="field-grid">
          <label>
            <span>分组</span>
            <input type="text" name="group_name" value="${escapeHtml(entry.group_name || "")}" placeholder="例如：方法、必读、项目参考">
          </label>
          <label class="checkbox-row">
            <input type="checkbox" name="is_read" ${entry.is_read ? "checked" : ""}>
            <span>标记为已读</span>
          </label>
        </div>
        <label class="field-grid field-grid--wide">
          <span>备注</span>
          <textarea name="note" rows="4" placeholder="记录阅读要点、实验观察或后续行动">${escapeHtml(entry.note || "")}</textarea>
        </label>
        <div class="card-actions">
          <button class="button button-secondary" type="submit">保存信息</button>
        </div>
      </form>
    </details>
  `;
}

function groupItems(items, listType) {
  const groups = new Map();
  for (const paper of items) {
    const entry = paper.saved?.[listType] || {};
    const groupName = entry.group_name?.trim() || "未分组";
    if (!groups.has(groupName)) groups.set(groupName, []);
    groups.get(groupName).push(paper);
  }
  return [...groups.entries()].sort((a, b) => {
    if (a[0] === "未分组") return 1;
    if (b[0] === "未分组") return -1;
    return a[0].localeCompare(b[0], "zh-CN");
  });
}

function renderSavedCard(paper, listType) {
  const entry = paper.saved?.[listType] || {
    group_name: "",
    note: "",
    is_read: false,
  };
  const href = buildPaperUrl(paper.id, {
    conference: paper.conference,
    year: paper.year,
  });
  return `
    <article class="paper-card">
      <div class="paper-card__meta">
        <span class="pill">${escapeHtml(paper.conference.toUpperCase())}</span>
        <span class="pill">${escapeHtml(paper.year)}</span>
        <span class="pill">${escapeHtml(paper.track_label || paper.track || "未分类")}</span>
      </div>
      <h3>${escapeHtml(paper.title_display || paper.title)}</h3>
      <p class="authors">${escapeHtml(paper.authors_text || "")}</p>
      ${renderSavedSignals(entry, paper)}
      ${renderTagRow(paper.tags || [])}
      ${entry.note ? `<div class="note-box">${escapeHtml(entry.note)}</div>` : ""}
      <p class="preview summary-preview">${escapeHtml(paper.summary_preview || "进入详情页查看导读。")}</p>
      <div class="card-actions">
        <a class="button button-primary" href="${href}">查看详情</a>
        ${paper.pdf_url ? `<a class="button button-ghost" href="${escapeHtml(paper.pdf_url)}" target="_blank" rel="noreferrer">打开 PDF</a>` : ""}
        <button class="button button-chip active" type="button" data-save-toggle="${paper.id}:${escapeHtml(listType)}:0">移出列表</button>
      </div>
      ${renderEditor(paper, listType, entry)}
    </article>
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

  const groups = groupItems(items, listType);
  return `
    <section class="list-panel panel">
      <div class="section-head">
        <div>
          <h2>${escapeHtml(title)}</h2>
          <p>共 ${items.length} 篇，按分组整理</p>
        </div>
      </div>
      <div class="group-stack">
        ${groups
          .map(
            ([groupName, papers]) => `
              <section class="saved-group">
                <div class="saved-group__head">
                  <h3>${escapeHtml(groupName)}</h3>
                  <span class="pill">${papers.length} 篇</span>
                </div>
                <div class="paper-list">
                  ${papers.map((paper) => renderSavedCard(paper, listType)).join("")}
                </div>
              </section>
            `,
          )
          .join("")}
      </div>
    </section>
  `;
}

function renderHero(state) {
  return renderPageHero({
    eyebrow: "Reading Workspace",
    title: "把你准备深入读的论文真正整理起来。",
    description:
      "收藏和待读不该只是两个堆积按钮。这里按分组、阅读状态和备注把论文整理成一套可继续推进的阅读工作台。",
    stats: [
      { value: state.counts.favorite || 0, label: "收藏" },
      { value: state.counts.reading || 0, label: "待读" },
    ],
    actions: [
      { href: "/explore", label: "继续找论文", className: "button-primary" },
      { href: "/themes", label: "从主题进入", className: "button-secondary" },
    ],
    note: state.message,
  });
}

function render() {
  const state = store.getState();
  document.getElementById("app").innerHTML = `
    <main class="app-shell">
      ${renderTopNav("lists")}
      ${renderHero(state)}
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

  document.querySelectorAll("[data-update-entry]").forEach((form) => {
    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      const raw = String(form.getAttribute("data-update-entry") || "");
      const [paperIdText, listType] = raw.split(":");
      const paperId = Number(paperIdText || 0);
      if (!paperId || !listType) return;
      const formData = new FormData(form);
      store.setState({
        loading: true,
        message: "正在保存阅读信息...",
      });
      render();
      try {
        await apiClient.updateSavedPaper({
          paperId,
          listType,
          groupName: String(formData.get("group_name") || "").trim(),
          note: String(formData.get("note") || "").trim(),
          isRead: formData.get("is_read") === "on",
        });
        await loadAll();
        store.setState({
          message: "阅读信息已保存。",
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
