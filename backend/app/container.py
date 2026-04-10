from __future__ import annotations

from dataclasses import dataclass

from backend.app.core.config import Settings, get_settings
from backend.app.core.http_client import HttpClient
from backend.app.integrations.sources.acl import ACLSource
from backend.app.integrations.sources.iclr import ICLRSource
from backend.app.integrations.sources.icml import ICMLSource
from backend.app.integrations.sources.neurips import NeurIPSSource
from backend.app.jobs.refresh_scheduler import RefreshScheduler
from backend.app.repositories.sqlite import SqliteRepository
from backend.app.services.catalog_service import CatalogService
from backend.app.services.enrichment_service import EnrichmentService
from backend.app.services.paper_service import PaperService
from backend.app.services.summary_service import SummaryService
from backend.app.services.sync_service import SyncService
from backend.app.services.tag_service import TagService


@dataclass
class AppContainer:
    settings: Settings
    http_client: HttpClient
    repository: SqliteRepository
    catalog_service: CatalogService
    sync_service: SyncService
    tag_service: TagService
    enrichment_service: EnrichmentService
    summary_service: SummaryService
    paper_service: PaperService
    scheduler: RefreshScheduler


def build_container() -> AppContainer:
    settings = get_settings()
    http_client = HttpClient(settings)
    repository = SqliteRepository(settings.db_path)
    sources = {
        "acl": ACLSource(http_client),
        "neurips": NeurIPSSource(http_client),
        "iclr": ICLRSource(http_client),
        "icml": ICMLSource(http_client),
    }
    catalog_service = CatalogService(settings)
    sync_service = SyncService(settings, repository, sources)
    tag_service = TagService()
    enrichment_service = EnrichmentService(settings, http_client)
    summary_service = SummaryService(settings, http_client, tag_service)
    paper_service = PaperService(repository, sync_service, summary_service, enrichment_service, tag_service, sources)
    scheduler = RefreshScheduler(settings, sync_service)
    return AppContainer(
        settings=settings,
        http_client=http_client,
        repository=repository,
        catalog_service=catalog_service,
        sync_service=sync_service,
        tag_service=tag_service,
        enrichment_service=enrichment_service,
        summary_service=summary_service,
        paper_service=paper_service,
        scheduler=scheduler,
    )
