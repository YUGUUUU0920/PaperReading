from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from difflib import SequenceMatcher
from urllib.parse import quote_plus

from backend.app.core.config import Settings
from backend.app.core.http_client import HttpClient
from backend.app.core.utils import infer_link_kind, normalize_match_text, normalize_title_display, utc_now_iso
from backend.app.domain.entities import Paper


@dataclass
class OpenAlexCandidate:
    payload: dict
    score: float


class EnrichmentService:
    def __init__(self, settings: Settings, http_client: HttpClient):
        self.settings = settings
        self.http_client = http_client

    def enrich_metadata(self, paper: Paper) -> dict:
        metadata = dict(paper.metadata)
        metadata["resource_links"] = self._sanitize_resource_links(metadata.get("resource_links", []))
        if self._is_fresh(metadata.get("signals_refreshed_at", "")):
            metadata["code_url"] = self._pick_code_url(metadata.get("resource_links", []))
            return metadata

        metadata["title_normalized"] = normalize_title_display(paper.title)
        if metadata.get("resource_links_checked"):
            metadata["code_url"] = self._pick_code_url(metadata.get("resource_links", []))

        try:
            candidate = self._fetch_openalex_candidate(paper)
        except Exception:
            candidate = None

        if candidate:
            result = candidate.payload
            metadata.update(
                {
                    "openalex_id": result.get("id", ""),
                    "openalex_url": result.get("id", ""),
                    "citation_count": int(result.get("cited_by_count") or 0),
                    "top_10_percent_cited": bool(
                        ((result.get("citation_normalized_percentile") or {}).get("is_in_top_10_percent"))
                    ),
                    "open_access": bool(((result.get("open_access") or {}).get("is_oa"))),
                    "concepts_en": [
                        concept.get("display_name", "")
                        for concept in (result.get("concepts") or [])
                        if concept.get("display_name")
                    ][:6],
                    "topics_en": [
                        topic.get("display_name", "")
                        for topic in (result.get("topics") or [])
                        if topic.get("display_name")
                    ][:6],
                    "openalex_match_score": round(candidate.score, 3),
                }
            )

        metadata["signals_refreshed_at"] = utc_now_iso()
        metadata["resource_links"] = self._sanitize_resource_links(metadata.get("resource_links", []))
        metadata["code_url"] = self._pick_code_url(metadata.get("resource_links", []))
        return metadata

    def _fetch_openalex_candidate(self, paper: Paper) -> OpenAlexCandidate | None:
        normalized_title = normalize_title_display(paper.title)
        url = (
            "https://api.openalex.org/works"
            f"?search={quote_plus(normalized_title)}"
            f"&filter=publication_year:{paper.year}"
            "&per-page=5"
        )
        response = self.http_client.get_json(url)
        results = response.get("results") or []
        best: OpenAlexCandidate | None = None
        paper_title = normalize_match_text(paper.title)
        paper_authors = {normalize_match_text(name) for name in paper.authors if name.strip()}

        for result in results:
            candidate_title = normalize_match_text(result.get("display_name") or result.get("title") or "")
            if not candidate_title:
                continue
            title_score = SequenceMatcher(None, paper_title, candidate_title).ratio()
            author_names = {
                normalize_match_text(((item.get("author") or {}).get("display_name") or ""))
                for item in (result.get("authorships") or [])
            }
            author_names.discard("")
            author_score = 0.0
            if paper_authors and author_names:
                overlap = len(paper_authors & author_names)
                author_score = overlap / max(len(paper_authors), 1)
            score = title_score * 0.82 + author_score * 0.18
            if best is None or score > best.score:
                best = OpenAlexCandidate(payload=result, score=score)

        if best and best.score >= 0.58:
            return best
        return None

    def _is_fresh(self, value: str) -> bool:
        if not value:
            return False
        try:
            timestamp = datetime.fromisoformat(value)
        except ValueError:
            return False
        return datetime.now(timezone.utc) - timestamp < timedelta(days=30)

    def _pick_code_url(self, resource_links: list[dict]) -> str:
        for item in resource_links or []:
            kind = str(item.get("kind", "")).lower()
            if kind in {"github", "gitlab"}:
                return str(item.get("url", "")).strip()
        return ""

    def _sanitize_resource_links(self, resource_links: list[dict]) -> list[dict]:
        cleaned: list[dict] = []
        seen: set[str] = set()
        for item in resource_links or []:
            url = str(item.get("url", "")).strip()
            label = str(item.get("label", "")).strip()
            kind = infer_link_kind(url, label)
            if not url or not kind or url in seen:
                continue
            seen.add(url)
            cleaned.append(
                {
                    "kind": kind,
                    "url": url,
                    "label": label or kind,
                }
            )
        return cleaned
