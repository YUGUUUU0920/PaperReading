#!/usr/bin/env python3
"""
Codex-native search and recommendation interface for the vendored UI style library.

Adapted from nextlevelbuilder/ui-ux-pro-max-skill (MIT):
https://github.com/nextlevelbuilder/ui-ux-pro-max-skill
"""

from __future__ import annotations

import argparse
import csv
import json
import re
from collections import defaultdict
from math import log
from pathlib import Path


DATA_DIR = (
    Path(__file__).resolve().parent.parent
    / "vendor"
    / "ui-ux-pro-max"
    / "data"
)
MAX_RESULTS = 5

CSV_CONFIG = {
    "style": {
        "file": "styles.csv",
        "search_cols": [
            "Style Category",
            "Keywords",
            "Best For",
            "Type",
            "AI Prompt Keywords",
        ],
        "output_cols": [
            "Style Category",
            "Type",
            "Keywords",
            "Primary Colors",
            "Secondary Colors",
            "Effects & Animation",
            "Best For",
            "Light Mode ✓",
            "Dark Mode ✓",
            "Performance",
            "Accessibility",
            "Mobile-Friendly",
            "Framework Compatibility",
            "Complexity",
            "Implementation Checklist",
            "Design System Variables",
        ],
    },
    "color": {
        "file": "colors.csv",
        "search_cols": ["Product Type", "Notes"],
        "output_cols": [
            "Product Type",
            "Primary",
            "On Primary",
            "Secondary",
            "On Secondary",
            "Accent",
            "On Accent",
            "Background",
            "Foreground",
            "Card",
            "Card Foreground",
            "Muted",
            "Muted Foreground",
            "Border",
            "Destructive",
            "On Destructive",
            "Ring",
            "Notes",
        ],
    },
    "product": {
        "file": "products.csv",
        "search_cols": [
            "Product Type",
            "Keywords",
            "Primary Style Recommendation",
            "Secondary Styles",
            "Landing Page Pattern",
            "Key Considerations",
        ],
        "output_cols": [
            "Product Type",
            "Primary Style Recommendation",
            "Secondary Styles",
            "Landing Page Pattern",
            "Dashboard Style (if applicable)",
            "Color Palette Focus",
            "Key Considerations",
        ],
    },
    "landing": {
        "file": "landing.csv",
        "search_cols": [
            "Pattern Name",
            "Keywords",
            "Conversion Optimization",
            "Section Order",
        ],
        "output_cols": [
            "Pattern Name",
            "Section Order",
            "Primary CTA Placement",
            "Color Strategy",
            "Recommended Effects",
            "Conversion Optimization",
        ],
    },
    "typography": {
        "file": "typography.csv",
        "search_cols": [
            "Font Pairing Name",
            "Category",
            "Heading Font",
            "Body Font",
            "Mood/Style Keywords",
            "Best For",
        ],
        "output_cols": [
            "Font Pairing Name",
            "Category",
            "Heading Font",
            "Body Font",
            "Mood/Style Keywords",
            "Best For",
            "Google Fonts URL",
            "CSS Import",
            "Tailwind Config",
            "Notes",
        ],
    },
    "ux": {
        "file": "ux-guidelines.csv",
        "search_cols": ["Category", "Issue", "Description", "Platform"],
        "output_cols": [
            "Category",
            "Issue",
            "Platform",
            "Description",
            "Do",
            "Don't",
            "Severity",
        ],
    },
    "chart": {
        "file": "charts.csv",
        "search_cols": [
            "Data Type",
            "Keywords",
            "Best Chart Type",
            "When to Use",
            "When NOT to Use",
            "Accessibility Notes",
        ],
        "output_cols": [
            "Data Type",
            "Best Chart Type",
            "Secondary Options",
            "When to Use",
            "When NOT to Use",
            "Data Volume Threshold",
            "Color Guidance",
            "Accessibility Grade",
            "A11y Fallback",
            "Library Recommendation",
            "Interactive Level",
        ],
    },
    "web": {
        "file": "app-interface.csv",
        "search_cols": ["Category", "Issue", "Keywords", "Description"],
        "output_cols": [
            "Category",
            "Issue",
            "Platform",
            "Description",
            "Do",
            "Don't",
            "Severity",
        ],
    },
    "react": {
        "file": "react-performance.csv",
        "search_cols": ["Category", "Issue", "Keywords", "Description"],
        "output_cols": [
            "Category",
            "Issue",
            "Platform",
            "Description",
            "Do",
            "Don't",
            "Severity",
        ],
    },
    "icons": {
        "file": "icons.csv",
        "search_cols": ["Category", "Icon Name", "Keywords", "Best For"],
        "output_cols": [
            "Category",
            "Icon Name",
            "Keywords",
            "Library",
            "Usage",
            "Best For",
            "Style",
        ],
    },
    "google-fonts": {
        "file": "google-fonts.csv",
        "search_cols": [
            "Family",
            "Category",
            "Stroke",
            "Classifications",
            "Keywords",
            "Subsets",
            "Designers",
        ],
        "output_cols": [
            "Family",
            "Category",
            "Stroke",
            "Classifications",
            "Styles",
            "Variable Axes",
            "Subsets",
            "Designers",
            "Popularity Rank",
            "Google Fonts URL",
        ],
    },
}

