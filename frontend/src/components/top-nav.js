export function renderTopNav(active) {
  const items = [
    { key: "home", href: "/", label: "首页" },
    { key: "explore", href: "/explore", label: "搜索" },
    { key: "themes", href: "/themes", label: "主题" },
    { key: "lineage", href: "/lineage", label: "研究脉络" },
    { key: "lists", href: "/lists", label: "阅读清单" },
    { key: "datasets", href: "/datasets", label: "数据概览" },
  ];

  return `
    <header class="top-nav panel">
      <a class="brand-block brand-block--link" href="/">
        <p class="eyebrow">Research Atlas</p>
        <strong class="brand-title">中文研究发现工作台</strong>
        <span class="brand-subtitle">把搜索、主题、脉络与阅读清单放进同一套阅读流程</span>
      </a>
      <div class="top-nav__cluster">
        <nav class="nav-links" aria-label="主导航">
          ${items
            .map((item) => {
              const cls = item.key === active ? "nav-link active" : "nav-link";
              return `<a class="${cls}" href="${item.href}">${item.label}</a>`;
            })
            .join("")}
        </nav>
        <p class="top-nav__meta">先建立方向感，再决定哪些论文值得深读。</p>
      </div>
    </header>
  `;
}
