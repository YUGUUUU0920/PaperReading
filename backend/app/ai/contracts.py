from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class SummarySections:
    problem: str
    core_idea: str
    method: str
    experiments: str
    results: str
    value: str
    verdict: str
    tags: list[str] = field(default_factory=list)

    def to_markdown(self) -> str:
        return (
            "### 这篇论文想解决什么\n"
            f"{self.problem.strip()}\n\n"
            "### 核心思路\n"
            f"{self.core_idea.strip()}\n\n"
            "### 方法怎么做\n"
            f"{self.method.strip()}\n\n"
            "### 用了什么数据与实验\n"
            f"{self.experiments.strip()}\n\n"
            "### 结果说明了什么\n"
            f"{self.results.strip()}\n\n"
            "### 为什么值得关注\n"
            f"{self.value.strip()}\n\n"
            "### 一句话判断\n"
            f"{self.verdict.strip()}"
        )
