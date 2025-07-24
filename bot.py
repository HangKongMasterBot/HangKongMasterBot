import os
import json
import random
import time
from flask import Flask, request
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, Bot
from telegram.ext import Dispatcher, CommandHandler, CallbackQueryHandler, CallbackContext
from telegram.utils.request import Request

BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN")
CHANNEL_USERNAME = "@grandlakeofficial"
ADMIN_ID = 6059977122  # তোমার আইডি
DATA_FILE = "users.json"
WITHDRAW_FILE = "withdraw.json"
PROMO_FILE = "promo.json"

users_data = json.load(open(DATA_FILE)) if os.path.exists(DATA_FILE) else {}
withdraw_requests = json.load(open(WITHDRAW_FILE)) if os.path.exists(WITHDRAW_FILE) else []
promo_codes = json.load(open(PROMO_FILE)) if os.path.exists(PROMO_FILE) else {}

def save_all():
    json.dump(users_data, open(DATA_FILE, "w"))
    json.dump(withdraw_requests, open(WITHDRAW_FILE, "w"))
    json.dump(promo_codes, open(PROMO_FILE, "w"))

app = Flask(__name__)
bot = Bot(token=BOT_TOKEN)

# Dispatcher with worker threads (workers=4) for async callbacks
dispatcher = Dispatcher(bot, None, workers=4, use_context=True)

def is_member(user_id, context):
    try:
        member = context.bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in ["member", "administrator", "creator"]
    except:
        return False

