import asyncio
import time
import random
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from telegram.error import RetryAfter, BadRequest

BOT_TOKEN = "8487272111:AAEkEnUUuOg-YuJxyGS0z9lqGhhWn6HPokU"

EMOJIS = ["🔥","⚡","💀","👑","😈","🚀","💥","🌀","🧨","🎯","🐉","🦁","☠️"]

FORCE_JOIN_CHANNEL = "@TITANXBOTMAKING"  # Yahan apna public channel username daalo

gcnc_tasks = {}

# Force join check function
async def check_force_join_channel(update, context):
    user_id = update.effective_user.id
    try:
        member = await context.bot.get_chat_member(FORCE_JOIN_CHANNEL, user_id)
        if member.status in ['left', 'kicked']:
            await update.message.reply_text(
                f"⚠️ Pehle is channel ko join karo:\nhttps://t.me/{FORCE_JOIN_CHANNEL.strip('@')}"
            )
            return False
    except Exception:
        await update.message.reply_text("⚠️ Membership check me error aaya, thoda baad try karo.")
        return False
    return True

# Admin check for group commands
async def is_user_admin(update, context):
    chat = update.effective_chat
    user_id = update.effective_user.id
    if chat.type not in ['group', 'supergroup']:
        return False
    member = await context.bot.get_chat_member(chat.id, user_id)
    return member.status in ['administrator', 'creator']

async def start(update, context):
    if not await check_force_join_channel(update, context):
        return
    await update.message.reply_text("🤖 Bot Online\n/help")

async def help_cmd(update, context):
    if not await check_force_join_channel(update, context):
        return
    await update.message.reply_text(
        "/spam <count> <text>\n"
        "/gcnc <count> <name>\n"
        "/stopgcnc"
    )

async def spam(update, context):
    if not await check_force_join_channel(update, context):
        return
    if not await is_user_admin(update, context):
        await update.message.reply_text("❌ Sirf group admins hi ye command chala sakte hain.")
        return

    try:
        count = int(context.args[0])
        text = " ".join(context.args[1:])
    except (IndexError, ValueError):
        await update.message.reply_text("Usage: /spam <count> <text>")
        return

    for _ in range(count):
        await update.message.reply_text(text)
        await asyncio.sleep(0.1)

async def gcnc(update, context):
    if not await check_force_join_channel(update, context):
        return
    if not await is_user_admin(update, context):
        await update.message.reply_text("❌ Sirf group admins hi ye command chala sakte hain.")
        return

    parts = update.message.text.split(maxsplit=2)
    if len(parts) < 3:
        await update.message.reply_text("Usage: /gcnc <count> <name>")
        return

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
    if not await check_force_join_channel(update, context):
        return
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
