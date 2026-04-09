from __future__ import annotations

import html
import re
from datetime import datetime, timezone


TAG_RE = re.compile(r"<[^>]+>")
WHITESPACE_RE = re.compile(r"\s+")
LATEX_BRACED_CMD_RE = re.compile(r"\\[A-Za-z]+\s*\{([^{}]+)\}")
LATEX_SIMPLE_CMD_RE = re.compile(r"\\(?:bf|rm|it|tt|mathrm|textrm|mathit|mathtt|mathbf|mathbb|mathcal|mathsf)\s*")

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
