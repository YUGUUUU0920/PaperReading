from __future__ import annotations

import json
import re

from backend.app.ai.contracts import SeedComment
from backend.app.core.utils import normalize_title_display
from backend.app.domain.entities import Paper


JSON_BLOCK_RE = re.compile(r"```(?:json)?\s*(\[.*\])\s*```", re.S)


class CommentSeedHarness:
    def build_messages(self, paper: Paper, tags: list[str], summary_preview: str) -> list[dict[str, str]]:
        tags_text = "、".join(tags[:8]) if tags else "无"
        return [
            {
                "role": "system",
                "content": (
                    "你在为 AI 论文产品生成开场讨论观点。"
                    "这些观点会被展示成“开场观点”，语气要像真实读者在论文页留下的第一反应。"
                    "你必须输出严格 JSON 数组，不要输出 Markdown，不要输出解释。"
                ),
            },
            {
                "role": "user",
                "content": (
                    "请围绕下面这篇论文，写 3 条中文开场观点。\n"
                    "每条都来自不同视角：\n"
                    "1. 偏工程的读者\n"
                    "2. 做实验的人\n"
                    "3. 爱抠细节的人\n\n"
                    "JSON 数组里每个对象必须只有 display_name 和 content 两个字段。\n"
                    "要求：\n"
                    "1. 每条 1 到 3 句话，像真实评论，不要像总结报告。\n"
                    "2. 可以有判断、有保留、有好奇心，但不要阴阳怪气。\n"
                    "3. 不要重复标题，不要自称 AI，不要说“作为一个模型”。\n"
                    "4. 优先评论方法价值、实验可信度、落地门槛或值得追问的点。\n"
                    "5. 三条观点的角度要明显不同，避免套话。\n\n"
                    f"标题：{normalize_title_display(paper.title)}\n"
                    f"会议：{paper.conference.upper()} {paper.year}\n"
                    f"标签：{tags_text}\n"
                    f"摘要预览：{summary_preview}\n"
                    f"摘要：{paper.abstract}\n"
                ),
            },
        ]

    def response_format(self) -> dict:
        return {
            "type": "json_schema",
            "json_schema": {
                "name": "paper_comment_seeds",
                "strict": True,
                "schema": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "display_name": {"type": "string"},
                            "content": {"type": "string"},
                        },
                        "required": ["display_name", "content"],
                        "additionalProperties": False,
                    },
                    "minItems": 3,
                    "maxItems": 3,
                },
            },
        }

    def parse_response(self, content: str) -> list[SeedComment]:
        text = content.strip()
        match = JSON_BLOCK_RE.search(text)
        if match:
            text = match.group(1)
        payload = json.loads(text)
        if not isinstance(payload, list):
            raise ValueError("Comment seed payload must be a JSON array")
        comments: list[SeedComment] = []
        for item in payload[:3]:
            if not isinstance(item, dict):
                continue
            display_name = str(item.get("display_name") or "").strip()
            comment_text = str(item.get("content") or "").strip()
            if not display_name or not comment_text:
                continue
            comments.append(SeedComment(display_name=display_name, content=comment_text))
        if len(comments) < 3:
            raise ValueError("Comment seed payload is incomplete")
        return comments
