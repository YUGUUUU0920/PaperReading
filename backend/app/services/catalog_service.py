from __future__ import annotations

from backend.app.core.config import Settings
from backend.app.services.tag_service import TagService


class CatalogService:
    CONFERENCES = [
        {"code": "acl", "label": "ACL", "years": [2024, 2025]},
        {"code": "neurips", "label": "NeurIPS", "years": [2024, 2025]},
        {"code": "icml", "label": "ICML", "years": [2023, 2024, 2025]},
        {"code": "iclr", "label": "ICLR", "years": [2024, 2025]},
    ]

    SORT_OPTIONS = [
        {"value": "default", "label": "默认排序"},
        {"value": "citations_desc", "label": "引用量从高到低"},
        {"value": "citations_asc", "label": "引用量从低到高"},
        {"value": "title_asc", "label": "标题 A-Z"},
        {"value": "title_desc", "label": "标题 Z-A"},
    ]

    def __init__(self, settings: Settings, tag_service: TagService):
        self.settings = settings
        self.tag_service = tag_service

    def bootstrap(self) -> dict:
        return {
            "conferences": self.CONFERENCES,
            "tagOptions": self.tag_service.catalog_tags(),
            "sortOptions": self.SORT_OPTIONS,
            "defaults": {
                "conference": self.settings.default_conference,
                "year": self.settings.default_year,
                "tags": [],
                "sort": "default",
            },
            "summaryEnabled": bool(self.settings.openai_api_key),
        }
