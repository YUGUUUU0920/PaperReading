from __future__ import annotations

import re
from urllib.parse import urljoin

from backend.app.core.http_client import HttpClient
from backend.app.core.utils import clean_html_fragment, extract_resource_links, split_authors, utc_now_iso
from backend.app.domain.entities import Paper
from backend.app.integrations.sources.base import ConferenceSource


LIST_ITEM_RE = re.compile(
    r'<li class="(?P<kind>[^"]+)"[^>]*>\s*<div class="paper-content">\s*'
    r'<a title="paper title" href="(?P<href>[^"]+)">(?P<title>.*?)</a>\s*'
    r'<span class="paper-authors">(?P<authors>.*?)</span>\s*'
    r"</div>\s*<span class=\"paper-track-badge\">(?P<track>.*?)</span>",
    re.S,
)
PDF_META_RE = re.compile(r'<meta name="citation_pdf_url" content="(?P<pdf>[^"]+)">', re.S)
ABSTRACT_RE = re.compile(r"<h2 class=\"section-label\">Abstract</h2>\s*<p[^>]*>(?P<abstract>.*?)</p>", re.S)
HASH_RE = re.compile(r"/hash/(?P<value>[^-]+)-Abstract", re.S)


class ProceedingsSource(ConferenceSource):
    list_base_url: str

    def __init__(self, http_client: HttpClient):
        self.http_client = http_client

    def list_url(self, year: int) -> str:
        return self.list_base_url.format(year=year)

    def fetch_listing(self, year: int) -> list[Paper]:
        url = self.list_url(year)
        html = self.http_client.get_text(url)
        now = utc_now_iso()
        items: list[Paper] = []
        for match in LIST_ITEM_RE.finditer(html):
            detail_href = match.group("href")
            hash_match = HASH_RE.search(detail_href)
            external_id = f"{year}:{hash_match.group('value') if hash_match else detail_href}"
            items.append(
                Paper(
                    id=None,
                    source=self.code,
                    conference=self.code,
                    year=year,
                    track=clean_html_fragment(match.group("track")),
                    external_id=external_id,
                    title=clean_html_fragment(match.group("title")),
                    authors=split_authors(match.group("authors")),
                    abstract="",
                    paper_url=urljoin(url, detail_href),
                    pdf_url="",
                    summary="",
                    summary_model="",
                    metadata={},
                    last_synced_at=now,
                    summary_updated_at="",
                )
            )
        return items

    def hydrate_paper(self, paper: Paper) -> Paper:
        if paper.abstract.strip() and paper.pdf_url.strip() and paper.metadata.get("resource_links_checked"):
            return paper
        html = self.http_client.get_text(paper.paper_url)
        abstract_match = ABSTRACT_RE.search(html)
        pdf_match = PDF_META_RE.search(html)
        paper.abstract = clean_html_fragment(abstract_match.group("abstract") if abstract_match else "")
        paper.pdf_url = pdf_match.group("pdf") if pdf_match else paper.pdf_url
        paper.metadata = dict(paper.metadata)
        paper.metadata["resource_links"] = extract_resource_links(html, paper.paper_url)
        paper.metadata["resource_links_checked"] = True
        paper.last_synced_at = utc_now_iso()
        return paper
