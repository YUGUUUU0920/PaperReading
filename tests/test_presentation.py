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
    def test_frontend_routes_return_html_pages(self) -> None:
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

            home = app.dispatch("GET", "/")
            explore = app.dispatch("GET", "/explore")
            themes = app.dispatch("GET", "/themes")
            lineage = app.dispatch("GET", "/lineage")

        self.assertEqual(home.status.value, 200)
        self.assertEqual(explore.status.value, 200)
        self.assertEqual(themes.status.value, 200)
        self.assertEqual(lineage.status.value, 200)
        self.assertIn(b"Research Atlas", home.body)
        self.assertIn(b"frontend/src/main.js", explore.body)
        self.assertIn(b"frontend/src/themes.js", themes.body)
        self.assertIn(b"frontend/src/lineage.js", lineage.body)

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

    def test_viewer_endpoint_creates_guest_identity(self) -> None:
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

            response = app.dispatch("GET", "/api/viewer")
            payload = json.loads(response.body.decode("utf-8"))

        self.assertEqual(response.status.value, 200)
        self.assertTrue(payload["viewer"]["id"].startswith("viewer-"))
        self.assertTrue(payload["viewer"]["is_guest"])
        self.assertIn("访客-", payload["viewer"]["display_name"])

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
                        title="A Multimodal Retrieval-Augmented Language Model for Reasoning",
                        authors=["Author A"],
                        abstract="A multimodal retrieval augmented generation system for large language models and reasoning.",
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
                "/api/papers?conference=iclr&year=2025&tag=多模态&tag=大模型&sort=citations_desc&auto_sync=0",
            )
            payload = json.loads(response.body.decode("utf-8"))

        self.assertEqual(response.status.value, 200)
        self.assertEqual(payload["total"], 1)
        self.assertEqual(payload["items"][0]["citation_count"], 100)
        self.assertIn("多模态", payload["items"][0]["tags"])
        self.assertIn("大模型", payload["items"][0]["tags"])
        self.assertEqual(payload["selected_tags"], ["多模态", "大模型"])

    def test_showcase_endpoint_returns_ranked_launches_collections_and_makers(self) -> None:
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
                        track="Spotlight",
                        external_id="ranked-1",
                        title="A Multimodal Retrieval-Augmented Language Model for Reasoning",
                        authors=["Alice", "Bob"],
                        abstract="A multimodal retrieval augmented generation system for large language models and reasoning.",
                        paper_url="",
                        pdf_url="",
                        summary="结构化导读",
                        summary_model="heuristic-auto",
                        metadata={"citation_count": 120, "code_url": "https://example.com/code", "open_access": True},
                    ),
                    Paper(
                        id=None,
                        source="iclr",
                        conference="iclr",
                        year=2025,
                        track="Conference",
                        external_id="ranked-2",
                        title="Multimodal Language Model Agents for Strong Tool Use",
                        authors=["Alice", "Cara"],
                        abstract="A multimodal language model agent system for reasoning and tool use.",
                        paper_url="",
                        pdf_url="",
                        summary="",
                        summary_model="",
                        metadata={"citation_count": 45},
                    ),
                    Paper(
                        id=None,
                        source="acl",
                        conference="acl",
                        year=2025,
                        track="Oral",
                        external_id="ranked-3",
                        title="Graph Retrieval for Enterprise Search",
                        authors=["Dan"],
                        abstract="A graph retrieval method for enterprise search.",
                        paper_url="",
                        pdf_url="",
                        summary="",
                        summary_model="",
                        metadata={"citation_count": 60},
                    ),
                ]
            )

            response = app.dispatch("GET", "/api/showcase")
            payload = json.loads(response.body.decode("utf-8"))

        self.assertEqual(response.status.value, 200)
        self.assertEqual(payload["overview"]["total_papers"], 3)
        self.assertEqual(payload["overview"]["latest_year"], 2025)
        self.assertTrue(payload["ranked_launches"])
        self.assertEqual(payload["ranked_launches"][0]["external_id"], "ranked-1")
        self.assertIn("launch_score", payload["ranked_launches"][0])
        self.assertTrue(payload["collections"])
        self.assertIn("theme", payload["collections"][0])
        self.assertTrue(payload["collections"][0]["items"])
        self.assertTrue(payload["makers"])
        self.assertEqual(payload["makers"][0]["name"], "Alice")
        self.assertIn("top_theme", payload["makers"][0])

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
            update = app.dispatch(
                "POST",
                "/api/lists/update",
                body=json.dumps(
                    {
                        "paper_id": paper_id,
                        "list_type": "favorite",
                        "group_name": "必读",
                        "note": "先看方法部分",
                        "is_read": True,
                    }
                ).encode("utf-8"),
            )
            update_payload = json.loads(update.body.decode("utf-8"))
            listing = app.dispatch("GET", "/api/lists")
            listing_payload = json.loads(listing.body.decode("utf-8"))

        self.assertEqual(toggle.status.value, 200)
        self.assertTrue(toggle_payload["item"]["saved"]["favorite"])
        self.assertEqual(update.status.value, 200)
        self.assertEqual(update_payload["item"]["saved"]["favorite"]["group_name"], "必读")
        self.assertEqual(update_payload["item"]["saved"]["favorite"]["note"], "先看方法部分")
        self.assertTrue(update_payload["item"]["saved"]["favorite"]["is_read"])
        self.assertEqual(listing.status.value, 200)
        self.assertEqual(listing_payload["counts"]["favorite"], 1)
        self.assertEqual(len(listing_payload["favorite"]), 1)
        self.assertEqual(listing_payload["favorite"][0]["saved"]["favorite"]["group_name"], "必读")

    def test_lineage_endpoint_returns_theme_tree(self) -> None:
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
                        track="Oral",
                        external_id="lineage-a",
                        title="Large Language Model Reasoning with Retrieval",
                        authors=["Author A"],
                        abstract="A large language model with reasoning and retrieval augmented generation.",
                        paper_url="",
                        pdf_url="",
                        summary="",
                        summary_model="",
                        metadata={"citation_count": 120, "code_url": "https://github.com/example/a"},
                    ),
                    Paper(
                        id=None,
                        source="iclr",
                        conference="iclr",
                        year=2025,
                        track="Conference",
                        external_id="lineage-b",
                        title="Reasoning Agents for Large Language Models",
                        authors=["Author B"],
                        abstract="Agent planning for large language models and reasoning workflows.",
                        paper_url="",
                        pdf_url="",
                        summary="",
                        summary_model="",
                        metadata={"citation_count": 42},
                    ),
                    Paper(
                        id=None,
                        source="iclr",
                        conference="iclr",
                        year=2025,
                        track="Spotlight",
                        external_id="lineage-c",
                        title="Multimodal Large Language Model Planning",
                        authors=["Author C"],
                        abstract="A multimodal large language model for planning and tool use.",
                        paper_url="",
                        pdf_url="",
                        summary="",
                        summary_model="",
                        metadata={"citation_count": 28},
                    ),
                ]
            )

            response = app.dispatch("GET", "/api/lineage?theme=大模型&limit=1")
            payload = json.loads(response.body.decode("utf-8"))

        self.assertEqual(response.status.value, 200)
        self.assertEqual(payload["count"], 1)
        self.assertEqual(payload["items"][0]["theme"], "大模型")
        self.assertGreaterEqual(len(payload["items"][0]["nodes"]), 3)
        self.assertGreaterEqual(len(payload["items"][0]["links"]), 2)
        self.assertTrue(payload["items"][0]["highlights"])
        self.assertIn(2024, payload["items"][0]["years"])
        self.assertIn(2025, payload["items"][0]["years"])

    def test_comment_endpoints_seed_discussion_and_accept_user_comment(self) -> None:
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
                        external_id="comment-demo",
                        title="Reasoning Agents for Large Language Models",
                        authors=["Author A"],
                        abstract="Agent planning for large language models and reasoning workflows.",
                        paper_url="",
                        pdf_url="",
                        summary="",
                        summary_model="",
                        metadata={"citation_count": 42, "code_url": "https://github.com/example/project"},
                    )
                ]
            )
            paper_id = app.container.repository.search_papers(conference="iclr", year=2025, limit=1, offset=0)[0].id

            viewer = app.dispatch("GET", "/api/viewer")
            viewer_payload = json.loads(viewer.body.decode("utf-8"))
            headers = {"X-Viewer-Id": viewer_payload["viewer"]["id"], "X-Viewer-Name": viewer_payload["viewer"]["display_name"]}

            seeded = app.dispatch("GET", f"/api/papers/{paper_id}/comments", headers=headers)
            seeded_payload = json.loads(seeded.body.decode("utf-8"))
            created = app.dispatch(
                "POST",
                f"/api/papers/{paper_id}/comments",
                body=json.dumps({"content": "我最想看它的消融实验是不是足够扎实。"}).encode("utf-8"),
                headers=headers,
            )
            created_payload = json.loads(created.body.decode("utf-8"))
            listing = app.dispatch("GET", f"/api/papers/{paper_id}/comments", headers=headers)
            listing_payload = json.loads(listing.body.decode("utf-8"))

        self.assertEqual(seeded.status.value, 200)
        self.assertEqual(seeded_payload["seed_count"], 3)
        self.assertEqual(len(seeded_payload["items"]), 3)
        self.assertTrue(all(item["is_seed"] for item in seeded_payload["items"]))
        self.assertEqual(created.status.value, 200)
        self.assertFalse(created_payload["item"]["is_seed"])
        self.assertEqual(listing.status.value, 200)
        self.assertEqual(listing_payload["count"], 4)
        self.assertEqual(len([item for item in listing_payload["items"] if not item["is_seed"]]), 1)


if __name__ == "__main__":
    unittest.main()
