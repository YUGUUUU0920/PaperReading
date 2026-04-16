from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from backend.app.services.community_service import CommunityService
from backend.app.core.config import get_settings
from backend.app.core.http_client import HttpClient
from backend.app.ai.harness import SummaryHarness
from backend.app.domain.entities import Paper
from backend.app.repositories.sqlite import SqliteRepository
from backend.app.services.summary_service import SummaryService
from backend.app.services.tag_service import TagService


class SummaryHarnessTests(unittest.TestCase):
    def test_parses_json_and_keeps_candidate_tags(self) -> None:
        harness = SummaryHarness(fallback_tags=["多模态", "高被引"])
        sections = harness.parse_response(
            '{"problem":"研究多模态模型。","core_idea":"先把不同模态的信息放到同一空间里理解。","method":"提出新的训练方案。","experiments":"在公开基准上做了对比实验。","results":"实验优于基线。","value":"适合拿来理解多模态系统怎么做稳定训练。","verdict":"值得精读。","tags":["多模态","视觉语言模型"]}'
        )
        self.assertEqual(sections.problem, "研究多模态模型。")
        self.assertEqual(sections.core_idea, "先把不同模态的信息放到同一空间里理解。")
        self.assertIn("多模态", sections.tags)
        self.assertIn("高被引", sections.tags)


class TagServiceTests(unittest.TestCase):
    def test_builds_domain_and_signal_tags(self) -> None:
        service = TagService()
        paper = Paper(
            id=1,
            source="iclr",
            conference="iclr",
            year=2025,
            track="Spotlight",
            external_id="demo",
            title="A Multimodal Retrieval-Augmented Language Model for Reasoning",
            authors=["Alice", "Bob"],
            abstract="We study multimodal reasoning with retrieval augmented generation and strong language models.",
            paper_url="https://example.com/paper",
            pdf_url="https://example.com/paper.pdf",
            summary="",
            summary_model="",
            metadata={
                "citation_count": 88,
                "top_10_percent_cited": True,
                "open_access": True,
                "code_url": "https://github.com/example/project",
                "resource_links": [{"kind": "openreview", "url": "https://openreview.net/forum?id=1", "label": "OpenReview"}],
            },
        )
        tags = service.build_tags(paper)
        self.assertIn("多模态", tags)
        self.assertIn("RAG", tags)
        self.assertIn("大模型", tags)
        self.assertIn("引用量高", tags)
        self.assertIn("影响力强", tags)
        self.assertIn("开源了代码", tags)
        self.assertIn("开放获取", tags)
        self.assertEqual(service.primary_theme(tags=tags), "大模型")


class SummaryServiceTests(unittest.TestCase):
    def test_preview_prefers_verdict_and_value_sections(self) -> None:
        settings = get_settings()
        service = SummaryService(settings, HttpClient(settings), TagService())
        paper = Paper(
            id=1,
            source="iclr",
            conference="iclr",
            year=2025,
            track="Conference",
            external_id="preview",
            title="A Reasoning Paper",
            authors=["Alice"],
            abstract="This paper studies reasoning.",
            paper_url="https://example.com/paper",
            pdf_url="https://example.com/paper.pdf",
            summary=(
                "### 这篇论文想解决什么\n"
                "作者想解决复杂推理场景里的错误累积问题。\n\n"
                "### 为什么值得关注\n"
                "如果你在比较不同推理路线，这篇论文把收益点和成本写得都比较清楚。\n\n"
                "### 一句话判断\n"
                "适合先看主实验和误差分析，再决定是否精读。"
            ),
            summary_model="heuristic-auto",
        )

        preview = service.build_preview(paper)

        self.assertEqual(preview, "适合先看主实验和误差分析，再决定是否精读。")


class CommunityServiceTests(unittest.TestCase):
    def test_local_seed_comments_use_human_like_perspectives(self) -> None:
        settings = get_settings()
        with TemporaryDirectory() as temp_dir:
            repository = SqliteRepository(Path(temp_dir) / "papers.db")
            service = CommunityService(
                repository,
                settings,
                HttpClient(settings),
                SummaryService(settings, HttpClient(settings), TagService()),
                TagService(),
            )
            paper = Paper(
                id=1,
                source="iclr",
                conference="iclr",
                year=2025,
                track="Conference",
                external_id="community",
                title="A Multimodal Retrieval-Augmented Language Model for Reasoning",
                authors=["Alice"],
                abstract="A multimodal retrieval augmented generation system for large language models and reasoning.",
                paper_url="https://example.com/paper",
                pdf_url="https://example.com/paper.pdf",
                summary="",
                summary_model="",
                metadata={"code_url": "https://github.com/example/project"},
            )

            comments = service._seed_comments_locally(paper)

        self.assertEqual(len(comments), 3)
        self.assertIn("偏工程的读者", [item.display_name for item in comments])
        self.assertTrue(any("复现" in item.content or "工程" in item.content for item in comments))
        self.assertTrue(all("作为 AI" not in item.content for item in comments))
