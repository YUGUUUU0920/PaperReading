from __future__ import annotations

from backend.app.core.utils import utc_now_iso
from backend.app.domain.entities import Paper
from backend.app.integrations.sources.base import ConferenceSource
from backend.app.repositories.sqlite import SqliteRepository
from backend.app.services.summary_service import SummaryService
from backend.app.services.sync_service import SyncService


class PaperService:
    def __init__(
        self,
        repository: SqliteRepository,
        sync_service: SyncService,
        summary_service: SummaryService,
        sources: dict[str, ConferenceSource],
    ):
        self.repository = repository
        self.sync_service = sync_service
        self.summary_service = summary_service
        self.sources = sources

    def search_papers(
        self,
        *,
        conference: str = "",
        year: int | None = None,
        query: str = "",
        limit: int = 120,
        auto_sync: bool = True,
    ) -> dict:
        dataset = None
        if auto_sync and conference and year:
            dataset = self.sync_service.ensure_dataset_loaded(conference, year)
        elif conference and year:
            dataset = self.repository.get_dataset(conference, year) or self.repository.ensure_dataset_from_existing_data(conference, year)

        items = self.repository.search_papers(query=query, conference=conference, year=year, limit=limit)
        return {
            "items": [item.to_dict() for item in items],
            "count": len(items),
            "dataset": dataset.to_dict() if dataset else None,
        }

    def get_paper(self, paper_id: int) -> dict:
        paper = self.repository.get_paper(paper_id)
        if not paper:
            raise KeyError(f"Paper {paper_id} not found")
        paper = self.ensure_details(paper)
        if self.summary_service.should_refresh_local_summary(paper):
            summary = self.summary_service.build_local_summary(paper)
            self.repository.update_summary(paper.id, summary, "heuristic-auto", utc_now_iso())
            paper = self.repository.get_paper(paper.id) or paper
        return paper.to_dict()

    def summarize_paper(self, paper_id: int) -> dict:
        paper = self.repository.get_paper(paper_id)
        if not paper:
            raise KeyError(f"Paper {paper_id} not found")
        paper = self.ensure_details(paper)
        summary, model = self.summary_service.summarize(paper)
        self.repository.update_summary(paper.id, summary, model, utc_now_iso())
        refreshed = self.repository.get_paper(paper_id)
        if not refreshed:
            raise KeyError(f"Paper {paper_id} not found after summary update")
        return refreshed.to_dict()

    def refresh_dataset(self, conference: str, year: int) -> dict:
        dataset = self.sync_service.refresh_dataset(conference, year)
        return dataset.to_dict()

    def list_datasets(self) -> list[dict]:
        return [dataset.to_dict() for dataset in self.repository.list_tracked_datasets()]

    def ensure_details(self, paper: Paper) -> Paper:
        source = self.sources.get(paper.source)
        if not source:
            return paper
        needs_abstract = not paper.abstract.strip()
        needs_pdf = not paper.pdf_url.strip()
        if not needs_abstract and not needs_pdf:
            return paper
        hydrated = source.hydrate_paper(paper)
        self.repository.update_paper_details(
            hydrated.id,
            abstract=hydrated.abstract,
            pdf_url=hydrated.pdf_url,
            metadata=hydrated.metadata,
            last_synced_at=hydrated.last_synced_at or utc_now_iso(),
        )
        return self.repository.get_paper(hydrated.id) or hydrated
