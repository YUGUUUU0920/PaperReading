import { escapeHtml } from "../utils/dom.js";

export function renderStatusBanner(state) {
  const { message, dataset } = state;
  const datasetMeta = dataset
    ? `<span class="pill">${escapeHtml(dataset.conference.toUpperCase())} ${escapeHtml(dataset.year)}</span>
       <span class="pill">${escapeHtml(dataset.status)}</span>
       <span class="pill">${escapeHtml(dataset.item_count)} 篇</span>`
    : `<span class="pill">等待检索</span>`;

  return `
    <section class="status-banner panel">
      <div>
        <h2>当前检索快照</h2>
        <p>${escapeHtml(message)}</p>
      </div>
      <div class="status-pills">
        ${datasetMeta}
      </div>
    </section>
  `;
}
