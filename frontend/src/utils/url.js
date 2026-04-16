export function readSearchParams() {
  return new URLSearchParams(window.location.search);
}

export function buildSearchUrl(filters = {}) {
  const params = new URLSearchParams();
  if (filters.conference) params.set("conference", filters.conference);
  if (filters.year) params.set("year", String(filters.year));
  if (filters.query) params.set("query", filters.query);
  for (const tag of filters.tags || []) {
    if (tag) params.append("tag", tag);
  }
  if (filters.sort && filters.sort !== "default") params.set("sort", filters.sort);
  if (filters.page && Number(filters.page) > 1) params.set("page", String(filters.page));
  const suffix = params.toString();
  return suffix ? `/explore?${suffix}` : "/explore";
}

export function buildLineageUrl({ theme = "" } = {}) {
  const params = new URLSearchParams();
  if (theme) params.set("theme", theme);
  const suffix = params.toString();
  return suffix ? `/lineage?${suffix}` : "/lineage";
}

export function buildPaperUrl(paperId, filters = {}) {
  const params = new URLSearchParams();
  params.set("id", String(paperId));
  if (filters.conference) params.set("conference", filters.conference);
  if (filters.year) params.set("year", String(filters.year));
  if (filters.query) params.set("query", filters.query);
  for (const tag of filters.tags || []) {
    if (tag) params.append("tag", tag);
  }
  if (filters.sort && filters.sort !== "default") params.set("sort", filters.sort);
  if (filters.page && Number(filters.page) > 1) params.set("page", String(filters.page));
  return `/paper?${params.toString()}`;
}
