import asyncio
import random
from telegram import Update, ChatMember, ChatMemberUpdated
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ChatMemberHandler,
    filters,
    ContextTypes,
)
from telegram.constants import ChatMemberStatus

# -------- CONFIG --------
BOT_TOKEN = "8487272111:AAEkEnUUuOg-YuJxyGS0z9lqGhhWn6HPokU"
FORCE_JOIN_CHANNEL = "@TITANXBOTMAKING"
OWNER_ID = 8453291493  # Aapka user id for broadcast permissions

EMOJIS = ["🔥","⚡","💀","👑","😈","🚀","💥","🌀","🧨","🎯","🐉","🦁","☠️"]

# Storage for ongoing gcnc tasks and groups
gcnc_tasks = {}
joined_groups = set()

# -------- FORCE JOIN CHECK --------
async def check_force_join(user_id: int, app: Application) -> bool:
    try:
        member = await app.bot.get_chat_member(FORCE_JOIN_CHANNEL, user_id)
        return member.status in [
            ChatMemberStatus.MEMBER,
            ChatMemberStatus.ADMINISTRATOR,
            ChatMemberStatus.OWNER,
            ChatMemberStatus.RESTRICTED,
        ]
    except Exception:
        return False

# -------- COMMANDS --------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 Bot Online!\nUse /help for commands."
    )

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "/spam <count> <text> - Spam message (GC admins only)\n"
        "/gcnc <count> <name> - Change GC name repeatedly (GC admins only)\n"
        "/stopgcnc - Stop name changing (GC admins only)\n"
        "/stats - Show bot stats\n"
        "/broadcast <message> - Broadcast message to all groups (Owner only)"
    )

async def spam(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat = update.effective_chat

    # Force join check
    if not await check_force_join(user.id, context.application):
        return await update.message.reply_text(
            f"❗ Please join {FORCE_JOIN_CHANNEL} channel first."
        )

    # GC or private chat check
    if chat.type in ["group", "supergroup"]:
        member = await chat.get_member(user.id)
        if not member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
            return await update.message.reply_text("❌ Only group admins can use this command here.")
    else:
        # Private chat allowed
        pass

    if len(context.args) < 2:
        return await update.message.reply_text("Usage: /spam <count> <text>")

    try:
        count = int(context.args[0])
        text = " ".join(context.args[1:])
    except:
        return await update.message.reply_text("Invalid arguments.")

    for _ in range(count):
        await update.message.reply_text(text)
        await asyncio.sleep(0.1)

async def gcnc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat = update.effective_chat

    # Force join check
    if not await check_force_join(user.id, context.application):
        return await update.message.reply_text(
            f"❗ Please join {FORCE_JOIN_CHANNEL} channel first."
        )

    # GC only and admin check
    if chat.type not in ["group", "supergroup"]:
        return await update.message.reply_text("This command can only be used in groups.")
    member = await chat.get_member(user.id)
    if not member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
        return await update.message.reply_text("❌ Only group admins can use this command.")

    parts = update.message.text.split(maxsplit=2)
    if len(parts) < 3:
        return await update.message.reply_text("Usage: /gcnc <count> <base_name>")

    base = parts[2]

    async def loop():
        i = 0
        while True:
            try:
                await chat.set_title(f"{random.choice(EMOJIS)} {base} {i+1}")
                i += 1
                await asyncio.sleep(2)
            except Exception as e:
                await asyncio.sleep(5)

    # Cancel previous if running
    if chat.id in gcnc_tasks:
        gcnc_tasks[chat.id].cancel()

    gcnc_tasks[chat.id] = asyncio.create_task(loop())
    await update.message.reply_text("✅ GCNC started")

async def stopgcnc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user = update.effective_user

    if chat.type not in ["group", "supergroup"]:
        return await update.message.reply_text("This command can only be used in groups.")
    member = await chat.get_member(user.id)
    if not member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
        return await update.message.reply_text("❌ Only group admins can use this command.")

    task = gcnc_tasks.pop(chat.id, None)
    if task:
        task.cancel()
        await update.message.reply_text("🛑 GCNC stopped")
    else:
        await update.message.reply_text("No GCNC task running.")

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"📊 Bot Stats:\nGroups: {len(joined_groups)}"
    )

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id != OWNER_ID:
        return await update.message.reply_text("❌ You are not authorized to use this.")

    if not context.args:
        return await update.message.reply_text("Usage: /broadcast <message>")

    message = " ".join(context.args)
    count = 0
    for group_id in joined_groups:
        try:
            await context.bot.send_message(chat_id=group_id, text=message)
            count += 1
        except:
            pass

    await update.message.reply_text(f"✅ Broadcast sent to {count} groups.")

# -------- NEW USER NOTIFY --------
async def welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    if chat.type not in ["group", "supergroup"]:
        return
    for member in update.message.new_chat_members:
        await update.message.reply_text(
            f"👋 Welcome {member.mention_html()} to {chat.title}!",
            parse_mode="HTML"
        )

# -------- TRACK JOINED GROUPS --------
async def track_groups(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    if chat.type in ["group", "supergroup"]:
        joined_groups.add(chat.id)

# -------- MAIN --------

async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❓ Unknown command. Use /help.")

def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("spam", spam))
    app.add_handler(CommandHandler("gcnc", gcnc))
    app.add_handler(CommandHandler("stopgcnc", stopgcnc))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("broadcast", broadcast))
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome))
    app.add_handler(MessageHandler(filters.COMMAND, unknown))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, track_groups))

    app.run_polling()

if __name__ == "__main__":
    main()
