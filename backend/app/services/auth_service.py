from __future__ import annotations

import hashlib
import hmac
import re
import secrets
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode, urlparse

from backend.app.core.config import Settings
from backend.app.core.http_client import HttpClient
from backend.app.domain.entities import ViewerProfile
from backend.app.repositories.sqlite import SqliteRepository


WHITESPACE_RE = re.compile(r"\s+")
DISPLAY_NAME_RE = re.compile(r"[^\w\u4e00-\u9fff·\- ]+")


class AuthService:
    GITHUB_AUTHORIZE_URL = "https://github.com/login/oauth/authorize"
    GITHUB_TOKEN_URL = "https://github.com/login/oauth/access_token"
    GITHUB_USER_URL = "https://api.github.com/user"

    def __init__(self, repository: SqliteRepository, settings: Settings, http_client: HttpClient):
        self.repository = repository
        self.settings = settings
        self.http_client = http_client

    def auth_catalog(self) -> dict:
        return {
            "githubEnabled": self.github_enabled,
            "providers": [{"code": "github", "label": "GitHub"}] if self.github_enabled else [],
        }

    @property
    def github_enabled(self) -> bool:
        return bool(self.settings.github_oauth_client_id and self.settings.github_oauth_client_secret)

    def begin_github_login(self, return_path: str = "/paper") -> str:
        if not self.github_enabled:
            raise ValueError("GitHub 登录暂未启用")
        normalized_return_path = self._normalize_return_path(return_path)
        state = secrets.token_urlsafe(18)
        self.repository.create_oauth_state(state, normalized_return_path)
        query = urlencode(
            {
                "client_id": self.settings.github_oauth_client_id,
                "redirect_uri": f"{self.settings.public_base_url}/api/auth/github/callback",
                "scope": "read:user user:email",
                "state": state,
            }
        )
        return f"{self.GITHUB_AUTHORIZE_URL}?{query}"

    def complete_github_login(self, *, code: str = "", state: str = "", error: str = "") -> str:
        normalized_state = state.strip()
        return_path = self.repository.consume_oauth_state(normalized_state) if normalized_state else None
        fallback_path = self._normalize_return_path(return_path or "/paper")
        if error.strip():
            return self._append_query(fallback_path, "auth_error", "github_login_cancelled")
        if not return_path:
            return self._append_query(fallback_path, "auth_error", "github_state_expired")
        if not code.strip():
            return self._append_query(fallback_path, "auth_error", "github_code_missing")

        token_response = self.http_client.post_form(
            self.GITHUB_TOKEN_URL,
            {
                "client_id": self.settings.github_oauth_client_id,
                "client_secret": self.settings.github_oauth_client_secret,
                "code": code.strip(),
                "redirect_uri": f"{self.settings.public_base_url}/api/auth/github/callback",
            },
            headers={"Accept": "application/json"},
        )
        access_token = str(token_response.get("access_token") or "").strip()
        if not access_token:
            return self._append_query(fallback_path, "auth_error", "github_token_failed")

        profile = self._upsert_github_profile(access_token)
        session_token = secrets.token_urlsafe(24)
        expires_at = (datetime.now(timezone.utc) + timedelta(minutes=10)).replace(microsecond=0).isoformat()
        self.repository.create_auth_session(session_token, profile.id, fallback_path, expires_at)
        return self._append_query(fallback_path, "auth_session", session_token)

    def consume_auth_session(self, token: str) -> dict:
        normalized = token.strip()
        if not normalized:
            raise ValueError("缺少登录会话")
        consumed = self.repository.consume_auth_session(normalized)
        if not consumed:
            raise ValueError("登录会话已失效，请重新登录")
        profile_id, return_path = consumed
        profile = self.repository.get_profile(profile_id)
        if not profile:
            raise ValueError("登录身份不存在")
        return {
            "viewer": profile.to_dict(),
            "returnPath": return_path,
        }

    def _upsert_github_profile(self, access_token: str) -> ViewerProfile:
        user = self.http_client.get_json(
            self.GITHUB_USER_URL,
            headers={
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {access_token}",
                "X-GitHub-Api-Version": "2022-11-28",
            },
        )
        external_id = str(user.get("id") or "").strip()
        login = str(user.get("login") or "").strip()
        if not external_id or not login:
            raise ValueError("GitHub 返回的用户信息不完整")

        existing = self.repository.get_profile_by_auth("github", external_id)
        profile_id = existing.id if existing else self._build_profile_id("github", external_id)
        display_name = self._normalize_display_name(str(user.get("name") or "")) or self._normalize_display_name(login) or "GitHub 用户"
        avatar_url = str(user.get("avatar_url") or "").strip()
        timestamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
        self.repository.upsert_profile(
            ViewerProfile(
                id=profile_id,
                display_name=display_name,
                profile_type="oauth",
                auth_provider="github",
                external_auth_id=external_id,
                avatar_url=avatar_url,
                created_at=existing.created_at if existing else timestamp,
                updated_at=timestamp,
            )
        )
        stored = self.repository.get_profile(profile_id)
        if not stored:
            raise RuntimeError("保存登录身份失败")
        return stored

    def _build_profile_id(self, provider: str, external_id: str) -> str:
        digest = hmac.new(
            self.settings.auth_secret.encode("utf-8"),
            f"{provider}:{external_id}".encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()[:20]
        return f"member-{digest}"

    def _normalize_display_name(self, display_name: str) -> str:
        cleaned = DISPLAY_NAME_RE.sub("", str(display_name or "").strip())
        cleaned = WHITESPACE_RE.sub(" ", cleaned).strip()
        return cleaned[:20]

    def _normalize_return_path(self, return_path: str) -> str:
        parsed = urlparse(str(return_path or "").strip())
        if parsed.scheme or parsed.netloc:
            return "/paper"
        path = parsed.path or "/paper"
        if not path.startswith("/"):
            path = f"/{path}"
        query = f"?{parsed.query}" if parsed.query else ""
        return f"{path}{query}"

    def _append_query(self, path: str, key: str, value: str) -> str:
        separator = "&" if "?" in path else "?"
        return f"{path}{separator}{key}={value}"
