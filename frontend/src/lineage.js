import { apiClient } from "./api/client.js";
import { renderLineageExplorer } from "./components/lineage-sections.js";
import { renderPageHero } from "./components/page-hero.js";
import { renderTopNav } from "./components/top-nav.js";
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

function scrollToHashTarget() {
  const hash = window.location.hash || "";
  if (!hash.startsWith("#theme-")) return;
  const target = document.getElementById(hash.slice(1));
  if (!target) return;
  target.scrollIntoView({ block: "start", behavior: "auto" });
}

function renderHero() {
  const coverage = state.payload.coverage || {};
  return renderPageHero({
    eyebrow: "Research Lineage",
    title: "顺着主干，看清一个方向怎么长出来。",
    description:
      "这里不是按论文列表散看，而是把同一主题下的代表论文串成主干与分支。你可以先看起点，再看后来怎样推进和分叉。",
    stats: [
      { value: coverage.paper_count || 0, label: "已串联论文" },
      { value: coverage.dataset_count || 0, label: "追踪数据源" },
      { value: state.payload.items?.length || 0, label: "主题脉络" },
    ],
    actions: [
      { href: "/themes", label: "先看主题", className: "button-secondary" },
      { href: "/explore", label: "打开搜索", className: "button-ghost" },
    ],
    note: state.message,
  });
}

function render() {
  document.getElementById("app").innerHTML = `
    <main class="app-shell app-shell--home">
      ${renderTopNav("lineage")}
      ${renderHero()}
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
  scrollToHashTarget();
}

window.addEventListener("hashchange", scrollToHashTarget);

bootstrap();
