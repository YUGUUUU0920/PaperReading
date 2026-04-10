# Data Sources

## Official Conference Sources

- ACL: `https://aclanthology.org/events/acl-{year}/`
- ICML: `https://proceedings.mlr.press/v{volume}/`
- ICLR: `https://proceedings.iclr.cc/paper_files/paper/{year}`
- NeurIPS:
  - 2024 and earlier: `https://proceedings.neurips.cc/paper/{year}`
  - 2025 and later: `https://neurips.cc/virtual/{year}/papers.html`

## Supported Years

- ACL: 2024, 2025
- NeurIPS: 2024, 2025
- ICML: 2023, 2024, 2025
- ICLR: 2024, 2025

## Enrichment Sources

- OpenAlex for citation count, open access, and topic signals.

## Source Adapter Rules

- Prefer official proceedings or official conference portals.
- Extract structured links such as OpenReview, GitHub, GitLab, and Hugging Face when available.
- Preserve cached enrichment metadata during future refreshes.
