from __future__ import annotations

import re
from urllib.parse import urljoin

from backend.app.core.http_client import HttpClient
from backend.app.core.utils import clean_html_fragment, extract_resource_links, utc_now_iso
from backend.app.domain.entities import Paper
from backend.app.integrations.sources.base import ConferenceSource


ENTRY_SPLIT = '<div class="d-sm-flex align-items-stretch mb-3">'
PAPER_RE = re.compile(
    r"<strong><a class=align-middle href=(?P<paper>[^ >]+)>(?P<title>.*?)</a></strong><br>(?P<authors>.*?)</span></div>"
    r'<div class="card bg-light mb-2 mb-lg-3 collapse abstract-collapse"[^>]*><div class="card-body p-3 small">(?P<abstract>.*?)</div>',
    re.S,
)
PDF_RE = re.compile(r'<a class="badge text-bg-primary[^"]*" href=(?P<pdf>[^ >]+)[^>]*>pdf', re.S)
AUTHOR_RE = re.compile(r"<a href=[^>]+>(?P<name>.*?)</a>", re.S)


class ACLSource(ConferenceSource):
    code = "acl"
    label = "ACL"
    allowed_track_fragments = ("acl-long", "acl-short", "findings-acl")

    def __init__(self, http_client: HttpClient):
        self.http_client = http_client

    def fetch_listing(self, year: int) -> list[Paper]:
        url = f"https://aclanthology.org/events/acl-{year}/"
        html = self.http_client.get_text(url)
        now = utc_now_iso()
        items: list[Paper] = []
        for chunk in html.split(ENTRY_SPLIT)[1:]:
            paper_match = PAPER_RE.search(chunk)
            pdf_match = PDF_RE.search(chunk)
            if not paper_match:
                continue
            paper_href = paper_match.group("paper").strip('"')
            external_id = paper_href.strip("/").split("/")[-1]
            if not any(fragment in external_id for fragment in self.allowed_track_fragments):
                continue
            authors = [
                clean_html_fragment(author_match.group("name"))
                for author_match in AUTHOR_RE.finditer(paper_match.group("authors"))
            ]
            items.append(
                Paper(
                    id=None,
                    source=self.code,
                    conference=self.code,
                    year=year,
                    track=self._pretty_track(external_id),
                    external_id=external_id,
                    title=clean_html_fragment(paper_match.group("title")),
                    authors=[author for author in authors if author],
                    abstract=clean_html_fragment(paper_match.group("abstract")),
                    paper_url=urljoin(url, paper_href),
                    pdf_url=urljoin(url, pdf_match.group("pdf").strip('"')) if pdf_match else "",
                    summary="",
                    summary_model="",
                    metadata={},
                    last_synced_at=now,
                    summary_updated_at="",
                )
            )
        return items

    def _pretty_track(self, external_id: str) -> str:
        if "acl-long" in external_id:
            return "Long Papers"
        if "acl-short" in external_id:
            return "Short Papers"
        if "findings-acl" in external_id:
            return "Findings"
        return "ACL"

    def hydrate_paper(self, paper: Paper) -> Paper:
        if paper.abstract.strip() and paper.pdf_url.strip() and paper.metadata.get("resource_links_checked"):
            return paper
        html = self.http_client.get_text(paper.paper_url)
        paper.metadata = dict(paper.metadata)
        paper.metadata["resource_links"] = extract_resource_links(html, paper.paper_url)
        paper.metadata["resource_links_checked"] = True
        paper.last_synced_at = utc_now_iso()
        return paper