STACK_CONFIG = {
    "react": "react.csv",
    "nextjs": "nextjs.csv",
    "vue": "vue.csv",
    "svelte": "svelte.csv",
    "astro": "astro.csv",
    "swiftui": "swiftui.csv",
    "react-native": "react-native.csv",
    "flutter": "flutter.csv",
    "nuxtjs": "nuxtjs.csv",
    "nuxt-ui": "nuxt-ui.csv",
    "html-tailwind": "html-tailwind.csv",
    "shadcn": "shadcn.csv",
    "jetpack-compose": "jetpack-compose.csv",
    "threejs": "threejs.csv",
    "angular": "angular.csv",
    "laravel": "laravel.csv",
}

STACK_COLS = {
    "search_cols": ["Category", "Guideline", "Description", "Do", "Don't"],
    "output_cols": [
        "Category",
        "Guideline",
        "Description",
        "Do",
        "Don't",
        "Severity",
        "Docs URL",
    ],
}

DOMAIN_HINTS = {
    "color": [
        "color",
        "palette",
        "semantic",
        "accent",
        "foreground",
        "background",
        "token",
    ],
    "chart": [
        "chart",
        "graph",
        "trend",
        "bar",
        "line",
        "heatmap",
        "visualization",
    ],
    "landing": [
        "landing",
        "hero",
        "cta",
        "pricing",
        "testimonial",
        "conversion",
    ],
    "product": [
        "saas",
        "dashboard",
        "crm",
        "marketplace",
        "portfolio",
        "fintech",
        "research",
        "reading",
    ],
    "style": [
        "style",
        "visual",
        "aesthetic",
        "glassmorphism",
        "minimalism",
        "brutalism",
        "editorial",
        "dashboard",
    ],
    "ux": [
        "ux",
        "accessibility",
        "mobile",
        "touch",
        "keyboard",
        "navigation",
        "loading",
    ],
    "typography": ["font", "type", "typography", "headline", "body copy"],
    "icons": ["icon", "glyph", "symbol", "lucide", "heroicons"],
    "react": ["react", "next", "waterfall", "rerender", "suspense"],
    "web": ["aria", "focus", "form", "input", "semantic", "autocomplete"],
}

REASONING_FILE = DATA_DIR / "ui-reasoning.csv"


