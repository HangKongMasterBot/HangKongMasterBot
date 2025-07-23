import os
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, CallbackContext
from telegram.error import BadRequest

# তোমার চ্যানেল Username
CHANNEL_USERNAME = "@grandlakeofficial"

# Replit Secret থেকে BOT_TOKEN নাও
TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    print("❌ BOT_TOKEN পাওয়া যায়নি! Replit এর Secrets এ সেট করো।")
    exit()

# ইউজারদের ডাটা
users_data = {}

# চেক করবে ইউজার চ্যানেল জয়েন করেছে কিনা
def is_member(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    try:
        chat_member = context.bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return chat_member.status in ['member', 'creator', 'administrator']
    except BadRequest:
        return False

# /start কমান্ড
def start(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if not is_member(update, context):
        keyboard = [
            [InlineKeyboardButton("✅ Join Channel", url=f"https://t.me/{CHANNEL_USERNAME.strip('@')}")],
            [InlineKeyboardButton("✅ Check", callback_data='check_join')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        update.message.reply_text(
            "Please join our channel first to play HangKong Master",
            reply_markup=reply_markup
        )
        return

    if user_id not in users_data:
        users_data[user_id] = {"coins": 0}

    keyboard = [[InlineKeyboardButton("💰 Tap to Earn", callback_data='tap')]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    update.message.reply_text(
        "Welcome to HangKong Master!\nCollect coins by tapping the button below.",
        reply_markup=reply_markup
    )

# বাটনের Action
def button(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = query.from_user.id
    query.answer()

    if query.data == 'tap':
        if user_id not in users_data:
            users_data[user_id] = {"coins": 0}
        users_data[user_id]['coins'] += 1
        keyboard = [[InlineKeyboardButton("💰 Tap to Earn", callback_data='tap')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        query.edit_message_text(
            text=f"💰 Coins: {users_data[user_id]['coins']}",
            reply_markup=reply_markup
        )
    elif query.data == 'check_join':
        if is_member(update=query, context=context):
            if user_id not in users_data:
                users_data[user_id] = {"coins": 0}
            keyboard = [[InlineKeyboardButton("💰 Tap to Earn", callback_data='tap')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            query.edit_message_text(
                text="✅ Welcome to HangKong Master!\nCollect coins by tapping the button below.",
                reply_markup=reply_markup
            )
        else:
            query.answer(text="❌ You are not a member yet. Please join the channel.", show_alert=True)

# মেইন ফাংশন
def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CallbackQueryHandler(button))

    print("✅ Bot is running...")
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
