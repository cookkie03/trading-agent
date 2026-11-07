from __future__ import annotations

import os
import shlex
import sqlite3
import subprocess
import uuid
from dataclasses import dataclass
from pathlib import Path

MODELS = {"my-combo", "gpt", "gemini"}
EFFORTS = {"low", "medium", "high", "max"}


@dataclass(frozen=True)
class BridgeConfig:
    allowed_user_id: int
    bot_token: str
    project_dir: Path = Path(__file__).resolve().parents[2]
    cli_command: str = "claude-my-combo"
    default_model: str = "my-combo"
    default_effort: str = "high"

    @classmethod
    def from_env(cls) -> BridgeConfig:
        token = os.environ.get("TELEGRAM_BOT_TOKEN")
        user_id = os.environ.get("TELEGRAM_ALLOWED_USER_ID")
        if not token or not user_id:
            raise RuntimeError(
                "Set TELEGRAM_BOT_TOKEN and TELEGRAM_ALLOWED_USER_ID before starting the bridge."
            )
        return cls(allowed_user_id=int(user_id), bot_token=token)


@dataclass(frozen=True)
class ParsedCommand:
    name: str | None
    args: list[str]
    raw: str

    def validated(self, config: BridgeConfig) -> SessionSettings:
        if self.name == "model":
            if len(self.args) != 1 or self.args[0] not in MODELS:
                raise ValueError("Model must be one of: my-combo, gpt, gemini")
            return SessionSettings(model=self.args[0])
        if self.name == "effort":
            if len(self.args) != 1 or self.args[0] not in EFFORTS:
                raise ValueError("Effort must be one of: low, medium, high, max")
            return SessionSettings(effort=self.args[0])
        return SessionSettings()


@dataclass(frozen=True)
class SessionSettings:
    model: str | None = None
    effort: str | None = None


class CommandRouter:
    def parse(self, text: str) -> ParsedCommand:
        if not text.startswith("/"):
            return ParsedCommand(None, [], text)
        parts = shlex.split(text)
        command = parts[0][1:].split("@", 1)[0].lower()
        known = {
            "new",
            "sessions",
            "resume",
            "model",
            "effort",
            "goal",
            "rewind",
            "status",
            "stop",
            "help",
        }
        if command not in known:
            return ParsedCommand("passthrough", parts[1:], text)
        return ParsedCommand(command, parts[1:], text)


@dataclass(frozen=True)
class Session:
    chat_id: int
    session_id: str
    model: str
    effort: str
    goal: str = ""


class SessionStore:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.path) as db:
            db.execute("""CREATE TABLE IF NOT EXISTS sessions (
                chat_id INTEGER PRIMARY KEY,
                session_id TEXT NOT NULL,
                model TEXT NOT NULL,
                effort TEXT NOT NULL,
                goal TEXT NOT NULL DEFAULT ''
            )""")

    def get_or_create(self, chat_id: int, config: BridgeConfig | None = None) -> str:
        row = self._get(chat_id)
        if row:
            return row.session_id
        config = config or BridgeConfig(0, "")
        session_id = str(uuid.uuid4())
        self.save(Session(chat_id, session_id, config.default_model, config.default_effort))
        return session_id

    def _get(self, chat_id: int) -> Session | None:
        with sqlite3.connect(self.path) as db:
            row = db.execute(
                "SELECT chat_id, session_id, model, effort, goal "
                "FROM sessions WHERE chat_id = ?",
                (chat_id,),
            ).fetchone()
        return Session(*row) if row else None

    def get(self, chat_id: int) -> Session | None:
        return self._get(chat_id)

    def save(self, session: Session) -> None:
        with sqlite3.connect(self.path) as db:
            db.execute(
                "INSERT OR REPLACE INTO sessions VALUES (?, ?, ?, ?, ?)",
                tuple(session.__dict__.values()),
            )

    def list_sessions(self, chat_id: int) -> list[Session]:
        session = self._get(chat_id)
        return [session] if session else []


class ClaudeCodeRunner:
    def __init__(self, config: BridgeConfig) -> None:
        self.config = config

    def run(self, prompt: str, session: Session) -> str:
        command = [
            self.config.cli_command,
            "-p",
            prompt,
            "--resume",
            session.session_id,
            "--effort",
            session.effort,
            "--model",
            session.model,
        ]
        if session.goal:
            command[2] = (
                f"Project goal: {session.goal}\n\nUser request: {prompt}"
            )
        result = subprocess.run(
            command,
            cwd=self.config.project_dir,
            capture_output=True,
            text=True,
            timeout=900,
        )
        output = result.stdout.strip() or result.stderr.strip()
        if result.returncode:
            raise RuntimeError(output or f"Claude Code exited with {result.returncode}")
        return output or "(Claude Code returned no text.)"


def split_telegram_message(text: str, limit: int = 4000) -> list[str]:
    return [text[i : i + limit] for i in range(0, len(text), limit)] or [""]
