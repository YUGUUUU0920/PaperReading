export function readSearchParams() {
  return new URLSearchParams(window.location.search);
}

export function buildSearchUrl(filters = {}) {
  const params = new URLSearchParams();
  if (filters.conference) params.set("conference", filters.conference);
  if (filters.year) params.set("year", String(filters.year));
  if (filters.query) params.set("query", filters.query);
  const suffix = params.toString();
  return suffix ? `/?${suffix}` : "/";
}

export function buildPaperUrl(paperId, filters = {}) {
  const params = new URLSearchParams();
  params.set("id", String(paperId));
  if (filters.conference) params.set("conference", filters.conference);
  if (filters.year) params.set("year", String(filters.year));
  if (filters.query) params.set("query", filters.query);
  return `/paper?${params.toString()}`;
}

