"""Small loopback HTTP adapter for the dashboard read contract."""

from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread
from urllib.parse import urlsplit

from .dashboard import ControlSurfaceReadModel, DashboardReadModel


class DashboardServer:
    """Espone il read model su loopback senza endpoint di scrittura."""

    def __init__(
        self,
        read_model: DashboardReadModel,
        host: str = "localhost",
        port: int = 8000,
        control_surface: ControlSurfaceReadModel | None = None,
    ) -> None:
        self._read_model = read_model
        self._control_surface = control_surface
        self._server = ThreadingHTTPServer((host, port), self._handler())
        self._thread: Thread | None = None

    def _handler(self) -> type[BaseHTTPRequestHandler]:
        read_model = self._read_model
        control_surface = self._control_surface

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self) -> None:  # noqa: N802
                path = urlsplit(self.path).path
                if path == "/api/dashboard":
                    self._send_json(200, read_model.snapshot().to_dict())
                elif path == "/api/control-surface" and control_surface is not None:
                    self._send_json(200, control_surface.snapshot().to_dict())
                elif path == "/api/health":
                    self._send_json(200, {"status": "ok", "read_only": True})
                else:
                    self._send_json(404, {"error": "not found"})

            def do_POST(self) -> None:  # noqa: N802
                self._send_json(404, {"error": "not found"})

            def do_PUT(self) -> None:  # noqa: N802
                self._send_json(404, {"error": "not found"})

            def do_PATCH(self) -> None:  # noqa: N802
                self._send_json(404, {"error": "not found"})

            def do_DELETE(self) -> None:  # noqa: N802
                self._send_json(404, {"error": "not found"})

            def _send_json(self, status: int, payload: dict[str, object]) -> None:
                body = json.dumps(payload).encode("utf-8")
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "http://localhost:5173")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, format: str, *args: object) -> None:
                return

        return Handler

    @property
    def address(self) -> tuple[str, int]:
        return self._server.server_address

    def url(self, path: str = "") -> str:
        return f"http://localhost:{self.address[1]}{path}"

    def start(self) -> None:
        self._thread = Thread(target=self._server.serve_forever, daemon=True)
        self._thread.start()

    def close(self) -> None:
        self._server.shutdown()
        self._server.server_close()
        if self._thread is not None:
            self._thread.join(timeout=2)
