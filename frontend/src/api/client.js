const VIEWER_STORAGE_KEY = "researchAtlasViewer";

let viewerCache = null;
let viewerPromise = null;
let authNotice = "";

function readCurrentUrl() {
  return new URL(window.location.href);
}

function buildCleanCurrentPath() {
  const url = readCurrentUrl();
  url.searchParams.delete("auth_session");
  url.searchParams.delete("auth_error");
  const query = url.searchParams.toString();
  return `${url.pathname}${query ? `?${query}` : ""}`;
}

function replaceCurrentUrl(path) {
  window.history.replaceState({}, "", path);
}

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

function consumeAuthErrorSignal() {
  const url = readCurrentUrl();
  const error = url.searchParams.get("auth_error");
  if (!error) return;
  const messages = {
    github_login_unavailable: "当前站点暂未启用 GitHub 登录。",
    github_login_cancelled: "你刚刚取消了 GitHub 登录。",
    github_state_expired: "这次登录链接已经过期，请重新发起一次登录。",
    github_code_missing: "登录过程没有拿到授权码，请再试一次。",
    github_token_failed: "GitHub 登录没有成功换取身份，请稍后重试。",
    github_login_failed: "GitHub 登录暂时失败了，请稍后再试。",
  };
  authNotice = messages[error] || "登录没有完成，我们先回到当前页面。";
  replaceCurrentUrl(buildCleanCurrentPath());
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

async function consumePendingAuthSession() {
  const url = readCurrentUrl();
  const token = url.searchParams.get("auth_session");
  if (!token) return null;
  try {
    const data = await rawRequest(`/api/auth/session?token=${encodeURIComponent(token)}`);
    if (data.viewer?.id) {
      storeViewer(data.viewer);
      authNotice = data.viewer.is_oauth ? "GitHub 身份已连接，可以继续参与讨论了。" : authNotice;
    }
    return data.viewer || null;
  } catch (error) {
    authNotice = error.message || "登录会话已失效，请重新登录。";
    return null;
  } finally {
    replaceCurrentUrl(buildCleanCurrentPath());
  }
}

async function ensureViewer() {
  consumeAuthErrorSignal();
  const upgraded = await consumePendingAuthSession();
  if (upgraded?.id) return upgraded;
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

  consumeAuthNotice() {
    const value = authNotice;
    authNotice = "";
    return value;
  },

  buildGithubLoginUrl(returnPath = buildCleanCurrentPath()) {
    return `/api/auth/github/start?return_path=${encodeURIComponent(returnPath || "/paper")}`;
  },

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

  addComment(paperId, { content, parentCommentId = null }) {
    return request(`/api/papers/${paperId}/comments`, {
      method: "POST",
      body: JSON.stringify({
        content,
        parent_comment_id: parentCommentId,
      }),
    });
  },

  toggleCommentLike(commentId, { enabled }) {
    return request(`/api/comments/${commentId}/like`, {
      method: "POST",
      body: JSON.stringify({ enabled }),
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
