from __future__ import annotations

import re

from backend.app.ai.contracts import SummarySections
from backend.app.ai.harness import SummaryHarness
from backend.app.core.config import Settings
from backend.app.core.http_client import HttpClient
from backend.app.core.utils import normalize_title_display
from backend.app.domain.entities import Paper
from backend.app.services.tag_service import TagService


SENTENCE_RE = re.compile(r"(?<=[.!?])\s+")
ASCII_WORD_RE = re.compile(r"[A-Za-z]{4,}")
MARKDOWN_TOKEN_RE = re.compile(r"[#>*`_~\-]+")
WHITESPACE_RE = re.compile(r"\s+")
SECTION_LABEL_RE = re.compile(r"^(研究问题|方法概览|主要发现|适用场景|一句话判断)\s*")

TOPIC_HINTS = [
    ("multimodal", "多模态模型"),
    ("vision-language", "视觉语言模型"),
    ("language model", "语言模型"),
    ("large language model", "大语言模型"),
    ("diffusion", "扩散模型"),
    ("transformer", "Transformer 模型"),
    ("reinforcement learning", "强化学习"),
    ("bandit", "多臂赌博机"),
    ("graph", "图学习"),
    ("time series", "时间序列"),
    ("uncertainty", "不确定性建模"),
    ("alignment", "模型对齐"),
    ("reasoning", "推理能力"),
    ("knowledge editing", "知识编辑"),
    ("retrieval", "检索增强"),
    ("audio", "音频建模"),
    ("video", "视频理解"),
    ("robot", "机器人学习"),
]

GOAL_HINTS = [
    ("efficient", "降低计算开销"),
    ("efficiency", "提升效率"),
    ("fast", "提升运行速度"),
    ("compression", "减少模型或缓存开销"),
    ("robust", "提升鲁棒性"),
    ("generalization", "提升泛化能力"),
    ("interpretability", "增强可解释性"),
    ("uncertainty", "改善不确定性估计"),
    ("fair", "改善公平性"),
    ("reasoning", "增强推理能力"),
    ("alignment", "改善模型对齐表现"),
    ("inference", "优化推理过程"),
]


