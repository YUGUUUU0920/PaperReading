from __future__ import annotations

import re

from backend.app.ai.contracts import SummarySections
from backend.app.ai.harness import SummaryHarness
from backend.app.core.config import Settings
from backend.app.core.http_client import HttpClient
from backend.app.core.utils import normalize_title_display
from backend.app.domain.entities import Paper
from backend.app.services.tag_service import TagService


ASCII_WORD_RE = re.compile(r"[A-Za-z]{4,}")
MARKDOWN_TOKEN_RE = re.compile(r"[#>*`_~\-]+")
WHITESPACE_RE = re.compile(r"\s+")
SECTION_LABEL_RE = re.compile(
    r"^(这篇论文想解决什么|核心思路|方法怎么做|用了什么数据与实验|结果说明了什么|为什么值得关注|研究问题|方法概览|主要发现|适用场景|一句话判断)\s*"
)

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
            "temperature": 0.15,
        }
        if self._should_request_structured_output():
            payload["response_format"] = harness.response_format()
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
        return f"AI 导读 · {model_name}"

    def should_refresh_local_summary(self, paper: Paper) -> bool:
        if not paper.summary.strip():
            return True
        if not paper.summary_model.startswith("heuristic"):
            return False
        if any(label in paper.summary for label in ("### 研究问题", "### 方法概览", "### 主要发现", "### 适用场景")):
            return True
        english_hits = ASCII_WORD_RE.findall(paper.summary)
        return len(english_hits) >= 5

    def _heuristic_summary(self, paper: Paper) -> str:
        abstract = paper.abstract.strip()
        title_display = normalize_title_display(paper.title)
        topic = self._infer_topic(paper)
        goal = self._infer_goal(paper)
        experiments = self._infer_experiments(paper)
        results = self._infer_results(paper)

        if not abstract:
            sections = SummarySections(
                problem=f"这篇论文大概率围绕{topic}展开，目标是{goal}，但当前还没有拿到摘要，所以问题定义只能先做粗粒度判断。",
                core_idea="仅从标题看，作者应该是在现有方法上提出了新的建模方式、训练策略或系统设计，用来改善这一方向的关键痛点。",
                method="建议优先打开 PDF 的方法图、引言和实验设置部分，这样最快能看清作者究竟改了模型、训练流程还是评测方案。",
                experiments="摘要未提供，暂时无法确认作者用了哪些数据集、任务设置或对比基线。",
                results="当前信息不足，不能负责任地判断它到底提升了性能、效率还是鲁棒性。",
                value=f"如果你正在跟踪 {paper.conference.upper()} {paper.year} 的 {topic} 研究，这篇论文仍然值得先放进待读列表。",
                verdict="目前信息还不够，但它看起来与当前检索主题高度相关，适合后续补读。",
                tags=self.tag_service.build_candidate_tags(paper),
            )
            return sections.to_markdown()

        sections = SummarySections(
            problem=f"这篇论文主要在解决{topic}里的核心痛点，重点想办法{goal}，也就是让这类系统更能用、更稳或更省。",
            core_idea=(
                f"从标题和摘要看，作者的核心想法不是简单调参，而是围绕 {title_display} 对关键模块做重新设计，"
                "希望用更直接的机制把问题卡点拆开处理。"
            ),
            method=(
                "作者大概率提出了一套新的模型结构、训练流程、推理策略或路由机制，"
                "并把这些设计组合成一个完整方案，而不是只改某一个小技巧。"
            ),
            experiments=experiments,
            results=results,
            value=(
                f"如果你在关注 {topic}，这篇论文的价值在于它不只是给出结论，还提供了一种可复用的解决思路。"
                "读它时优先看方法图、主表格和消融实验，会更快抓住重点。"
            ),
            verdict=f"这是一篇围绕{topic}、试图{goal}的工作，适合先看方法框架和主实验，再决定是否精读。",
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
            if text in {"这篇论文想解决什么", "核心思路", "方法怎么做", "用了什么数据与实验", "结果说明了什么", "为什么值得关注", "一句话判断"}:
                continue
            if len(text) > 88:
                return f"{text[:88].rstrip('，。；;、 ')}..."
            return text
        return ""

    def _should_request_structured_output(self) -> bool:
        return "openai.com" in self.settings.openai_base_url

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

    def _infer_experiments(self, paper: Paper) -> str:
        haystack = f"{paper.title} {paper.abstract}".lower()
        hints: list[str] = []
        if any(token in haystack for token in ("benchmark", "evaluation", "dataset", "task", "tasks")):
            hints.append("作者在公开任务或基准上做了对比实验")
        if any(token in haystack for token in ("simulation", "simulator", "robot", "control")):
            hints.append("实验里很可能包含仿真或控制场景")
        if any(token in haystack for token in ("real-world", "real world", "in-the-wild")):
            hints.append("摘要还暗示作者关注真实场景表现")
        if any(token in haystack for token in ("ablation", "analysis")):
            hints.append("并补了分析或消融来解释方法为什么有效")
        if not hints:
            return "摘要没有完整列出数据集名称，但可以判断作者至少做了和现有方法的对比实验，用来验证方案是否真正带来收益。"
        return f"{'，'.join(hints[:3])}。摘要没有把所有数据集名称展开，因此更细的实验设置还需要看正文。"

    def _infer_results(self, paper: Paper) -> str:
        haystack = f"{paper.title} {paper.abstract}".lower()
        hints: list[str] = []
        if any(token in haystack for token in ("state-of-the-art", "sota", "outperform", "superior", "better than", "improves over")):
            hints.append("结果指向性能优于已有方法")
        if any(token in haystack for token in ("efficient", "efficiency", "faster", "speed", "latency")):
            hints.append("同时强调了效率或速度上的改进")
        if any(token in haystack for token in ("robust", "robustness", "generalization", "generalize")):
            hints.append("还提到模型在泛化或稳定性上更可靠")
        if any(token in haystack for token in ("reduce", "lower", "less", "compression")):
            hints.append("并可能降低了算力、内存或误差成本")
        if not hints:
            return "摘要明确传达了实验结果是正向的，但没有把提升幅度写得很细；更值得去正文里看主表格和误差分析。"
        return f"{'；'.join(hints[:3])}。这说明它不是只讲想法，而是试图用实验证明方案确实更实用。"

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
