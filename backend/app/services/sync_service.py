from __future__ import annotations

from datetime import datetime, timezone

from backend.app.core.config import Settings
from backend.app.core.utils import utc_now_iso
from backend.app.domain.entities import DatasetStatus
from backend.app.integrations.sources.base import ConferenceSource
from backend.app.repositories.sqlite import SqliteRepository


class SyncService:
    def __init__(self, settings: Settings, repository: SqliteRepository, sources: dict[str, ConferenceSource]):
        self.settings = settings
        self.repository = repository
        self.sources = sources

    def ensure_dataset_loaded(self, conference: str, year: int, force: bool = False) -> DatasetStatus:
        code = conference.lower()
        existing = self.repository.get_dataset(code, year) or self.repository.ensure_dataset_from_existing_data(code, year)
        if existing and not force and existing.item_count > 0 and not self._is_stale(existing.last_synced_at):
            return existing
        return self.refresh_dataset(code, year)

    def refresh_dataset(self, conference: str, year: int) -> DatasetStatus:
        code = conference.lower()
        if code not in self.sources:
            raise ValueError(f"Unsupported conference: {conference}")

        syncing = DatasetStatus(
            conference=code,
            year=year,
            status="syncing",
            item_count=self.repository.count_papers(conference=code, year=year),
            last_synced_at=self.repository.get_dataset(code, year).last_synced_at if self.repository.get_dataset(code, year) else "",
            last_error="",
            updated_at=utc_now_iso(),
        )
        self.repository.upsert_dataset(syncing)

        try:
            papers = self.sources[code].fetch_listing(year)
            self.repository.upsert_papers(papers)
            status = DatasetStatus(
                conference=code,
                year=year,
                status="ready",
                item_count=len(papers),
                last_synced_at=utc_now_iso(),
                last_error="",
                updated_at=utc_now_iso(),
            )
            self.repository.upsert_dataset(status)
            return status
        except Exception as exc:
            failed = DatasetStatus(
                conference=code,
                year=year,
                status="error",
                item_count=self.repository.count_papers(conference=code, year=year),
                last_synced_at=self.repository.get_dataset(code, year).last_synced_at if self.repository.get_dataset(code, year) else "",
                last_error=str(exc),
                updated_at=utc_now_iso(),
            )
            self.repository.upsert_dataset(failed)
            raise

    def refresh_stale_datasets(self) -> None:
        for dataset in self.repository.list_tracked_datasets():
            if self._is_stale(dataset.last_synced_at):
                try:
                    self.refresh_dataset(dataset.conference, dataset.year)
                except Exception:
                    continue

    def _is_stale(self, value: str) -> bool:
        if not value:
            return True
        try:
            synced_at = datetime.fromisoformat(value)
        except ValueError:
            return True
        age_seconds = (datetime.now(timezone.utc) - synced_at).total_seconds()
        return age_seconds > self.settings.refresh_ttl_hours * 3600