class BM25:
    def __init__(self, k1: float = 1.5, b: float = 0.75) -> None:
        self.k1 = k1
        self.b = b
        self.corpus: list[list[str]] = []
        self.doc_lengths: list[int] = []
        self.avg_doc_length = 0.0
        self.idf: dict[str, float] = {}
        self.doc_freqs: dict[str, int] = defaultdict(int)

    @staticmethod
    def tokenize(text: str) -> list[str]:
        normalized = re.sub(r"[^\w\s#-]", " ", str(text).lower())
        return [token for token in normalized.split() if len(token) > 1]

    def fit(self, documents: list[str]) -> None:
        self.corpus = [self.tokenize(document) for document in documents]
        if not self.corpus:
            return

        self.doc_lengths = [len(document) for document in self.corpus]
        self.avg_doc_length = sum(self.doc_lengths) / len(self.doc_lengths)

        for document in self.corpus:
            seen: set[str] = set()
            for token in document:
                if token not in seen:
                    self.doc_freqs[token] += 1
                    seen.add(token)

        total_docs = len(self.corpus)
        for token, freq in self.doc_freqs.items():
            self.idf[token] = log((total_docs - freq + 0.5) / (freq + 0.5) + 1)

    def score(self, query: str) -> list[tuple[int, float]]:
        query_tokens = self.tokenize(query)
        ranked: list[tuple[int, float]] = []
        for index, document in enumerate(self.corpus):
            doc_length = self.doc_lengths[index]
            frequencies: dict[str, int] = defaultdict(int)
            for token in document:
                frequencies[token] += 1

            score = 0.0
            for token in query_tokens:
                if token not in self.idf:
                    continue
                term_frequency = frequencies[token]
                numerator = term_frequency * (self.k1 + 1)
                denominator = term_frequency + self.k1 * (
                    1 - self.b + self.b * doc_length / max(self.avg_doc_length, 1)
                )
                score += self.idf[token] * numerator / max(denominator, 1e-9)
            ranked.append((index, score))
        return sorted(ranked, key=lambda item: item[1], reverse=True)


def load_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def row_document(row: dict[str, str], columns: list[str]) -> str:
    return " ".join(str(row.get(column, "")) for column in columns)


def search_table(
    path: Path,
    search_cols: list[str],
    output_cols: list[str],
    query: str,
    limit: int,
) -> list[dict[str, str]]:
    rows = load_csv(path)
    documents = [row_document(row, search_cols) for row in rows]
    engine = BM25()
    engine.fit(documents)
    ranked = engine.score(query)

    results: list[dict[str, str]] = []
    for index, score in ranked[:limit]:
        if score <= 0:
            continue
        row = rows[index]
        trimmed = {column: row.get(column, "") for column in output_cols if column in row}
        results.append(trimmed)
    return results


def detect_domain(query: str) -> str:
    query_lower = query.lower()
    scores = {
        domain: sum(1 for hint in hints if hint in query_lower)
        for domain, hints in DOMAIN_HINTS.items()
    }
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "style"


def search(query: str, domain: str | None = None, limit: int = MAX_RESULTS) -> dict:
    chosen_domain = domain or detect_domain(query)
    config = CSV_CONFIG[chosen_domain]
    path = DATA_DIR / config["file"]
    results = search_table(path, config["search_cols"], config["output_cols"], query, limit)
    return {
        "mode": "domain",
        "domain": chosen_domain,
        "query": query,
        "file": str(path.relative_to(DATA_DIR.parent.parent)),
        "count": len(results),
        "results": results,
    }


def search_stack(query: str, stack: str, limit: int = MAX_RESULTS) -> dict:
    filename = STACK_CONFIG[stack]
    path = DATA_DIR / "stacks" / filename
    results = search_table(
        path,
        STACK_COLS["search_cols"],
        STACK_COLS["output_cols"],
        query,
        limit,
    )
    return {
        "mode": "stack",
        "stack": stack,
        "query": query,
        "file": str(path.relative_to(DATA_DIR.parent.parent)),
        "count": len(results),
        "results": results,
    }


def load_reasoning() -> list[dict[str, str]]:
    if not REASONING_FILE.exists():
        return []
    return load_csv(REASONING_FILE)


def find_reasoning_rule(category: str, rows: list[dict[str, str]]) -> dict[str, str]:
    category_lower = category.lower()

    for row in rows:
        if row.get("UI_Category", "").lower() == category_lower:
            return row

    for row in rows:
        ui_category = row.get("UI_Category", "").lower()
        if ui_category and (ui_category in category_lower or category_lower in ui_category):
            return row

    for row in rows:
        ui_category = row.get("UI_Category", "").lower()
        keywords = ui_category.replace("/", " ").replace("-", " ").split()
        if any(keyword and keyword in category_lower for keyword in keywords):
            return row

    return {}


def parse_style_priority(value: str) -> list[str]:
    return [item.strip() for item in value.split("+") if item.strip()]


def select_priority_match(
    results: list[dict[str, str]],
    priority_keywords: list[str],
    key: str,
) -> dict[str, str]:
    if not results:
        return {}
    if not priority_keywords:
        return results[0]

    best_row = results[0]
    best_score = -1
    for row in results:
        haystack = json.dumps(row, ensure_ascii=False).lower()
        score = 0
        for keyword in priority_keywords:
            normalized = keyword.lower()
            if normalized in row.get(key, "").lower():
                score += 10
            elif normalized in haystack:
                score += 2
        if score > best_score:
            best_score = score
            best_row = row
    return best_row


