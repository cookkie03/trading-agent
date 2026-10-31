from __future__ import annotations

import json
import os
from threading import Thread
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from .models import DashboardReadModel, EmptyDashboardReadModel


class DashboardServer:
    def __init__(
        self,
        read_model: DashboardReadModel | None = None,
        host: str = "localhost",
        port: int = 8765,
        static_dir: Path | None = None,
    ) -> None:
        self.read_model = read_model or EmptyDashboardReadModel()
        self.host = host
        self.port = port
        self.static_dir = static_dir or Path(__file__).parent.parent / "static"
        self._httpd: ThreadingHTTPServer | None = None
        self._thread: Thread | None = None

    def handler(self):
        server = self

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self) -> None:
                path = urlparse(self.path).path
                if path in ("/health", "/api/health"):
                    self._json({"status": "ok", "read_only": True})
                elif path == "/api/dashboard":
                    snapshot = server.read_model.snapshot()
                    self._json({
                        "source": snapshot.source,
                        "freshness": snapshot.freshness,
                        "portfolio": snapshot.portfolio.__dict__,
                        "watchlist": snapshot.watchlist,
                        "observations": snapshot.observations,
                        "modules": snapshot.modules,
                    })
                elif path == "/":
                    self._file("index.html")
                else:
                    self.send_error(404)

            def do_POST(self) -> None:
                self.send_error(404)

            def _json(self, value: object) -> None:
                body = json.dumps(value).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Cache-Control", "no-store")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def _file(self, name: str) -> None:
                path = server.static_dir / name
                if not path.exists():
                    self.send_error(404)
                    return
                body = path.read_bytes()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Cache-Control", "no-store")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, *_: object) -> None:
                pass

        return Handler

    def start(self) -> None:
        if self._httpd is not None:
            return
        self._httpd = ThreadingHTTPServer((self.host, self.port), self.handler())
        self.port = self._httpd.server_address[1]
        self._thread = Thread(target=self._httpd.serve_forever, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        if self._httpd is None:
            return
        self._httpd.shutdown()
        self._httpd.server_close()
        if self._thread is not None:
            self._thread.join(timeout=2)
        self._httpd = None
        self._thread = None

    def url(self, path: str = "/") -> str:
        return f"http://{self.host}:{self.port}{path}"

    def serve(self, host: str | None = None, port: int | None = None) -> None:
        if host is not None:
            self.host = host
        if port is not None:
            self.port = port
        httpd = ThreadingHTTPServer((self.host, self.port), self.handler())
        self.port = httpd.server_address[1]
        try:
            httpd.serve_forever()
        finally:
            httpd.server_close()


def main() -> None:
    DashboardServer().serve(os.getenv("OPENBB_UI_HOST", "localhost"), int(os.getenv("OPENBB_UI_PORT", "8765")))


if __name__ == "__main__":
    main()
