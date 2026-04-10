from __future__ import annotations

import html
import re
from datetime import datetime, timezone
from urllib.parse import urljoin, urlparse


TAG_RE = re.compile(r"<[^>]+>")
WHITESPACE_RE = re.compile(r"\s+")
LATEX_BRACED_CMD_RE = re.compile(r"\\[A-Za-z]+\s*\{([^{}]+)\}")
LATEX_SIMPLE_CMD_RE = re.compile(r"\\(?:bf|rm|it|tt|mathrm|textrm|mathit|mathtt|mathbf|mathbb|mathcal|mathsf)\s*")
HREF_RE = re.compile(r'<a[^>]+href=["\'](?P<href>[^"\']+)["\'][^>]*>(?P<label>.*?)</a>', re.S)
RESOURCE_HOSTS = {
    "github.com": "github",
    "gitlab.com": "gitlab",
    "huggingface.co": "huggingface",
    "colab.research.google.com": "colab",
    "openreview.net": "openreview",
}
NON_RESOURCE_LABELS = ("code of conduct", "code of ethics", "github account")

LATEX_TOKEN_MAP = {
    "\\alpha": "α",
    "\\beta": "β",
    "\\gamma": "γ",
    "\\delta": "δ",
    "\\epsilon": "ε",
    "\\theta": "θ",
    "\\lambda": "λ",
    "\\mu": "μ",
    "\\pi": "π",
    "\\sigma": "σ",
    "\\phi": "φ",
    "\\Phi": "Φ",
    "\\psi": "ψ",
    "\\omega": "ω",
    "\\Omega": "Ω",
}


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def clean_html_fragment(value: str) -> str:
    if not value:
        return ""
    text = value.replace("<br>", "\n").replace("<br/>", "\n").replace("<br />", "\n")
    text = text.replace("</p>", "\n\n").replace("</div>", "\n")
    text = TAG_RE.sub(" ", text)
    text = html.unescape(text)
    text = re.sub(r"\s+\n", "\n", text)
    text = re.sub(r"\n\s+", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def normalize_text(value: str) -> str:
    return WHITESPACE_RE.sub(" ", clean_html_fragment(value)).strip()


def split_authors(value: str) -> list[str]:
    cleaned = normalize_text(value)
    if not cleaned:
        return []
    return [part.strip() for part in cleaned.split(",") if part.strip()]


def normalize_title_display(value: str) -> str:
    text = clean_html_fragment(value)
    if not text:
        return ""

    text = text.replace("$", "")
    for token, replacement in LATEX_TOKEN_MAP.items():
        text = text.replace(token, replacement)

    previous = None
    while previous != text:
        previous = text
        text = LATEX_BRACED_CMD_RE.sub(r"\1", text)

    text = LATEX_SIMPLE_CMD_RE.sub("", text)
    text = text.replace("\\_", "_")
    text = text.replace("\\&", "&")
    text = text.replace("\\%", "%")
    text = text.replace("{", "")
    text = text.replace("}", "")
    text = text.replace("\\", "")
    text = re.sub(r"(?<=\S)_(?=\S)", "", text)
    text = re.sub(r"\s+:", ":", text)
    text = re.sub(r"\(\s+", "(", text)
    text = re.sub(r"\s+\)", ")", text)
    text = re.sub(r"\s{2,}", " ", text)
    return text.strip()


def normalize_match_text(value: str) -> str:
    text = normalize_title_display(value).lower()
    text = re.sub(r"[^a-z0-9\u4e00-\u9fff]+", " ", text)
    return WHITESPACE_RE.sub(" ", text).strip()


def extract_resource_links(value: str, base_url: str = "") -> list[dict[str, str]]:
    if not value:
        return []
    links: list[dict[str, str]] = []
    seen: set[str] = set()
    for match in HREF_RE.finditer(value):
        href = html.unescape(match.group("href")).strip()
        if not href:
            continue
        absolute = urljoin(base_url, href) if base_url else href
        kind = infer_link_kind(absolute, clean_html_fragment(match.group("label")))
        if not kind or absolute in seen:
            continue
        seen.add(absolute)
        links.append(
            {
                "kind": kind,
                "url": absolute,
                "label": clean_html_fragment(match.group("label")) or kind,
            }
        )
    return links


def infer_link_kind(url: str, label: str = "") -> str:
    parsed = urlparse(url)
    host = parsed.netloc.lower()
    label_text = label.lower().strip()
    combined_text = f"{label} {url}".lower()
    if any(fragment in combined_text for fragment in NON_RESOURCE_LABELS):
        return ""
    if host == "raw.githubusercontent.com":
        return ""
    if "download pdf" in label_text or label_text == "pdf":
        return ""
    if host == "github.com" and ("/edit/" in parsed.path or label_text in {"edit", "history"}):
        return ""
    for fragment, kind in RESOURCE_HOSTS.items():
        if fragment in host:
            return kind
    if "github" in label_text or "source code" in label_text or "code repo" in label_text or "repository" in label_text:
        return "code"
    if "demo" in label_text:
        return "demo"
    return ""
