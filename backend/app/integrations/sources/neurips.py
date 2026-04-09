from __future__ import annotations

from backend.app.integrations.sources.proceedings import ProceedingsSource


class NeurIPSSource(ProceedingsSource):
    code = "neurips"
    label = "NeurIPS"
    list_base_url = "https://proceedings.neurips.cc/paper/{year}"

