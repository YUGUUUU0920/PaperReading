from __future__ import annotations

import os
import unittest
from unittest.mock import patch

from backend.app.core.config import get_settings


class SettingsTests(unittest.TestCase):
    def test_uses_platform_port_defaults_for_cloud_deploy(self) -> None:
        with patch.dict(os.environ, {"PORT": "9000"}, clear=True):
            settings = get_settings()
        self.assertEqual(settings.host, "0.0.0.0")
        self.assertEqual(settings.port, 9000)

    def test_prefers_explicit_project_port_when_present(self) -> None:
        with patch.dict(
            os.environ,
            {
                "PORT": "9000",
                "PAPER_ASSISTANT_HOST": "127.0.0.1",
                "PAPER_ASSISTANT_PORT": "8765",
            },
            clear=True,
        ):
            settings = get_settings()
        self.assertEqual(settings.host, "127.0.0.1")
        self.assertEqual(settings.port, 8765)


if __name__ == "__main__":
    unittest.main()

