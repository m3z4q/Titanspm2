import asyncio
import random
import time
import platform
import psutil
import io
import requests
import qrcode

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)
from telegram.error import RetryAfter, BadRequest

# ================= CONFIG =================

BOT_TOKEN = "8487272111:AAEkEnUUuOg-YuJxyGS0z9lqGhhWn6HPokU"
OWNER_ID = 8453291493  # Replace with your Telegram user ID

FORCE_CHANNEL = "@TITANXBOTMAKING"  # Replace with your channel username
FORCE_CHANNEL_URL = "https://t.me/TITANXBOTMAKING"  # Replace with your channel URL

AI_API_URL = "https://deepseek-op.hosters.club/api/?q={}"  # Replace with your AI API URL

EMOJIS = [
    "🔥","⚡","💀","👑","😈","🚀","💥","🌀","🧨","🎯",
    "🐉","🦁","☠️","👹","👺","🧠","🗿","🦅","🐺","🐍",
    "🦂","🕷️","💣","🔪","⚔️","🛡️","🏴‍☠️","👁️","🩸","🧬",
    "🌪️","🌋","🌑","🌕","💎","🔮","📛","🚨","🧿","🎭",
    "🦇","🐲","🦈","🐯","🦍","🐗","🦊","🐻","🐼","🐅"
]

# ================= STORAGE =================

users = set()
groups = set()

spam_tasks = {}
gcnc_tasks = {}
raid_tasks = {}

# ================= HELPERS =================

def is_owner(update):
    return update.effective_user.id == OWNER_ID

async def is_admin(update, context):
    if update.effective_chat.type == "private":
        return True
    try:
        admins = await context.bot.get_chat_administrators(
            update.effective_chat.id
        )
        return any(a.user.id == update.effective_user.id for a in admins)
    except:
        return False

async def force_join(update, context):
    if is_owner(update):
        return True
    try:
        m = await context.bot.get_chat_member(
            FORCE_CHANNEL, update.effective_user.id
        )
        return m.status in ["member", "administrator", "creator"]
    except:
        return False

# ================= START / HELP =================

async def start(update, context):
    if not await force_join(update, context):
        btn = [[InlineKeyboardButton(
            "✅ Join Channel", url=FORCE_CHANNEL_URL
        )]]
        await update.message.reply_text(
            "🔒 Bot use karne ke liye channel join karo",
            reply_markup=InlineKeyboardMarkup(btn)
        )
        return

    users.add(update.effective_user.id)
    if update.effective_chat.type != "private":
        groups.add(update.effective_chat.id)

    await update.message.reply_text("🤖 Bot Online\n/help")

async def help_cmd(update, context):
    await update.message.reply_text(
        "🔧 UTILITIES\n"
        "/ping - Check bot latency\n"
        "/info - Chat information\n"
        "/sysinfo - System statistics\n"
        "/qr <text> - Generate QR code\n\n"
        "💬 CHAT TOOLS (Admin Only)\n"
        "/spam <n> <text> - Spam messages\n"
        "/stopspam - Stop spam\n"
        "/flood <n> <text> - Flood messages\n"
        "/gcnc <n> <name> - Group name change\n"
        "/stopgcnc - Stop GCNC\n"
        "/raid - Start raid mode\n"
        "/stopraid - Stop raid mode\n\n"
        "👮 ADMIN\n"
        "/ban (reply) - Ban a user\n"
        "/mute (reply) - Mute a user\n\n"
        "🔐 OWNER\n"
        "/broadcast <msg> - Broadcast message\n"
        "/stats - Show stats\n\n"
        "© Bot Framework by @TITANXCONTACT"
    )

# ================= UTILITIES =================

async def ping(update, context):
    t = time.time()
    m = await update.message.reply_text("🏓 Pinging...")
    await m.edit_text(f"🏓 Pong: {int((time.time()-t)*1000)} ms")

async def info(update, context):
    c = update.effective_chat
    await update.message.reply_text(
        f"ℹ️ Chat Info\nID: {c.id}\nType: {c.type}\nTitle: {c.title}"
    )

async def sysinfo(update, context):
    await update.message.reply_text(
        f"🖥 OS: {platform.system()}\n"
        f"CPU: {psutil.cpu_percent()}%\n"
        f"RAM: {psutil.virtual_memory().percent}%"
    )

async def qr_cmd(update, context):
    img = qrcode.make(" ".join(context.args))
    bio = io.BytesIO()
    img.save(bio, "PNG")
    bio.seek(0)
    await update.message.reply_photo(bio)

# ================= SPAM / FLOOD =================

