from __future__ import annotations

import json
import re
from dataclasses import asdict

from backend.app.ai.contracts import SummarySections
from backend.app.core.utils import normalize_title_display
from backend.app.domain.entities import Paper


JSON_BLOCK_RE = re.compile(r"```(?:json)?\s*(\{.*\})\s*```", re.S)


class SummaryHarness:
    def __init__(self, *, fallback_tags: list[str] | None = None):
        self.fallback_tags = fallback_tags or []

    def build_messages(self, paper: Paper, candidate_tags: list[str]) -> list[dict[str, str]]:
        tags_text = "、".join(candidate_tags[:12]) if candidate_tags else "无"
        return [
            {
                "role": "system",
                "content": (
                    "你是严谨的 AI 论文助理。"
                    "你必须输出严格 JSON，不要输出 Markdown，不要输出解释。"
                ),
            },
            {
                "role": "user",
                "content": (
                    "请用简洁中文总结这篇 AI 论文，并输出 JSON 对象，字段必须是：\n"
                    'problem, method, findings, scenarios, verdict, tags\n\n'
                    "要求：\n"
                    "1. 不要照搬英文摘要原句。\n"
                    "2. tags 必须是中文短标签数组，尽量从候选标签中选。\n"
                    "3. 每个字段都必须是非空字符串；tags 最多 8 个。\n\n"
                    f"标题：{normalize_title_display(paper.title)}\n"
                    f"会议：{paper.conference.upper()} {paper.year}\n"
                    f"作者：{', '.join(paper.authors)}\n"
                    f"候选标签：{tags_text}\n"
                    f"摘要：{paper.abstract}\n"
                ),
            },
        ]

    def parse_response(self, content: str) -> SummarySections:
        payload = self._load_json(content)
        sections = SummarySections(
            problem=self._clean_text(payload.get("problem")),
            method=self._clean_text(payload.get("method")),
            findings=self._clean_text(payload.get("findings")),
            scenarios=self._clean_text(payload.get("scenarios")),
            verdict=self._clean_text(payload.get("verdict")),
            tags=self._clean_tags(payload.get("tags")),
        )
        self._validate_sections(sections)
        return sections

    def serialize(self, sections: SummarySections) -> dict:
        return asdict(sections)

    def _load_json(self, content: str) -> dict:
        text = content.strip()
        match = JSON_BLOCK_RE.search(text)
        if match:
            text = match.group(1)
        payload = json.loads(text)
        if not isinstance(payload, dict):
            raise ValueError("Summary payload must be a JSON object")
        return payload

    def _clean_text(self, value: object) -> str:
        return str(value or "").strip()

    def _clean_tags(self, value: object) -> list[str]:
        if isinstance(value, list):
            items = [str(item).strip() for item in value if str(item).strip()]
        elif isinstance(value, str):
            items = [part.strip() for part in re.split(r"[、,/|]", value) if part.strip()]
        else:
            items = []
        deduped: list[str] = []
        for item in items + self.fallback_tags:
            if item and item not in deduped:
                deduped.append(item)
        return deduped[:8]

    def _validate_sections(self, sections: SummarySections) -> None:
        for field_name in ("problem", "method", "findings", "scenarios", "verdict"):
            if not getattr(sections, field_name).strip():
                raise ValueError(f"Summary field {field_name} is empty")
