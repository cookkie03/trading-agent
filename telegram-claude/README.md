# Telegram Claude bridge

Project-scoped Telegram adapter for `trading-agent`. It launches `claude-my-combo` from the repository root, with persistent Claude sessions and a persistent SQLite mapping for Telegram chats.

## Configure credentials

Create a private env file outside Git, for example:

```bash
mkdir -p ~/.config/trading-agent
chmod 700 ~/.config/trading-agent
cat > ~/.config/trading-agent/telegram.env <<'EOF'
TELEGRAM_BOT_TOKEN=YOUR_BOT_TOKEN
TELEGRAM_ALLOWED_USER_ID=YOUR_NUMERIC_TELEGRAM_USER_ID
EOF
chmod 600 ~/.config/trading-agent/telegram.env
```

Do not put the real token in the repository, `.env`, chat messages, or commits.

## Install and run

From the repository root:

```bash
uv sync --extra telegram
set -a
source ~/.config/trading-agent/telegram.env
set +a
uv run --extra telegram python -m telegram_claude.app
```

The module lives in `telegram-claude/`, so set `PYTHONPATH` when running it:

```bash
PYTHONPATH=telegram-claude uv run --extra telegram python -m telegram_claude.app
```

The database is created at `telegram-claude/sessions.sqlite3`; it is local state and must not be committed.

## Telegram commands

- `/new` — new conversation
- `/sessions` — active session, model and effort
- `/resume SESSION_ID` — switch conversation
- `/model my-combo|gpt|gemini` — select routing model
- `/effort low|medium|high|max` — select effort; default is `high`
- `/goal TEXT` — prepend a project goal to later requests
- `/rewind TEXT` — forward a rewind request to Claude Code
- `/status` — bridge and project status
- `/stop` — reports that cancellation is not yet enabled
- `/help` — list commands

Telegram's command menu is installed automatically through Bot API. Telegram does not provide generic inline autocomplete for arbitrary arguments; the command menu covers slash-command suggestions, while model and effort values are validated and described by `/help`.

## Security

The bridge accepts messages only from `TELEGRAM_ALLOWED_USER_ID`, runs in `/home/luca/trading-agent`, and uses the existing `claude-my-combo` CLI. Review permission settings before enabling unattended write or shell operations.
