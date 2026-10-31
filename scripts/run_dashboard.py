"""Run the local read-only dashboard backend with an honest empty read model."""

from interface import (
    DashboardServer,
    EmptyControlSurfaceReadModel,
    EmptyDashboardReadModel,
)

server = DashboardServer(
    EmptyDashboardReadModel(),
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
