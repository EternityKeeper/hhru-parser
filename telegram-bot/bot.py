import asyncio
import logging
import os
import re
import time
from datetime import datetime

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

from db import Database
from checker import check_subscription

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHECK_INTERVAL = int(os.environ.get("CHECK_INTERVAL", "30"))
DATA_DIR = os.environ.get("DATA_DIR", "/app/data")
SCRAPER_BIN = os.environ.get("SCRAPER_BIN", "/usr/local/bin/scraper")

db = Database(os.path.join(DATA_DIR, "bot.db"))


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 <b>HH.ru Vacancy Bot</b>\n\n"
        "Я отслеживаю новые вакансии с hh.ru по вашим подпискам.\n\n"
        "<b>Команды:</b>\n\n"
        "<code>/subscribe &lt;запрос&gt;</code> — подписаться\n"
        "  Параметры (опционально):\n"
        "    <code>-areas</code>    ID городов через запятую\n"
        "      1=Москва, 2=СПб, 92=Тула, 88=Казань,\n"
        "      4=Новосибирск, 53=Краснодар, 3=Екатеринбург\n"
        "    <code>-period</code>   период в днях (1-7, по умолч. 3)\n"
        "    <code>-level</code>    junior / middle / senior\n\n"
        "  <b>Пример:</b>\n"
        "  <code>/subscribe Golang -areas 1,2 -period 7 -level senior</code>\n\n"
        "<code>/list</code> — показать подписки\n"
        "<code>/unsubscribe &lt;id&gt;</code> — удалить подписку\n"
        "<code>/check</code> — проверить новые вакансии сейчас",
        parse_mode="HTML",
    )


def _parse_subscribe_args(text: str) -> dict | str:
    parts = text.strip().split()
    if not parts:
        return "Укажите поисковый запрос.\nПример: <code>/subscribe Golang -areas 1,2</code>"

    query = parts[0]
    kwargs = {"areas": "1,2", "period": 3, "level_filter": ""}

    i = 1
    while i < len(parts):
        if parts[i].startswith("-"):
            key = parts[i][1:]
            i += 1
            if i >= len(parts):
                return f"После <code>-{key}</code> нужно указать значение."
            val = parts[i]
            if key == "areas":
                kwargs["areas"] = val
            elif key == "period":
                try:
                    kwargs["period"] = max(1, min(7, int(val)))
                except ValueError:
                    return "Период должен быть числом (1-7)."
            elif key == "level":
                if val.lower() not in ("junior", "middle", "senior"):
                    return "Уровень: junior, middle или senior."
                kwargs["level_filter"] = val.lower()
            else:
                return f"Неизвестный параметр: <code>-{key}</code>"
        i += 1

    return {"query": query, **kwargs}


async def cmd_subscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(
            "Укажите запрос.\nПример:\n"
            "<code>/subscribe Golang -areas 1,2 -period 7 -level senior</code>",
            parse_mode="HTML",
        )
        return

    text = " ".join(context.args)
    result = _parse_subscribe_args(text)
    if isinstance(result, str):
        await update.message.reply_text(result, parse_mode="HTML")
        return

    user = update.effective_user
    sub_id = db.add_subscription(
        user_id=user.id,
        chat_id=update.effective_chat.id,
        query=result["query"],
        areas=result["areas"],
        period=result["period"],
        level_filter=result["level_filter"],
    )

    if sub_id is None:
        await update.message.reply_text(
            "❌ Такая подписка уже существует."
        )
        return

    areas_str = ", ".join(
        {"1": "Москва", "2": "СПб", "3": "Екб", "4": "Нск",
         "53": "Краснодар", "88": "Казань", "92": "Тула"}.get(
            a.strip(), a.strip()
        )
        for a in result["areas"].split(",")
    )

    text = (
        f"✅ <b>Подписка #{sub_id} создана</b>\n"
        f"Запрос: {result['query']}\n"
        f"Города: {areas_str}\n"
        f"Период: {result['period']} дн."
    )
    if result["level_filter"]:
        text += f"\nУровень: {result['level_filter']}"

    await update.message.reply_text(text, parse_mode="HTML")


