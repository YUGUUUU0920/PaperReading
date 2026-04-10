from __future__ import annotations

from backend.app.core.config import Settings


class CatalogService:
    CONFERENCES = [
        {"code": "acl", "label": "ACL", "years": [2024, 2025]},
        {"code": "neurips", "label": "NeurIPS", "years": [2024, 2025]},
        {"code": "icml", "label": "ICML", "years": [2023, 2024, 2025]},
        {"code": "iclr", "label": "ICLR", "years": [2024, 2025]},
    ]

    def __init__(self, settings: Settings):
        self.settings = settings

    def bootstrap(self) -> dict:
        return {
            "conferences": self.CONFERENCES,
            "defaults": {
                "conference": self.settings.default_conference,
                "year": self.settings.default_year,
            },
            "summaryEnabled": bool(self.settings.openai_api_key),
        }