class SummaryService:
    def __init__(self, settings: Settings, http_client: HttpClient, tag_service: TagService):
        self.settings = settings
        self.http_client = http_client
        self.tag_service = tag_service

    def summarize(self, paper: Paper) -> tuple[str, str]:
        if self.settings.openai_api_key:
            try:
                return self._summarize_with_llm(paper), self.settings.openai_model
            except Exception:
                return self._heuristic_summary(paper), "heuristic-fallback"
        return self._heuristic_summary(paper), "heuristic"

    def _summarize_with_llm(self, paper: Paper) -> str:
        candidate_tags = self.tag_service.build_candidate_tags(paper)
        harness = SummaryHarness(fallback_tags=candidate_tags)
        payload = {
            "model": self.settings.openai_model,
            "messages": harness.build_messages(paper, candidate_tags),
            "temperature": 0.2,
        }
        response = self.http_client.post_json(
            f"{self.settings.openai_base_url}/chat/completions",
            payload,
            headers={"Authorization": f"Bearer {self.settings.openai_api_key}"},
        )
        choices = response.get("choices") or []
        if not choices:
            raise RuntimeError("No summary choices returned")
        content = (choices[0].get("message") or {}).get("content", "").strip()
        if not content:
            raise RuntimeError("Empty summary content returned")
        sections = harness.parse_response(content)
        return sections.to_markdown()

    def build_local_summary(self, paper: Paper) -> str:
        return self._heuristic_summary(paper)

    def build_preview(self, paper: Paper) -> str:
        summary = paper.summary.strip()
        if summary:
            preview = self._preview_from_summary(summary)
            if preview:
                return preview
        if paper.abstract.strip():
            topic = self._infer_topic(paper)
            goal = self._infer_goal(paper)
            return f"聚焦{topic}，重点尝试{goal}，适合先看方法设计和核心实验。"
        return "进入详情页查看摘要、导读与相关资源。"

    def describe_summary_source(self, model_name: str) -> str:
        if not model_name:
            return ""
        if model_name.startswith("heuristic"):
            return "即时导读"
        return f"OpenAI · {model_name}"

    def should_refresh_local_summary(self, paper: Paper) -> bool:
        if not paper.summary.strip():
            return True
        if not paper.summary_model.startswith("heuristic"):
            return False
        english_hits = ASCII_WORD_RE.findall(paper.summary)
        return len(english_hits) >= 5

    def _heuristic_summary(self, paper: Paper) -> str:
        abstract = paper.abstract.strip()
        title_display = normalize_title_display(paper.title)
        topic = self._infer_topic(paper)
        goal = self._infer_goal(paper)

        if not abstract:
            sections = SummarySections(
                problem=f"这篇论文大致围绕{topic}展开，但当前还没有拿到摘要内容，因此无法给出更细的中文总结。",
                method="建议先打开详情页补全摘要，或直接查看 PDF 中的方法与实验部分。",
                findings="当前数据不足，暂时无法判断作者的核心实验结果。",
                scenarios=f"适合先加入待读列表，后续再深入阅读 {paper.conference.upper()} {paper.year} 的相关工作。",
                verdict="目前信息不足，但可以确定它属于你当前检索主题下的相关论文。",
                tags=self.tag_service.build_candidate_tags(paper),
            )
            return sections.to_markdown()

        sections = SummarySections(
            problem=f"这篇论文主要关注{topic}，目标大概率是{goal}。",
            method=(
                "从标题和摘要来看，作者提出或改造了一套面向该问题的新方法，"
                f"并围绕模型结构、训练策略、路由机制或评估流程做了专门设计。论文标题可以概括为：{title_display}。"
            ),
            findings="摘要显示，该工作在实验中取得了正向结果，重点收益通常体现在性能、效率、推理成本或泛化能力中的一个或多个方面。",
            scenarios=f"适合正在跟踪 {paper.conference.upper()} {paper.year}、并希望快速筛选{topic}方向论文的读者。",
            verdict=f"这是一篇围绕{topic}展开、重点尝试{goal}的论文，值得先看摘要、方法图和实验表。",
            tags=self.tag_service.build_candidate_tags(paper),
        )
        return sections.to_markdown()

    def _preview_from_summary(self, summary: str) -> str:
        paragraphs = [part.strip() for part in summary.split("\n\n") if part.strip()]
        for paragraph in paragraphs:
            text = MARKDOWN_TOKEN_RE.sub(" ", paragraph)
            text = WHITESPACE_RE.sub(" ", text).strip()
            text = SECTION_LABEL_RE.sub("", text).strip()
            if len(text) < 18:
                continue
            if text in {"研究问题", "方法概览", "主要发现", "适用场景", "一句话判断"}:
                continue
            if len(text) > 88:
                return f"{text[:88].rstrip('，。；;、 ')}..."
            return text
        return ""

    def _infer_topic(self, paper: Paper) -> str:
        haystack = f"{paper.title} {paper.abstract}".lower()
        hits = [label for pattern, label in TOPIC_HINTS if pattern in haystack]
        if not hits:
            return "AI 模型与算法"
        unique_hits = []
        for hit in hits:
            if hit not in unique_hits:
                unique_hits.append(hit)
        return "、".join(unique_hits[:3])

    def _infer_goal(self, paper: Paper) -> str:
        haystack = f"{paper.title} {paper.abstract}".lower()
        hits = [label for pattern, label in GOAL_HINTS if pattern in haystack]
        if not hits:
            return "解决该方向里的关键性能或效率问题"
        unique_hits = []
        for hit in hits:
            if hit not in unique_hits:
                unique_hits.append(hit)
        return "、".join(unique_hits[:3])
