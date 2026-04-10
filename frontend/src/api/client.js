async function request(url, options = {}) {
  const response = await fetch(url, {
    headers: {
      "Content-Type": "application/json",
    },
    ...options,
  });
  const data = await response.json();
  if (!response.ok || data.ok === false) {
    throw new Error(data.error || "请求失败");
  }
  return data;
}

export const apiClient = {
  getBootstrap() {
    return request("/api/bootstrap");
  },

  getDatasets() {
    return request("/api/datasets");
  },

  getSavedLists() {
    return request("/api/lists");
  },

  searchPapers({ conference, year, query, tag, sort = "default", limit = 24, page = 1, autoSync = true }) {
    const params = new URLSearchParams();
    if (conference) params.set("conference", conference);
    if (year) params.set("year", String(year));
    if (query) params.set("query", query);
    if (tag) params.set("tag", tag);
    if (sort && sort !== "default") params.set("sort", sort);
    params.set("limit", String(limit));
    params.set("page", String(page));
    params.set("auto_sync", autoSync ? "1" : "0");
    return request(`/api/papers?${params.toString()}`);
  },

  getPaper(paperId) {
    return request(`/api/papers/${paperId}`);
  },

  summarizePaper(paperId) {
    return request(`/api/papers/${paperId}/summarize`, {
      method: "POST",
      body: JSON.stringify({}),
    });
  },

  refreshDataset({ conference, year }) {
    return request("/api/datasets/refresh", {
      method: "POST",
      body: JSON.stringify({ conference, year }),
    });
  },

  toggleSavedPaper({ paperId, listType, enabled }) {
    return request("/api/lists/toggle", {
      method: "POST",
      body: JSON.stringify({ paper_id: paperId, list_type: listType, enabled }),
    });
  },
};