def first_result(result: dict) -> dict[str, str]:
    rows = result.get("results", [])
    return rows[0] if rows else {}


def recommend(query: str, project_name: str | None = None) -> dict:
    product_result = search(query, "product", limit=3)
    product_match = first_result(product_result)
    product_type = product_match.get("Product Type", "General")

    reasoning_rows = load_reasoning()
    reasoning_row = find_reasoning_rule(product_type, reasoning_rows)
    style_priority = parse_style_priority(reasoning_row.get("Style_Priority", ""))
    landing_hint = reasoning_row.get("Recommended_Pattern", "")
    typography_mood = reasoning_row.get("Typography_Mood", "")

    style_query = " ".join(part for part in [query, " ".join(style_priority[:2])] if part).strip()
    color_query = product_type if product_type != "General" else query
    typography_query = " ".join(part for part in [query, typography_mood] if part).strip()
    landing_query = landing_hint or query

    style_result = search(style_query or query, "style", limit=4)
    color_result = search(color_query, "color", limit=3)
    typography_result = search(typography_query or query, "typography", limit=3)
    landing_result = search(landing_query, "landing", limit=3)

    best_style = select_priority_match(
        style_result.get("results", []),
        style_priority,
        "Style Category",
    )
    best_color = first_result(color_result)
    best_typography = first_result(typography_result)
    best_landing = first_result(landing_result)

    decision_rules = {}
    raw_rules = reasoning_row.get("Decision_Rules", "")
    if raw_rules:
        try:
            decision_rules = json.loads(raw_rules)
        except json.JSONDecodeError:
            decision_rules = {"raw": raw_rules}

    return {
        "query": query,
        "project_name": project_name or query,
        "product_type": product_type,
        "product_match": product_match,
        "style_priority": style_priority,
        "style": best_style,
        "colors": best_color,
        "typography": best_typography,
        "landing": best_landing,
        "reasoning": {
            "recommended_pattern": landing_hint,
            "color_mood": reasoning_row.get("Color_Mood", ""),
            "typography_mood": typography_mood,
            "key_effects": reasoning_row.get("Key_Effects", ""),
            "anti_patterns": reasoning_row.get("Anti_Patterns", ""),
            "severity": reasoning_row.get("Severity", "MEDIUM"),
            "decision_rules": decision_rules,
        },
        "next_searches": [
            f"search '{query}' --domain ux",
            f"search '{query}' --domain react",
        ],
    }


def truncate(value: str, limit: int = 220) -> str:
    text = str(value).strip()
    return text if len(text) <= limit else text[: limit - 3] + "..."


def format_search_markdown(result: dict) -> str:
    label = result.get("stack") or result.get("domain")
    lines = [
        "# Frontend Design Library Search",
        f"- Query: {result['query']}",
        f"- Target: {label}",
        f"- Source: {result['file']}",
        f"- Matches: {result['count']}",
        "",
    ]
    for index, row in enumerate(result.get("results", []), start=1):
        lines.append(f"## Match {index}")
        for key, value in row.items():
            if not value:
                continue
            lines.append(f"- {key}: {truncate(value)}")
        lines.append("")
    return "\n".join(lines).strip()


