from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from backend.app.core.utils import utc_now_iso
from backend.app.domain.entities import DatasetStatus, Paper


class SqliteRepository:
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS papers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source TEXT NOT NULL,
                    conference TEXT NOT NULL,
                    year INTEGER NOT NULL,
                    track TEXT NOT NULL,
                    external_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    authors_json TEXT NOT NULL,
                    authors_text TEXT NOT NULL,
                    abstract TEXT NOT NULL DEFAULT '',
                    paper_url TEXT NOT NULL DEFAULT '',
                    pdf_url TEXT NOT NULL DEFAULT '',
                    summary TEXT NOT NULL DEFAULT '',
                    summary_model TEXT NOT NULL DEFAULT '',
                    metadata_json TEXT NOT NULL DEFAULT '{}',
                    last_synced_at TEXT NOT NULL DEFAULT '',
                    summary_updated_at TEXT NOT NULL DEFAULT '',
                    UNIQUE(source, external_id)
                );

                CREATE INDEX IF NOT EXISTS idx_papers_conference_year
                ON papers(conference, year);

                CREATE INDEX IF NOT EXISTS idx_papers_title
                ON papers(title);

                CREATE TABLE IF NOT EXISTS datasets (
                    conference TEXT NOT NULL,
                    year INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    item_count INTEGER NOT NULL DEFAULT 0,
                    last_synced_at TEXT NOT NULL DEFAULT '',
                    last_error TEXT NOT NULL DEFAULT '',
                    updated_at TEXT NOT NULL DEFAULT '',
                    PRIMARY KEY (conference, year)
                );
                """
            )

    def upsert_papers(self, papers: list[Paper]) -> None:
        if not papers:
            return

        rows = [
            (
                paper.source,
                paper.conference,
                paper.year,
                paper.track,
                paper.external_id,
                paper.title,
                json.dumps(paper.authors, ensure_ascii=False),
                ", ".join(paper.authors),
                paper.abstract,
                paper.paper_url,
                paper.pdf_url,
                paper.summary,
                paper.summary_model,
                json.dumps(paper.metadata, ensure_ascii=False),
                paper.last_synced_at,
                paper.summary_updated_at,
            )
            for paper in papers
        ]

        with self._connect() as connection:
            connection.executemany(
                """
                INSERT INTO papers (
                    source, conference, year, track, external_id, title,
                    authors_json, authors_text, abstract, paper_url, pdf_url,
                    summary, summary_model, metadata_json, last_synced_at, summary_updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(source, external_id) DO UPDATE SET
                    conference = excluded.conference,
                    year = excluded.year,
                    track = excluded.track,
                    title = excluded.title,
                    authors_json = excluded.authors_json,
                    authors_text = excluded.authors_text,
                    abstract = CASE
                        WHEN excluded.abstract <> '' THEN excluded.abstract
                        ELSE papers.abstract
                    END,
                    paper_url = excluded.paper_url,
                    pdf_url = CASE
                        WHEN excluded.pdf_url <> '' THEN excluded.pdf_url
                        ELSE papers.pdf_url
                    END,
                    metadata_json = excluded.metadata_json,
                    last_synced_at = excluded.last_synced_at
                """,
                rows,
            )

    def search_papers(
        self,
        *,
        query: str = "",
        conference: str = "",
        year: int | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Paper]:
        where_sql, params = self._build_search_where(query=query, conference=conference, year=year)
        params.extend([max(limit, 1), max(offset, 0)])

        with self._connect() as connection:
            rows = connection.execute(
                f"""
                SELECT *
                FROM papers
                {where_sql}
                ORDER BY year DESC, conference ASC, title COLLATE NOCASE ASC
                LIMIT ?
                OFFSET ?
                """,
                params,
            ).fetchall()
        return [self._row_to_paper(row) for row in rows]

    def count_search_papers(
        self,
        *,
        query: str = "",
        conference: str = "",
        year: int | None = None,
    ) -> int:
        where_sql, params = self._build_search_where(query=query, conference=conference, year=year)
        with self._connect() as connection:
            row = connection.execute(
                f"""
                SELECT COUNT(*) AS count
                FROM papers
                {where_sql}
                """,
                params,
            ).fetchone()
        return int(row["count"]) if row else 0

    def count_papers(self, *, conference: str, year: int) -> int:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT COUNT(*) AS count FROM papers WHERE conference = ? AND year = ?",
                (conference.lower(), year),
            ).fetchone()
        return int(row["count"]) if row else 0

    def _build_search_where(
        self,
        *,
        query: str = "",
        conference: str = "",
        year: int | None = None,
    ) -> tuple[str, list[object]]:
        clauses = []
        params: list[object] = []

        if query.strip():
            clauses.append("(title LIKE ? OR authors_text LIKE ? OR abstract LIKE ?)")
            pattern = f"%{query.strip()}%"
            params.extend([pattern, pattern, pattern])

        if conference.strip():
            clauses.append("conference = ?")
            params.append(conference.strip().lower())

        if year:
            clauses.append("year = ?")
            params.append(year)

        where_sql = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        return where_sql, params

    def get_paper(self, paper_id: int) -> Paper | None:
        with self._connect() as connection:
            row = connection.execute("SELECT * FROM papers WHERE id = ?", (paper_id,)).fetchone()
        if not row:
            return None
        return self._row_to_paper(row)

    def update_paper_details(
        self,
        paper_id: int,
        *,
        abstract: str | None = None,
        pdf_url: str | None = None,
        metadata: dict | None = None,
        last_synced_at: str | None = None,
    ) -> None:
        current = self.get_paper(paper_id)
        if not current:
            return
        merged_metadata = dict(current.metadata)
        if metadata:
            merged_metadata.update(metadata)

        with self._connect() as connection:
            connection.execute(
                """
                UPDATE papers
                SET abstract = ?,
                    pdf_url = ?,
                    metadata_json = ?,
                    last_synced_at = ?
                WHERE id = ?
                """,
                (
                    abstract if abstract is not None else current.abstract,
                    pdf_url if pdf_url is not None else current.pdf_url,
                    json.dumps(merged_metadata, ensure_ascii=False),
                    last_synced_at or current.last_synced_at,
                    paper_id,
                ),
            )

    def update_summary(self, paper_id: int, summary: str, summary_model: str, summary_updated_at: str) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                UPDATE papers
                SET summary = ?, summary_model = ?, summary_updated_at = ?
                WHERE id = ?
                """,
                (summary, summary_model, summary_updated_at, paper_id),
            )

    def get_dataset(self, conference: str, year: int) -> DatasetStatus | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM datasets WHERE conference = ? AND year = ?",
                (conference.lower(), year),
            ).fetchone()
        if not row:
            return None
        return self._row_to_dataset(row)

    def upsert_dataset(self, dataset: DatasetStatus) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO datasets (
                    conference, year, status, item_count, last_synced_at, last_error, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(conference, year) DO UPDATE SET
                    status = excluded.status,
                    item_count = excluded.item_count,
                    last_synced_at = excluded.last_synced_at,
                    last_error = excluded.last_error,
                    updated_at = excluded.updated_at
                """,
                (
                    dataset.conference.lower(),
                    dataset.year,
                    dataset.status,
                    dataset.item_count,
                    dataset.last_synced_at,
                    dataset.last_error,
                    dataset.updated_at,
                ),
            )

    def list_tracked_datasets(self) -> list[DatasetStatus]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT *
                FROM datasets
                WHERE item_count > 0 OR status = 'ready'
                ORDER BY updated_at DESC
                """
            ).fetchall()
        return [self._row_to_dataset(row) for row in rows]

    def ensure_dataset_from_existing_data(self, conference: str, year: int) -> DatasetStatus | None:
        count = self.count_papers(conference=conference, year=year)
        if count <= 0:
            return None
        status = DatasetStatus(
            conference=conference.lower(),
            year=year,
            status="ready",
            item_count=count,
            last_synced_at=utc_now_iso(),
            last_error="",
            updated_at=utc_now_iso(),
        )
        self.upsert_dataset(status)
        return status

    def _row_to_paper(self, row: sqlite3.Row) -> Paper:
        return Paper(
            id=row["id"],
            source=row["source"],
            conference=row["conference"],
            year=row["year"],
            track=row["track"],
            external_id=row["external_id"],
            title=row["title"],
            authors=json.loads(row["authors_json"]),
            abstract=row["abstract"],
            paper_url=row["paper_url"],
            pdf_url=row["pdf_url"],
            summary=row["summary"],
            summary_model=row["summary_model"],
            metadata=json.loads(row["metadata_json"]),
            last_synced_at=row["last_synced_at"],
            summary_updated_at=row["summary_updated_at"],
        )

    def _row_to_dataset(self, row: sqlite3.Row) -> DatasetStatus:
        return DatasetStatus(
            conference=row["conference"],
            year=row["year"],
            status=row["status"],
            item_count=row["item_count"],
            last_synced_at=row["last_synced_at"],
            last_error=row["last_error"],
            updated_at=row["updated_at"],
        )
