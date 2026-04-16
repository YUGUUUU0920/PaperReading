from __future__ import annotations

from collections import defaultdict
from math import log1p

from backend.app.core.utils import normalize_match_text, utc_now_iso
from backend.app.domain.entities import Paper
from backend.app.repositories.sqlite import SqliteRepository
from backend.app.services.catalog_service import CatalogService
from backend.app.services.summary_service import SummaryService
from backend.app.services.tag_service import THEME_PRIORITY, TagService


SIGNAL_TAGS = {
    "开源了代码",
    "开放获取",
    "开源模型",
    "含 OpenReview",
    "引用量高",
    "高被引",
    "新晋热门",
    "影响力强",
    "口头报告",
    "聚光论文",
    "补充收录",
}
FOCUS_SKIP_TAGS = SIGNAL_TAGS | {"人工智能", "数据集", "基准评测", "评测分析"}
BRANCH_LANES = (-2, -1, 1, 2)


class LineageService:
    def __init__(
        self,
        repository: SqliteRepository,
        tag_service: TagService,
        summary_service: SummaryService,
    ):
        self.repository = repository
        self.tag_service = tag_service
        self.summary_service = summary_service
        self.conference_labels = {
            item["code"]: item["label"] for item in CatalogService.CONFERENCES
        }

    def list_lineages(self, *, theme: str = "", limit: int = 6) -> dict:
        papers = self.repository.list_matching_papers()
        coverage = self._build_coverage(papers)
        grouped = self._group_by_theme(papers, theme=theme)
        ranked_themes = self._rank_themes(grouped)

        items: list[dict] = []
        for theme_name, _ in ranked_themes:
            lineage = self._build_theme_lineage(theme_name, grouped.get(theme_name, []))
            if not lineage:
                continue
            items.append(lineage)
            if len(items) >= max(1, limit):
                break

        return {
            "items": items,
            "count": len(items),
            "available_themes": [theme_name for theme_name, _ in ranked_themes],
            "coverage": coverage,
            "generated_at": utc_now_iso(),
        }

    def _group_by_theme(
        self,
        papers: list[Paper],
        *,
        theme: str = "",
    ) -> dict[str, list[tuple[Paper, list[str]]]]:
        selected_theme = theme.strip()
        grouped: dict[str, list[tuple[Paper, list[str]]]] = defaultdict(list)
        for paper in papers:
            tags = self.tag_service.build_tags(paper)
            primary_theme = self.tag_service.primary_theme(tags=tags)
            if selected_theme and primary_theme != selected_theme:
                continue
            grouped[primary_theme].append((paper, tags))
        return grouped

    def _rank_themes(
        self,
        grouped: dict[str, list[tuple[Paper, list[str]]]],
    ) -> list[tuple[str, tuple[int, int, float, int]]]:
        ranked: list[tuple[str, tuple[int, int, float, int]]] = []
        for theme_name, themed_papers in grouped.items():
            if theme_name == "人工智能" and len(grouped) > 3:
                continue
            years = {paper.year for paper, _ in themed_papers}
            if len(themed_papers) < 3:
                continue
            impact = sum(
                sorted(
                    (self._importance_score(paper, tags) for paper, tags in themed_papers),
                    reverse=True,
                )[:4]
            )
            theme_order = THEME_PRIORITY.index(theme_name) if theme_name in THEME_PRIORITY else len(THEME_PRIORITY)
            ranked.append(
                (
                    theme_name,
                    (
                        len(years),
                        len(themed_papers),
                        round(impact, 2),
                        -theme_order,
                    ),
                )
            )
        ranked.sort(key=lambda item: item[1], reverse=True)
        return ranked

    def _build_theme_lineage(
        self,
        theme_name: str,
        themed_papers: list[tuple[Paper, list[str]]],
    ) -> dict | None:
        if len(themed_papers) < 3:
            return None

        papers_by_year: dict[int, list[tuple[Paper, list[str]]]] = defaultdict(list)
        for paper, tags in themed_papers:
            papers_by_year[paper.year].append((paper, tags))

        years = sorted(papers_by_year)
        if len(years) < 2 and len(themed_papers) < 6:
            return None

        focus_tag = self._dominant_focus_tag(theme_name, themed_papers)

        selected_by_year: dict[int, list[tuple[Paper, list[str]]]] = {}
        for year in years:
            ranked = sorted(
                papers_by_year[year],
                key=lambda item: (-self._selection_score(item[0], item[1], focus_tag), item[0].title.lower()),
            )
            budget = 3 if len(ranked) >= 12 else 2
            selected_by_year[year] = ranked[:budget]

        trunk: list[tuple[Paper, list[str]]] = []
        for year in years:
            candidates = selected_by_year[year]
            if not candidates:
                continue
            if not trunk:
                trunk.append(candidates[0])
                continue
            previous_paper, previous_tags = trunk[-1]
            next_paper = max(
                candidates,
                key=lambda item: self._connection_score(previous_paper, item[0], previous_tags, item[1])
                + self._selection_score(item[0], item[1], focus_tag) * 0.28,
            )
            trunk.append(next_paper)

        if not trunk:
            return None

        selected_lookup: dict[int, tuple[Paper, list[str]]] = {}
        for candidates in selected_by_year.values():
            for paper, tags in candidates:
                if paper.id is not None:
                    selected_lookup[paper.id] = (paper, tags)

        trunk_ids = {paper.id for paper, _ in trunk if paper.id is not None}
        branch_candidates = [
            item
            for item in selected_lookup.values()
            if item[0].id is not None and item[0].id not in trunk_ids
        ]
        branch_candidates.sort(
            key=lambda item: (item[0].year, -self._selection_score(item[0], item[1], focus_tag), item[0].title.lower())
        )

        year_lane_counts: dict[int, int] = defaultdict(int)
        node_lookup: dict[int, dict] = {}
        nodes: list[dict] = []
        links: list[dict] = []
        year_index = {year: index for index, year in enumerate(years)}

        previous_trunk_id: int | None = None
        for index, (paper, tags) in enumerate(trunk):
            if paper.id is None:
                continue
            node = self._serialize_node(
                paper,
                tags,
                theme_name=theme_name,
                year_index=year_index.get(paper.year, 0),
                lane=0,
                kind="trunk",
                phase=self._trunk_phase_label(index, len(trunk)),
                parent_id=previous_trunk_id,
            )
            nodes.append(node)
            node_lookup[paper.id] = node
            if previous_trunk_id is not None:
                previous = node_lookup.get(previous_trunk_id)
                if previous:
                    links.append(
                        {
                            "from": previous_trunk_id,
                            "to": paper.id,
                            "kind": "trunk",
                            "strength": round(
                                self._connection_score(
                                    previous["_paper"],
                                    paper,
                                    previous["_tags"],
                                    tags,
                                ),
                                2,
                            ),
                        }
                    )
            previous_trunk_id = paper.id

        for paper, tags in branch_candidates:
            if paper.id is None:
                continue
            parents = [
                candidate
                for candidate, candidate_tags in trunk
                if candidate.id is not None and candidate.year <= paper.year and candidate.id != paper.id
            ]
            if not parents:
                parents = [trunk[0][0]]
            parent = max(
                parents,
                key=lambda candidate: self._connection_score(
                    candidate,
                    paper,
                    node_lookup.get(candidate.id, {}).get("_tags", self.tag_service.build_tags(candidate)),
                    tags,
                ),
            )
            lane_index = year_lane_counts[paper.year]
            year_lane_counts[paper.year] += 1
            lane = self._lane_for_index(lane_index)
            node = self._serialize_node(
                paper,
                tags,
                theme_name=theme_name,
                year_index=year_index.get(paper.year, 0),
                lane=lane,
                kind="branch",
                phase="分支",
                parent_id=parent.id,
            )
            nodes.append(node)
            node_lookup[paper.id] = node
            if parent.id is not None:
                links.append(
                    {
                        "from": parent.id,
                        "to": paper.id,
                        "kind": "branch",
                        "strength": round(
                            self._connection_score(
                                parent,
                                paper,
                                node_lookup.get(parent.id, {}).get("_tags", self.tag_service.build_tags(parent)),
                                tags,
                            ),
                            2,
                        ),
                    }
                )

        nodes.sort(key=lambda item: (item["year"], abs(item["lane"]), item["lane"], item["title"].lower()))
        cleaned_nodes = [self._strip_internal_fields(item) for item in nodes]

        return {
            "theme": theme_name,
            "focus_tag": focus_tag,
            "story": self._build_story(theme_name, trunk, focus_tag=focus_tag),
            "summary": self._build_summary(theme_name, themed_papers, trunk, focus_tag=focus_tag),
            "coverage": {
                "paper_count": len(themed_papers),
                "milestone_count": len(cleaned_nodes),
                "years": years,
                "year_count": len(years),
                "conferences": self._conference_labels(themed_papers),
            },
            "years": years,
            "nodes": cleaned_nodes,
            "links": links,
            "highlights": self._build_highlights(cleaned_nodes),
            "latest_year": max(years),
        }

    def _serialize_node(
        self,
        paper: Paper,
        tags: list[str],
        *,
        theme_name: str,
        year_index: int,
        lane: int,
        kind: str,
        phase: str,
        parent_id: int | None,
    ) -> dict:
        title_payload = paper.to_dict()
        citation_count = int(paper.metadata.get("citation_count") or 0)
        signals: list[str] = []
        if citation_count:
            signals.append(f"被引 {citation_count}")
        if paper.metadata.get("code_url"):
            signals.append("附代码")
        if paper.metadata.get("top_10_percent_cited"):
            signals.append("高影响力")
        track_label = self._track_label(paper.track)
        if track_label not in {"未分类", "会议论文", "论文集收录"}:
            signals.append(track_label)
        return {
            "id": paper.id,
            "paper_id": paper.id,
            "parent_id": parent_id,
            "conference": paper.conference,
            "conference_label": self.conference_labels.get(paper.conference, paper.conference.upper()),
            "year": paper.year,
            "year_index": year_index,
            "lane": lane,
            "kind": kind,
            "phase": phase,
            "theme": theme_name,
            "title": paper.title,
            "title_display": title_payload["title_display"],
            "authors_text": ", ".join(paper.authors),
            "track_label": track_label,
            "summary_preview": self.summary_service.build_preview(paper),
            "tags": tags[:5],
            "citation_count": citation_count,
            "signals": signals[:3],
            "paper_url": paper.paper_url,
            "pdf_url": paper.pdf_url,
            "_paper": paper,
            "_tags": tags,
        }

    def _strip_internal_fields(self, node: dict) -> dict:
        payload = dict(node)
        payload.pop("_paper", None)
        payload.pop("_tags", None)
        return payload

    def _build_coverage(self, papers: list[Paper]) -> dict:
        datasets = self.repository.list_tracked_datasets()
        return {
            "paper_count": len(papers),
            "dataset_count": len(datasets),
            "datasets": [dataset.to_dict() for dataset in datasets],
            "years": sorted({paper.year for paper in papers}),
        }

    def _conference_labels(self, themed_papers: list[tuple[Paper, list[str]]]) -> list[str]:
        labels = {self.conference_labels.get(paper.conference, paper.conference.upper()) for paper, _ in themed_papers}
        return sorted(labels)

    def _importance_score(self, paper: Paper, tags: list[str]) -> float:
        metadata = paper.metadata or {}
        citations = int(metadata.get("citation_count") or 0)
        score = log1p(max(citations, 0)) * 5
        if metadata.get("top_10_percent_cited"):
            score += 8
        if metadata.get("code_url"):
            score += 2
        if metadata.get("open_access"):
            score += 1
        track = paper.track.lower()
        if "oral" in track:
            score += 6
        elif "spotlight" in track:
            score += 4
        elif "findings" in track:
            score += 1.5
        if "高被引" in tags:
            score += 4
        elif "引用量高" in tags:
            score += 2.5
        elif "新晋热门" in tags:
            score += 1.5
        return round(score, 2)

    def _selection_score(self, paper: Paper, tags: list[str], focus_tag: str) -> float:
        score = self._importance_score(paper, tags)
        conceptual_tags = [tag for tag in tags if tag not in FOCUS_SKIP_TAGS and tag != paper.conference]
        score += min(len(conceptual_tags), 3) * 0.9
        if focus_tag and focus_tag in tags:
            score += 5.5
        if paper.abstract.strip():
            score += 0.8
        return round(score, 2)

    def _connection_score(
        self,
        left: Paper,
        right: Paper,
        left_tags: list[str],
        right_tags: list[str],
    ) -> float:
        tag_overlap = len(set(left_tags) & set(right_tags))
        left_title_terms = self._title_terms(left.title)
        right_title_terms = self._title_terms(right.title)
        title_overlap = len(left_title_terms & right_title_terms)
        left_focus_terms = self._focus_terms(left)
        right_focus_terms = self._focus_terms(right)
        focus_overlap = len(left_focus_terms & right_focus_terms)
        left_authors = {normalize_match_text(author) for author in left.authors if author.strip()}
        right_authors = {normalize_match_text(author) for author in right.authors if author.strip()}
        author_overlap = len(left_authors & right_authors)
        year_gap = max(right.year - left.year, 0)
        recency_bonus = 1 / (1 + year_gap)
        return round(tag_overlap * 3 + title_overlap * 1.8 + focus_overlap * 0.35 + author_overlap * 2 + recency_bonus, 2)

    def _build_story(
        self,
        theme_name: str,
        trunk: list[tuple[Paper, list[str]]],
        *,
        focus_tag: str = "",
    ) -> str:
        first_paper, first_tags = trunk[0]
        first_title = first_paper.to_dict()["title_display"]
        if len(trunk) == 1:
            focus = self._focus_label(first_tags, theme_name, focus_tag=focus_tag)
            return f"{first_paper.year} 年的《{first_title}》奠定了这条 {theme_name} 线索的观察起点，重点围绕 {focus} 展开。"

        last_paper, last_tags = trunk[-1]
        last_title = last_paper.to_dict()["title_display"]
        first_focus = self._focus_label(first_tags, theme_name, focus_tag=focus_tag)
        last_focus = self._focus_label(last_tags, theme_name, focus_tag=focus_tag)
        return (
            f"这条脉络从 {first_paper.year} 年的《{first_title}》起步，先把 {first_focus} 推到前台，"
            f"随后逐步延展到 {last_paper.year} 年《{last_title}》所代表的 {last_focus}。"
        )

    def _build_summary(
        self,
        theme_name: str,
        themed_papers: list[tuple[Paper, list[str]]],
        trunk: list[tuple[Paper, list[str]]],
        *,
        focus_tag: str = "",
    ) -> str:
        conferences = self._conference_labels(themed_papers)
        years = sorted({paper.year for paper, _ in themed_papers})
        latest_focus = self._focus_label(trunk[-1][1], theme_name, focus_tag=focus_tag)
        return (
            f"当前收录的 {theme_name} 脉络横跨 {years[0]} 到 {years[-1]} 年，覆盖 {'、'.join(conferences)}。"
            f"这条线更适合从“{latest_focus}”这一视角切入，再顺着主干节点往前回看。"
        )

    def _focus_label(self, tags: list[str], theme_name: str, *, focus_tag: str = "") -> str:
        if focus_tag and focus_tag in tags:
            return focus_tag
        focus_tags = [tag for tag in tags if tag not in FOCUS_SKIP_TAGS and tag != theme_name]
        if focus_tags:
            return "、".join(focus_tags[:2])
        return "方法设计与实验结果"

    def _dominant_focus_tag(
        self,
        theme_name: str,
        themed_papers: list[tuple[Paper, list[str]]],
    ) -> str:
        counts: dict[str, int] = defaultdict(int)
        year_coverage: dict[str, set[int]] = defaultdict(set)
        for paper, tags in themed_papers:
            for tag in tags:
                if tag == theme_name or tag in FOCUS_SKIP_TAGS:
                    continue
                counts[tag] += 1
                year_coverage[tag].add(paper.year)
        ranked = sorted(
            counts,
            key=lambda tag: (len(year_coverage[tag]), counts[tag], -THEME_PRIORITY.index(tag) if tag in THEME_PRIORITY else 0, tag),
            reverse=True,
        )
        return ranked[0] if ranked else ""

    def _focus_terms(self, paper: Paper) -> set[str]:
        text = normalize_match_text(f"{paper.title} {paper.abstract}")
        return {term for term in text.split() if len(term) >= 4}

    def _title_terms(self, value: str) -> set[str]:
        text = normalize_match_text(value)
        return {term for term in text.split() if len(term) >= 3}

    def _lane_for_index(self, index: int) -> int:
        base = BRANCH_LANES[index % len(BRANCH_LANES)]
        tier = index // len(BRANCH_LANES)
        if tier == 0:
            return base
        direction = -1 if base < 0 else 1
        return base + direction * tier * 2

    def _trunk_phase_label(self, index: int, total: int) -> str:
        if index == 0:
            return "起点"
        if index == total - 1:
            return "最新"
        if index == 1:
            return "扩展"
        return "推进"

    def _track_label(self, track: str) -> str:
        lowered = track.strip().lower()
        if not lowered:
            return "未分类"
        if "oral" in lowered:
            return "口头报告"
        if "spotlight" in lowered:
            return "聚光论文"
        if "findings" in lowered:
            return "补充收录"
        if "poster" in lowered:
            return "海报展示"
        if "proceedings" in lowered:
            return "论文集收录"
        if "conference" in lowered:
            return "会议论文"
        return track

    def _build_highlights(self, nodes: list[dict]) -> list[dict]:
        if not nodes:
            return []
        trunk_nodes = [node for node in nodes if node.get("kind") == "trunk"]
        branch_nodes = [node for node in nodes if node.get("kind") == "branch"]
        candidates: list[tuple[str, dict]] = []
        if trunk_nodes:
            candidates.append(("起点", trunk_nodes[0]))
            candidates.append(("最新推进", trunk_nodes[-1]))
        if branch_nodes:
            breakout = max(
                branch_nodes,
                key=lambda node: (int(node.get("citation_count") or 0), node.get("year") or 0, node.get("title", "")),
            )
            candidates.append(("代表分支", breakout))

        highlights: list[dict] = []
        seen_ids: set[int] = set()
        for label, node in candidates:
            node_id = int(node.get("id") or 0)
            if node_id in seen_ids:
                continue
            seen_ids.add(node_id)
            highlights.append(
                {
                    "label": label,
                    "paper_id": node.get("paper_id"),
                    "title": node.get("title"),
                    "title_display": node.get("title_display"),
                    "conference": node.get("conference"),
                    "year": node.get("year"),
                    "tags": node.get("tags", [])[:3],
                    "summary_preview": node.get("summary_preview", ""),
                }
            )
        return highlights
