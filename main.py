import asyncio
import random
from telegram import Update, ChatMember, Chat, ParseMode
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
from telegram.error import RetryAfter, BadRequest

BOT_TOKEN = "8487272111:AAEkEnUUuOg-YuJxyGS0z9lqGhhWn6HPokU"
OWNER_ID = 8453291493  # Apna Telegram user ID yahan daalein
FORCE_JOIN_CHANNEL = "@TITANXBOTMAKING"  # Jo public channel user ko join karna hoga

EMOJIS = ["🔥","⚡","💀","👑","😈","🚀","💥","🌀","🧨","🎯","🐉","🦁","☠️"]
gcnc_tasks = {}
joined_users = set()
groups = set()

async def is_user_admin(update: Update, user_id: int) -> bool:
    chat = update.effective_chat
    try:
        member = await chat.get_member(user_id)
        return member.status in [ChatMember.ADMINISTRATOR, ChatMember.CREATOR]
    except Exception:
        return False

async def has_joined_channel(user_id: int, app: Application) -> bool:
    try:
        member = await app.bot.get_chat_member(FORCE_JOIN_CHANNEL, user_id)
        return member.status not in ["left", "kicked"]
    except Exception:
        return False

async def permission_check(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    chat = update.effective_chat
    user = update.effective_user

    # Force join check
    if not await has_joined_channel(user.id, context.application):
        await update.message.reply_text(
            f"🚫 Pehle {FORCE_JOIN_CHANNEL} channel join karein phir commands use karein."
        )
        return False

    if chat.type == "private":
        return True
    elif chat.type in ["group", "supergroup"]:
        return await is_user_admin(update, user.id)
    else:
        return False

# Notify owner about new user in any group
async def new_user_notify(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.new_chat_members:
        for new_member in update.message.new_chat_members:
            # Notify owner
            try:
                text = (f"👤 New user joined:\n"
                        f"User: {new_member.mention_html()}\n"
                        f"Group: {update.effective_chat.title} ({update.effective_chat.id})")
                await context.bot.send_message(
                    OWNER_ID, text, parse_mode=ParseMode.HTML
                )
            except Exception:
                pass

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await permission_check(update, context):
        return
    await update.message.reply_text("🤖 Bot Online\n/help")

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await permission_check(update, context):
        return
    await update.message.reply_text(
        "/spam <count> <text>\n"
        "/gcnc <count> <name>\n"
        "/stopgcnc\n"
        "/stats\n"
        "/broadcast <message> (owner only)"
    )

async def spam(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await permission_check(update, context):
        return

    if len(context.args) < 2:
        await update.message.reply_text("Usage: /spam <count> <text>")
        return

    try:
        count = int(context.args[0])
    except ValueError:
        await update.message.reply_text("Count must be a number.")
        return

    text = " ".join(context.args[1:])
    for _ in range(count):
        await update.message.reply_text(text)
        await asyncio.sleep(0.1)

async def gcnc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await permission_check(update, context):
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

    if chat.id in gcnc_tasks:
        await update.message.reply_text("⚠️ GCNC pehle se chal raha hai.")
        return

    gcnc_tasks[chat.id] = asyncio.create_task(loop())
    groups.add(chat.id)
    await update.message.reply_text("✅ GCNC started")

async def stopgcnc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await permission_check(update, context):
        return

    task = gcnc_tasks.pop(update.effective_chat.id, None)
    if task:
        task.cancel()
        await update.message.reply_text("🛑 GCNC stopped")
    else:
        await update.message.reply_text("Koi GCNC chal nahi raha hai.")

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    total_groups = len(groups)
    total_gcnc = len(gcnc_tasks)
    text = (
        f"📊 Bot Stats:\n"
        f"Groups: {total_groups}\n"
        f"Running GCNC tasks: {total_gcnc}"
    )
    await update.message.reply_text(text)

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id != OWNER_ID:
        await update.message.reply_text("❌ Sirf owner hi broadcast kar sakta hai.")
        return

    if not context.args:
        await update.message.reply_text("Usage: /broadcast <message>")
        return

    message = " ".join(context.args)
    success = 0
    failed = 0

    for chat_id in list(groups):
        try:
            await context.bot.send_message(chat_id, f"📢 Broadcast:\n\n{message}")
            success += 1
            await asyncio.sleep(0.1)  # Throttle to avoid flood limits
        except Exception:
            failed += 1

    await update.message.reply_text(f"Broadcast complete.\nSuccess: {success}\nFailed: {failed}")

async def track_groups(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Track all groups where bot is added
    chat = update.effective_chat
    if chat.type in ["group", "supergroup"]:
        groups.add(chat.id)

app = Application.builder().token(BOT_TOKEN).build()

# Command handlers
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("help", help_cmd))
app.add_handler(CommandHandler("spam", spam))
app.add_handler(CommandHandler("gcnc", gcnc))
app.add_handler(CommandHandler("stopgcnc", stopgcnc))
app.add_handler(CommandHandler("stats", stats))
app.add_handler(CommandHandler("broadcast", broadcast))

# New user notify in groups
app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, new_user_notify))

# Track groups when bot joins or gets message
app.add_handler(MessageHandler(filters.ALL & filters.ChatType.GROUPS, track_groups))

app.run_polling()
