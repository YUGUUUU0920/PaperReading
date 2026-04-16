const VIEWER_STORAGE_KEY = "researchAtlasViewer";

let viewerCache = null;
let viewerPromise = null;

function loadStoredViewer() {
  if (viewerCache) return viewerCache;
  try {
    const raw = window.localStorage.getItem(VIEWER_STORAGE_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw);
    if (parsed?.id) {
      viewerCache = parsed;
      return parsed;
    }
  } catch {
    return null;
  }
  return null;
}

function storeViewer(viewer) {
  if (!viewer?.id) return;
  viewerCache = viewer;
  try {
    window.localStorage.setItem(VIEWER_STORAGE_KEY, JSON.stringify(viewer));
  } catch {
    // Ignore storage failures and keep the in-memory viewer.
  }
}

async function rawRequest(url, options = {}) {
  const response = await fetch(url, {
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
    ...options,
  });
  const data = await response.json();
  if (!response.ok || data.ok === false) {
    throw new Error(data.error || "请求失败");
  }
  if (data.viewer?.id) {
    storeViewer(data.viewer);
  }
  return data;
}

async function ensureViewer() {
  const cached = loadStoredViewer();
  if (cached?.id) return cached;
  if (!viewerPromise) {
    viewerPromise = rawRequest("/api/viewer")
      .then((data) => {
        storeViewer(data.viewer);
        return data.viewer;
      })
      .finally(() => {
        viewerPromise = null;
      });
  }
  return viewerPromise;
}

async function request(url, options = {}, { viewer = true } = {}) {
  const headers = { ...(options.headers || {}) };
  if (viewer) {
    const currentViewer = await ensureViewer();
    if (currentViewer?.id) {
      headers["X-Viewer-Id"] = currentViewer.id;
    }
  }
  return rawRequest(url, {
    ...options,
    headers,
  });
}

export const apiClient = {
  ensureViewer,

  getViewer() {
    return request("/api/viewer");
  },

  updateViewer({ displayName }) {
    return request("/api/viewer", {
      method: "POST",
      body: JSON.stringify({ display_name: displayName }),
    });
  },

  getBootstrap() {
    return request("/api/bootstrap");
  },

  getLineage({ theme = "", limit = 6 } = {}) {
    const params = new URLSearchParams();
    if (theme) params.set("theme", theme);
    if (limit) params.set("limit", String(limit));
    const suffix = params.toString();
    return request(suffix ? `/api/lineage?${suffix}` : "/api/lineage");
  },

  getShowcase() {
    return request("/api/showcase");
  },

  getDatasets() {
    return request("/api/datasets");
  },

  getSavedLists() {
    return request("/api/lists");
  },

  getComments(paperId) {
    return request(`/api/papers/${paperId}/comments`);
  },

  addComment(paperId, { content }) {
    return request(`/api/papers/${paperId}/comments`, {
      method: "POST",
      body: JSON.stringify({ content }),
    });
  },

  searchPapers({ conference, year, query, tags = [], sort = "default", limit = 24, page = 1, autoSync = true }) {
    const params = new URLSearchParams();
    if (conference) params.set("conference", conference);
    if (year) params.set("year", String(year));
    if (query) params.set("query", query);
    for (const tag of tags) {
      if (tag) params.append("tag", tag);
    }
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

  updateSavedPaper({ paperId, listType, groupName, note, isRead }) {
    return request("/api/lists/update", {
      method: "POST",
      body: JSON.stringify({
        paper_id: paperId,
        list_type: listType,
        group_name: groupName,
        note,
        is_read: isRead,
      }),
    });
  },
};
