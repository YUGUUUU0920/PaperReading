from __future__ import annotations

import re

from backend.app.core.http_client import HttpClient
from backend.app.core.utils import clean_html_fragment, extract_resource_links, split_authors, utc_now_iso
from backend.app.domain.entities import Paper
from backend.app.integrations.sources.base import ConferenceSource


ICML_VOLUMES = {
    2021: 139,
    2022: 162,
    2023: 202,
    2024: 235,
    2025: 267,
}

PAPER_RE = re.compile(
    r'<div class="paper">\s*<p class="title">(?P<title>.*?)</p>.*?'
    r'<span class="authors">(?P<authors>.*?)</span>;.*?'
    r'\[<a href="(?P<abs>[^"]+)">abs</a>]\[<a href="(?P<pdf>[^"]+)"[^>]*>Download PDF</a>]',
    re.S,
)
ABSTRACT_RE = re.compile(r'<div id="abstract" class="abstract">\s*(?P<abstract>.*?)\s*</div>', re.S)


class ICMLSource(ConferenceSource):
    code = "icml"
    label = "ICML"

    def __init__(self, http_client: HttpClient):
        self.http_client = http_client

    def fetch_listing(self, year: int) -> list[Paper]:
        volume = ICML_VOLUMES.get(year)
        if volume is None:
            raise ValueError(f"ICML {year} is not configured yet.")
        url = f"https://proceedings.mlr.press/v{volume}/"
        html = self.http_client.get_text(url)
        now = utc_now_iso()
        items: list[Paper] = []
        for match in PAPER_RE.finditer(html):
            abs_url = match.group("abs")
            slug = abs_url.rstrip("/").split("/")[-1].replace(".html", "")
            items.append(
                Paper(
                    id=None,
                    source=self.code,
                    conference=self.code,
                    year=year,
                    track="Proceedings",
                    external_id=f"{year}:{slug}",
                    title=clean_html_fragment(match.group("title")),
                    authors=split_authors(match.group("authors")),
                    abstract="",
                    paper_url=abs_url,
                    pdf_url=match.group("pdf"),
                    summary="",
                    summary_model="",
                    metadata={"volume": volume},
                    last_synced_at=now,
                    summary_updated_at="",
                )
            )
        return items

    def hydrate_paper(self, paper: Paper) -> Paper:
        if paper.abstract.strip() and paper.metadata.get("resource_links_checked"):
            return paper
        html = self.http_client.get_text(paper.paper_url)
        match = ABSTRACT_RE.search(html)
        paper.abstract = clean_html_fragment(match.group("abstract") if match else "")
        paper.metadata = dict(paper.metadata)
        paper.metadata["resource_links"] = extract_resource_links(match.group("abstract") if match else "", paper.paper_url)
        paper.metadata["resource_links_checked"] = True
        paper.last_synced_at = utc_now_iso()
        return paper
