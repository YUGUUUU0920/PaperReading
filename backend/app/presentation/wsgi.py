from __future__ import annotations

import atexit

from backend.app.container import build_container
from backend.app.presentation.application import Application


_container = build_container()
_container.scheduler.start()
atexit.register(_container.scheduler.stop)
_application = Application(_container)


def app(environ, start_response):
    method = environ.get("REQUEST_METHOD", "GET").upper()
    path = environ.get("PATH_INFO", "/")
    query_string = environ.get("QUERY_STRING", "")
    raw_path = f"{path}?{query_string}" if query_string else path
    body_length = int(environ.get("CONTENT_LENGTH") or "0")
    body = environ["wsgi.input"].read(body_length) if body_length > 0 else b""
    headers = {
        key[5:].replace("_", "-"): value
        for key, value in environ.items()
        if key.startswith("HTTP_")
    }

    response = _application.dispatch(method, raw_path, body, headers)
    start_response(
        f"{response.status.value} {response.status.phrase}",
        [
            ("Content-Type", response.content_type),
            ("Content-Length", str(len(response.body))),
            *response.headers,
        ],
    )
    return [response.body]


__all__ = ["app"]
