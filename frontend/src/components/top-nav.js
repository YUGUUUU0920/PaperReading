export function renderTopNav(active) {
  const items = [
    { key: "papers", href: "/", label: "论文检索" },
    { key: "datasets", href: "/datasets", label: "论文库" },
    { key: "lists", href: "/lists", label: "收藏与待读" },
  ];

  return `
    <header class="top-nav panel">
      <div class="brand-block">
        <p class="eyebrow">Paper Reading</p>
        <strong class="brand-title">顶会论文助手</strong>
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
