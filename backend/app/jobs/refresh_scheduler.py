from __future__ import annotations

import threading
import time

from backend.app.core.config import Settings
from backend.app.services.sync_service import SyncService


class RefreshScheduler:
    def __init__(self, settings: Settings, sync_service: SyncService):
        self.settings = settings
        self.sync_service = sync_service
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()

    def start(self) -> None:
        if not self.settings.scheduler_enabled:
            return
        if self._thread and self._thread.is_alive():
            return
        self._thread = threading.Thread(target=self._run_loop, name="paper-refresh-scheduler", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1)

    def _run_loop(self) -> None:
        interval = max(self.settings.scheduler_interval_minutes * 60, 60)
        while not self._stop_event.is_set():
            try:
                self.sync_service.refresh_stale_datasets()
            except Exception:
                pass
            self._stop_event.wait(interval)

