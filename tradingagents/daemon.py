"""Run the whole system in the background from the terminal.

    python -m tradingagents.cli start   # launches everything detached, returns
    python -m tradingagents.cli stop    # stops it
    python -m tradingagents.cli status  # is it running?

``start`` spawns a detached child that runs the autonomous loop, writes its PID
and streams output to ``~/.tradingagents/``. It returns immediately with a
one-line confirmation. ``stop`` signals that PID to shut down.
"""

from __future__ import annotations

import os
import signal
import subprocess
import sys
from pathlib import Path
from typing import Optional

_HOME = Path(os.path.expanduser("~")) / ".tradingagents"
_PID_FILE = _HOME / "agent.pid"
_LOG_FILE = _HOME / "agent.log"
_BT_PID_FILE = _HOME / "backtest.pid"
_BT_LOG_FILE = _HOME / "backtest.log"


def _read_pid() -> Optional[int]:
    try:
        return int(_PID_FILE.read_text().strip())
    except (FileNotFoundError, ValueError):
        return None


def _alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)  # signal 0 = existence check
        return True
    except (OSError, ProcessLookupError):
        return False


def is_running() -> Optional[int]:
    pid = _read_pid()
    return pid if (pid is not None and _alive(pid)) else None


def start(interval: Optional[float] = None, *, config: Optional[str] = None,
          db: Optional[str] = None) -> str:
    """Launch the autonomous loop detached in the background. Returns a message."""
    running = is_running()
    if running:
        return f"trading-agent already running (pid {running}); use 'stop' first."

    _HOME.mkdir(parents=True, exist_ok=True)
    from .config import load_settings
    settings = load_settings(config)
    if interval is None:  # default loop period from config
        interval = settings.cycle.interval_seconds

    cmd = [sys.executable, "-m", "tradingagents.cli", "run", "--loop", str(interval)]
    if config:
        cmd += ["--config", config]
    if db:
        cmd += ["--db", db]

    log = open(_LOG_FILE, "a")
    proc = subprocess.Popen(
        cmd,
        stdout=log,
        stderr=subprocess.STDOUT,
        stdin=subprocess.DEVNULL,
        start_new_session=True,  # detach from the controlling terminal
        cwd=os.getcwd(),
    )
    _PID_FILE.write_text(str(proc.pid))

    # Nightly threshold-validator backtest as a SECOND detached process.
    bt_msg = ""
    if settings.backtest.nightly_enabled:
        bt_cmd = [sys.executable, "-m", "tradingagents.cli", "backtest", "--nightly"]
        if config:
            bt_cmd += ["--config", config]
        if db:
            bt_cmd += ["--db", db]
        bt_log = open(_BT_LOG_FILE, "a")
        bt_proc = subprocess.Popen(
            bt_cmd, stdout=bt_log, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL,
            start_new_session=True, cwd=os.getcwd(),
        )
        _BT_PID_FILE.write_text(str(bt_proc.pid))
        bt_msg = (f"\n  backtest (nightly @ {settings.backtest.nightly_hour:02d}:00): "
                  f"pid {bt_proc.pid}, logs {_BT_LOG_FILE}")

    return (
        f"trading-agent started in background (pid {proc.pid}).\n"
        f"  logs:  {_LOG_FILE}{bt_msg}\n"
        f"  stop:  python -m tradingagents.cli stop"
    )


def _stop_pidfile(pid_file: Path, label: str) -> str:
    try:
        pid = int(pid_file.read_text().strip())
    except (FileNotFoundError, ValueError):
        return ""
    if not _alive(pid):
        pid_file.unlink(missing_ok=True)
        return f"{label} not running (stale pid {pid} cleared)."
    try:
        os.kill(pid, signal.SIGTERM)
    except OSError as exc:  # pragma: no cover
        return f"could not stop {label} pid {pid}: {exc}"
    pid_file.unlink(missing_ok=True)
    return f"{label} stop signal sent (pid {pid})."


def stop(*, timeout: float = 10.0) -> str:
    """Signal the background system (trading loop + nightly backtest) to shut down."""
    msgs = []
    main = _stop_pidfile(_PID_FILE, "trading-agent")
    msgs.append(main or "trading-agent is not running (no pid file).")
    bt = _stop_pidfile(_BT_PID_FILE, "backtest (nightly)")
    if bt:
        msgs.append(bt)
    return "\n".join(msgs)


def status() -> str:
    pid = is_running()
    main = (f"trading-agent is RUNNING (pid {pid})." if pid else "trading-agent is STOPPED.")
    try:
        bt_pid = int(_BT_PID_FILE.read_text().strip())
        bt = (f"backtest (nightly) is RUNNING (pid {bt_pid})." if _alive(bt_pid)
              else "backtest (nightly) is STOPPED (stale pid).")
    except (FileNotFoundError, ValueError):
        bt = "backtest (nightly) is STOPPED."
    return f"{main}\n{bt}"