async def cmd_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    subs = db.get_user_subscriptions(update.effective_user.id)
    if not subs:
        await update.message.reply_text(
            "У вас нет подписок.\n"
            "Создайте через <code>/subscribe &lt;запрос&gt;</code>",
            parse_mode="HTML",
        )
        return

    lines = ["<b>Ваши подписки:</b>\n"]
    for s in subs:
        line = (
            f"\n#{s['id']} — <b>{s['query']}</b>\n"
            f"   Города: {s['areas']} · период: {s['period']} дн."
        )
        if s["level_filter"]:
            line += f" · уровень: {s['level_filter']}"
        lines.append(line)

    await update.message.reply_text("".join(lines), parse_mode="HTML")


async def cmd_unsubscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args or not context.args[0].isdigit():
        await update.message.reply_text(
            "Укажите ID подписки.\n"
            "Пример: <code>/unsubscribe 1</code>",
            parse_mode="HTML",
        )
        return

    sub_id = int(context.args[0])
    if db.remove_subscription(sub_id, update.effective_user.id):
        await update.message.reply_text(f"✅ Подписка #{sub_id} удалена.")
    else:
        await update.message.reply_text(
            "❌ Подписка не найдена. Проверьте ID через /list"
        )


async def cmd_check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    subs = db.get_user_subscriptions(update.effective_user.id)
    if not subs:
        await update.message.reply_text(
            "У вас нет подписок.\n"
            "Создайте через <code>/subscribe &lt;запрос&gt;</code>",
            parse_mode="HTML",
        )
        return

    await update.message.reply_text("🔍 Проверяю новые вакансии...")

    total_new = 0
    for sub in subs:
        msg = check_subscription(sub, SCRAPER_BIN, DATA_DIR, db)
        if msg:
            try:
                await update.message.reply_text(msg, parse_mode="HTML")
                total_new += 1
            except Exception as e:
                logger.error("Failed to send message: %s", e)

    if total_new == 0:
        await update.message.reply_text("Новых вакансий нет.")


async def scheduled_check(context: ContextTypes.DEFAULT_TYPE):
    subs = db.get_subscriptions()
    if not subs:
        return

    logger.info("Scheduled check: %d subscriptions", len(subs))
    for sub in subs:
        try:
            msg = check_subscription(sub, SCRAPER_BIN, DATA_DIR, db)
            if msg:
                await context.bot.send_message(
                    chat_id=sub["chat_id"], text=msg, parse_mode="HTML"
                )
        except Exception as e:
            logger.error(
                "Check failed for sub #%d (chat=%d): %s",
                sub["id"], sub["chat_id"], e,
            )


def main():
    logger.info("Starting bot...")
    app = (
        Application.builder()
        .token(TOKEN)
        .connect_timeout(30)
        .read_timeout(30)
        .write_timeout(30)
        .build()
    )

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("subscribe", cmd_subscribe))
    app.add_handler(CommandHandler("list", cmd_list))
    app.add_handler(CommandHandler("unsubscribe", cmd_unsubscribe))
    app.add_handler(CommandHandler("check", cmd_check))

    job_queue = app.job_queue
    job_queue.run_repeating(
        scheduled_check, interval=CHECK_INTERVAL * 60, first=15
    )

    logger.info(
        "Bot started. Check interval: %d min", CHECK_INTERVAL
    )
    max_retries = 5
    for attempt in range(1, max_retries + 1):
        try:
            asyncio.run(_start(app))
            break
        except Exception as e:
            logger.error(
                "Start attempt %d/%d failed: %s", attempt, max_retries, e
            )
            if attempt < max_retries:
                wait = 2 ** attempt
                logger.info("Retrying in %d seconds...", wait)
                time.sleep(wait)


async def _start(app: Application) -> None:
    await app.initialize()
    await app.start()
    await app.updater.start_polling(allowed_updates=Update.ALL_TYPES)
    logger.info("Bot is running")
    while True:
        await asyncio.sleep(3600)


if __name__ == "__main__":
    main()
