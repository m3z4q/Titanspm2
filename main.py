import asyncio
import aiohttp
import time
from datetime import datetime
from telegram import Update, ChatMember, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.error import RetryAfter

TOKEN = "8487272111:AAEkEnUUuOg-YuJxyGS0z9lqGhhWn6HPokU"
OWNER_ID = 8487272111
FORCE_JOIN_USER_ID = 8453291493
CHANNEL_USERNAME = "@TITANXBOTMAKING"
DEEPSEEK_API = "https://deepseek-op.hosters.club/api/?q={}"

broadcast_list = set()
raid_tasks = {}
blocked_users = set()
spam_tasks = {}
gcnc_tasks = {}

# Utility: Check if user is owner
def is_owner(user_id: int) -> bool:
    return user_id == OWNER_ID

# Utility: Check if user is admin of a chat
async def is_admin(update: Update, user_id: int) -> bool:
    chat = update.effective_chat
    try:
        member = await chat.get_member(user_id)
        return member.status in [ChatMember.ADMINISTRATOR, ChatMember.CREATOR]
    except:
        return False

class TelegramBot:
    def __init__(self):
        self.app = Application.builder().token(TOKEN).build()
        self.setup_handlers()
        self.app.bot_data['start_time'] = time.time()

    def setup_handlers(self):
        self.app.add_handler(CommandHandler("start", self.start))
        self.app.add_handler(CommandHandler("help", self.help_command))

        self.app.add_handler(CommandHandler("broadcast", self.broadcast))
        self.app.add_handler(CommandHandler("stats", self.stats))
        self.app.add_handler(CommandHandler("newusernotify", self.new_user_notify))

        self.app.add_handler(CommandHandler("spam", self.spam))
        self.app.add_handler(CommandHandler("stopspam", self.stop_spam))
        self.app.add_handler(CommandHandler("gcnc", self.gcnc))
        self.app.add_handler(CommandHandler("stopgcnc", self.stop_gcnc))

        self.app.add_handler(CommandHandler("forcejoin", self.force_join))

        self.app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), self.ai_reply))

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(
            f"Hello! Use /help to see commands.\n\nPowered by {CHANNEL_USERNAME}"
        )

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        help_text = f"""
🔧 UTILITIES
/start - Start the bot
/help - Show this help

💬 CHAT TOOLS (Admin only in GC)
/spam <count> <text> <speed> - Spam messages
/stopspam - Stop spam
/gcnc <count> <name> <speed> - Change GC name repeatedly
/stopgcnc - Stop GC name change

🚨 OWNER COMMANDS
/broadcast <message> - Broadcast to all chats
/stats - Show bot stats
/newusernotify on/off - New user join notify toggle
/forcejoin - Force join button message

AI chat: Just send a message in private or GC

Powered by {CHANNEL_USERNAME}
"""
        await update.message.reply_text(help_text)

    # Broadcast - owner only
    async def broadcast(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not is_owner(update.effective_user.id):
            await update.message.reply_text("❌ Only owner can broadcast.")
            return

        if not context.args:
            await update.message.reply_text("Usage: /broadcast <message>")
            return

        message = ' '.join(context.args) + f"\n\n{CHANNEL_USERNAME}"
        count_sent = 0
        count_fail = 0

        for chat_id in list(broadcast_list):
            try:
                await context.bot.send_message(chat_id, message)
                count_sent += 1
                await asyncio.sleep(0.5)
            except Exception as e:
                count_fail += 1

        await update.message.reply_text(
            f"Broadcast completed.\nSent: {count_sent}\nFailed: {count_fail}"
        )

    # Stats - owner only
    async def stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not is_owner(update.effective_user.id):
            await update.message.reply_text("❌ Only owner can view stats.")
            return

        uptime_seconds = int(time.time() - context.bot_data['start_time'])
        uptime_str = str(datetime.utcfromtimestamp(uptime_seconds).strftime("%H:%M:%S"))

        text = f"""
Bot Stats:
Uptime: {uptime_str}
Chats: {len(broadcast_list)}
Blocked Users: {len(blocked_users)}

Powered by {CHANNEL_USERNAME}
"""
        await update.message.reply_text(text)

    # New User Notify toggle - owner only
    async def new_user_notify(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        # Simple toggle example, extendable with persistence
        if not is_owner(update.effective_user.id):
            await update.message.reply_text("❌ Only owner can toggle this.")
            return
        if not context.args or context.args[0].lower() not in ['on', 'off']:
            await update.message.reply_text("Usage: /newusernotify on/off")
            return
        val = context.args[0].lower()
        context.bot_data['new_user_notify'] = (val == 'on')
        await update.message.reply_text(f"New user notify set to {val}")

    # Spam command - only GC admin
    async def spam(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        if not update.effective_chat.type in ['group', 'supergroup']:
            await update.message.reply_text("This command works only in groups.")
            return
        if not await is_admin(update, user.id):
            await update.message.reply_text("❌ Only GC admins can use spam.")
            return

        if len(context.args) < 3:
            await update.message.reply_text("Usage: /spam <count> <text> <speed>")
            return

        try:
            count = int(context.args[0])
            speed = float(context.args[-1])
            text = ' '.join(context.args[1:-1])
        except:
            await update.message.reply_text("Invalid arguments. Usage: /spam <count> <text> <speed>")
            return

        chat_id = update.effective_chat.id

        if chat_id in spam_tasks:
            await update.message.reply_text("Spam is already running. Use /stopspam to stop.")
            return

        async def spam_task():
            for _ in range(count):
                try:
                    await context.bot.send_message(chat_id, text)
                    await asyncio.sleep(speed)
                except Exception:
                    break
            spam_tasks.pop(chat_id, None)

        spam_tasks[chat_id] = asyncio.create_task(spam_task())
        await update.message.reply_text(f"Started spamming {count} messages.")

    async def stop_spam(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        if not update.effective_chat.type in ['group', 'supergroup']:
            await update.message.reply_text("This command works only in groups.")
            return
        if not await is_admin(update, user.id):
            await update.message.reply_text("❌ Only GC admins can stop spam.")
            return

        chat_id = update.effective_chat.id
        task = spam_tasks.get(chat_id)
        if task:
            task.cancel()
            spam_tasks.pop(chat_id, None)
            await update.message.reply_text("Spam stopped.")
        else:
            await update.message.reply_text("No active spam task.")

    # GCNC command - only GC admin
    async def gcnc(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        if not update.effective_chat.type in ['group', 'supergroup']:
            await update.message.reply_text("This command works only in groups.")
            return
        if not await is_admin(update, user.id):
            await update.message.reply_text("❌ Only GC admins can use GCNC.")
            return

        if len(context.args) < 3:
            await update.message.reply_text("Usage: /gcnc <count> <name> <speed>")
            return

        try:
            count = int(context.args[0])
            speed = float(context.args[-1])
            name = ' '.join(context.args[1:-1])
        except:
            await update.message.reply_text("Invalid arguments. Usage: /gcnc <count> <name> <speed>")
            return

        chat_id = update.effective_chat.id

        if chat_id in gcnc_tasks:
            await update.message.reply_text("GCNC is already running. Use /stopgcnc to stop.")
            return

        async def gcnc_task():
            for _ in range(count):
                try:
                    await context.bot.set_chat_title(chat_id, name)
                    await asyncio.sleep(speed)
                except Exception:
                    break
            gcnc_tasks.pop(chat_id, None)

        gcnc_tasks[chat_id] = asyncio.create_task(gcnc_task())
        await update.message.reply_text(f"Started GC name change to '{name}' {count} times.")

    async def stop_gcnc(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        if not update.effective_chat.type in ['group', 'supergroup']:
            await update.message.reply_text("This command works only in groups.")
            return
        if not await is_admin(update, user.id):
            await update.message.reply_text("❌ Only GC admins can stop GCNC.")
            return

        chat_id = update.effective_chat.id
        task = gcnc_tasks.get(chat_id)
        if task:
            task.cancel()
            gcnc_tasks.pop(chat_id, None)
            await update.message.reply_text("GCNC stopped.")
        else:
            await update.message.reply_text("No active GCNC task.")

    # Force Join message with inline button
    async def force_join(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        if user.id != FORCE_JOIN_USER_ID:
            await update.message.reply_text("❌ You are not authorized for this command.")
            return
        button_url = f"https://t.me/joinchat/{FORCE_JOIN_USER_ID}"
        keyboard = InlineKeyboardMarkup(
            [[InlineKeyboardButton("Join Now", url=button_url)]]
        )
        await update.message.reply_text(
            "🚨 Please join our official channel to continue using the bot.",
            reply_markup=keyboard
        )

    # AI reply using DeepSeek API with channel tag
    async def ai_reply(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        text = update.message.text
        chat_type = update.effective_chat.type
        # Ignore commands
        if text.startswith('/'):
            return

        # Blocked user check
        if update.effective_user.id in blocked_users:
            return

        url = DEEPSEEK_API.format(text)
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        reply_text = data.get('reply') or "Sorry, no reply found."
                        reply_text += f"\n\nPowered by {CHANNEL_USERNAME}"
                        await update.message.reply_text(reply_text)
                    else:
                        await update.message.reply_text("❌ API Error. Try again later.")
            except Exception:
                await update.message.reply_text("❌ API Request Failed.")

    async def run(self):
        print("Bot started...")
        await self.app.run_polling()

if __name__ == "__main__":
    bot = TelegramBot()
    asyncio.run(bot.run())
