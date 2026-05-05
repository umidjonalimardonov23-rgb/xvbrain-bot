import os
import telebot
from telebot import types

BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_TOKEN_HERE")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
CHANNEL_ID = os.getenv("CHANNEL_ID", "@your_channel")

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

def check_sub(user_id):
    try:
        member = bot.get_chat_member(CHANNEL_ID, user_id)
        return member.status not in ["left", "kicked"]
    except:
        return False

def main_menu():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("🎁 Sovg'a olish", "📢 Kanal")
    return kb

@bot.message_handler(commands=["start"])
def start(message):
    if check_sub(message.from_user.id):
        bot.send_message(message.chat.id, "✅ <b>Xush kelibsiz!</b>\n\nSiz kanalga obuna bo'lgansiz.", reply_markup=main_menu())
    else:
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("📢 Kanalga obuna bo'lish", url=f"https://t.me/{CHANNEL_ID.lstrip('@')}"))
        kb.add(types.InlineKeyboardButton("✅ Obuna bo'ldim", callback_data="check_sub"))
        bot.send_message(message.chat.id, """⚠️ <b>Avval kanalga obuna bo'ling!</b>

Botdan foydalanish uchun quyidagi kanalga obuna bo'ling 👇""", reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data == "check_sub")
def verify_sub(call):
    if check_sub(call.from_user.id):
        bot.answer_callback_query(call.id, "✅ Tasdiqlandi!")
        bot.send_message(call.message.chat.id, "✅ <b>Rahmat!</b>\n\nEndi botdan foydalanishingiz mumkin.", reply_markup=main_menu())
    else:
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("📢 Obuna bo'lish", url=f"https://t.me/{CHANNEL_ID.lstrip('@')}"))
        kb.add(types.InlineKeyboardButton("✅ Tekshirish", callback_data="check_sub"))
        bot.answer_callback_query(call.id, "❌ Hali obuna bo'lmadingiz!")
        bot.send_message(call.message.chat.id, "❌ Siz hali obuna bo'lmadingiz. Avval obuna bo'ling!", reply_markup=kb)

@bot.message_handler(func=lambda m: m.text == "📢 Kanal")
def channel(message):
    bot.send_message(message.chat.id, f"📢 Kanal: {CHANNEL_ID}")

@bot.message_handler(func=lambda m: m.text == "🎁 Sovg'a olish")
def gift(message):
    if not check_sub(message.from_user.id):
        start(message)
        return
    bot.send_message(message.chat.id, "🎁 Sovg'angiz tez orada yuboriladi!")

print("Obuna bot ishga tushdi!")
bot.infinity_polling(skip_pending=True)
