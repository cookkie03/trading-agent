import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "telegram-claude"))

from telegram_claude.bridge import BridgeConfig, CommandRouter, SessionStore


def test_new_session_is_persisted_and_resumable(tmp_path):
    store = SessionStore(tmp_path / "sessions.sqlite3")
    first = store.get_or_create(123)
    second = store.get_or_create(123)

    assert first == second
    assert store.list_sessions(123)[0].session_id == first


def test_command_router_handles_session_controls():
    router = CommandRouter()

    assert router.parse("/new").name == "new"
    assert router.parse("/resume abc123").args == ["abc123"]
    assert router.parse("/model gemini").args == ["gemini"]
    assert router.parse("/goal improve tests").args == ["improve", "tests"]
    assert router.parse("hello").name is None


def test_model_and_effort_are_validated():
    config = BridgeConfig(allowed_user_id=123, bot_token="token")
    router = CommandRouter()

    assert router.parse("/model gpt").validated(config).model == "gpt"
    assert router.parse("/effort high").validated(config).effort == "high"


def test_unknown_slash_commands_are_forwarded():
    command = CommandRouter().parse("/compact now")

    assert command.name == "passthrough"
    assert command.raw == "/compact now"
