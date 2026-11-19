"""Telegram bot commands. Start with: python -m app.bot."""
import asyncio
import io
import logging
from pathlib import Path

from telegram import Update
from telegram.constants import ChatType
from telegram.ext import (
    Application, CommandHandler, ContextTypes, MessageHandler, filters,
)

from app.settings import Settings, load_settings
from app.store import MODELS, Store
from app.images import generate
from app.devin import create_session, get_session

log = logging.getLogger(__name__)
HELP = (
    "Luxury Design Bot\n"
    "Send an interior photo or moodboard to store a reference.\n"
    "/render <description> — design concept\n"
    "/edit <changes> — edit the latest image or an image you reply to\n"
    "/model flare|sunburst — choose speed/detail\n"
    "/refs and /clearrefs — manage references\n"
    "/devin <coding task> — ask Devin to develop this repository\n"
    "/devin_status <id> — check Devin coding session"
)


def authorized(update: Update, settings: Settings) -> bool:
    return bool(
        update.effective_user
        and update.effective_user.id in settings.allowed_ids
        and update.effective_chat
        and update.effective_chat.type == ChatType.PRIVATE
    )


def text_after_command(update: Update) -> str:
    message = update.effective_message
    text = message.text if message else ""
    return text.split(maxsplit=1)[1].strip() if text and len(text.split(maxsplit=1)) == 2 else ""


def get_media(message) -> tuple[str, str] | None:
    if message.photo:
        return message.photo[-1].file_id, "photo.jpg"
    doc = message.document
    if doc and doc.mime_type in {"image/png", "image/jpeg", "image/webp"}:
        name = Path(doc.file_name or "reference.png").name
        return doc.file_id, name
    return None


async def download_image(bot, file_id: str, filename: str) -> tuple[str, bytes]:
    file = await bot.get_file(file_id)
    data = bytes(await file.download_as_bytearray())
    return filename, data


def build_handlers(settings: Settings, store: Store):
    async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if authorized(update, settings):
            await update.effective_message.reply_text(HELP)

    async def set_model(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not authorized(update, settings):
            return
        key = text_after_command(update).lower()
        if key not in MODELS:
            await update.message.reply_text("Use /model flare or /model sunburst")
            return
        store.set_model(update.effective_user.id, key)
        await update.message.reply_text(f"Model selected: {MODELS[key]}")

    async def save_reference(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not authorized(update, settings):
            return
        media = get_media(update.message)
        if not media:
            return
        store.add_ref(update.effective_user.id, *media)
        await update.message.reply_text(
            f"Reference saved ({len(store.get_refs(update.effective_user.id))}/4). "
            "Use /render or /edit."
        )

    async def refs(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if authorized(update, settings):
            count = len(store.get_refs(update.effective_user.id))
            await update.message.reply_text(f"{count} reference image(s) saved (max 4).")

    async def clearrefs(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if authorized(update, settings):
            store.clear_refs(update.effective_user.id)
            await update.message.reply_text("References cleared.")

    async def render_or_edit(update: Update, context: ContextTypes.DEFAULT_TYPE, edit: bool):
        if not authorized(update, settings):
            return
        uid = update.effective_user.id
        prompt = text_after_command(update)
        if not prompt:
            await update.message.reply_text(
                "Usage: /edit replace the sofa with walnut furniture"
                if edit else "Usage: /render luxury living room with travertine walls"
            )
            return

        source = None
        if edit:
            reply = update.message.reply_to_message
            source = get_media(reply) if reply else None
            if not source:
                last = store.get_last_image(uid)
                if last:
                    source = (last, "previous.jpg")
            if not source:
                await update.message.reply_text(
                    "First generate an image with /render or reply to an image with /edit."
                )
                return

        await update.message.reply_text("Processing image request...")
        references = []
        if source:
            references.append(await download_image(context.bot, *source))
        for file_id, filename in store.get_refs(uid):
            if len(references) >= 5:
                break
            # Avoid sending a duplicate when the edit target is also a reference.
            if not source or file_id != source[0]:
                references.append(await download_image(context.bot, file_id, filename))

        result = await asyncio.to_thread(
            generate,
            settings.openai_api_key,
            MODELS[store.get_model(uid)],
            prompt,
            references,
            is_edit=edit,
        )
        sent = await update.message.reply_photo(
            photo=io.BytesIO(result),
            caption=f"Rendered with {MODELS[store.get_model(uid)]}",
        )
        if sent.photo:
            store.set_last_image(uid, sent.photo[-1].file_id)

    async def render(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await render_or_edit(update, context, edit=False)

    async def edit(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await render_or_edit(update, context, edit=True)

    async def devin(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not authorized(update, settings):
            return
        if not settings.devin_api_key or not settings.devin_org_id:
            await update.message.reply_text("Devin disabled: configure DEVIN_API_KEY and DEVIN_ORG_ID.")
            return
        task = text_after_command(update)
        if not task:
            await update.message.reply_text("Usage: /devin Add a material preset command")
            return
        session = await create_session(settings.devin_api_key, settings.devin_org_id, task)
        session_id = session.get("session_id") or session.get("id") or session.get("session", {}).get("session_id")
        url = session.get("url") or session.get("web_url") or ""
        await update.message.reply_text(f"Devin session: {session_id or 'created'}\n{url}")

    async def devin_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not authorized(update, settings):
            return
        if not settings.devin_api_key or not settings.devin_org_id:
            await update.message.reply_text("Devin integration is not configured.")
            return
        sid = text_after_command(update)
        if not sid:
            await update.message.reply_text("Usage: /devin_status SESSION_ID")
            return
        session = await get_session(settings.devin_api_key, settings.devin_org_id, sid)
        await update.message.reply_text(
            f"Session: {sid}\nStatus: {session.get('status', 'unknown')}"
        )

    async def handle_error(update: object, context: ContextTypes.DEFAULT_TYPE):
        log.error("Telegram handler failed", exc_info=context.error)
        if isinstance(update, Update) and authorized(update, settings):
            try:
                await update.effective_message.reply_text("Request failed. Check server logs.")
            except Exception:
                log.exception("Unable to send error message")

    return [
        CommandHandler("start", start),
        CommandHandler("help", start),
        CommandHandler("model", set_model),
        CommandHandler("refs", refs),
        CommandHandler("clearrefs", clearrefs),
        CommandHandler("render", render),
        CommandHandler("edit", edit),
        CommandHandler("devin", devin),
        CommandHandler("devin_status", devin_status),
        MessageHandler(filters.PHOTO | filters.Document.IMAGE, save_reference),
    ], handle_error


def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    settings = load_settings()
    store = Store(settings.db_path)
    application = Application.builder().token(settings.telegram_token).build()
    handlers, error_handler = build_handlers(settings, store)
    for handler in handlers:
        application.add_handler(handler)
    application.add_error_handler(error_handler)
    log.info("Starting Deven bot for %d allowlisted users", len(settings.allowed_ids))
    application.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
