from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx

from backend.app.core.config import Settings


class FetchError(RuntimeError):
    pass


@dataclass(frozen=True)
class NetworkAttempt:
    label: str
    trust_env: bool


class HttpClient:
    def __init__(self, settings: Settings):
        self.settings = settings
        self._headers = {
            "User-Agent": settings.user_agent,
            "Accept": "text/html,application/xhtml+xml,application/json;q=0.9,*/*;q=0.8",
        }

    def get_text(self, url: str) -> str:
        response = self._request("GET", url)
        return response.text

    def get_json(self, url: str, headers: dict[str, str] | None = None) -> dict[str, Any]:
        response = self._request("GET", url, headers=headers)
        try:
            return response.json()
        except ValueError as exc:
            raise FetchError(f"Invalid JSON response from {url}: {exc}") from exc

    def post_json(self, url: str, payload: dict[str, Any], headers: dict[str, str] | None = None) -> dict[str, Any]:
        merged_headers = dict(headers or {})
        merged_headers["Content-Type"] = "application/json"
        response = self._request("POST", url, json=payload, headers=merged_headers)
        try:
            return response.json()
        except ValueError as exc:
            raise FetchError(f"Invalid JSON response from {url}: {exc}") from exc

    def _request(self, method: str, url: str, **kwargs: Any) -> httpx.Response:
        attempts = self._network_attempts()
        failures: list[str] = []
        for attempt in attempts:
            try:
                with httpx.Client(
                    timeout=self.settings.request_timeout_seconds,
                    follow_redirects=True,
                    headers=self._headers,
                    trust_env=attempt.trust_env,
                ) as client:
                    response = client.request(method, url, **kwargs)
                    response.raise_for_status()
                    return response
            except Exception as exc:
                failures.append(f"{attempt.label}: {exc}")
        raise FetchError(f"Failed to fetch {url}. Attempts: {' | '.join(failures)}")

    def _network_attempts(self) -> list[NetworkAttempt]:
        mode = self.settings.network_mode
        if mode == "env":
            return [NetworkAttempt(label="env-proxy", trust_env=True)]
        if mode == "direct":
            return [NetworkAttempt(label="direct", trust_env=False)]
        return [
            NetworkAttempt(label="env-proxy", trust_env=True),
            NetworkAttempt(label="direct", trust_env=False),
        ]
