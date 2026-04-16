import { apiClient } from "./api/client.js";
import { renderTopNav } from "./components/top-nav.js";
import { renderLineageExplorer } from "./components/lineage-sections.js";
import { escapeHtml } from "./utils/dom.js";
import { readSearchParams } from "./utils/url.js";

const state = {
  loading: true,
  message: "正在整理研究脉络...",
  activeTheme: "",
  payload: {
    items: [],
    available_themes: [],
    coverage: {
      paper_count: 0,
      dataset_count: 0,
    },
  },
};

function render() {
  document.getElementById("app").innerHTML = `
    <main class="app-shell app-shell--home">
      ${renderTopNav("lineage")}
      <section class="toolbar panel toolbar--compact toolbar--browse">
        <div class="toolbar-copy toolbar-copy--compact">
          <p class="eyebrow">Research Lineage</p>
          <h1>研究脉络</h1>
          <p class="toolbar-text">${escapeHtml(state.message)}</p>
        </div>
      </section>
      ${renderLineageExplorer(state.payload, { activeTheme: state.activeTheme })}
    </main>
  `;
}

async function bootstrap() {
  const params = readSearchParams();
  state.activeTheme = params.get("theme") || "";
  render();
  try {
    const payload = await apiClient.getLineage({
      theme: state.activeTheme,
      limit: state.activeTheme ? 1 : 6,
    });
    state.payload = payload;
    state.loading = false;
    state.message = state.activeTheme
      ? `正在查看 ${state.activeTheme} 主题下的代表论文脉络。`
      : "从起点、推进到最新进展，按主题浏览当前最值得追踪的论文主线。";
  } catch (error) {
    state.loading = false;
    state.message = error.message;
  }
  render();
}

bootstrap();
