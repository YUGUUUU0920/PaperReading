export function renderTopNav(active) {
  const items = [
    { key: "papers", href: "/", label: "论文检索" },
    { key: "datasets", href: "/datasets", label: "数据集状态" },
  ];

  return `
    <header class="top-nav panel">
      <div class="brand-block">
        <p class="eyebrow">AI Research Workspace</p>
        <strong class="brand-title">Paper Assistant</strong>
      </div>
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

