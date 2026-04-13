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
        tags: list[str] | None = None,
        tag: str = "",
        sort: str = "default",
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

        selected_tags = self._normalize_tags(tags if tags is not None else ([tag] if tag else []))
        items = self.repository.list_matching_papers(
            query=query,
            conference=conference,
            year=year,
        )
        items = self._maybe_enrich_search_candidates(items, tags=selected_tags, sort=sort)
        items = self._filter_papers(items, tags=selected_tags)
        items = self._sort_papers(items, sort=sort)
        total = len(items)
        offset = (page - 1) * limit
        page_items = items[offset : offset + limit]
        saved_lookup = self.repository.get_saved_entries([item.id for item in page_items if item.id is not None])
        return {
            "items": [self._serialize_paper(item, saved_entries=saved_lookup.get(item.id or -1, {})) for item in page_items],
            "count": len(page_items),
            "total": total,
            "page": page,
            "page_size": limit,
            "has_next": offset + len(page_items) < total,
            "result_tags": self._top_tags(items),
            "selected_tags": selected_tags,
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
        saved_lookup = self.repository.get_saved_entries([paper.id] if paper.id else [])
        return self._serialize_paper(
            paper,
            include_related=True,
            saved_entries=saved_lookup.get(paper.id or -1, {}),
        )

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
        saved_lookup = self.repository.get_saved_entries([paper_id])
        return self._serialize_paper(
            refreshed,
            include_related=True,
            saved_entries=saved_lookup.get(paper_id, {}),
        )

    def refresh_dataset(self, conference: str, year: int) -> dict:
        dataset = self.sync_service.refresh_dataset(conference, year)
        return dataset.to_dict()

    def list_datasets(self) -> list[dict]:
        return [dataset.to_dict() for dataset in self.repository.list_tracked_datasets()]

    def list_saved_papers(self) -> dict:
        favorites = self.repository.list_saved_papers("favorite")
        reading = self.repository.list_saved_papers("reading")
        favorite_lookup = self.repository.get_saved_entries([paper.id for paper in favorites if paper.id is not None])
        reading_lookup = self.repository.get_saved_entries([paper.id for paper in reading if paper.id is not None])
        return {
            "favorite": [
                self._serialize_paper(paper, saved_entries=favorite_lookup.get(paper.id or -1, {}))
                for paper in favorites
            ],
            "reading": [
                self._serialize_paper(paper, saved_entries=reading_lookup.get(paper.id or -1, {}))
                for paper in reading
            ],
            "counts": {
                "favorite": self.repository.count_saved("favorite"),
                "reading": self.repository.count_saved("reading"),
            },
        }

    def set_saved_state(self, paper_id: int, list_type: str, enabled: bool) -> dict:
        paper = self.repository.get_paper(paper_id)
        if not paper:
            raise KeyError(f"Paper {paper_id} not found")
        self.repository.set_saved_state(paper_id, list_type, enabled)
        refreshed = self.repository.get_paper(paper_id) or paper
        saved_lookup = self.repository.get_saved_entries([paper_id])
        return self._serialize_paper(refreshed, saved_entries=saved_lookup.get(paper_id, {}))

    def update_saved_entry(
        self,
        paper_id: int,
        list_type: str,
        *,
        group_name: str = "",
        note: str = "",
        is_read: bool = False,
    ) -> dict:
        paper = self.repository.get_paper(paper_id)
        if not paper:
            raise KeyError(f"Paper {paper_id} not found")
        self.repository.update_saved_entry(
            paper_id,
            list_type,
            group_name=group_name,
            note=note,
            is_read=is_read,
        )
        refreshed = self.repository.get_paper(paper_id) or paper
        saved_lookup = self.repository.get_saved_entries([paper_id])
        return self._serialize_paper(refreshed, saved_entries=saved_lookup.get(paper_id, {}))

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

    def _serialize_paper(
        self,
        paper: Paper,
        *,
        include_related: bool = False,
        saved_entries: dict[str, dict] | None = None,
    ) -> dict:
        payload = paper.to_dict()
        tags = self.tag_service.build_tags(paper)
        metadata = paper.metadata or {}
        saved_entries = saved_entries or {}
        payload["summary_preview"] = self.summary_service.build_preview(paper)
        payload["summary_source_label"] = self.summary_service.describe_summary_source(paper.summary_model)
        payload["tags"] = tags
        payload["primary_theme"] = self.tag_service.primary_theme(tags=tags)
        payload["track_label"] = self._track_label(paper.track)
        payload["citation_count"] = int(metadata.get("citation_count") or 0)
        payload["top_10_percent_cited"] = bool(metadata.get("top_10_percent_cited"))
        payload["code_url"] = str(metadata.get("code_url", "")).strip()
        payload["open_access"] = bool(metadata.get("open_access"))
        payload["resource_links"] = metadata.get("resource_links", []) or []
        payload["saved"] = {
            "favorite": saved_entries.get("favorite"),
            "reading": saved_entries.get("reading"),
        }
        if include_related:
            payload["related_papers"] = self._build_related_papers(paper)
        return payload

    def _maybe_enrich_search_candidates(self, papers: list[Paper], *, tags: list[str], sort: str) -> list[Paper]:
        if not papers:
            return papers
        signal_tags = {"引用量高", "高被引", "新晋热门", "影响力强"}
        needs_signals = sort.startswith("citations") or any(tag in signal_tags for tag in tags)
        if not needs_signals:
            return papers
        refreshed: list[Paper] = []
        budget = 24
        for index, paper in enumerate(papers):
            if index < budget and self._needs_signal_refresh(paper):
                refreshed.append(self.ensure_enriched(paper))
            else:
                refreshed.append(paper)
        return refreshed

    def _needs_signal_refresh(self, paper: Paper) -> bool:
        metadata = paper.metadata or {}
        return not metadata.get("signals_refreshed_at")

    def _filter_papers(self, papers: list[Paper], *, tags: list[str]) -> list[Paper]:
        if not tags:
            return papers
        filtered: list[Paper] = []
        for paper in papers:
            paper_tags = set(self.tag_service.build_tags(paper))
            if all(tag in paper_tags for tag in tags):
                filtered.append(paper)
        return filtered

    def _sort_papers(self, papers: list[Paper], *, sort: str) -> list[Paper]:
        if sort == "citations_desc":
            return sorted(
                papers,
                key=lambda paper: (
                    int(paper.metadata.get("citation_count") or 0),
                    bool(paper.metadata.get("top_10_percent_cited")),
                    paper.title.lower(),
                ),
                reverse=True,
            )
        if sort == "citations_asc":
            return sorted(
                papers,
                key=lambda paper: (
                    int(paper.metadata.get("citation_count") or 0),
                    paper.title.lower(),
                ),
            )
        if sort == "title_desc":
            return sorted(papers, key=lambda paper: paper.title.lower(), reverse=True)
        if sort == "title_asc":
            return sorted(papers, key=lambda paper: paper.title.lower())
        return papers

    def _top_tags(self, papers: list[Paper], limit: int = 10) -> list[str]:
        counts: dict[str, int] = {}
        for paper in papers[:200]:
            for tag in self.tag_service.build_tags(paper):
                counts[tag] = counts.get(tag, 0) + 1
        ranked = sorted(counts.items(), key=lambda item: (-item[1], item[0]))
        return [tag for tag, _ in ranked[:limit]]

    def _normalize_tags(self, tags: list[str]) -> list[str]:
        normalized: list[str] = []
        for tag in tags:
            cleaned = tag.strip()
            if cleaned and cleaned not in normalized:
                normalized.append(cleaned)
        return normalized[:8]

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
                    "track_label": self._track_label(candidate.track),
                    "title": candidate.title,
                    "title_display": candidate.to_dict()["title_display"],
                    "authors_text": ", ".join(candidate.authors),
                    "summary_preview": self.summary_service.build_preview(candidate),
                    "tags": self.tag_service.build_tags(candidate),
                    "primary_theme": self.tag_service.primary_theme(candidate),
                    "citation_count": int(candidate.metadata.get("citation_count") or 0),
                }
            )
        return related_items

    def _track_label(self, track: str) -> str:
        lowered = track.strip().lower()
        if not lowered:
            return "未分类"
        if "oral" in lowered:
            return "口头报告"
        if "spotlight" in lowered:
            return "聚光论文"
        if "findings" in lowered:
            return "补充收录"
        if "poster" in lowered:
            return "海报展示"
        if "proceedings" in lowered:
            return "论文集收录"
        if "conference" in lowered:
            return "会议论文"
        return track
