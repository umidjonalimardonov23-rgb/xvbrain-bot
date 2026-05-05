import os
import telebot
from telebot import types

BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_TOKEN_HERE")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")
states = {}

def main_menu():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("📥 Ariza yuborish")
    kb.row("📞 Aloqa")
    return kb

@bot.message_handler(commands=["start"])
def start(message):
    bot.send_message(message.chat.id, "📥 <b>Zayavka Bot</b>\n\nAriza yuborish uchun tugmani bosing 👇", reply_markup=main_menu())

@bot.message_handler(func=lambda m: m.text == "📥 Ariza yuborish")
def apply(message):
    states[message.from_user.id] = {"step": "name"}
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("❌ Bekor qilish", callback_data="cancel"))
    bot.send_message(message.chat.id, "👤 <b>Ismingizni yozing:</b>", reply_markup=kb)

@bot.message_handler(func=lambda m: states.get(m.from_user.id, {}).get("step") == "name")
def get_name(message):
    states[message.from_user.id] = {"step": "phone", "name": message.text}
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    kb.add(types.KeyboardButton("📞 Raqamni yuborish", request_contact=True))
    bot.send_message(message.chat.id, "📞 <b>Telefon raqamingiz:</b>", reply_markup=kb)

@bot.message_handler(content_types=["contact"])
def get_contact(message):
    state = states.get(message.from_user.id)
    if not state or state.get("step") != "phone":
        return
    states[message.from_user.id] = {"step": "service", "name": state["name"], "phone": message.contact.phone_number}
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(
        types.InlineKeyboardButton("🛒 Tovar/Xizmat sotib olish", callback_data="svc_buy"),
        types.InlineKeyboardButton("🔧 Yordam so'rash", callback_data="svc_help"),
        types.InlineKeyboardButton("📋 Ma'lumot olish", callback_data="svc_info"),
    )
    bot.send_message(message.chat.id, "📋 <b>Xizmat turini tanlang:</b>", reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data.startswith("svc_"))
def get_service(call):
    services = {"svc_buy": "Tovar/Xizmat sotib olish", "svc_help": "Yordam so'rash", "svc_info": "Ma'lumot olish"}
    service = services.get(call.data, call.data)
    state = states.get(call.from_user.id, {})

    username = f"@{call.from_user.username}" if call.from_user.username else "yo'q"
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("💬 Javob berish", url=f"tg://user?id={call.from_user.id}"))

    bot.send_message(ADMIN_ID, f"""📥 <b>Yangi ariza</b>

👤 Ism: {state.get('name', '?')}
📞 Tel: {state.get('phone', '?')}
🆔 ID: <code>{call.from_user.id}</code>
📋 Xizmat: {service}""", reply_markup=kb)

    states.pop(call.from_user.id, None)
    bot.send_message(call.message.chat.id, "✅ <b>Arizangiz qabul qilindi!</b>\n\nAdmin tez orada siz bilan bog'lanadi.", reply_markup=main_menu())

@bot.callback_query_handler(func=lambda c: c.data == "cancel")
def cancel(call):
    states.pop(call.from_user.id, None)
    bot.send_message(call.message.chat.id, "❌ Bekor qilindi.", reply_markup=main_menu())

@bot.message_handler(func=lambda m: m.text == "📞 Aloqa")
def contact(message):
    bot.send_message(message.chat.id, "📞 Admin: @X_VBRAIN")

print("Zayavka bot ishga tushdi!")
bot.infinity_polling(skip_pending=True)
