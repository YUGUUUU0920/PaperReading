import { escapeHtml } from "../utils/dom.js";

function renderHeroStats(stats = []) {
  if (!stats.length) return "";
  return `
    <div class="page-hero__stats">
      ${stats
        .map(
          (item) => `
            <div class="hero-stat-card">
              <strong>${escapeHtml(item.value)}</strong>
              <span>${escapeHtml(item.label)}</span>
            </div>
          `,
        )
        .join("")}
    </div>
  `;
}

function renderHeroActions(actions = []) {
  if (!actions.length) return "";
  return `
    <div class="page-hero__actions">
      ${actions
        .map((action) => {
          const tag = action.href ? "a" : "button";
          const attrs = action.href
            ? `href="${escapeHtml(action.href)}"`
            : `type="${escapeHtml(action.type || "button")}"`;
          return `
            <${tag}
              class="button ${escapeHtml(action.className || "button-secondary")}"
              ${attrs}
            >
              ${escapeHtml(action.label)}
            </${tag}>
          `;
        })
        .join("")}
    </div>
  `;
}

export function renderPageHero({
  eyebrow = "Research Atlas",
  title,
  description,
  stats = [],
  actions = [],
  note = "",
  asideHtml = "",
  className = "",
} = {}) {
  return `
    <section class="page-hero panel ${escapeHtml(className).trim()}">
      <div class="page-hero__main">
        <p class="eyebrow">${escapeHtml(eyebrow)}</p>
        <h1>${escapeHtml(title || "")}</h1>
        <p class="page-hero__lead">${escapeHtml(description || "")}</p>
        ${renderHeroStats(stats)}
        ${renderHeroActions(actions)}
        ${note ? `<p class="page-hero__note">${escapeHtml(note)}</p>` : ""}
      </div>
      ${asideHtml ? `<div class="page-hero__aside">${asideHtml}</div>` : ""}
    </section>
  `;
}