def start(update: Update, context: CallbackContext):
    user_id = str(update.effective_user.id)
    username = update.effective_user.username or "User"
    ref_id = context.args[0] if len(context.args) > 0 else None

    if user_id not in users_data:
        users_data[user_id] = {"coins": 0, "referrals": 0, "last_daily": 0}
        if ref_id and ref_id != user_id and ref_id in users_data:
            users_data[ref_id]["coins"] += 50
            users_data[ref_id]["referrals"] += 1
        save_all()

    if not is_member(update.effective_user.id, context):
        update.message.reply_text("❌ চ্যানেলে জয়েন করুন!", reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("✅ Join", url=f"https://t.me/{CHANNEL_USERNAME[1:]}")]]
        ))
        return

    keyboard = [
        [InlineKeyboardButton("🎁 Collect Coins", callback_data="collect_coins")],
        [InlineKeyboardButton("💰 Balance", callback_data="check_balance"),
         InlineKeyboardButton("🏆 Leaderboard", callback_data="leaderboard")],
        [InlineKeyboardButton("🎲 Lucky Spin", callback_data="lucky_spin"),
         InlineKeyboardButton("🔢 Guess Game", callback_data="guess_game")],
        [InlineKeyboardButton("💳 Withdraw", callback_data="withdraw")]
    ]
    update.message.reply_text(
        f"👋 হ্যালো {username}!\nরেফারেল লিংক:\nhttps://t.me/{context.bot.username}?start={user_id}",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def daily(update: Update, context: CallbackContext):
    user_id = str(update.effective_user.id)
    now = int(time.time())
    if now - users_data[user_id].get("last_daily", 0) >= 86400:
        users_data[user_id]["coins"] += 20
        users_data[user_id]["last_daily"] = now
        save_all()
        update.message.reply_text("✅ আজকের ডেইলি বোনাস ক্লেইম হয়েছে! (+20 coins)")
    else:
        update.message.reply_text("❌ আপনি আজকে বোনাস নিয়েছেন। কাল চেষ্টা করুন!")

def profile(update: Update, context: CallbackContext):
    user_id = str(update.effective_user.id)
    coins = users_data[user_id]["coins"]
    refs = users_data[user_id]["referrals"]
    update.message.reply_text(f"👤 Profile:\n💰 Coins: {coins}\n👥 Referrals: {refs}")

def redeem(update: Update, context: CallbackContext):
    user_id = str(update.effective_user.id)
    code = context.args[0] if len(context.args) > 0 else None
    if code and code in promo_codes:
        amount = promo_codes.pop(code)
        users_data[user_id]["coins"] += amount
        save_all()
        update.message.reply_text(f"✅ Promo Code Applied! (+{amount} coins)")
    else:
        update.message.reply_text("❌ Invalid Promo Code!")

def create_promo(update: Update, context: CallbackContext):
    if update.effective_user.id != ADMIN_ID:
        update.message.reply_text("❌ Access Denied")
        return
    try:
        code, amount = context.args[0], int(context.args[1])
        promo_codes[code] = amount
        save_all()
        update.message.reply_text(f"✅ Promo Created: {code} (+{amount} coins)")
    except:
        update.message.reply_text("❌ Usage: /createpromo CODE AMOUNT")

def admin(update: Update, context: CallbackContext):
    if update.effective_user.id != ADMIN_ID:
        update.message.reply_text("❌ Access Denied")
        return
    keyboard = [
        [InlineKeyboardButton("📋 Withdraw Requests", callback_data="view_withdraw")],
        [InlineKeyboardButton("💎 Add Coins", callback_data="add_coins_menu")],
        [InlineKeyboardButton("🎁 Send Bonus", callback_data="send_bonus_menu")]
    ]
    update.message.reply_text("✅ Admin Panel:", reply_markup=InlineKeyboardMarkup(keyboard))

def button_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = str(query.from_user.id)

    if query.data == "collect_coins":
        users_data[user_id]["coins"] += 10
        save_all()
        query.edit_message_text(f"🎉 10 Coins যোগ হয়েছে!\nTotal: {users_data[user_id]['coins']}")
    
    elif query.data == "check_balance":
        coins = users_data[user_id]["coins"]
        refs = users_data[user_id]["referrals"]
        query.edit_message_text(f"💰 Coins: {coins}\n👥 Referrals: {refs}")
    
    elif query.data == "leaderboard":
        sorted_users = sorted(users_data.items(), key=lambda x: x[1]["coins"], reverse=True)[:5]
        lb = "\n".join([f"{i+1}. User {uid[-4:]} - {data['coins']} coins" for i, (uid, data) in enumerate(sorted_users)])
        query.edit_message_text(f"🏆 Leaderboard:\n{lb}")

    elif query.data == "lucky_spin":
        reward = random.choice([0, 10, 20, 50, 100])
        users_data[user_id]["coins"] += reward
        save_all()
        query.edit_message_text(f"🎲 Lucky Spin Result: +{reward} coins!")

    elif query.data == "guess_game":
        number = random.randint(1, 5)
        reward = 50 if number == 3 else 0
        users_data[user_id]["coins"] += reward
        save_all()
        query.edit_message_text(f"🔢 You guessed! Secret: {number}. Reward: +{reward} coins!")

    elif query.data == "withdraw":
        if users_data[user_id]["coins"] >= 100:
            withdraw_requests.append({"user_id": user_id, "amount": 100})
            users_data[user_id]["coins"] -= 100
            save_all()
            query.edit_message_text("✅ Withdraw Request Sent!")
        else:
            query.edit_message_text("❌ 100 coins দরকার!")

dispatcher.add_handler(CommandHandler("start", start))
dispatcher.add_handler(CommandHandler("daily", daily))
dispatcher.add_handler(CommandHandler("profile", profile))
dispatcher.add_handler(CommandHandler("redeem", redeem))
dispatcher.add_handler(CommandHandler("createpromo", create_promo))
dispatcher.add_handler(CommandHandler("admin", admin))
dispatcher.add_handler(CallbackQueryHandler(button_handler))

@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    dispatcher.process_update(update)
    return "ok", 200

@app.route("/")
def index():
    return "Bot is running!", 200

if __name__ == "__main__":
    PORT = int(os.environ.get("PORT", 5000))
    bot.delete_webhook()
    bot.set_webhook(url=f"https://{os.environ.get('RENDER_EXTERNAL_HOSTNAME')}/{BOT_TOKEN}")
    app.run(host="0.0.0.0", port=PORT)
