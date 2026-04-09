from __future__ import annotations

from abc import ABC, abstractmethod

from backend.app.domain.entities import Paper


class ConferenceSource(ABC):
    code: str
    label: str

    @abstractmethod
    def fetch_listing(self, year: int) -> list[Paper]:
        raise NotImplementedError

    def hydrate_paper(self, paper: Paper) -> Paper:
        return paper

