from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class SummarySections:
    problem: str
    method: str
    findings: str
    scenarios: str
    verdict: str
    tags: list[str] = field(default_factory=list)

    def to_markdown(self) -> str:
        return (
            "### 研究问题\n"
            f"{self.problem.strip()}\n\n"
            "### 方法概览\n"
            f"{self.method.strip()}\n\n"
            "### 主要发现\n"
            f"{self.findings.strip()}\n\n"
            "### 适用场景\n"
            f"{self.scenarios.strip()}\n\n"
            "### 一句话判断\n"
            f"{self.verdict.strip()}"
        )