async def spam(update, context):
    if not await is_admin(update, context):
        return

    chat_id = update.effective_chat.id
    n = int(context.args[0])
    text = " ".join(context.args[1:])

    async def loop():
        try:
            for _ in range(n):
                await update.message.reply_text(text)
                await asyncio.sleep(0.2)
        except asyncio.CancelledError:
            pass

    spam_tasks[chat_id] = asyncio.create_task(loop())

async def stopspam(update, context):
    if not await is_admin(update, context):
        return

    task = spam_tasks.pop(update.effective_chat.id, None)
    if task:
        task.cancel()
        await update.message.reply_text("🛑 Spam stopped")

async def flood(update, context):
    if not await is_admin(update, context):
        return

    n = int(context.args[0])
    text = " ".join(context.args[1:])
    for _ in range(min(n, 30)):
        await update.message.reply_text(text)
        await asyncio.sleep(0.1)

# ================= GCNC =================

async def gcnc(update, context):
    if not await is_admin(update, context):
        return

    chat = update.effective_chat
    n = int(context.args[0])
    base = " ".join(context.args[1:])

    async def loop():
        try:
            for i in range(n):
                await chat.set_title(
                    f"{random.choice(EMOJIS)} {base} {i+1}"
                )
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            pass

    gcnc_tasks[chat.id] = asyncio.create_task(loop())

async def stopgcnc(update, context):
    if not await is_admin(update, context):
        return

    task = gcnc_tasks.pop(update.effective_chat.id, None)
    if task:
        task.cancel()
        await update.message.reply_text("🛑 GCNC stopped")

# ================= RAID =================

async def raid(update, context):
    if not await is_admin(update, context):
        return

    cid = update.effective_chat.id

    async def loop():
        try:
            while True:
                await context.bot.send_message(cid, "🔥 RAID MODE 🔥")
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            pass

    raid_tasks[cid] = asyncio.create_task(loop())

async def stopraid(update, context):
    if not await is_admin(update, context):
        return

    t = raid_tasks.pop(update.effective_chat.id, None)
    if t:
        t.cancel()
        await update.message.reply_text("🛑 Raid stopped")

# ================= ADMIN =================

async def ban(update, context):
    if not await is_admin(update, context):
        return
    if update.message.reply_to_message:
        u = update.message.reply_to_message.from_user
        await context.bot.ban_chat_member(
            update.effective_chat.id, u.id
        )

async def mute(update, context):
    if not await is_admin(update, context):
        return
    if update.message.reply_to_message:
        u = update.message.reply_to_message.from_user
        await context.bot.restrict_chat_member(
            update.effective_chat.id,
            u.id,
            permissions={}
        )

# ================= OWNER =================

async def broadcast(update, context):
    if not is_owner(update):
        return

    msg = " ".join(context.args)
    for cid in users | groups:
        try:
            await context.bot.send_message(cid, msg)
            await asyncio.sleep(0.1)
        except:
            pass

async def stats(update, context):
    if not is_owner(update):
        return

    await update.message.reply_text(
        f"👤 Users: {len(users)}\n👥 Groups: {len(groups)}"
    )

# ================= AI CHAT =================

async def ai_chat(update, context):
    if update.message.text.startswith("/"):
        return

    if update.effective_chat.type != "private":
        if not await is_admin(update, context):
            return

    try:
        r = requests.post(
            AI_API_URL,
            json={"message": update.message.text},
            timeout=10
        )
        data = r.json()

        reply = (
            data.get("reply")
            or data.get("response")
            or "No response"
        )

        reply += "\n\n— @TITANXBOTMAKING"

        await update.message.reply_text(reply)

    except:
        await update.message.reply_text("⚠️ AI error")

# ================= APP =================

app = Application.builder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("help", help_cmd))

app.add_handler(CommandHandler("ping", ping))
app.add_handler(CommandHandler("info", info))
app.add_handler(CommandHandler("sysinfo", sysinfo))
app.add_handler(CommandHandler("qr", qr_cmd))

app.add_handler(CommandHandler("spam", spam))
app.add_handler(CommandHandler("stopspam", stopspam))
app.add_handler(CommandHandler("flood", flood))

app.add_handler(CommandHandler("gcnc", gcnc))
app.add_handler(CommandHandler("stopgcnc", stopgcnc))

app.add_handler(CommandHandler("raid", raid))
app.add_handler(CommandHandler("stopraid", stopraid))

app.add_handler(CommandHandler("ban", ban))
app.add_handler(CommandHandler("mute", mute))

app.add_handler(CommandHandler("broadcast", broadcast))
app.add_handler(CommandHandler("stats", stats))

app.add_handler(
    MessageHandler(filters.TEXT & ~filters.COMMAND, ai_chat)
)

app.run_polling()
