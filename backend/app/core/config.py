from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def _bool_env(name: str, default: bool = False) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _int_env(name: str, default: int) -> int:
    raw = os.environ.get(name)
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


@dataclass(frozen=True)
class Settings:
    project_root: Path
    backend_root: Path
    frontend_root: Path
    data_root: Path
    db_path: Path
    host: str
    port: int
    request_timeout_seconds: int
    user_agent: str
    network_mode: str
    openai_api_key: str
    openai_base_url: str
    openai_model: str
    summary_language: str
    refresh_ttl_hours: int
    scheduler_interval_minutes: int
    scheduler_enabled: bool
    default_conference: str
    default_year: int


def get_settings() -> Settings:
    project_root = Path(__file__).resolve().parents[3]
    backend_root = project_root / "backend"
    frontend_root = project_root / "frontend"
    data_root = project_root / "data"
    data_root.mkdir(parents=True, exist_ok=True)
    platform_port = _int_env("PORT", 0)
    default_host = "0.0.0.0" if platform_port else "127.0.0.1"
    default_port = platform_port or 8765

    return Settings(
        project_root=project_root,
        backend_root=backend_root,
        frontend_root=frontend_root,
        data_root=data_root,
        db_path=Path(os.environ.get("PAPER_ASSISTANT_DB_PATH", data_root / "papers.db")),
        host=os.environ.get("PAPER_ASSISTANT_HOST", default_host),
        port=_int_env("PAPER_ASSISTANT_PORT", default_port),
        request_timeout_seconds=_int_env("PAPER_ASSISTANT_TIMEOUT", 30),
        user_agent=os.environ.get(
            "PAPER_ASSISTANT_USER_AGENT",
            "PaperAssistant/2.0 (+https://localhost)",
        ),
        network_mode=os.environ.get("PAPER_ASSISTANT_NETWORK_MODE", "auto").strip().lower(),
        openai_api_key=os.environ.get("OPENAI_API_KEY", "").strip(),
        openai_base_url=os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/"),
        openai_model=os.environ.get("OPENAI_MODEL", "gpt-4.1-mini"),
        summary_language=os.environ.get("PAPER_ASSISTANT_SUMMARY_LANGUAGE", "zh-CN"),
        refresh_ttl_hours=_int_env("PAPER_ASSISTANT_REFRESH_TTL_HOURS", 24 * 7),
        scheduler_interval_minutes=_int_env("PAPER_ASSISTANT_SCHEDULER_INTERVAL_MINUTES", 60),
        scheduler_enabled=_bool_env("PAPER_ASSISTANT_SCHEDULER_ENABLED", True),
        default_conference=os.environ.get("PAPER_ASSISTANT_DEFAULT_CONFERENCE", "icml").strip().lower(),
        default_year=_int_env("PAPER_ASSISTANT_DEFAULT_YEAR", 2024),
    )
