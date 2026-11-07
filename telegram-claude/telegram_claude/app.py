from __future__ import annotations

import asyncio
import logging
from pathlib import Path

from telegram import BotCommand, Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

from .bridge import (
    BridgeConfig,
    ClaudeCodeRunner,
    CommandRouter,
    Session,
    SessionStore,
    split_telegram_message,
)

LOG = logging.getLogger(__name__)
COMMANDS = [
    BotCommand("new", "start a new Claude conversation"),
    BotCommand("sessions", "show the active conversation"),
    BotCommand("resume", "resume a session by ID"),
    BotCommand("model", "set my-combo, gpt, or gemini"),
    BotCommand("effort", "set low, medium, high, or max"),
    BotCommand("goal", "set the current project goal"),
    BotCommand("rewind", "ask Claude to rewind the conversation"),
    BotCommand("status", "show bridge status"),
    BotCommand("stop", "cancel the current request"),
    BotCommand("help", "show Telegram commands"),
]


def build_application(config: BridgeConfig, database: Path) -> Application:
    store = SessionStore(database)
    runner = ClaudeCodeRunner(config)
    router = CommandRouter()
    application = Application.builder().token(config.bot_token).build()
    application.bot_data.update(config=config, store=store, runner=runner, router=router, locks={})
    application.add_handler(CommandHandler([item.command for item in COMMANDS], handle_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    application.post_init = post_init
    return application


async def post_init(application: Application) -> None:
    await application.bot.set_my_commands(COMMANDS)


def authorized(update: Update, config: BridgeConfig) -> bool:
    return bool(update.effective_user and update.effective_user.id == config.allowed_user_id)


def get_session(store: SessionStore, config: BridgeConfig, chat_id: int) -> Session:
    session = store.get(chat_id)
    if session:
        return session
    session_id = store.get_or_create(chat_id, config)
    return store.get(chat_id) or Session(
        chat_id, session_id, config.default_model, config.default_effort
    )


async def handle_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    config: BridgeConfig = context.application.bot_data["config"]
    if not authorized(update, config) or not update.message or not update.effective_chat:
        return
    text = update.message.text or ""
    command = context.application.bot_data["router"].parse(text)
    store: SessionStore = context.application.bot_data["store"]
    chat_id = update.effective_chat.id
    session = get_session(store, config, chat_id)

    try:
        if command.name == "help":
            help_text = "\n".join(
                f"/{item.command} — {item.description}" for item in COMMANDS
            )
            await update.message.reply_text(help_text)
            return
        if command.name == "new":
            import uuid

            session = Session(
                chat_id, uuid.uuid4().hex, config.default_model, config.default_effort
            )
            store.save(session)
            await update.message.reply_text(f"Nuova sessione: {session.session_id}")
            return
        if command.name == "resume":
            if len(command.args) != 1:
                raise ValueError("Uso: /resume SESSION_ID")
            session = Session(chat_id, command.args[0], session.model, session.effort, session.goal)
            store.save(session)
            await update.message.reply_text(f"Sessione attiva: {session.session_id}")
            return
        if command.name == "sessions":
            await update.message.reply_text(
                f"Sessione attiva: {session.session_id}\n"
                f"Modello: {session.model}\nEffort: {session.effort}"
            )
            return
        if command.name == "model":
            setting = command.validated(config)
            session = Session(
                chat_id,
                session.session_id,
                setting.model or session.model,
                session.effort,
                session.goal,
            )
            store.save(session)
            await update.message.reply_text(f"Modello impostato: {session.model}")
            return
        if command.name == "effort":
            setting = command.validated(config)
            session = Session(
                chat_id,
                session.session_id,
                session.model,
                setting.effort or session.effort,
                session.goal,
            )
            store.save(session)
            await update.message.reply_text(f"Effort impostato: {session.effort}")
            return
        if command.name == "goal":
            if not command.args:
                raise ValueError("Uso: /goal testo dell'obiettivo")
            session = Session(
                chat_id,
                session.session_id,
                session.model,
                session.effort,
                " ".join(command.args),
            )
            store.save(session)
            await update.message.reply_text(f"Goal impostato: {session.goal}")
            return
        if command.name == "status":
            await update.message.reply_text(
                f"Online\nDirectory: {config.project_dir}\n"
                f"Sessione: {session.session_id}"
            )
            return
        if command.name == "stop":
            await update.message.reply_text(
                "Non c'è una cancellazione sicura della subprocess già avviata "
                "in questa prima versione."
            )
            return
        if command.name == "rewind":
            prompt = "/rewind " + " ".join(command.args)
        else:
            prompt = command.raw
        await run_and_reply(update, context, prompt, session)
    except ValueError as error:
        await update.message.reply_text(str(error))


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    config: BridgeConfig = context.application.bot_data["config"]
    if not authorized(update, config) or not update.message or not update.effective_chat:
        return
    session = get_session(context.application.bot_data["store"], config, update.effective_chat.id)
    await run_and_reply(update, context, update.message.text or "", session)


async def run_and_reply(
    update: Update, context: ContextTypes.DEFAULT_TYPE, prompt: str, session: Session
) -> None:
    lock = context.application.bot_data["locks"].setdefault(session.chat_id, asyncio.Lock())
    async with lock:
        status = await update.message.reply_text("⏳ Claude Code sta lavorando…")
        try:
            output = await asyncio.to_thread(
                context.application.bot_data["runner"].run, prompt, session
            )
            for chunk in split_telegram_message(output):
                await update.message.reply_text(chunk)
        except Exception as error:  # noqa: BLE001
            LOG.exception("Claude Code request failed")
            await update.message.reply_text(f"Errore: {error}")
        finally:
            await status.delete()


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    config = BridgeConfig.from_env()
    database = config.project_dir / "telegram-claude" / "sessions.sqlite3"
    build_application(config, database).run_polling()


if __name__ == "__main__":
    main()
