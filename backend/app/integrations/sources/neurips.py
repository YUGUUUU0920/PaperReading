from __future__ import annotations

import json
import re
from urllib.parse import urljoin

from backend.app.core.utils import clean_html_fragment, extract_resource_links, utc_now_iso
from backend.app.domain.entities import Paper
from backend.app.integrations.sources.proceedings import ProceedingsSource


VIRTUAL_LIST_RE = re.compile(r'<a href="(?P<href>/virtual/(?P<year>\d{4})/poster/(?P<id>\d+))">(?P<title>.*?)</a>', re.S)
JSONLD_RE = re.compile(r'<script type="application/ld\+json">\s*(?P<payload>\{.*?\})\s*</script>', re.S)
VIRTUAL_ABSTRACT_RE = re.compile(r'<div class="abstract-content">.*?<p>(?P<abstract>.*?)</p>', re.S)


class NeurIPSSource(ProceedingsSource):
    code = "neurips"
    label = "NeurIPS"
    list_base_url = "https://proceedings.neurips.cc/paper/{year}"

    def fetch_listing(self, year: int) -> list[Paper]:
        if year < 2025:
            return super().fetch_listing(year)

        url = f"https://neurips.cc/virtual/{year}/papers.html"
        html = self.http_client.get_text(url)
        now = utc_now_iso()
        items: list[Paper] = []
        seen: set[str] = set()
        for match in VIRTUAL_LIST_RE.finditer(html):
            external_id = match.group("id")
            if external_id in seen:
                continue
            seen.add(external_id)
            items.append(
                Paper(
                    id=None,
                    source=self.code,
                    conference=self.code,
                    year=year,
                    track="Conference",
                    external_id=external_id,
                    title=clean_html_fragment(match.group("title")),
                    authors=[],
                    abstract="",
                    paper_url=urljoin(url, match.group("href")),
                    pdf_url="",
                    summary="",
                    summary_model="",
                    metadata={"listing": "virtual"},
                    last_synced_at=now,
                    summary_updated_at="",
                )
            )
        return items

    def hydrate_paper(self, paper: Paper) -> Paper:
        if paper.year < 2025:
            return super().hydrate_paper(paper)
        if paper.abstract.strip() and paper.metadata.get("resource_links_checked") and paper.authors:
            return paper

        html = self.http_client.get_text(paper.paper_url)
        abstract_match = VIRTUAL_ABSTRACT_RE.search(html)
        if abstract_match:
            paper.abstract = clean_html_fragment(abstract_match.group("abstract"))

        jsonld_match = JSONLD_RE.search(html)
        if jsonld_match:
            payload = json.loads(jsonld_match.group("payload"))
            title = clean_html_fragment(str(payload.get("name") or ""))
            if title:
                paper.title = title
            authors = payload.get("author") or []
            if isinstance(authors, dict):
                authors = [authors]
            paper.authors = [
                clean_html_fragment(str(author.get("name") or ""))
                for author in authors
                if clean_html_fragment(str(author.get("name") or ""))
            ]

        paper.metadata = dict(paper.metadata)
        paper.metadata["resource_links"] = extract_resource_links(html, paper.paper_url)
        paper.metadata["resource_links_checked"] = True
        paper.last_synced_at = utc_now_iso()
        return paper
