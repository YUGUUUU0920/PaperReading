from __future__ import annotations

import json
import os
import tempfile
import unittest
from unittest.mock import patch

from backend.app.container import build_container
from backend.app.domain.entities import Paper
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

    def test_search_endpoint_supports_pagination_and_preview(self) -> None:
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

            app.container.repository.upsert_papers(
                [
                    Paper(
                        id=None,
                        source="icml",
                        conference="icml",
                        year=2024,
                        track="Proceedings",
                        external_id="a",
                        title="A Paper",
                        authors=["Author A"],
                        abstract="This graph method improves generalization and efficient inference.",
                        paper_url="",
                        pdf_url="",
                        summary="",
                        summary_model="",
                    ),
                    Paper(
                        id=None,
                        source="icml",
                        conference="icml",
                        year=2024,
                        track="Proceedings",
                        external_id="b",
                        title="B Paper",
                        authors=["Author B"],
                        abstract="This graph method improves generalization and efficient inference.",
                        paper_url="",
                        pdf_url="",
                        summary="",
                        summary_model="",
                    ),
                ]
            )

            response = app.dispatch("GET", "/api/papers?conference=icml&year=2024&page=2&limit=1&auto_sync=0")
            payload = json.loads(response.body.decode("utf-8"))

        self.assertEqual(response.status.value, 200)
        self.assertEqual(payload["total"], 2)
        self.assertEqual(payload["page"], 2)
        self.assertEqual(payload["page_size"], 1)
        self.assertFalse(payload["has_next"])
        self.assertEqual(len(payload["items"]), 1)
        self.assertEqual(payload["items"][0]["title"], "B Paper")
        self.assertIn("聚焦", payload["items"][0]["summary_preview"])
        self.assertIn("tags", payload["items"][0])
        self.assertIsInstance(payload["items"][0]["tags"], list)

    def test_search_endpoint_supports_tag_filter_and_citation_sort(self) -> None:
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

            app.container.repository.upsert_papers(
                [
                    Paper(
                        id=None,
                        source="iclr",
                        conference="iclr",
                        year=2025,
                        track="Conference",
                        external_id="mm",
                        title="A Multimodal Retrieval-Augmented Language Model",
                        authors=["Author A"],
                        abstract="A multimodal retrieval augmented generation system for large language models.",
                        paper_url="",
                        pdf_url="",
                        summary="",
                        summary_model="",
                        metadata={"citation_count": 100},
                    ),
                    Paper(
                        id=None,
                        source="iclr",
                        conference="iclr",
                        year=2025,
                        track="Conference",
                        external_id="rl",
                        title="Bandit Optimization for Efficient Exploration",
                        authors=["Author B"],
                        abstract="A contextual bandit baseline.",
                        paper_url="",
                        pdf_url="",
                        summary="",
                        summary_model="",
                        metadata={"citation_count": 12},
                    ),
                ]
            )

            response = app.dispatch(
                "GET",
                "/api/papers?conference=iclr&year=2025&tag=多模态&sort=citations_desc&auto_sync=0",
            )
            payload = json.loads(response.body.decode("utf-8"))

        self.assertEqual(response.status.value, 200)
        self.assertEqual(payload["total"], 1)
        self.assertEqual(payload["items"][0]["citation_count"], 100)
        self.assertIn("多模态", payload["items"][0]["tags"])

    def test_saved_list_endpoints_persist_paper_state(self) -> None:
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

            app.container.repository.upsert_papers(
                [
                    Paper(
                        id=None,
                        source="icml",
                        conference="icml",
                        year=2024,
                        track="Proceedings",
                        external_id="fav",
                        title="Favorite Paper",
                        authors=["Author A"],
                        abstract="A paper to save.",
                        paper_url="",
                        pdf_url="",
                        summary="",
                        summary_model="",
                    )
                ]
            )
            paper_id = app.container.repository.search_papers(conference="icml", year=2024, limit=1, offset=0)[0].id

            toggle = app.dispatch(
                "POST",
                "/api/lists/toggle",
                body=json.dumps({"paper_id": paper_id, "list_type": "favorite", "enabled": True}).encode("utf-8"),
            )
            toggle_payload = json.loads(toggle.body.decode("utf-8"))
            listing = app.dispatch("GET", "/api/lists")
            listing_payload = json.loads(listing.body.decode("utf-8"))

        self.assertEqual(toggle.status.value, 200)
        self.assertTrue(toggle_payload["item"]["saved"]["favorite"])
        self.assertEqual(listing.status.value, 200)
        self.assertEqual(listing_payload["counts"]["favorite"], 1)
        self.assertEqual(len(listing_payload["favorite"]), 1)


if __name__ == "__main__":
    unittest.main()
