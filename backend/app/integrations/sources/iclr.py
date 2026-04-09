from __future__ import annotations

from backend.app.integrations.sources.proceedings import ProceedingsSource


class ICLRSource(ProceedingsSource):
    code = "iclr"
    label = "ICLR"
    list_base_url = "https://proceedings.iclr.cc/paper_files/paper/{year}"