def format_recommendation_markdown(result: dict) -> str:
    product = result.get("product_match", {})
    style = result.get("style", {})
    colors = result.get("colors", {})
    typography = result.get("typography", {})
    landing = result.get("landing", {})
    reasoning = result.get("reasoning", {})

    lines = [
        "# Frontend Direction Recommendation",
        f"- Project: {result['project_name']}",
        f"- Query: {result['query']}",
        f"- Product type: {result['product_type']}",
        "",
        "## Product Fit",
    ]
    for key in [
        "Primary Style Recommendation",
        "Secondary Styles",
        "Landing Page Pattern",
        "Dashboard Style (if applicable)",
        "Color Palette Focus",
        "Key Considerations",
    ]:
        if product.get(key):
            lines.append(f"- {key}: {truncate(product[key])}")

    lines.extend(["", "## Style Direction"])
    if result.get("style_priority"):
        lines.append(f"- Style Priority: {', '.join(result['style_priority'])}")
    for key in [
        "Style Category",
        "Keywords",
        "Effects & Animation",
        "Best For",
        "Accessibility",
        "Framework Compatibility",
        "Design System Variables",
    ]:
        if style.get(key):
            lines.append(f"- {key}: {truncate(style[key])}")

    lines.extend(["", "## Color System"])
    for key in [
        "Primary",
        "Secondary",
        "Accent",
        "Background",
        "Foreground",
        "Border",
        "Notes",
    ]:
        if colors.get(key):
            lines.append(f"- {key}: {truncate(colors[key])}")

    lines.extend(["", "## Typography"])
    for key in [
        "Font Pairing Name",
        "Heading Font",
        "Body Font",
        "Mood/Style Keywords",
        "Best For",
    ]:
        if typography.get(key):
            lines.append(f"- {key}: {truncate(typography[key])}")

    lines.extend(["", "## Layout Pattern"])
    for key in [
        "Pattern Name",
        "Section Order",
        "Primary CTA Placement",
        "Recommended Effects",
        "Conversion Optimization",
    ]:
        if landing.get(key):
            lines.append(f"- {key}: {truncate(landing[key])}")

    lines.extend(["", "## Reasoning Guardrails"])
    for key, label in [
        ("color_mood", "Color Mood"),
        ("typography_mood", "Typography Mood"),
        ("key_effects", "Key Effects"),
        ("anti_patterns", "Anti-patterns"),
        ("severity", "Severity"),
    ]:
        if reasoning.get(key):
            lines.append(f"- {label}: {truncate(reasoning[key])}")

    decision_rules = reasoning.get("decision_rules") or {}
    if decision_rules:
        lines.append("- Decision Rules:")
        for rule_key, value in decision_rules.items():
            lines.append(f"  - {rule_key}: {truncate(value)}")

    lines.extend(["", "## Next Searches"])
    for item in result.get("next_searches", []):
        lines.append(f"- {item}")

    return "\n".join(lines).strip()


def domain_summary() -> list[dict[str, str]]:
    items = []
    for domain, config in CSV_CONFIG.items():
        path = DATA_DIR / config["file"]
        rows = load_csv(path)
        items.append(
            {
                "name": domain,
                "file": config["file"],
                "rows": str(len(rows)),
            }
        )

    stack_names = ", ".join(sorted(STACK_CONFIG))
    items.append(
        {
            "name": "stacks",
            "file": "stacks/*.csv",
            "rows": stack_names,
        }
    )
    return items


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Search and recommend from the vendored frontend design library."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    search_parser = subparsers.add_parser("search", help="Search a domain or stack")
    search_parser.add_argument("query")
    search_parser.add_argument("--domain", choices=sorted(CSV_CONFIG))
    search_parser.add_argument("--stack", choices=sorted(STACK_CONFIG))
    search_parser.add_argument("--limit", type=int, default=MAX_RESULTS)
    search_parser.add_argument("--json", action="store_true")

    recommend_parser = subparsers.add_parser(
        "recommend",
        aliases=["design-system"],
        help="Recommend a product-fit visual direction",
    )
    recommend_parser.add_argument("query")
    recommend_parser.add_argument("--project-name")
    recommend_parser.add_argument("--json", action="store_true")

    domains_parser = subparsers.add_parser("domains", help="List supported domains")
    domains_parser.add_argument("--json", action="store_true")

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "search":
        if args.domain and args.stack:
            parser.error("--domain and --stack cannot be used together")
        result = (
            search_stack(args.query, args.stack, args.limit)
            if args.stack
            else search(args.query, args.domain, args.limit)
        )
        print(
            json.dumps(result, ensure_ascii=False, indent=2)
            if args.json
            else format_search_markdown(result)
        )
        return 0

    if args.command in {"recommend", "design-system"}:
        result = recommend(args.query, args.project_name)
        print(
            json.dumps(result, ensure_ascii=False, indent=2)
            if args.json
            else format_recommendation_markdown(result)
        )
        return 0

    summary = domain_summary()
    print(json.dumps(summary, ensure_ascii=False, indent=2) if args.json else "\n".join(
        f"- {item['name']}: {item['file']} ({item['rows']})" for item in summary
    ))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
