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

    def dispatch(self, method: str, raw_path: str, body: bytes = b"", headers: dict[str, str] | None = None) -> Response:
        parsed = urlparse(raw_path)
        path = parsed.path
        headers = headers or {}

        if method == "GET":
            if path in {"/", "/explore", "/papers", "/themes", "/lineage", "/paper", "/datasets", "/lists"} or path.startswith("/frontend/"):
                return self._serve_frontend(path)
            if path == "/api/health":
                return self._json_response({"ok": True})
            if path == "/api/auth/github/start":
                return self._handle_github_auth_start(parsed.query)
            if path == "/api/auth/github/callback":
                return self._handle_github_auth_callback(parsed.query)
            if path == "/api/auth/session":
                return self._handle_consume_auth_session(parsed.query)
            if path == "/api/viewer":
                return self._handle_viewer(headers)
            if path == "/api/bootstrap":
                payload = self.container.catalog_service.bootstrap()
                return self._json_response({"ok": True, **payload})
            if path == "/api/lineage":
                return self._handle_lineage(parsed.query)
            if path == "/api/showcase":
                payload = self.container.paper_service.build_showcase()
                return self._json_response({"ok": True, **payload})
            if path == "/api/papers":
                return self._handle_search(parsed.query)
            if path == "/api/datasets":
                return self._handle_list_datasets()
            if path == "/api/lists":
                return self._handle_list_saved_papers()
            if path.startswith("/api/papers/") and path.endswith("/comments"):
                return self._handle_list_comments(path, headers)
            if path.startswith("/api/papers/"):
                return self._handle_get_paper(path)
            return self._json_response(
                {"ok": False, "error": "Route not found"},
                status=HTTPStatus.NOT_FOUND,
            )

        if method == "POST":
            if path == "/api/viewer":
                return self._handle_update_viewer(body, headers)
            if path == "/api/datasets/refresh":
                return self._handle_refresh_dataset(body)
            if path == "/api/lists/toggle":
                return self._handle_toggle_saved(body)
            if path == "/api/lists/update":
                return self._handle_update_saved(body)
            if path.startswith("/api/papers/") and path.endswith("/comments"):
                return self._handle_add_comment(path, body, headers)
            if path.startswith("/api/comments/") and path.endswith("/like"):
                return self._handle_toggle_comment_like(path, body, headers)
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
            "/explore": self.container.settings.frontend_root / "explore.html",
            "/papers": self.container.settings.frontend_root / "explore.html",
            "/themes": self.container.settings.frontend_root / "themes.html",
            "/lineage": self.container.settings.frontend_root / "lineage.html",
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

    def _handle_viewer(self, headers: dict[str, str]) -> Response:
        viewer_id, viewer_name = self._viewer_headers(headers)
        try:
            viewer = self.container.community_service.ensure_viewer(viewer_id=viewer_id, display_name=viewer_name)
        except Exception as exc:
            return self._json_response(
                {"ok": False, "error": str(exc)},
                status=HTTPStatus.BAD_REQUEST,
            )
        return self._json_response({"ok": True, "viewer": viewer})

    def _handle_github_auth_start(self, query_string: str) -> Response:
        params = parse_qs(query_string)
        return_path = params.get("return_path", ["/paper"])[0]
        try:
            location = self.container.auth_service.begin_github_login(return_path)
        except Exception:
            location = self._append_query("/paper", "auth_error", "github_login_unavailable")
        return self._redirect_response(location)

    def _handle_github_auth_callback(self, query_string: str) -> Response:
        params = parse_qs(query_string)
        code = params.get("code", [""])[0]
        state = params.get("state", [""])[0]
        error = params.get("error", [""])[0]
        try:
            location = self.container.auth_service.complete_github_login(code=code, state=state, error=error)
        except Exception:
            location = self._append_query("/paper", "auth_error", "github_login_failed")
        return self._redirect_response(location)

    def _handle_consume_auth_session(self, query_string: str) -> Response:
        params = parse_qs(query_string)
        token = params.get("token", [""])[0]
        try:
            payload = self.container.auth_service.consume_auth_session(token)
        except Exception as exc:
            return self._json_response(
                {"ok": False, "error": str(exc)},
                status=HTTPStatus.BAD_REQUEST,
            )
        payload["ok"] = True
        return self._json_response(payload)

    def _handle_lineage(self, query_string: str) -> Response:
        params = parse_qs(query_string)
        theme = params.get("theme", [""])[0]
        limit_text = params.get("limit", ["6"])[0]
        limit = int(limit_text) if limit_text.strip().isdigit() else 6
        try:
            payload = self.container.lineage_service.list_lineages(
                theme=theme,
                limit=limit,
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

    def _handle_list_comments(self, path: str, headers: dict[str, str]) -> Response:
        paper_id = self._extract_paper_id(path)
        if paper_id is None:
            return self._json_response(
                {"ok": False, "error": "Invalid paper id"},
                status=HTTPStatus.BAD_REQUEST,
            )
        viewer_id, viewer_name = self._viewer_headers(headers)
        try:
            payload = self.container.community_service.list_comments(
                paper_id,
                viewer_id=viewer_id,
                display_name=viewer_name,
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
        payload["ok"] = True
        return self._json_response(payload)

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

    def _handle_update_viewer(self, body: bytes, headers: dict[str, str]) -> Response:
        try:
            payload = self._decode_json_body(body)
        except ValueError as exc:
            return self._json_response(
                {"ok": False, "error": str(exc)},
                status=HTTPStatus.BAD_REQUEST,
            )
        viewer_id, viewer_name = self._viewer_headers(headers)
        display_name = str(payload.get("display_name", "")).strip() or viewer_name
        try:
            viewer = self.container.community_service.update_viewer(viewer_id=viewer_id, display_name=display_name)
        except Exception as exc:
            return self._json_response(
                {"ok": False, "error": str(exc)},
                status=HTTPStatus.BAD_REQUEST,
            )
        return self._json_response({"ok": True, "viewer": viewer})

    def _handle_add_comment(self, path: str, body: bytes, headers: dict[str, str]) -> Response:
        paper_id = self._extract_paper_id(path)
        if paper_id is None:
            return self._json_response(
                {"ok": False, "error": "Invalid paper id"},
                status=HTTPStatus.BAD_REQUEST,
            )
        try:
            payload = self._decode_json_body(body)
        except ValueError as exc:
            return self._json_response(
                {"ok": False, "error": str(exc)},
                status=HTTPStatus.BAD_REQUEST,
            )
        viewer_id, viewer_name = self._viewer_headers(headers)
        content = str(payload.get("content", "")).strip()
        parent_comment_id = int(payload.get("parent_comment_id", 0) or 0) or None
        try:
            result = self.container.community_service.add_comment(
                paper_id,
                content=content,
                parent_comment_id=parent_comment_id,
                viewer_id=viewer_id,
                display_name=viewer_name,
            )
        except KeyError as exc:
            return self._json_response(
                {"ok": False, "error": str(exc)},
                status=HTTPStatus.NOT_FOUND,
            )
        except Exception as exc:
            return self._json_response(
                {"ok": False, "error": str(exc)},
                status=HTTPStatus.BAD_REQUEST,
            )
        return self._json_response({"ok": True, **result})

    def _handle_toggle_comment_like(self, path: str, body: bytes, headers: dict[str, str]) -> Response:
        comment_id = self._extract_comment_id(path)
        if comment_id is None:
            return self._json_response(
                {"ok": False, "error": "Invalid comment id"},
                status=HTTPStatus.BAD_REQUEST,
            )
        try:
            payload = self._decode_json_body(body)
        except ValueError as exc:
            return self._json_response(
                {"ok": False, "error": str(exc)},
                status=HTTPStatus.BAD_REQUEST,
            )
        viewer_id, viewer_name = self._viewer_headers(headers)
        enabled = bool(payload.get("enabled", True))
        try:
            result = self.container.community_service.toggle_like(
                comment_id,
                enabled=enabled,
                viewer_id=viewer_id,
                display_name=viewer_name,
            )
        except KeyError as exc:
            return self._json_response(
                {"ok": False, "error": str(exc)},
                status=HTTPStatus.NOT_FOUND,
            )
        except Exception as exc:
            return self._json_response(
                {"ok": False, "error": str(exc)},
                status=HTTPStatus.BAD_REQUEST,
            )
        return self._json_response({"ok": True, **result})

    def _extract_paper_id(self, path: str) -> int | None:
        parts = [part for part in path.split("/") if part]
        if len(parts) < 3:
            return None
        try:
            return int(parts[2])
        except ValueError:
            return None

    def _extract_comment_id(self, path: str) -> int | None:
        parts = [part for part in path.split("/") if part]
        if len(parts) < 3:
            return None
        try:
            return int(parts[2])
        except ValueError:
            return None

    def _viewer_headers(self, headers: dict[str, str]) -> tuple[str, str]:
        lowered = {str(key).lower(): str(value) for key, value in headers.items()}
        viewer_id = lowered.get("x-viewer-id", "").strip()
        viewer_name = lowered.get("x-viewer-name", "").strip()
        return viewer_id, viewer_name

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

    def _redirect_response(self, location: str, status: HTTPStatus = HTTPStatus.FOUND) -> Response:
        return Response(
            status=status,
            body=b"",
            content_type="text/plain; charset=utf-8",
            headers=[("Location", location)],
        )

    def _append_query(self, path: str, key: str, value: str) -> str:
        separator = "&" if "?" in path else "?"
        return f"{path}{separator}{key}={value}"
