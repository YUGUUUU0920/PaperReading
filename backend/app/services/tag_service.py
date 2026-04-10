from __future__ import annotations

from backend.app.domain.entities import Paper


TAG_RULES = [
    ("large language model", "大模型"),
    ("language model", "大模型"),
    ("llm", "大模型"),
    ("vision-language", "多模态"),
    ("multimodal", "多模态"),
    ("retrieval augmented generation", "RAG"),
    ("retrieval-augmented", "RAG"),
    ("rag", "RAG"),
    ("agent", "智能体"),
    ("reinforcement learning", "强化学习"),
    ("bandit", "强化学习"),
    ("policy optimization", "强化学习"),
    ("diffusion", "扩散模型"),
    ("graph", "图学习"),
    ("video", "视频理解"),
    ("audio", "语音音频"),
    ("speech", "语音音频"),
    ("time series", "时间序列"),
    ("forecast", "时间序列"),
    ("robot", "机器人"),
    ("federated", "联邦学习"),
    ("recommendation", "推荐系统"),
    ("reasoning", "推理"),
    ("alignment", "对齐"),
    ("code generation", "代码生成"),
    ("program synthesis", "代码生成"),
    ("privacy", "隐私安全"),
    ("security", "隐私安全"),
    ("medical", "医疗AI"),
    ("clinical", "医疗AI"),
    ("health", "医疗AI"),
    ("benchmark", "基准评测"),
    ("dataset", "数据集"),
    ("evaluation", "评测分析"),
    ("world model", "世界模型"),
]

CONCEPT_RULES = [
    ("artificial intelligence", "人工智能"),
    ("computer vision", "计算机视觉"),
    ("natural language processing", "自然语言处理"),
    ("robotics", "机器人"),
    ("reinforcement learning", "强化学习"),
]

TAG_CATALOG = [
    "大模型",
    "多模态",
    "RAG",
    "智能体",
    "强化学习",
    "扩散模型",
    "图学习",
    "视频理解",
    "语音音频",
    "时间序列",
    "机器人",
    "联邦学习",
    "推荐系统",
    "推理",
    "对齐",
    "代码生成",
    "隐私安全",
    "医疗AI",
    "基准评测",
    "数据集",
    "评测分析",
    "世界模型",
    "计算机视觉",
    "自然语言处理",
    "开源了代码",
    "开放获取",
    "开源模型",
    "含 OpenReview",
    "引用量高",
    "高被引",
    "新晋热门",
    "影响力强",
    "口头报告",
    "Spotlight",
    "Findings",
]


class TagService:
    def catalog_tags(self) -> list[str]:
        return TAG_CATALOG[:]

    def build_tags(self, paper: Paper) -> list[str]:
        metadata = paper.metadata or {}
        haystack = f"{paper.title} {paper.abstract}".lower()
        tags: list[str] = []

        self._append(tags, self._resource_tags(metadata))
        self._append(tags, self._impact_tags(paper.year, metadata))

        for keyword, tag in TAG_RULES:
            if keyword in haystack:
                self._append(tags, [tag])

        for concept in metadata.get("concepts_en", []):
            lowered = str(concept).lower()
            for keyword, tag in CONCEPT_RULES:
                if keyword in lowered:
                    self._append(tags, [tag])

        track = paper.track.lower()
        if "oral" in track:
            self._append(tags, ["口头报告"])
        if "spotlight" in track:
            self._append(tags, ["Spotlight"])
        if "findings" in track:
            self._append(tags, ["Findings"])

        if not tags:
            self._append(tags, ["人工智能"])
        return tags[:8]

    def build_candidate_tags(self, paper: Paper) -> list[str]:
        return self.build_tags(paper)

    def _resource_tags(self, metadata: dict) -> list[str]:
        tags: list[str] = []
        code_url = str(metadata.get("code_url", "")).strip()
        if code_url:
            self._append(tags, ["开源了代码"])
        if metadata.get("open_access"):
            self._append(tags, ["开放获取"])
        for resource in metadata.get("resource_links", []) or []:
            kind = str(resource.get("kind", "")).lower()
            if kind == "huggingface":
                self._append(tags, ["开源模型"])
            if kind == "openreview":
                self._append(tags, ["含 OpenReview"])
        return tags

    def _impact_tags(self, year: int, metadata: dict) -> list[str]:
        tags: list[str] = []
        citations = int(metadata.get("citation_count") or 0)
        if citations >= 200:
            self._append(tags, ["高被引"])
        elif citations >= 60:
            self._append(tags, ["引用量高"])
        elif year >= 2025 and citations >= 15:
            self._append(tags, ["新晋热门"])
        if metadata.get("top_10_percent_cited"):
            self._append(tags, ["影响力强"])
        return tags

    def _append(self, target: list[str], values: list[str]) -> None:
        for value in values:
            if value and value not in target:
                target.append(value)
