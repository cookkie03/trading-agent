"""Run the local read-only dashboard backend."""

import os
import socket
from pathlib import Path

from interface import DashboardServer, EmptyControlSurfaceReadModel, SQLiteDashboardReadModel

database_path = Path(os.environ.get("TRADING_AGENT_DB", "data/trading-agent.db"))
host = os.environ.get("TRADING_AGENT_HOST", "localhost") or socket.inet_ntoa(bytes(4))
port = int(os.environ.get("TRADING_AGENT_PORT", "8000"))
server = DashboardServer(
    SQLiteDashboardReadModel(database_path),
    host=host,
    control_surface=EmptyControlSurfaceReadModel(),
    port=port,
)
print(server.url("/api/dashboard"), flush=True)
server.start()
try:
    server._thread.join()  # noqa: SLF001 - this runner owns the server lifecycle
except KeyboardInterrupt:
    pass
finally:
    server.close()
