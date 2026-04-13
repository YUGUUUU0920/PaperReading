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
                    "你是资深 AI 论文导读编辑。"
                    "你要把论文内容解释给懂技术但不一定熟悉该细分方向的读者。"
                    "你必须输出严格 JSON，不要输出 Markdown，不要输出解释。"
                ),
            },
            {
                "role": "user",
                "content": (
                    "请写一份通俗但专业的中文论文导读，并输出 JSON 对象。\n"
                    "字段必须严格是：\n"
                    'problem, core_idea, method, experiments, results, value, verdict, tags\n\n'
                    "要求：\n"
                    "1. 先说论文真正想解决的痛点，再说方法。\n"
                    "2. 术语第一次出现时，要顺手用白话解释，不要只堆英文缩写。\n"
                    "3. 不要照搬英文摘要原句，也不要把标题改写一遍就结束。\n"
                    "4. 如果摘要没有明确写出数据集、任务、指标或结果，请直接写“摘要未明确说明”，不要编造。\n"
                    "5. 每个字段用 1 到 2 句话说清楚，口吻专业、克制、易懂。\n"
                    "6. verdict 要像给同事的阅读建议，直接说明这篇论文值不值得优先看。\n"
                    "7. tags 必须是中文短标签数组，尽量从候选标签中选，最多 8 个。\n\n"
                    f"标题：{normalize_title_display(paper.title)}\n"
                    f"会议：{paper.conference.upper()} {paper.year}\n"
                    f"作者：{', '.join(paper.authors)}\n"
                    f"候选标签：{tags_text}\n"
                    f"摘要：{paper.abstract}\n"
                ),
            },
        ]

    def response_format(self) -> dict:
        return {
            "type": "json_schema",
            "json_schema": {
                "name": "paper_summary",
                "strict": True,
                "schema": {
                    "type": "object",
                    "properties": {
                        "problem": {"type": "string"},
                        "core_idea": {"type": "string"},
                        "method": {"type": "string"},
                        "experiments": {"type": "string"},
                        "results": {"type": "string"},
                        "value": {"type": "string"},
                        "verdict": {"type": "string"},
                        "tags": {
                            "type": "array",
                            "items": {"type": "string"},
                        },
                    },
                    "required": [
                        "problem",
                        "core_idea",
                        "method",
                        "experiments",
                        "results",
                        "value",
                        "verdict",
                        "tags",
                    ],
                    "additionalProperties": False,
                },
            },
        }

    def parse_response(self, content: str) -> SummarySections:
        payload = self._load_json(content)
        sections = SummarySections(
            problem=self._clean_text(payload.get("problem")),
            core_idea=self._clean_text(payload.get("core_idea")),
            method=self._clean_text(payload.get("method")),
            experiments=self._clean_text(payload.get("experiments")),
            results=self._clean_text(payload.get("results")),
            value=self._clean_text(payload.get("value")),
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
        for field_name in ("problem", "core_idea", "method", "experiments", "results", "value", "verdict"):
            if not getattr(sections, field_name).strip():
                raise ValueError(f"Summary field {field_name} is empty")
