from __future__ import annotations

from backend.app.core.utils import normalize_match_text, utc_now_iso
from backend.app.domain.entities import Paper
from backend.app.integrations.sources.base import ConferenceSource
from backend.app.repositories.sqlite import SqliteRepository
from backend.app.services.enrichment_service import EnrichmentService
from backend.app.services.summary_service import SummaryService
from backend.app.services.sync_service import SyncService
from backend.app.services.tag_service import TagService


class PaperService:
    def __init__(
        self,
        repository: SqliteRepository,
        sync_service: SyncService,
        summary_service: SummaryService,
        enrichment_service: EnrichmentService,
        tag_service: TagService,
        sources: dict[str, ConferenceSource],
    ):
        self.repository = repository
        self.sync_service = sync_service
        self.summary_service = summary_service
        self.enrichment_service = enrichment_service
        self.tag_service = tag_service
        self.sources = sources

    def search_papers(
        self,
        *,
        conference: str = "",
        year: int | None = None,
        query: str = "",
        limit: int = 24,
        page: int = 1,
        auto_sync: bool = True,
    ) -> dict:
        page = max(page, 1)
        limit = min(max(limit, 1), 60)
        dataset = None
        if auto_sync and conference and year:
            dataset = self.sync_service.ensure_dataset_loaded(conference, year)
        elif conference and year:
            dataset = self.repository.get_dataset(conference, year) or self.repository.ensure_dataset_from_existing_data(conference, year)

        total = self.repository.count_search_papers(query=query, conference=conference, year=year)
        offset = (page - 1) * limit
        items = self.repository.search_papers(
            query=query,
            conference=conference,
            year=year,
            limit=limit,
            offset=offset,
        )
        return {
            "items": [self._serialize_paper(item) for item in items],
            "count": len(items),
            "total": total,
            "page": page,
            "page_size": limit,
            "has_next": offset + len(items) < total,
            "dataset": dataset.to_dict() if dataset else None,
        }

    def get_paper(self, paper_id: int) -> dict:
        paper = self.repository.get_paper(paper_id)
        if not paper:
            raise KeyError(f"Paper {paper_id} not found")
        paper = self.ensure_details(paper)
        paper = self.ensure_enriched(paper)
        if self.summary_service.should_refresh_local_summary(paper):
            summary = self.summary_service.build_local_summary(paper)
            self.repository.update_summary(paper.id, summary, "heuristic-auto", utc_now_iso())
            paper = self.repository.get_paper(paper.id) or paper
        return self._serialize_paper(paper, include_related=True)

    def summarize_paper(self, paper_id: int) -> dict:
        paper = self.repository.get_paper(paper_id)
        if not paper:
            raise KeyError(f"Paper {paper_id} not found")
        paper = self.ensure_details(paper)
        paper = self.ensure_enriched(paper)
        summary, model = self.summary_service.summarize(paper)
        self.repository.update_summary(paper.id, summary, model, utc_now_iso())
        refreshed = self.repository.get_paper(paper_id)
        if not refreshed:
            raise KeyError(f"Paper {paper_id} not found after summary update")
        return self._serialize_paper(refreshed, include_related=True)

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
        needs_resources = not bool(paper.metadata.get("resource_links_checked"))
        if not needs_abstract and not needs_pdf and not needs_resources:
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

    def ensure_enriched(self, paper: Paper) -> Paper:
        metadata = self.enrichment_service.enrich_metadata(paper)
        if metadata == paper.metadata:
            return paper
        self.repository.update_paper_details(
            paper.id,
            metadata=metadata,
            last_synced_at=paper.last_synced_at or utc_now_iso(),
        )
        return self.repository.get_paper(paper.id) or paper

    def _serialize_paper(self, paper: Paper, *, include_related: bool = False) -> dict:
        payload = paper.to_dict()
        tags = self.tag_service.build_tags(paper)
        metadata = paper.metadata or {}
        payload["summary_preview"] = self.summary_service.build_preview(paper)
        payload["summary_source_label"] = self.summary_service.describe_summary_source(paper.summary_model)
        payload["tags"] = tags
        payload["citation_count"] = int(metadata.get("citation_count") or 0)
        payload["top_10_percent_cited"] = bool(metadata.get("top_10_percent_cited"))
        payload["code_url"] = str(metadata.get("code_url", "")).strip()
        payload["open_access"] = bool(metadata.get("open_access"))
        payload["resource_links"] = metadata.get("resource_links", []) or []
        if include_related:
            payload["related_papers"] = self._build_related_papers(paper)
        return payload

    def _build_related_papers(self, paper: Paper, limit: int = 4) -> list[dict]:
        seed_tags = self.tag_service.build_tags(paper)
        seed_tag_set = set(seed_tags)
        seed_title_terms = {term for term in normalize_match_text(paper.title).split() if len(term) >= 3}
        seed_authors = {normalize_match_text(author) for author in paper.authors if author.strip()}
        candidates = self.repository.search_papers(
            conference=paper.conference,
            year=paper.year,
            limit=80,
            offset=0,
        )

        scored: list[tuple[float, Paper]] = []
        for candidate in candidates:
            if candidate.id == paper.id:
                continue
            candidate_tags = self.tag_service.build_tags(candidate)
            overlap = len(seed_tag_set & set(candidate_tags))
            title_terms = {term for term in normalize_match_text(candidate.title).split() if len(term) >= 3}
            author_overlap = len(seed_authors & {normalize_match_text(author) for author in candidate.authors if author.strip()})
            title_overlap = len(seed_title_terms & title_terms)
            score = overlap * 4 + author_overlap * 2 + title_overlap
            if candidate.track == paper.track:
                score += 1
            if candidate.metadata.get("top_10_percent_cited"):
                score += 0.5
            if score <= 0:
                continue
            scored.append((score, candidate))

        scored.sort(
            key=lambda item: (
                item[0],
                int(item[1].metadata.get("citation_count") or 0),
                item[1].title.lower(),
            ),
            reverse=True,
        )
        related_items: list[dict] = []
        for _, candidate in scored[:limit]:
            related_items.append(
                {
                    "id": candidate.id,
                    "conference": candidate.conference,
                    "year": candidate.year,
                    "track": candidate.track,
                    "title": candidate.title,
                    "title_display": candidate.to_dict()["title_display"],
                    "authors_text": ", ".join(candidate.authors),
                    "summary_preview": self.summary_service.build_preview(candidate),
                    "tags": self.tag_service.build_tags(candidate),
                    "citation_count": int(candidate.metadata.get("citation_count") or 0),
                }
            )
        return related_items
