from __future__ import annotations

import unittest

from backend.app.ai.harness import SummaryHarness
from backend.app.domain.entities import Paper
from backend.app.services.tag_service import TagService


class SummaryHarnessTests(unittest.TestCase):
    def test_parses_json_and_keeps_candidate_tags(self) -> None:
        harness = SummaryHarness(fallback_tags=["多模态", "高被引"])
        sections = harness.parse_response(
            '{"problem":"研究多模态模型。","method":"提出新的训练方案。","findings":"实验优于基线。","scenarios":"适合多模态检索。","verdict":"值得精读。","tags":["多模态","视觉语言模型"]}'
        )
        self.assertEqual(sections.problem, "研究多模态模型。")
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

