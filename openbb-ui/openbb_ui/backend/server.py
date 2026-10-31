from __future__ import annotations

import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from .models import DashboardReadModel, EmptyDashboardReadModel


class DashboardServer:
    def __init__(self, read_model: DashboardReadModel | None = None, static_dir: Path | None = None) -> None:
        self.read_model = read_model or EmptyDashboardReadModel()
        self.static_dir = static_dir or Path(__file__).parent.parent / "static"

    def handler(self):
        server = self

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self) -> None:
                path = urlparse(self.path).path
                if path == "/api/health":
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
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, *_: object) -> None:
                pass

        return Handler

    def serve(self, host: str = "localhost", port: int = 8765) -> None:
        ThreadingHTTPServer((host, port), self.handler()).serve_forever()


def main() -> None:
    DashboardServer().serve(os.getenv("OPENBB_UI_HOST", "localhost"), int(os.getenv("OPENBB_UI_PORT", "8765")))


if __name__ == "__main__":
    main()
