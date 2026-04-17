export function renderTopNav(active) {
  const items = [
    { key: "home", href: "/", label: "首页" },
    { key: "explore", href: "/explore", label: "搜索" },
    { key: "lineage", href: "/lineage", label: "研究脉络" },
    { key: "lists", href: "/lists", label: "阅读清单" },
  ];

  return `
    <header class="top-nav panel">
      <a class="brand-block brand-block--link" href="/">
        <p class="eyebrow">Research Atlas</p>
        <strong class="brand-title">论文研究图谱</strong>
      </a>
      <nav class="nav-links">
        ${items
          .map((item) => {
            const cls = item.key === active ? "nav-link active" : "nav-link";
            return `<a class="${cls}" href="${item.href}">${item.label}</a>`;
          })
          .join("")}
      </nav>
    </header>
  `;
}
