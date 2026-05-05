import os
import telebot
from telebot import types

BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_TOKEN_HERE")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")
states = {}

def main_menu():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("🚕 Taksi chaqirish")
    kb.row("📞 Aloqa")
    return kb

@bot.message_handler(commands=["start"])
def start(message):
    bot.send_message(message.chat.id, "🚕 <b>Taxi Bot</b>\n\nTaksi chaqirish uchun tugmani bosing 👇", reply_markup=main_menu())

@bot.message_handler(func=lambda m: m.text == "🚕 Taksi chaqirish")
def order_taxi(message):
    states[message.from_user.id] = {"step": "from"}
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("❌ Bekor qilish", callback_data="cancel"))
    bot.send_message(message.chat.id, "📍 <b>Qayerdan?</b>\n\nManzilni yozing:", reply_markup=kb)

@bot.message_handler(func=lambda m: states.get(m.from_user.id, {}).get("step") == "from")
def get_from(message):
    states[message.from_user.id] = {"step": "to", "from": message.text}
    bot.send_message(message.chat.id, "📍 <b>Qayerga?</b>\n\nManzilni yozing:")

@bot.message_handler(func=lambda m: states.get(m.from_user.id, {}).get("step") == "to")
def get_to(message):
    states[message.from_user.id]["to"] = message.text
    states[message.from_user.id]["step"] = "phone"
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    kb.add(types.KeyboardButton("📞 Raqamni yuborish", request_contact=True))
    bot.send_message(message.chat.id, "📞 <b>Telefon raqamingiz?</b>", reply_markup=kb)

@bot.message_handler(content_types=["contact"])
def get_contact(message):
    state = states.get(message.from_user.id)
    if not state or state.get("step") != "phone":
        return
    phone = message.contact.phone_number
    username = f"@{message.from_user.username}" if message.from_user.username else "yo'q"

    bot.send_message(ADMIN_ID, f"""🚕 <b>Yangi taksi buyurtma</b>

👤 User: {username}
🆔 ID: <code>{message.from_user.id}</code>
📞 Tel: {phone}

📍 Qayerdan: {state['from']}
📍 Qayerga: {state['to']}""")

    states.pop(message.from_user.id, None)
    bot.send_message(message.chat.id, "✅ <b>Buyurtma qabul qilindi!</b>\n\nHaydovchi tez orada siz bilan bog'lanadi.", reply_markup=main_menu())

@bot.callback_query_handler(func=lambda c: c.data == "cancel")
def cancel(call):
    states.pop(call.from_user.id, None)
    bot.send_message(call.message.chat.id, "❌ Bekor qilindi.", reply_markup=main_menu())

@bot.message_handler(func=lambda m: m.text == "📞 Aloqa")
def contact(message):
    bot.send_message(message.chat.id, "📞 Admin: @X_VBRAIN")

print("Taxi bot ishga tushdi!")
bot.infinity_polling(skip_pending=True)
