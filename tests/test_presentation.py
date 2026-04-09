from __future__ import annotations

import os
import tempfile
import unittest
from unittest.mock import patch

from backend.app.container import build_container
from backend.app.presentation.application import Application


class ApplicationTests(unittest.TestCase):
    def test_health_endpoint_returns_ok(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = os.path.join(temp_dir, "papers.db")
            with patch.dict(
                os.environ,
                {
                    "PAPER_ASSISTANT_DB_PATH": db_path,
                    "PAPER_ASSISTANT_SCHEDULER_ENABLED": "0",
                },
                clear=False,
            ):
                app = Application(build_container())

            response = app.dispatch("GET", "/api/health")

        self.assertEqual(response.status.value, 200)
        self.assertIn(b'"ok": true', response.body)


if __name__ == "__main__":
    unittest.main()

