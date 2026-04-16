from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from backend.app.core.utils import utc_now_iso
from backend.app.domain.entities import DatasetStatus, Paper, PaperComment, ViewerProfile


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

                CREATE TABLE IF NOT EXISTS saved_entries (
                    paper_id INTEGER NOT NULL,
                    list_type TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT '',
                    updated_at TEXT NOT NULL DEFAULT '',
                    PRIMARY KEY (paper_id, list_type)
                );

                CREATE INDEX IF NOT EXISTS idx_saved_entries_list_type
                ON saved_entries(list_type, updated_at DESC);

                CREATE TABLE IF NOT EXISTS profiles (
                    id TEXT PRIMARY KEY,
                    display_name TEXT NOT NULL,
                    profile_type TEXT NOT NULL DEFAULT 'guest',
                    auth_provider TEXT NOT NULL DEFAULT '',
                    external_auth_id TEXT NOT NULL DEFAULT '',
                    avatar_url TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL DEFAULT '',
                    updated_at TEXT NOT NULL DEFAULT ''
                );

                CREATE TABLE IF NOT EXISTS comments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    paper_id INTEGER NOT NULL,
                    profile_id TEXT NOT NULL,
                    source TEXT NOT NULL DEFAULT 'user',
                    content TEXT NOT NULL,
                    parent_comment_id INTEGER,
                    created_at TEXT NOT NULL DEFAULT '',
                    updated_at TEXT NOT NULL DEFAULT '',
                    sort_order INTEGER NOT NULL DEFAULT 0
                );

                CREATE INDEX IF NOT EXISTS idx_comments_paper
                ON comments(paper_id, sort_order ASC, created_at ASC);

                CREATE TABLE IF NOT EXISTS comment_likes (
                    comment_id INTEGER NOT NULL,
                    profile_id TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT '',
                    PRIMARY KEY (comment_id, profile_id)
                );

                CREATE TABLE IF NOT EXISTS oauth_states (
                    state TEXT PRIMARY KEY,
                    return_path TEXT NOT NULL DEFAULT '/',
                    created_at TEXT NOT NULL DEFAULT ''
                );

                CREATE TABLE IF NOT EXISTS auth_sessions (
                    token TEXT PRIMARY KEY,
                    profile_id TEXT NOT NULL,
                    return_path TEXT NOT NULL DEFAULT '/',
                    created_at TEXT NOT NULL DEFAULT '',
                    expires_at TEXT NOT NULL DEFAULT ''
                );
                """
            )
            self._ensure_saved_entry_columns(connection)
            self._ensure_profile_columns(connection)
            self._ensure_comment_columns(connection)

    def upsert_papers(self, papers: list[Paper]) -> None:
        if not papers:
            return

        existing_metadata = self._load_existing_metadata(papers)
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
                json.dumps(self._merge_metadata(existing_metadata.get((paper.source, paper.external_id), {}), paper.metadata), ensure_ascii=False),
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
                    paper_url = CASE
                        WHEN excluded.paper_url <> '' THEN excluded.paper_url
                        ELSE papers.paper_url
                    END,
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

    def list_matching_papers(
        self,
        *,
        query: str = "",
        conference: str = "",
        year: int | None = None,
    ) -> list[Paper]:
        where_sql, params = self._build_search_where(query=query, conference=conference, year=year)
        with self._connect() as connection:
            rows = connection.execute(
                f"""
                SELECT *
                FROM papers
                {where_sql}
                ORDER BY year DESC, conference ASC, title COLLATE NOCASE ASC
                """,
                params,
            ).fetchall()
        return [self._row_to_paper(row) for row in rows]

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

    def set_saved_state(self, paper_id: int, list_type: str, enabled: bool) -> None:
        normalized = list_type.strip().lower()
        if normalized not in {"favorite", "reading"}:
            raise ValueError(f"Unsupported list_type: {list_type}")
        timestamp = utc_now_iso()
        with self._connect() as connection:
            if enabled:
                connection.execute(
                    """
                    INSERT INTO saved_entries (paper_id, list_type, created_at, updated_at)
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT(paper_id, list_type) DO UPDATE SET
                        updated_at = excluded.updated_at
                    """,
                    (paper_id, normalized, timestamp, timestamp),
                )
            else:
                connection.execute(
                    "DELETE FROM saved_entries WHERE paper_id = ? AND list_type = ?",
                    (paper_id, normalized),
                )

    def update_saved_entry(
        self,
        paper_id: int,
        list_type: str,
        *,
        group_name: str = "",
        note: str = "",
        is_read: bool = False,
    ) -> None:
        normalized = list_type.strip().lower()
        if normalized not in {"favorite", "reading"}:
            raise ValueError(f"Unsupported list_type: {list_type}")
        timestamp = utc_now_iso()
        group_value = group_name.strip()
        note_value = note.strip()
        read_updated_at = timestamp if is_read else ""
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO saved_entries (
                    paper_id, list_type, created_at, updated_at, group_name, note, is_read, read_updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(paper_id, list_type) DO UPDATE SET
                    updated_at = excluded.updated_at,
                    group_name = excluded.group_name,
                    note = excluded.note,
                    is_read = excluded.is_read,
                    read_updated_at = CASE
                        WHEN saved_entries.is_read <> excluded.is_read THEN excluded.read_updated_at
                        ELSE saved_entries.read_updated_at
                    END
                """,
                (
                    paper_id,
                    normalized,
                    timestamp,
                    timestamp,
                    group_value,
                    note_value,
                    1 if is_read else 0,
                    read_updated_at,
                ),
            )

    def get_saved_states(self, paper_ids: list[int]) -> dict[int, set[str]]:
        if not paper_ids:
            return {}
        placeholders = ",".join("?" for _ in paper_ids)
        with self._connect() as connection:
            rows = connection.execute(
                f"""
                SELECT paper_id, list_type
                FROM saved_entries
                WHERE paper_id IN ({placeholders})
                """,
                paper_ids,
            ).fetchall()
        states: dict[int, set[str]] = {}
        for row in rows:
            states.setdefault(int(row["paper_id"]), set()).add(str(row["list_type"]))
        return states

    def get_saved_entries(self, paper_ids: list[int]) -> dict[int, dict[str, dict]]:
        if not paper_ids:
            return {}
        placeholders = ",".join("?" for _ in paper_ids)
        with self._connect() as connection:
            rows = connection.execute(
                f"""
                SELECT *
                FROM saved_entries
                WHERE paper_id IN ({placeholders})
                """,
                paper_ids,
            ).fetchall()
        payload: dict[int, dict[str, dict]] = {}
        for row in rows:
            payload.setdefault(int(row["paper_id"]), {})[str(row["list_type"])] = self._row_to_saved_entry(row)
        return payload

    def list_saved_papers(self, list_type: str) -> list[Paper]:
        normalized = list_type.strip().lower()
        if normalized not in {"favorite", "reading"}:
            raise ValueError(f"Unsupported list_type: {list_type}")
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT p.*
                FROM saved_entries AS s
                JOIN papers AS p
                    ON p.id = s.paper_id
                WHERE s.list_type = ?
                ORDER BY s.updated_at DESC, p.year DESC, p.title COLLATE NOCASE ASC
                """,
                (normalized,),
            ).fetchall()
        return [self._row_to_paper(row) for row in rows]

    def count_saved(self, list_type: str) -> int:
        normalized = list_type.strip().lower()
        if normalized not in {"favorite", "reading"}:
            raise ValueError(f"Unsupported list_type: {list_type}")
        with self._connect() as connection:
            row = connection.execute(
                "SELECT COUNT(*) AS count FROM saved_entries WHERE list_type = ?",
                (normalized,),
            ).fetchone()
        return int(row["count"]) if row else 0

    def get_profile(self, profile_id: str) -> ViewerProfile | None:
        normalized = profile_id.strip()
        if not normalized:
            return None
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM profiles WHERE id = ?",
                (normalized,),
            ).fetchone()
        if not row:
            return None
        return self._row_to_profile(row)

    def get_profile_by_auth(self, auth_provider: str, external_auth_id: str) -> ViewerProfile | None:
        if not auth_provider.strip() or not external_auth_id.strip():
            return None
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT *
                FROM profiles
                WHERE auth_provider = ? AND external_auth_id = ?
                """,
                (auth_provider.strip(), external_auth_id.strip()),
            ).fetchone()
        if not row:
            return None
        return self._row_to_profile(row)

    def upsert_profile(self, profile: ViewerProfile) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO profiles (
                    id, display_name, profile_type, auth_provider, avatar_url, external_auth_id, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    display_name = excluded.display_name,
                    profile_type = excluded.profile_type,
                    auth_provider = excluded.auth_provider,
                    avatar_url = excluded.avatar_url,
                    external_auth_id = excluded.external_auth_id,
                    updated_at = excluded.updated_at
                """,
                (
                    profile.id,
                    profile.display_name,
                    profile.profile_type,
                    profile.auth_provider,
                    profile.avatar_url,
                    profile.external_auth_id,
                    profile.created_at,
                    profile.updated_at,
                ),
            )

    def update_profile_name(self, profile_id: str, display_name: str) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                UPDATE profiles
                SET display_name = ?, updated_at = ?
                WHERE id = ?
                """,
                (display_name, utc_now_iso(), profile_id),
            )

    def create_oauth_state(self, state: str, return_path: str) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT OR REPLACE INTO oauth_states (state, return_path, created_at)
                VALUES (?, ?, ?)
                """,
                (state, return_path, utc_now_iso()),
            )

    def consume_oauth_state(self, state: str) -> str | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT return_path FROM oauth_states WHERE state = ?",
                (state,),
            ).fetchone()
            connection.execute("DELETE FROM oauth_states WHERE state = ?", (state,))
        return str(row["return_path"]) if row else None

    def create_auth_session(self, token: str, profile_id: str, return_path: str, expires_at: str) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT OR REPLACE INTO auth_sessions (token, profile_id, return_path, created_at, expires_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (token, profile_id, return_path, utc_now_iso(), expires_at),
            )

    def consume_auth_session(self, token: str) -> tuple[str, str] | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT profile_id, return_path, expires_at FROM auth_sessions WHERE token = ?",
                (token,),
            ).fetchone()
            connection.execute("DELETE FROM auth_sessions WHERE token = ?", (token,))
        if not row:
            return None
        expires_at = str(row["expires_at"] or "")
        if expires_at and expires_at < utc_now_iso():
            return None
        return str(row["profile_id"]), str(row["return_path"])

    def get_comment(self, comment_id: int, *, viewer_id: str = "") -> PaperComment | None:
        with self._connect() as connection:
            row = connection.execute(
                f"""
                SELECT c.*, p.display_name, p.profile_type, p.avatar_url,
                       p.auth_provider,
                       COALESCE(likes.like_count, 0) AS like_count,
                       CASE WHEN viewer.profile_id IS NULL THEN 0 ELSE 1 END AS liked_by_viewer
                FROM comments AS c
                JOIN profiles AS p
                    ON p.id = c.profile_id
                LEFT JOIN (
                    SELECT comment_id, COUNT(*) AS like_count
                    FROM comment_likes
                    GROUP BY comment_id
                ) AS likes
                    ON likes.comment_id = c.id
                LEFT JOIN (
                    SELECT comment_id, profile_id
                    FROM comment_likes
                    WHERE profile_id = ?
                ) AS viewer
                    ON viewer.comment_id = c.id
                WHERE c.id = ?
                """,
                (viewer_id.strip(), comment_id),
            ).fetchone()
        if not row:
            return None
        return self._row_to_comment(row)

    def list_comments(self, paper_id: int, *, viewer_id: str = "") -> list[PaperComment]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT c.*, p.display_name, p.profile_type, p.avatar_url,
                       p.auth_provider,
                       COALESCE(likes.like_count, 0) AS like_count,
                       CASE WHEN viewer.profile_id IS NULL THEN 0 ELSE 1 END AS liked_by_viewer
                FROM comments AS c
                JOIN profiles AS p
                    ON p.id = c.profile_id
                LEFT JOIN (
                    SELECT comment_id, COUNT(*) AS like_count
                    FROM comment_likes
                    GROUP BY comment_id
                ) AS likes
                    ON likes.comment_id = c.id
                LEFT JOIN (
                    SELECT comment_id, profile_id
                    FROM comment_likes
                    WHERE profile_id = ?
                ) AS viewer
                    ON viewer.comment_id = c.id
                WHERE c.paper_id = ?
                ORDER BY
                    CASE WHEN c.source = 'seed' THEN 0 ELSE 1 END ASC,
                    COALESCE(c.parent_comment_id, c.id) ASC,
                    CASE WHEN c.parent_comment_id IS NULL THEN 0 ELSE 1 END ASC,
                    c.sort_order ASC,
                    c.created_at ASC,
                    c.id ASC
                """,
                (viewer_id.strip(), paper_id),
            ).fetchall()
        return [self._row_to_comment(row) for row in rows]

    def count_comments(self, paper_id: int) -> int:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT COUNT(*) AS count FROM comments WHERE paper_id = ?",
                (paper_id,),
            ).fetchone()
        return int(row["count"]) if row else 0

    def has_seed_comments(self, paper_id: int) -> bool:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT 1 FROM comments WHERE paper_id = ? AND source = 'seed' LIMIT 1",
                (paper_id,),
            ).fetchone()
        return row is not None

    def add_comment(
        self,
        *,
        paper_id: int,
        profile_id: str,
        source: str,
        content: str,
        parent_comment_id: int | None = None,
        sort_order: int = 0,
    ) -> PaperComment:
        timestamp = utc_now_iso()
        with self._connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO comments (
                    paper_id, profile_id, source, content, parent_comment_id, created_at, updated_at, sort_order
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    paper_id,
                    profile_id,
                    source,
                    content,
                    parent_comment_id,
                    timestamp,
                    timestamp,
                    sort_order,
                ),
            )
            row = connection.execute(
                """
                SELECT c.*, p.display_name, p.profile_type, p.avatar_url,
                       p.auth_provider,
                       COALESCE(likes.like_count, 0) AS like_count,
                       0 AS liked_by_viewer
                FROM comments AS c
                JOIN profiles AS p
                    ON p.id = c.profile_id
                LEFT JOIN (
                    SELECT comment_id, COUNT(*) AS like_count
                    FROM comment_likes
                    GROUP BY comment_id
                ) AS likes
                    ON likes.comment_id = c.id
                WHERE c.id = ?
                """,
                (cursor.lastrowid,),
            ).fetchone()
        if not row:
            raise RuntimeError("Failed to insert comment")
        return self._row_to_comment(row)

    def set_comment_like(self, comment_id: int, profile_id: str, enabled: bool) -> None:
        with self._connect() as connection:
            if enabled:
                connection.execute(
                    """
                    INSERT OR IGNORE INTO comment_likes (comment_id, profile_id, created_at)
                    VALUES (?, ?, ?)
                    """,
                    (comment_id, profile_id, utc_now_iso()),
                )
            else:
                connection.execute(
                    "DELETE FROM comment_likes WHERE comment_id = ? AND profile_id = ?",
                    (comment_id, profile_id),
                )

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

    def _row_to_profile(self, row: sqlite3.Row) -> ViewerProfile:
        return ViewerProfile(
            id=str(row["id"]),
            display_name=str(row["display_name"]),
            profile_type=str(row["profile_type"] or "guest"),
            auth_provider=str(row["auth_provider"] or ""),
            external_auth_id=str(row["external_auth_id"] or ""),
            avatar_url=str(row["avatar_url"] or ""),
            created_at=str(row["created_at"] or ""),
            updated_at=str(row["updated_at"] or ""),
        )

    def _row_to_comment(self, row: sqlite3.Row) -> PaperComment:
        return PaperComment(
            id=int(row["id"]),
            paper_id=int(row["paper_id"]),
            profile_id=str(row["profile_id"]),
            display_name=str(row["display_name"]),
            profile_type=str(row["profile_type"] or "guest"),
            source=str(row["source"] or "user"),
            content=str(row["content"] or ""),
            auth_provider=str(row["auth_provider"] or ""),
            avatar_url=str(row["avatar_url"] or ""),
            parent_comment_id=int(row["parent_comment_id"]) if row["parent_comment_id"] is not None else None,
            like_count=int(row["like_count"] or 0),
            liked_by_viewer=bool(row["liked_by_viewer"]),
            created_at=str(row["created_at"] or ""),
            updated_at=str(row["updated_at"] or ""),
            sort_order=int(row["sort_order"] or 0),
        )

    def _load_existing_metadata(self, papers: list[Paper]) -> dict[tuple[str, str], dict]:
        keys_by_source: dict[str, set[str]] = {}
        for paper in papers:
            keys_by_source.setdefault(paper.source, set()).add(paper.external_id)

        result: dict[tuple[str, str], dict] = {}
        with self._connect() as connection:
            for source, external_ids in keys_by_source.items():
                if not external_ids:
                    continue
                placeholders = ",".join("?" for _ in external_ids)
                rows = connection.execute(
                    f"""
                    SELECT source, external_id, metadata_json
                    FROM papers
                    WHERE source = ? AND external_id IN ({placeholders})
                    """,
                    [source, *external_ids],
                ).fetchall()
                for row in rows:
                    try:
                        metadata = json.loads(row["metadata_json"] or "{}")
                    except json.JSONDecodeError:
                        metadata = {}
                    result[(row["source"], row["external_id"])] = metadata if isinstance(metadata, dict) else {}
        return result

    def _merge_metadata(self, existing: dict, incoming: dict) -> dict:
        merged = dict(existing or {})
        merged.update(incoming or {})
        return merged

    def _ensure_saved_entry_columns(self, connection: sqlite3.Connection) -> None:
        rows = connection.execute("PRAGMA table_info(saved_entries)").fetchall()
        columns = {str(row["name"]) for row in rows}
        additions = {
            "group_name": "TEXT NOT NULL DEFAULT ''",
            "note": "TEXT NOT NULL DEFAULT ''",
            "is_read": "INTEGER NOT NULL DEFAULT 0",
            "read_updated_at": "TEXT NOT NULL DEFAULT ''",
        }
        for name, definition in additions.items():
            if name not in columns:
                connection.execute(f"ALTER TABLE saved_entries ADD COLUMN {name} {definition}")

    def _ensure_profile_columns(self, connection: sqlite3.Connection) -> None:
        rows = connection.execute("PRAGMA table_info(profiles)").fetchall()
        columns = {str(row["name"]) for row in rows}
        additions = {
            "auth_provider": "TEXT NOT NULL DEFAULT ''",
            "external_auth_id": "TEXT NOT NULL DEFAULT ''",
            "avatar_url": "TEXT NOT NULL DEFAULT ''",
        }
        for name, definition in additions.items():
            if name not in columns:
                connection.execute(f"ALTER TABLE profiles ADD COLUMN {name} {definition}")

    def _ensure_comment_columns(self, connection: sqlite3.Connection) -> None:
        rows = connection.execute("PRAGMA table_info(comments)").fetchall()
        columns = {str(row["name"]) for row in rows}
        additions = {
            "parent_comment_id": "INTEGER",
        }
        for name, definition in additions.items():
            if name not in columns:
                connection.execute(f"ALTER TABLE comments ADD COLUMN {name} {definition}")

    def _row_to_saved_entry(self, row: sqlite3.Row) -> dict:
        return {
            "enabled": True,
            "list_type": str(row["list_type"]),
            "group_name": str(row["group_name"] or ""),
            "note": str(row["note"] or ""),
            "is_read": bool(row["is_read"]),
            "created_at": str(row["created_at"] or ""),
            "updated_at": str(row["updated_at"] or ""),
            "read_updated_at": str(row["read_updated_at"] or ""),
        }
