"""Run the local read-only dashboard backend."""

from pathlib import Path

from config import Settings
from interface import DashboardServer, EmptyControlSurfaceReadModel, SQLiteDashboardReadModel

settings = Settings()
server = DashboardServer(
    SQLiteDashboardReadModel(Path(settings.database_path)),
    host=settings.dashboard_host,
    control_surface=EmptyControlSurfaceReadModel(),
    port=settings.dashboard_port,
)
print(server.url("/api/dashboard"), flush=True)
server.start()
try:
    server._thread.join()  # noqa: SLF001 - this runner owns the server lifecycle
except KeyboardInterrupt:
    pass
finally:
    server.close()
