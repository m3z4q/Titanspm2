import asyncio
import random
from telegram import Update, ChatMember, Chat
from telegram.constants import ParseMode
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    ContextTypes, filters
)
from telegram.error import RetryAfter, BadRequest

# ------------- CONFIGURATION -----------------

BOT_TOKEN = "8487272111:AAEkEnUUuOg-YuJxyGS0z9lqGhhWn6HPokU"
OWNER_ID = 8453291493
FORCE_JOIN_CHANNEL = "@TITANXBOTMAKING"  # Public channel username

EMOJIS = ["🔥","⚡","💀","👑","😈","🚀","💥","🌀","🧨","🎯","🐉","🦁","☠️"]

# --------------------------------------------

gcnc_tasks = {}
joined_chats = set()
user_stats = {}

async def check_force_join(user_id: int, app: Application) -> bool:
    try:
        member = await app.bot.get_chat_member(FORCE_JOIN_CHANNEL, user_id)
        return member.status != ChatMember.LEFT
    except Exception:
        return False

async def is_user_admin(update: Update, user_id: int) -> bool:
    try:
        admins = await update.effective_chat.get_administrators()
        return any(admin.user.id == user_id for admin in admins)
    except Exception:
        return False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    if chat.type == Chat.PRIVATE:
        await update.message.reply_text(
            "🤖 Bot Online\nUse /help to see commands."
        )
    else:
        await update.message.reply_text("This bot works mainly in private chat.")

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "/spam <count> <text> - Spam message (GC admins only)\n"
        "/gcnc <name> - Start GC name changer (GC admins only)\n"
        "/stopgcnc - Stop GC name changer (GC admins only)\n"
        "/stats - Show your spam stats\n"
        "/broadcast <message> - Send broadcast (Owner only)\n"
    )
    await update.message.reply_text(text)

async def spam(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user = update.effective_user

    # Private chat allowed
    if chat.type != Chat.PRIVATE:
        if not await is_user_admin(update, user.id):
            return await update.message.reply_text("❌ Only GC admins can use this in groups.")

    # Force join check
    if not await check_force_join(user.id, context.application):
        return await update.message.reply_text(f"❗ Please join {FORCE_JOIN_CHANNEL} first.")

    if len(context.args) < 2:
        return await update.message.reply_text("Usage: /spam <count> <text>")

    try:
        count = int(context.args[0])
        if count > 20:
            return await update.message.reply_text("Max 20 messages allowed.")
        text = " ".join(context.args[1:])
    except:
        return await update.message.reply_text("Invalid usage. Usage: /spam <count> <text>")

    for _ in range(count):
        await update.message.reply_text(text)
        await asyncio.sleep(0.5)

    user_stats[user.id] = user_stats.get(user.id, 0) + count

async def gcnc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user = update.effective_user

    if chat.type == Chat.PRIVATE:
        return await update.message.reply_text("❌ This command works only in groups.")

    if not await is_user_admin(update, user.id):
        return await update.message.reply_text("❌ Only GC admins can use this.")

    if not await check_force_join(user.id, context.application):
        return await update.message.reply_text(f"❗ Please join {FORCE_JOIN_CHANNEL} first.")

    if len(context.args) == 0:
        return await update.message.reply_text("Usage: /gcnc <name>")

    base = " ".join(context.args)

    async def loop():
        i = 0
        while True:
            try:
                new_title = f"{random.choice(EMOJIS)} {base} {i+1}"
                await chat.set_title(new_title)
                i += 1
                await asyncio.sleep(2)
            except RetryAfter as e:
                await asyncio.sleep(e.retry_after)
            except BadRequest:
                await asyncio.sleep(5)

    if chat.id in gcnc_tasks:
        gcnc_tasks[chat.id].cancel()

    gcnc_tasks[chat.id] = asyncio.create_task(loop())
    joined_chats.add(chat.id)
    await update.message.reply_text("✅ GCNC started.")

async def stopgcnc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user = update.effective_user

    if chat.type == Chat.PRIVATE:
        return await update.message.reply_text("❌ This command works only in groups.")

    if not await is_user_admin(update, user.id):
        return await update.message.reply_text("❌ Only GC admins can stop GCNC.")

    task = gcnc_tasks.pop(chat.id, None)
    if task:
        task.cancel()
        await update.message.reply_text("🛑 GCNC stopped.")
    else:
        await update.message.reply_text("No active GCNC found.")

async def new_user_notify(update: Update, context: ContextTypes.DEFAULT_TYPE):
    for member in update.message.new_chat_members:
        await update.message.reply_text(
            f"Welcome, {member.mention_html()}!", parse_mode=ParseMode.HTML
        )

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    count = user_stats.get(user.id, 0)
    await update.message.reply_text(f"📊 You have sent {count} spam messages so far.")

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    if user.id != OWNER_ID:
        return await update.message.reply_text("❌ You are not authorized to use this command.")

    if len(context.args) == 0:
        return await update.message.reply_text("Usage: /broadcast <message>")

    message = " ".join(context.args)
    count = 0

    for chat_id in joined_chats:
        try:
            await context.bot.send_message(chat_id, message)
            count += 1
        except Exception:
            continue

    await update.message.reply_text(f"📢 Broadcast sent to {count} chats.")

async def track_joined_chats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    if chat.type in [Chat.GROUP, Chat.SUPERGROUP]:
        joined_chats.add(chat.id)

# --------- SETUP AND RUN -----------

app = Application.builder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("help", help_cmd))
app.add_handler(CommandHandler("spam", spam))
app.add_handler(CommandHandler("gcnc", gcnc))
app.add_handler(CommandHandler("stopgcnc", stopgcnc))
app.add_handler(CommandHandler("stats", stats))
app.add_handler(CommandHandler("broadcast", broadcast))
app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, new_user_notify))
app.add_handler(MessageHandler(filters.ALL, track_joined_chats))

app.run_polling()
