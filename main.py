import asyncio
import time
import random
import aiohttp
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler, filters, ContextTypes
)
from telegram.error import RetryAfter, BadRequest

# Configurations
TOKEN = "8487272111:AAEkEnUUuOg-YuJxyGS0z9lqGhhWn6HPokU"
OWNER_ID = 8487272111
CHANNEL_USERNAME = "@TITANXBOTMAKING"
FORCE_JOIN_USER_ID = 8453291493
DEEPSEEK_API = "https://deepseek-op.hosters.club/api/?q={}"

EMOJIS = [
    "🔥","⚡","💀","👑","😈","🚀","💥","🌀","🧨","🎯","🐉","🦁","☠️",
    "🌟","🌈","💫","✨","💣","🎉","🎊","🚨","⚔️","🛡️","💎","🎵","🎶",
    "🌪️","⚡","🕷️","🦄","🦅","🐺","🐍","🐢","🐬","🦖","🦈","🐉","👹",
    "👻","🤖","🧙‍♂️","🧛‍♂️","🧟‍♂️","💀","👽","👾","🎃","🛸","🚁","🚀",
    "🛡️","⚔️","🗡️","🔫","🧨","💣"
]

# Storage
broadcast_list = set()
gcnc_tasks = {}
spam_tasks = {}
raid_tasks = {}
blocked_users = set()

