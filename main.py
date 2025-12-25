import asyncio
import time
import random
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters
)
from telegram.error import RetryAfter, BadRequest

# ================= MULTI BOT CONFIG =================
BOT_TOKENS = [
    "8519181173:AAF9dPbQ5J5N_Q6iAaQBULFpaDJTX_CNmGs",
    "8510189857:AAE1FWYZcsLRM_a8vMBoytnpbkGxaQN5Tok",
    "8017630980:AAE622-he5-FFoZ9PkTpdS2nO9lLY0nCd8g"
]

OWNER_ID = 8453291493

# ================= STORAGE =================
raid_tasks = {}
gcnc_tasks = {}

EMOJIS = ["🔥","⚡","💀","👑","😈","🚀","💥","🌀","🧨","🎯","🐉","🦁","☠️"]

# ================= COMMANDS =================
async def start(update, context):
    await update.message.reply_text("🤖 Multi Bot Online\n/help")

async def help_cmd(update, context):
    await update.message.reply_text(
        "/spam <count> <text>\n"
        "/raid <count> <text>\n"
        "/stopraid\n"
        "/gcnc <count> <name>\n"
        "/stopgcnc"
    )

async def spam(update, context):
    try:
        count = int(context.args[0])
        text = " ".join(context.args[1:])
        for _ in range(count):
            await update.message.reply_text(text)
            await asyncio.sleep(0.4)
    except:
        await update.message.reply_text("Usage: /spam <count> <text>")

async def raid(update, context):
    try:
        chat_id = update.effective_chat.id
        count = int(context.args[0])
        text = " ".join(context.args[1:])

        async def task():
            for _ in range(count):
                await update.message.reply_text(text)
                await asyncio.sleep(0.5)

        raid_tasks[chat_id] = asyncio.create_task(task())
        await update.message.reply_text("🔥 Raid started")
    except:
        await update.message.reply_text("Usage: /raid <count> <text>")

async def stopraid(update, context):
    task = raid_tasks.pop(update.effective_chat.id, None)
    if task:
        task.cancel()
        await update.message.reply_text("🛑 Raid stopped")

async def gcnc(update, context):
    parts = update.message.text.split(maxsplit=2)
    if len(parts) < 3:
        await update.message.reply_text("Usage: /gcnc <count> <name>")
        return

    chat = update.effective_chat
    base_name = parts[2]

    async def task():
        i = 0
        while True:
            try:
                title = f"{random.choice(EMOJIS)} {base_name} {i+1}"
                await chat.set_title(title)
                i += 1
                await asyncio.sleep(2)
            except RetryAfter as e:
                await asyncio.sleep(e.retry_after + 2)
            except BadRequest:
                await asyncio.sleep(5)

    gcnc_tasks[chat.id] = asyncio.create_task(task())
    await update.message.reply_text("✅ GC Name Change Started (Unlimited)")

async def stopgcnc(update, context):
    task = gcnc_tasks.pop(update.effective_chat.id, None)
    if task:
        task.cancel()
        await update.message.reply_text("🛑 GC Name Change Stopped")

# ================= BOT STARTER =================
def run_bot(token):
    app = Application.builder().token(token).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("spam", spam))
    app.add_handler(CommandHandler("raid", raid))
    app.add_handler(CommandHandler("stopraid", stopraid))
    app.add_handler(CommandHandler("gcnc", gcnc))
    app.add_handler(CommandHandler("stopgcnc", stopgcnc))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, start))

    app.run_polling(close_loop=False)

# ================= MAIN =================
async def main():
    tasks = []
    for token in BOT_TOKENS:
        tasks.append(asyncio.to_thread(run_bot, token))
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(main())