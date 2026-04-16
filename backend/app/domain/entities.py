from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from backend.app.core.utils import normalize_title_display


@dataclass
class Paper:
    id: int | None
    source: str
    conference: str
    year: int
    track: str
    external_id: str
    title: str
    authors: list[str]
    abstract: str
    paper_url: str
    pdf_url: str
    summary: str
    summary_model: str
    metadata: dict[str, Any] = field(default_factory=dict)
    last_synced_at: str = ""
    summary_updated_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["authors_text"] = ", ".join(self.authors)
        payload["title_display"] = normalize_title_display(self.title)
        payload["has_abstract"] = bool(self.abstract.strip())
        payload["has_summary"] = bool(self.summary.strip())
        return payload


@dataclass
class DatasetStatus:
    conference: str
    year: int
    status: str
    item_count: int
    last_synced_at: str
    last_error: str
    updated_at: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ViewerProfile:
    id: str
    display_name: str
    profile_type: str = "guest"
    created_at: str = ""
    updated_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["is_guest"] = self.profile_type == "guest"
        payload["is_seed"] = self.profile_type == "seed"
        return payload


@dataclass
class PaperComment:
    id: int | None
    paper_id: int
    profile_id: str
    display_name: str
    profile_type: str
    source: str
    content: str
    created_at: str = ""
    updated_at: str = ""
    sort_order: int = 0

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["is_seed"] = self.source == "seed" or self.profile_type == "seed"
        return payload