class Bot:
    def __init__(self):
        self.app = Application.builder().token(TOKEN).build()
        self.setup_handlers()

    def is_owner(self, user_id):
        return user_id == OWNER_ID

    async def is_chat_admin(self, update: Update):
        user_id = update.effective_user.id
        chat = update.effective_chat

        if chat.type == "private":
            return True  # private chat, treat as admin for ease

        member = await self.app.bot.get_chat_member(chat.id, user_id)
        return member.status in ["administrator", "creator"]

    def setup_handlers(self):
        # Basic commands
        self.app.add_handler(CommandHandler("start", self.start))
        self.app.add_handler(CommandHandler("help", self.help_command))
        self.app.add_handler(CommandHandler("ping", self.ping))
        self.app.add_handler(CommandHandler("info", self.info))
        self.app.add_handler(CommandHandler("sysinfo", self.sysinfo))

        # Owner-only commands
        self.app.add_handler(CommandHandler("broadcast", self.broadcast))
        self.app.add_handler(CommandHandler("stats", self.stats))

        # Chat commands restricted to admins only
        self.app.add_handler(CommandHandler("spam", self.spam))
        self.app.add_handler(CommandHandler("stopspam", self.stop_spam))
        self.app.add_handler(CommandHandler("gcnc", self.gcnc))
        self.app.add_handler(CommandHandler("stopgcnc", self.stop_gcnc))
        self.app.add_handler(CommandHandler("flood", self.flood))
        self.app.add_handler(CommandHandler("raid", self.raid))
        self.app.add_handler(CommandHandler("stopraid", self.stop_raid))

        # AI chat reply
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.ai_reply))

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.effective_chat.id
        if chat_id not in broadcast_list:
            broadcast_list.add(chat_id)

        keyboard = [
            [InlineKeyboardButton("👉 Join Channel 👈", url=f"https://t.me/{CHANNEL_USERNAME.lstrip('@')}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            f"🤖 Bot Online!\nUse /help for commands.\n\nPlease join our channel: {CHANNEL_USERNAME}",
            reply_markup=reply_markup
        )

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        help_text = f"""🔧 UTILITIES
/ping - Check bot latency
/info - Chat information
/sysinfo - System statistics

💬 CHAT TOOLS (Admin only)
/spam <count> <text> <speed> - Spam messages
/stopspam - Stop spam
/gcnc <count> <name> <speed> - Group name change
/stopgcnc - Stop group name change
/flood <count> <text> <speed> - Flood messages
/raid <count> <text> - Start raid
/stopraid - Stop raid

👮 OWNER ONLY
/broadcast <message> - Broadcast message to all groups
/stats - Bot statistics

───────
🔧 Powered by {CHANNEL_USERNAME}"""
        await update.message.reply_text(help_text)

    async def ping(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        start_time = time.time()
        msg = await update.message.reply_text("🏓 Pinging...")
        end_time = time.time()
        latency = round((end_time - start_time)*1000, 2)
        await msg.edit_text(f"🏓 Pong!\nLatency: {latency}ms\n\n🔧 {CHANNEL_USERNAME}")

    async def info(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat = update.effective_chat
        user = update.effective_user
        text = f"""📊 Chat Info

Chat ID: {chat.id}
Chat Type: {chat.type}
Chat Title: {chat.title or 'N/A'}

Your ID: {user.id}
Username: {user.username or 'N/A'}
Name: {user.full_name}

───────
🔧 Powered by {CHANNEL_USERNAME}"""
        await update.message.reply_text(text)

    async def sysinfo(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        uptime_seconds = time.time() - context.bot_data.get("start_time", time.time())
        hours = int(uptime_seconds // 3600)
        minutes = int((uptime_seconds % 3600) // 60)
        text = f"""🖥 System Info

Uptime: {hours}h {minutes}m

───────
🔧 Powered by {CHANNEL_USERNAME}"""
        await update.message.reply_text(text)

    async def broadcast(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not self.is_owner(update.effective_user.id):
            await update.message.reply_text("❌ Only owner can broadcast!")
            return

        if not context.args:
            await update.message.reply_text("❌ Usage: /broadcast <message>")
            return

        message = ' '.join(context.args)
        watermark = f"\n\n───────\n🔧 Powered by {CHANNEL_USERNAME}"
        full_msg = f"📢 Broadcast message:\n\n{message}{watermark}"

        sent = 0
        failed = 0
        status_msg = await update.message.reply_text("📢 Broadcasting...")

        for chat_id in list(broadcast_list):
            try:
                await context.bot.send_message(chat_id, full_msg)
                sent += 1
                await asyncio.sleep(0.3)
            except Exception as e:
                failed += 1
                print(f"Broadcast failed to {chat_id}: {e}")

        await status_msg.edit_text(f"✅ Broadcast completed!\nSent: {sent}\nFailed: {failed}")

    async def spam(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not await self.is_chat_admin(update):
            await update.message.reply_text("❌ Only group admins can use /spam!")
            return

        if len(context.args) < 3:
            await update.message.reply_text("❌ Usage: /spam <count> <text> <speed>")
            return

        try:
            count = int(context.args[0])
            speed = float(context.args[-1])
            text = " ".join(context.args[1:-1])
        except Exception:
            await update.message.reply_text("❌ Invalid parameters.")
            return

        chat_id = update.effective_chat.id

        async def spam_loop():
            for _ in range(count):
                try:
                    await context.bot.send_message(chat_id, text)
                    await asyncio.sleep(speed)
                except RetryAfter as e:
                    await asyncio.sleep(e.retry_after)
                except BadRequest:
                    await asyncio.sleep(1)

        if chat_id in spam_tasks:
            spam_tasks[chat_id].cancel()
        spam_tasks[chat_id] = asyncio.create_task(spam_loop())
        await update.message.reply_text("✅ Started spamming!")

    async def stop_spam(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not await self.is_chat_admin(update):
            await update.message.reply_text("❌ Only group admins can use /stopspam!")
            return

        chat_id = update.effective_chat.id
        task = spam_tasks.pop(chat_id, None)
        if task:
            task.cancel()
            await update.message.reply_text("🛑 Spam stopped!")
        else:
            await update.message.reply_text("ℹ️ No active spam to stop.")

    async def gcnc(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not await self.is_chat_admin(update):
            await update.message.reply_text("❌ Only group admins can use /gcnc!")
            return

        if len(context.args) < 3:
            await update.message.reply_text("❌ Usage: /gcnc <count> <name> <speed>")
            return

        try:
            count = int(context.args[0])
            name = context.args[1]
            speed = float(context.args[2])
        except Exception:
            await update.message.reply_text("❌ Invalid parameters.")
            return

        chat_id = update.effective_chat.id

        async def gcnc_loop():
            for i in range(count):
                try:
                    new_title = f"{random.choice(EMOJIS)} {name} {i+1}"
                    await context.bot.set_chat_title(chat_id, new_title)
                    await asyncio.sleep(speed)
                except RetryAfter as e:
                    await asyncio.sleep(e.retry_after)
                except BadRequest:
                    await asyncio.sleep(2)

        if chat_id in gcnc_tasks:
            gcnc_tasks[chat_id].cancel()
        gcnc_tasks[chat_id] = asyncio.create_task(gcnc_loop())
        await update.message.reply_text("✅ Started GC name changer!")

    async def stop_gcnc(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not await self.is_chat_admin(update):
            await update.message.reply_text("❌ Only group admins can use /stopgcnc!")
            return

        chat_id = update.effective_chat.id
        task = gcnc_tasks.pop(chat_id, None)
        if task:
            task.cancel()
            await update.message.reply_text("🛑 GC name changer stopped!")
        else:
            await update.message.reply_text("ℹ️ No active GC name changer.")

    async def flood(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not await self.is_chat_admin(update):
            await update.message.reply_text("❌ Only group admins can use /flood!")
            return

        if len(context.args) < 3:
            await update.message.reply_text("❌ Usage: /flood <count> <text> <speed>")
            return

        try:
            count = int(context.args[0])
            text = context.args[1]
            speed = float(context.args[2])
        except Exception:
            await update.message.reply_text("❌ Invalid parameters.")
            return

        chat_id = update.effective_chat.id

        for _ in range(count):
            try:
                await context.bot.send_message(chat_id, text)
                await asyncio.sleep(speed)
            except RetryAfter as e:
                await asyncio.sleep(e.retry_after)
            except BadRequest:
                await asyncio.sleep(1)

        await update.message.reply_text("✅ Flood completed!")

    async def raid(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not await self.is_chat_admin(update):
            await update.message.reply_text("❌ Only group admins can use /raid!")
            return

        if len(context.args) < 2:
            await update.message.reply_text("❌ Usage: /raid <count> <text>")
            return

        try:
            count = int(context.args[0])
            text = " ".join(context.args[1:])
        except Exception:
            await update.message.reply_text("❌ Invalid parameters.")
            return

        chat_id = update.effective_chat.id

        async def raid_loop():
            for _ in range(count):
                try:
                    await context.bot.send_message(chat_id, text)
                    await asyncio.sleep(0.5)
                except RetryAfter as e:
                    await asyncio.sleep(e.retry_after)
                except BadRequest:
                    await asyncio.sleep(1)

        if chat_id in raid_tasks:
            raid_tasks[chat_id].cancel()
        raid_tasks[chat_id] = asyncio.create_task(raid_loop())
        await update.message.reply_text("✅ Raid started!")

    async def stop_raid(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not await self.is_chat_admin(update):
            await update.message.reply_text("❌ Only group admins can use /stopraid!")
            return

        chat_id = update.effective_chat.id
        task = raid_tasks.pop(chat_id, None)
        if task:
            task.cancel()
            await update.message.reply_text("🛑 Raid stopped!")
        else:
            await update.message.reply_text("ℹ️ No active raid.")

    async def stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not self.is_owner(update.effective_user.id):
            await update.message.reply_text("❌ Owner only!")
            return

        uptime_seconds = time.time() - context.bot_data.get("start_time", time.time())
        hours = int(uptime_seconds // 3600)
        minutes = int((uptime_seconds % 3600) // 60)

        text = f"""📊 Bot Stats:

Uptime: {hours}h {minutes}m
Active Groups: {len(broadcast_list)}
Active Spam Tasks: {len(spam_tasks)}
Active GCNC Tasks: {len(gcnc_tasks)}
Active Raid Tasks: {len(raid_tasks)}
Blocked Users: {len(blocked_users)}

───────
🔧 Powered by {CHANNEL_USERNAME}"""
        await update.message.reply_text(text)

    async def ai_reply(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        # Ignore blocked users
        if update.effective_user.id in blocked_users:
            return

        text = update.message.text.strip()
        if not text:
            return

        query = text.replace(" ", "+")
        url = DEEPSEEK_API.format(query)

        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, timeout=10) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        answer = data.get("answer") or "Sorry, I don't know about that."
                        reply = f"{answer}\n\n🔧 {CHANNEL_USERNAME}"
                        await update.message.reply_text(reply)
                    else:
                        await update.message.reply_text(f"⚠️ API error. Please try again later.\n\n🔧 {CHANNEL_USERNAME}")
            except Exception as e:
                await update.message.reply_text(f"⚠️ Error: {str(e)}\n\n🔧 {CHANNEL_USERNAME}")

    def run(self):
        self.app.run_polling()

if __name__ == "__main__":
    bot = Bot()
    bot.run()
