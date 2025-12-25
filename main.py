import asyncio
import time
import random
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from telegram.error import RetryAfter, BadRequest

BOT_TOKEN = "8510189857:AAE1FWYZcsLRM_a8vMBoytnpbkGxaQN5Tok"

EMOJIS = ["🔥","⚡","💀","👑","😈","🚀","💥","🌀","🧨","🎯","🐉","🦁","☠️"]

gcnc_tasks = {}

async def start(update, context):
    await update.message.reply_text("🤖 Bot Online\n/help")

async def help_cmd(update, context):
    await update.message.reply_text(
        "/spam <count> <text>\n"
        "/gcnc <count> <name>\n"
        "/stopgcnc"
    )

async def spam(update, context):
    count = int(context.args[0])
    text = " ".join(context.args[1:])
    for _ in range(count):
        await update.message.reply_text(text)
        await asyncio.sleep(0.1)

async def gcnc(update, context):
    parts = update.message.text.split(maxsplit=2)
    chat = update.effective_chat
    base = parts[2]

    async def loop():
        i = 0
        while True:
            try:
                await chat.set_title(f"{random.choice(EMOJIS)} {base} {i+1}")
                i += 1
                await asyncio.sleep(2)
            except RetryAfter as e:
                await asyncio.sleep(e.retry_after)
            except BadRequest:
                await asyncio.sleep(5)

    gcnc_tasks[chat.id] = asyncio.create_task(loop())
    await update.message.reply_text("✅ GCNC started")

async def stopgcnc(update, context):
    task = gcnc_tasks.pop(update.effective_chat.id, None)
    if task:
        task.cancel()
        await update.message.reply_text("🛑 GCNC stopped")

app = Application.builder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("help", help_cmd))
app.add_handler(CommandHandler("spam", spam))
app.add_handler(CommandHandler("gcnc", gcnc))
app.add_handler(CommandHandler("stopgcnc", stopgcnc))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, start))

app.run_polling()
