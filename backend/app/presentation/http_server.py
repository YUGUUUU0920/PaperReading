from __future__ import annotations

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from backend.app.container import build_container
from backend.app.presentation.application import Application


class ApiHandler(BaseHTTPRequestHandler):
    server_version = "PaperAssistant/2.1"
    app = Application(build_container())

    def do_GET(self) -> None:
        self._dispatch("GET")

    def do_POST(self) -> None:
        self._dispatch("POST")

    def log_message(self, fmt: str, *args) -> None:
        return

    def _dispatch(self, method: str) -> None:
        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length) if length else b""
        response = self.app.dispatch(method, self.path, body)
        self.send_response(response.status)
        self.send_header("Content-Type", response.content_type)
        for header, value in response.headers:
            self.send_header(header, value)
        self.send_header("Content-Length", str(len(response.body)))
        self.end_headers()
        self.wfile.write(response.body)


def run_server() -> None:
    app = ApiHandler.app
    app.container.scheduler.start()
    server = None
    try:
        server = ThreadingHTTPServer((app.container.settings.host, app.container.settings.port), ApiHandler)
        print(f"Paper Assistant running at http://{app.container.settings.host}:{app.container.settings.port}")
        server.serve_forever()
    except OSError as exc:
        print(
            f"Failed to start server on http://{app.container.settings.host}:{app.container.settings.port}. "
            f"Reason: {exc}"
        )
    except KeyboardInterrupt:
        pass
    finally:
        app.container.scheduler.stop()
        if server is not None:
            server.server_close()
