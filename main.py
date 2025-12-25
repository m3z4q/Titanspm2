import asyncio
import aiohttp
import time
import random
from datetime import datetime
from telegram import Update, ChatMember, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.error import RetryAfter, BadRequest

BOT_TOKEN = "8519181173:AAF9dPbQ5J5N_Q6iAaQBULFpaDJTX_CNmGs"
OWNER_ID = 8487272111  # Change to your owner id
CHANNEL_USERNAME = "@TITANXBOTMAKING"
DEEPSEEK_API = "https://deepseek-op.hosters.club/api/?q={}"

EMOJIS = ["🔥","⚡","💀","👑","😈","🚀","💥","🌀","🧨","🎯","🐉","🦁","☠️"]

broadcast_list = set()
blocked_users = set()
gcnc_tasks = {}
spam_tasks = {}
new_user_notify = False

# Check owner
def is_owner(user_id: int) -> bool:
    return user_id == OWNER_ID

# Check admin in group
async def is_admin(update: Update, user_id: int) -> bool:
    chat = update.effective_chat
    try:
        member = await chat.get_member(user_id)
        return member.status in [ChatMember.ADMINISTRATOR, ChatMember.CREATOR]
    except:
        return False

class TelegramBot:
    def __init__(self):
        self.app = Application.builder().token(BOT_TOKEN).build()
        self.app.bot_data['start_time'] = time.time()
        self.setup_handlers()

    def setup_handlers(self):
        self.app.add_handler(CommandHandler("start", self.start))
        self.app.add_handler(CommandHandler("help", self.help_cmd))

        self.app.add_handler(CommandHandler("broadcast", self.broadcast))
        self.app.add_handler(CommandHandler("stats", self.stats))
        self.app.add_handler(CommandHandler("newusernotify", self.new_user_notify_cmd))

        self.app.add_handler(CommandHandler("spam", self.spam))
        self.app.add_handler(CommandHandler("stopspam", self.stop_spam))

        self.app.add_handler(CommandHandler("gcnc", self.gcnc))
        self.app.add_handler(CommandHandler("stopgcnc", self.stop_gcnc))

        self.app.add_handler(CommandHandler("forcejoin", self.force_join))

        self.app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), self.ai_reply))
        self.app.add_handler(MessageHandler(filters.ALL, self.track_chat))

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        # Add chat id to broadcast list
        broadcast_list.add(update.effective_chat.id)
        await update.message.reply_text(f"🤖 Bot Online!\nUse /help\n\nPowered by {CHANNEL_USERNAME}")

    async def help_cmd(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        help_text = f"""
/start - Start the bot
/help - This help message

Owner only:
/broadcast <message> - Broadcast message
/stats - Show stats
/newusernotify on/off - Toggle new user notify

Group Admin only:
/spam <count> <text> <speed> - Spam messages
/stopspam - Stop spam
/gcnc <count> <name> <speed> - Change group name repeatedly
/stopgcnc - Stop GCNC

General:
/forcejoin - Join official channel
"""
        await update.message.reply_text(help_text)

    async def broadcast(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not is_owner(update.effective_user.id):
            await update.message.reply_text("❌ Only owner can broadcast.")
            return
        if not context.args:
            await update.message.reply_text("Usage: /broadcast <message>")
            return
        message = ' '.join(context.args) + f"\n\nPowered by {CHANNEL_USERNAME}"
        sent = 0
        failed = 0
        for chat_id in list(broadcast_list):
            try:
                await context.bot.send_message(chat_id, message)
                sent += 1
                await asyncio.sleep(0.5)
            except Exception:
                failed += 1
        await update.message.reply_text(f"Broadcast done.\nSent: {sent}\nFailed: {failed}")

    async def stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not is_owner(update.effective_user.id):
            await update.message.reply_text("❌ Only owner can view stats.")
            return
        uptime = int(time.time() - context.bot_data['start_time'])
        uptime_str = str(datetime.utcfromtimestamp(uptime).strftime("%H:%M:%S"))
        text = f"Bot Stats:\nUptime: {uptime_str}\nChats: {len(broadcast_list)}\nBlocked Users: {len(blocked_users)}\n\nPowered by {CHANNEL_USERNAME}"
        await update.message.reply_text(text)

    async def new_user_notify_cmd(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not is_owner(update.effective_user.id):
            await update.message.reply_text("❌ Only owner can toggle this.")
            return
        if not context.args or context.args[0].lower() not in ['on', 'off']:
            await update.message.reply_text("Usage: /newusernotify on/off")
            return
        global new_user_notify
        new_user_notify = (context.args[0].lower() == 'on')
        await update.message.reply_text(f"New user notify set to {context.args[0].lower()}")

    async def spam(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        chat = update.effective_chat
        if chat.type not in ['group', 'supergroup']:
            await update.message.reply_text("This command is only for groups.")
            return
        if not await is_admin(update, user.id):
            await update.message.reply_text("❌ Only group admins can use this command.")
            return
        if len(context.args) < 3:
            await update.message.reply_text("Usage: /spam <count> <text> <speed>")
            return
        try:
            count = int(context.args[0])
            speed = float(context.args[-1])
            text = ' '.join(context.args[1:-1])
        except:
            await update.message.reply_text("Invalid args. Usage: /spam <count> <text> <speed>")
            return
        if chat.id in spam_tasks:
            await update.message.reply_text("Spam already running. Use /stopspam to stop.")
            return

        async def spam_task():
            for _ in range(count):
                try:
                    await context.bot.send_message(chat.id, text)
                    await asyncio.sleep(speed)
                except Exception:
                    break
            spam_tasks.pop(chat.id, None)

        spam_tasks[chat.id] = asyncio.create_task(spam_task())
        await update.message.reply_text(f"Started spamming {count} messages.")

    async def stop_spam(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        chat = update.effective_chat
        if chat.type not in ['group', 'supergroup']:
            await update.message.reply_text("This command is only for groups.")
            return
        if not await is_admin(update, user.id):
            await update.message.reply_text("❌ Only group admins can use this command.")
            return
        task = spam_tasks.pop(chat.id, None)
        if task:
            task.cancel()
            await update.message.reply_text("Stopped spam.")
        else:
            await update.message.reply_text("No spam running.")

    async def gcnc(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        chat = update.effective_chat
        if chat.type not in ['group', 'supergroup']:
            await update.message.reply_text("This command is only for groups.")
            return
        if not await is_admin(update, user.id):
            await update.message.reply_text("❌ Only group admins can use this command.")
            return
        if len(context.args) < 3:
            await update.message.reply_text("Usage: /gcnc <count> <name> <speed>")
            return
        try:
            count = int(context.args[0])
            speed = float(context.args[-1])
            base_name = ' '.join(context.args[1:-1])
        except:
            await update.message.reply_text("Invalid args. Usage: /gcnc <count> <name> <speed>")
            return
        if chat.id in gcnc_tasks:
            await update.message.reply_text("GCNC already running. Use /stopgcnc to stop.")
            return

        async def gcnc_task():
            for i in range(count):
                try:
                    await context.bot.set_chat_title(chat.id, f"{random.choice(EMOJIS)} {base_name} {i+1}")
                    await asyncio.sleep(speed)
                except RetryAfter as e:
                    await asyncio.sleep(e.retry_after)
                except BadRequest:
                    await asyncio.sleep(5)
            gcnc_tasks.pop(chat.id, None)

        gcnc_tasks[chat.id] = asyncio.create_task(gcnc_task())
        await update.message.reply_text(f"Started GC name change {count} times.")

    async def stop_gcnc(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        chat = update.effective_chat
        if chat.type not in ['group', 'supergroup']:
            await update.message.reply_text("This command is only for groups.")
            return
        if not await is_admin(update, user.id):
            await update.message.reply_text("❌ Only group admins can use this command.")
            return
        task = gcnc_tasks.pop(chat.id, None)
        if task:
            task.cancel()
            await update.message.reply_text("Stopped GCNC.")
        else:
            await update.message.reply_text("No GCNC running.")

    async def force_join(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        button_url = "https://t.me/joinchat/your_invite_link_here"  # Replace with actual invite link
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("Join Now", url=button_url)]])
        await update.message.reply_text("🚨 Please join our official channel to continue using the bot.", reply_markup=keyboard)

    async def ai_reply(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        text = update.message.text
        if text.startswith('/'):
            return
        if update.effective_user.id in blocked_users:
            return
        url = DEEPSEEK_API.format(text)
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        reply = data.get('reply', "Sorry, no reply found.")
                        reply += f"\n\nPowered by {CHANNEL_USERNAME}"
                        await update.message.reply_text(reply)
                    else:
                        await update.message.reply_text("❌ API Error. Try again later.")
            except Exception:
                await update.message.reply_text("❌ API Request Failed.")

    async def track_chat(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        # Save chat id for broadcasting
        broadcast_list.add(update.effective_chat.id)

    async def run(self):
        print("Bot started...")
        await self.app.run_polling()

if __name__ == "__main__":
    bot = TelegramBot()
    asyncio.run(bot.run())
