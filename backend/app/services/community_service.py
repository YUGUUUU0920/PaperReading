from __future__ import annotations

import re
import secrets

from backend.app.ai.comment_harness import CommentSeedHarness
from backend.app.ai.contracts import SeedComment
from backend.app.core.config import Settings
from backend.app.core.http_client import HttpClient
from backend.app.core.utils import utc_now_iso
from backend.app.domain.entities import Paper, ViewerProfile
from backend.app.repositories.sqlite import SqliteRepository
from backend.app.services.summary_service import SummaryService
from backend.app.services.tag_service import TagService


WHITESPACE_RE = re.compile(r"\s+")
DISPLAY_NAME_RE = re.compile(r"[^\w\u4e00-\u9fff·\- ]+")

SEED_PROFILES = [
    ("seed-engineer", "偏工程的读者"),
    ("seed-experimenter", "做实验的人"),
    ("seed-skeptic", "爱抠细节的人"),
]


class CommunityService:
    def __init__(
        self,
        repository: SqliteRepository,
        settings: Settings,
        http_client: HttpClient,
        summary_service: SummaryService,
        tag_service: TagService,
    ):
        self.repository = repository
        self.settings = settings
        self.http_client = http_client
        self.summary_service = summary_service
        self.tag_service = tag_service

    def ensure_viewer(self, viewer_id: str = "", display_name: str = "") -> dict:
        profile = self._ensure_viewer_profile(viewer_id=viewer_id, display_name=display_name)
        return profile.to_dict()

    def update_viewer(self, viewer_id: str = "", display_name: str = "") -> dict:
        normalized_name = self._normalize_display_name(display_name)
        if not normalized_name:
            raise ValueError("昵称不能为空")
        profile = self._ensure_viewer_profile(viewer_id=viewer_id)
        self.repository.update_profile_name(profile.id, normalized_name)
        updated = self.repository.get_profile(profile.id)
        if not updated:
            raise RuntimeError("更新身份信息失败")
        return updated.to_dict()

    def list_comments(self, paper_id: int, *, viewer_id: str = "", display_name: str = "") -> dict:
        paper = self.repository.get_paper(paper_id)
        if not paper:
            raise KeyError(f"Paper {paper_id} not found")
        viewer = self._ensure_viewer_profile(viewer_id=viewer_id, display_name=display_name)
        self._ensure_seed_comments(paper)
        comments = self.repository.list_comments(paper_id)
        return {
            "viewer": viewer.to_dict(),
            "items": [item.to_dict() for item in comments],
            "count": len(comments),
            "seed_count": len([item for item in comments if item.source == "seed"]),
        }

    def add_comment(
        self,
        paper_id: int,
        *,
        content: str,
        viewer_id: str = "",
        display_name: str = "",
    ) -> dict:
        paper = self.repository.get_paper(paper_id)
        if not paper:
            raise KeyError(f"Paper {paper_id} not found")
        viewer = self._ensure_viewer_profile(viewer_id=viewer_id, display_name=display_name)
        normalized_content = self._normalize_comment_content(content)
        if len(normalized_content) < 4:
            raise ValueError("评论至少写 4 个字")
        if len(normalized_content) > 520:
            raise ValueError("评论请控制在 520 个字以内")
        comment = self.repository.add_comment(
            paper_id=paper_id,
            profile_id=viewer.id,
            source="user",
            content=normalized_content,
        )
        return {
            "viewer": viewer.to_dict(),
            "item": comment.to_dict(),
            "count": self.repository.count_comments(paper_id),
        }

    def _ensure_viewer_profile(self, *, viewer_id: str = "", display_name: str = "") -> ViewerProfile:
        normalized_id = viewer_id.strip()
        existing = self.repository.get_profile(normalized_id) if normalized_id else None
        if existing:
            if display_name.strip():
                normalized_name = self._normalize_display_name(display_name)
                if normalized_name and normalized_name != existing.display_name:
                    self.repository.update_profile_name(existing.id, normalized_name)
                    refreshed = self.repository.get_profile(existing.id)
                    if refreshed:
                        return refreshed
            return existing

        profile_id = normalized_id or self._generate_viewer_id()
        profile = ViewerProfile(
            id=profile_id,
            display_name=self._normalize_display_name(display_name) or self._guest_name(profile_id),
            profile_type="guest",
            created_at=utc_now_iso(),
            updated_at=utc_now_iso(),
        )
        self.repository.upsert_profile(profile)
        stored = self.repository.get_profile(profile_id)
        if not stored:
            raise RuntimeError("创建访客身份失败")
        return stored

    def _ensure_seed_comments(self, paper: Paper) -> None:
        if paper.id is None or self.repository.has_seed_comments(paper.id):
            return
        for profile_id, display_name in SEED_PROFILES:
            existing = self.repository.get_profile(profile_id)
            if existing:
                continue
            self.repository.upsert_profile(
                ViewerProfile(
                    id=profile_id,
                    display_name=display_name,
                    profile_type="seed",
                    created_at=utc_now_iso(),
                    updated_at=utc_now_iso(),
                )
            )

        for index, comment in enumerate(self._seed_comments(paper)):
            profile_id, _ = SEED_PROFILES[index % len(SEED_PROFILES)]
            self.repository.add_comment(
                paper_id=paper.id,
                profile_id=profile_id,
                source="seed",
                content=comment.content,
                sort_order=index,
            )

    def _seed_comments(self, paper: Paper) -> list[SeedComment]:
        if self.settings.openai_api_key:
            try:
                return self._seed_comments_with_llm(paper)
            except Exception:
                pass
        return self._seed_comments_locally(paper)

    def _seed_comments_with_llm(self, paper: Paper) -> list[SeedComment]:
        tags = self.tag_service.build_candidate_tags(paper)
        preview = self.summary_service.build_preview(paper)
        harness = CommentSeedHarness()
        payload = {
            "model": self.settings.openai_model,
            "messages": harness.build_messages(paper, tags, preview),
            "temperature": 0.85,
        }
        if "openai.com" in self.settings.openai_base_url:
            payload["response_format"] = harness.response_format()
        response = self.http_client.post_json(
            f"{self.settings.openai_base_url}/chat/completions",
            payload,
            headers={"Authorization": f"Bearer {self.settings.openai_api_key}"},
        )
        choices = response.get("choices") or []
        if not choices:
            raise RuntimeError("No seeded comments returned")
        content = (choices[0].get("message") or {}).get("content", "").strip()
        if not content:
            raise RuntimeError("Empty seeded comments content returned")
        parsed = harness.parse_response(content)
        fixed_names = []
        for index, item in enumerate(parsed):
            _, display_name = SEED_PROFILES[index % len(SEED_PROFILES)]
            fixed_names.append(SeedComment(display_name=display_name, content=item.content.strip()))
        return fixed_names

    def _seed_comments_locally(self, paper: Paper) -> list[SeedComment]:
        tags = self.tag_service.build_candidate_tags(paper)
        topic = tags[0] if tags else "这个方向"
        second_tag = next((tag for tag in tags if tag != topic and tag not in {"开放获取", "开源了代码"}), "")
        goal = self._goal_phrase(paper, tags)
        has_code = bool((paper.metadata or {}).get("code_url"))
        return [
            SeedComment(
                display_name=SEED_PROFILES[0][1],
                content=(
                    f"我会先看这篇到底把 {goal} 做到了什么程度。"
                    f"如果它在 {topic} 场景里不只是涨点，而是真的把落地门槛压下来了，那价值会很高。"
                    + ("好在它还给了代码，复现门槛看起来没那么吓人。" if has_code else "")
                ),
            ),
            SeedComment(
                display_name=SEED_PROFILES[1][1],
                content=(
                    f"我第一反应是去看主实验稳不稳，尤其是它在 {topic}"
                    + (f" 和 {second_tag}" if second_tag else "")
                    + " 这些维度上有没有持续收益。"
                    "如果优势只集中在少数设置里，我会保守一点看这篇。"
                ),
            ),
            SeedComment(
                display_name=SEED_PROFILES[2][1],
                content=(
                    "思路听起来是顺的，但我会重点盯它没展开说透的地方："
                    "失败案例、对比基线是不是够强，以及结论能不能跳出特定数据设置。"
                ),
            ),
        ]

    def _goal_phrase(self, paper: Paper, tags: list[str]) -> str:
        haystack = f"{paper.title} {paper.abstract}".lower()
        if "retrieval" in haystack or "rag" in haystack:
            return "检索增强这件事"
        if "reason" in haystack:
            return "推理链条"
        if "align" in haystack:
            return "模型对齐"
        if "efficient" in haystack or "faster" in haystack or "speed" in haystack:
            return "效率问题"
        if tags:
            return tags[0]
        return "这个问题"

    def _normalize_comment_content(self, content: str) -> str:
        return WHITESPACE_RE.sub(" ", str(content or "").strip())

    def _normalize_display_name(self, display_name: str) -> str:
        cleaned = DISPLAY_NAME_RE.sub("", str(display_name or "").strip())
        cleaned = WHITESPACE_RE.sub(" ", cleaned).strip()
        return cleaned[:20]

    def _guest_name(self, profile_id: str) -> str:
        suffix = profile_id.split("-")[-1][-4:].upper()
        return f"访客-{suffix}"

    def _generate_viewer_id(self) -> str:
        return f"viewer-{secrets.token_hex(4)}"
