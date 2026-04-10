from __future__ import annotations

import json
import mimetypes
from dataclasses import dataclass, field
from http import HTTPStatus
from urllib.parse import parse_qs, urlparse

from backend.app.container import AppContainer


@dataclass
class Response:
    status: HTTPStatus
    body: bytes
    content_type: str
    headers: list[tuple[str, str]] = field(default_factory=list)


class Application:
    def __init__(self, container: AppContainer):
        self.container = container

    def dispatch(self, method: str, raw_path: str, body: bytes = b"") -> Response:
        parsed = urlparse(raw_path)
        path = parsed.path

        if method == "GET":
            if path in {"/", "/papers", "/paper", "/datasets", "/lists"} or path.startswith("/frontend/"):
                return self._serve_frontend(path)
            if path == "/api/health":
                return self._json_response({"ok": True})
            if path == "/api/bootstrap":
                payload = self.container.catalog_service.bootstrap()
                return self._json_response({"ok": True, **payload})
            if path == "/api/papers":
                return self._handle_search(parsed.query)
            if path == "/api/datasets":
                return self._handle_list_datasets()
            if path == "/api/lists":
                return self._handle_list_saved_papers()
            if path.startswith("/api/papers/"):
                return self._handle_get_paper(path)
            return self._json_response(
                {"ok": False, "error": "Route not found"},
                status=HTTPStatus.NOT_FOUND,
            )

        if method == "POST":
            if path == "/api/datasets/refresh":
                return self._handle_refresh_dataset(body)
            if path == "/api/lists/toggle":
                return self._handle_toggle_saved(body)
            if path == "/api/lists/update":
                return self._handle_update_saved(body)
            if path.startswith("/api/papers/") and path.endswith("/summarize"):
                return self._handle_summarize(path)
            return self._json_response(
                {"ok": False, "error": "Route not found"},
                status=HTTPStatus.NOT_FOUND,
            )

        return self._json_response(
            {"ok": False, "error": f"Method {method} not allowed"},
            status=HTTPStatus.METHOD_NOT_ALLOWED,
        )

    def _serve_frontend(self, path: str) -> Response:
        route_map = {
            "/": self.container.settings.frontend_root / "index.html",
            "/papers": self.container.settings.frontend_root / "index.html",
            "/paper": self.container.settings.frontend_root / "paper.html",
            "/datasets": self.container.settings.frontend_root / "datasets.html",
            "/lists": self.container.settings.frontend_root / "lists.html",
        }
        if path in route_map:
            file_path = route_map[path]
        else:
            relative = path.lstrip("/")
            file_path = self.container.settings.project_root / relative
        if not file_path.exists() or not file_path.is_file():
            return self._json_response(
                {"ok": False, "error": "Frontend asset not found"},
                status=HTTPStatus.NOT_FOUND,
            )
        content_type = mimetypes.guess_type(file_path.name)[0] or "application/octet-stream"
        if content_type.startswith("text/") or content_type == "application/javascript":
            content_type = f"{content_type}; charset=utf-8"
        return Response(
            status=HTTPStatus.OK,
            body=file_path.read_bytes(),
            content_type=content_type,
        )

    def _handle_search(self, query_string: str) -> Response:
        params = parse_qs(query_string)
        conference = params.get("conference", [""])[0]
        year_text = params.get("year", [""])[0]
        query = params.get("query", [""])[0]
        tags = self._parse_multi_values(params.get("tag", []))
        sort = params.get("sort", ["default"])[0]
        limit_text = params.get("limit", ["24"])[0]
        page_text = params.get("page", ["1"])[0]
        auto_sync_text = params.get("auto_sync", ["1"])[0]
        year = int(year_text) if year_text.strip().isdigit() else None
        limit = int(limit_text) if limit_text.strip().isdigit() else 24
        page = int(page_text) if page_text.strip().isdigit() else 1
        auto_sync = auto_sync_text != "0"
        try:
            payload = self.container.paper_service.search_papers(
                conference=conference,
                year=year,
                query=query,
                tags=tags,
                sort=sort,
                limit=limit,
                page=page,
                auto_sync=auto_sync,
            )
        except Exception as exc:
            return self._json_response(
                {"ok": False, "error": str(exc)},
                status=HTTPStatus.BAD_GATEWAY,
            )
        payload["ok"] = True
        return self._json_response(payload)

    def _handle_get_paper(self, path: str) -> Response:
        paper_id = self._extract_paper_id(path)
        if paper_id is None:
            return self._json_response(
                {"ok": False, "error": "Invalid paper id"},
                status=HTTPStatus.BAD_REQUEST,
            )
        try:
            item = self.container.paper_service.get_paper(paper_id)
        except KeyError as exc:
            return self._json_response(
                {"ok": False, "error": str(exc)},
                status=HTTPStatus.NOT_FOUND,
            )
        except Exception as exc:
            return self._json_response(
                {"ok": False, "error": str(exc)},
                status=HTTPStatus.BAD_GATEWAY,
            )
        return self._json_response({"ok": True, "item": item})

    def _handle_list_datasets(self) -> Response:
        items = self.container.paper_service.list_datasets()
        return self._json_response({"ok": True, "items": items, "count": len(items)})

    def _handle_list_saved_papers(self) -> Response:
        payload = self.container.paper_service.list_saved_papers()
        payload["ok"] = True
        return self._json_response(payload)

    def _handle_summarize(self, path: str) -> Response:
        paper_id = self._extract_paper_id(path)
        if paper_id is None:
            return self._json_response(
                {"ok": False, "error": "Invalid paper id"},
                status=HTTPStatus.BAD_REQUEST,
            )
        try:
            item = self.container.paper_service.summarize_paper(paper_id)
        except KeyError as exc:
            return self._json_response(
                {"ok": False, "error": str(exc)},
                status=HTTPStatus.NOT_FOUND,
            )
        except Exception as exc:
            return self._json_response(
                {"ok": False, "error": str(exc)},
                status=HTTPStatus.BAD_GATEWAY,
            )
        return self._json_response({"ok": True, "item": item})

    def _handle_refresh_dataset(self, body: bytes) -> Response:
        try:
            payload = self._decode_json_body(body)
        except ValueError as exc:
            return self._json_response(
                {"ok": False, "error": str(exc)},
                status=HTTPStatus.BAD_REQUEST,
            )
        conference = str(payload.get("conference", "")).strip().lower()
        year = int(payload.get("year", 0))
        if not conference or not year:
            return self._json_response(
                {"ok": False, "error": "conference and year are required"},
                status=HTTPStatus.BAD_REQUEST,
            )
        try:
            dataset = self.container.paper_service.refresh_dataset(conference, year)
        except Exception as exc:
            return self._json_response(
                {"ok": False, "error": str(exc)},
                status=HTTPStatus.BAD_GATEWAY,
            )
        return self._json_response({"ok": True, "dataset": dataset})

    def _handle_toggle_saved(self, body: bytes) -> Response:
        try:
            payload = self._decode_json_body(body)
        except ValueError as exc:
            return self._json_response(
                {"ok": False, "error": str(exc)},
                status=HTTPStatus.BAD_REQUEST,
            )
        paper_id = int(payload.get("paper_id", 0))
        list_type = str(payload.get("list_type", "")).strip().lower()
        enabled = bool(payload.get("enabled", False))
        if not paper_id or list_type not in {"favorite", "reading"}:
            return self._json_response(
                {"ok": False, "error": "paper_id and valid list_type are required"},
                status=HTTPStatus.BAD_REQUEST,
            )
        try:
            item = self.container.paper_service.set_saved_state(paper_id, list_type, enabled)
        except KeyError as exc:
            return self._json_response(
                {"ok": False, "error": str(exc)},
                status=HTTPStatus.NOT_FOUND,
            )
        except Exception as exc:
            return self._json_response(
                {"ok": False, "error": str(exc)},
                status=HTTPStatus.BAD_GATEWAY,
            )
        return self._json_response({"ok": True, "item": item})

    def _handle_update_saved(self, body: bytes) -> Response:
        try:
            payload = self._decode_json_body(body)
        except ValueError as exc:
            return self._json_response(
                {"ok": False, "error": str(exc)},
                status=HTTPStatus.BAD_REQUEST,
            )
        paper_id = int(payload.get("paper_id", 0))
        list_type = str(payload.get("list_type", "")).strip().lower()
        group_name = str(payload.get("group_name", "")).strip()
        note = str(payload.get("note", "")).strip()
        is_read = bool(payload.get("is_read", False))
        if not paper_id or list_type not in {"favorite", "reading"}:
            return self._json_response(
                {"ok": False, "error": "paper_id and valid list_type are required"},
                status=HTTPStatus.BAD_REQUEST,
            )
        try:
            item = self.container.paper_service.update_saved_entry(
                paper_id,
                list_type,
                group_name=group_name,
                note=note,
                is_read=is_read,
            )
        except KeyError as exc:
            return self._json_response(
                {"ok": False, "error": str(exc)},
                status=HTTPStatus.NOT_FOUND,
            )
        except Exception as exc:
            return self._json_response(
                {"ok": False, "error": str(exc)},
                status=HTTPStatus.BAD_GATEWAY,
            )
        return self._json_response({"ok": True, "item": item})

    def _extract_paper_id(self, path: str) -> int | None:
        parts = [part for part in path.split("/") if part]
        if len(parts) < 3:
            return None
        try:
            return int(parts[2])
        except ValueError:
            return None

    def _decode_json_body(self, body: bytes) -> dict:
        if not body:
            return {}
        try:
            payload = json.loads(body.decode("utf-8"))
        except json.JSONDecodeError as exc:
            raise ValueError("Invalid JSON body") from exc
        if not isinstance(payload, dict):
            raise ValueError("JSON body must be an object")
        return payload

    def _parse_multi_values(self, values: list[str]) -> list[str]:
        items: list[str] = []
        for value in values:
            for part in value.split(","):
                cleaned = part.strip()
                if cleaned and cleaned not in items:
                    items.append(cleaned)
        return items

    def _json_response(self, payload: dict, status: HTTPStatus = HTTPStatus.OK) -> Response:
        return Response(
            status=status,
            body=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            content_type="application/json; charset=utf-8",
        )
