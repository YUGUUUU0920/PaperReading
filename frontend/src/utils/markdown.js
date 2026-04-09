import { escapeHtml } from "./dom.js";

export function markdownToHtml(input) {
  const text = String(input || "").trim();
  if (!text) return "<p>暂无内容</p>";
  return text
    .split(/\n{2,}/)
    .map((block) => {
      const trimmed = block.trim();
      if (!trimmed) return "";
      if (trimmed.startsWith("### ")) {
        return `<h3>${escapeHtml(trimmed.slice(4))}</h3>`;
      }
      if (trimmed.startsWith("#### ")) {
        return `<h4>${escapeHtml(trimmed.slice(5))}</h4>`;
      }
      return `<p>${escapeHtml(trimmed).replaceAll("\n", "<br>")}</p>`;
    })
    .join("");
}

