"""Run the local read-only dashboard backend."""

import os
from pathlib import Path

from interface import DashboardServer, EmptyControlSurfaceReadModel, SQLiteDashboardReadModel


database_path = Path(os.environ.get("TRADING_AGENT_DB", "data/trading-agent.db"))
server = DashboardServer(
    SQLiteDashboardReadModel(database_path),
    control_surface=EmptyControlSurfaceReadModel(),
    port=8000,
)
print(server.url("/api/dashboard"), flush=True)
server.start()
try:
    server._thread.join()  # noqa: SLF001 - this runner owns the server lifecycle
except KeyboardInterrupt:
    pass
finally:
    server.close()
