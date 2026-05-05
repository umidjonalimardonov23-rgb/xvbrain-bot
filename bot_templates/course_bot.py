import os
import telebot
from telebot import types

BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_TOKEN_HERE")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
CARD = os.getenv("CARD_NUMBER", "0000000000000000")

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

COURSES = {
    "python": {"name": "🐍 Python kursi", "price": 150000, "link": "https://t.me/your_channel/1"},
    "web": {"name": "🌐 Web dasturlash", "price": 200000, "link": "https://t.me/your_channel/2"},
    "smm": {"name": "📱 SMM kursi", "price": 100000, "link": "https://t.me/your_channel/3"},
}

states = {}

def main_menu():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("📚 Kurslar", "📋 Mening kurslarim")
    kb.row("📞 Aloqa")
    return kb

@bot.message_handler(commands=["start"])
def start(message):
    bot.send_message(message.chat.id, "📚 <b>Kurs Bot</b>\n\nOnline kurslarimiz bilan tanishing! 👇", reply_markup=main_menu())

@bot.message_handler(func=lambda m: m.text == "📚 Kurslar")
def courses(message):
    kb = types.InlineKeyboardMarkup(row_width=1)
    for code, c in COURSES.items():
        kb.add(types.InlineKeyboardButton(f"{c['name']} — {c['price']:,} so'm", callback_data=f"course_{code}"))
    bot.send_message(message.chat.id, "📚 <b>Kurslar</b>\n\nBirini tanlang:", reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data.startswith("course_"))
def show_course(call):
    code = call.data.replace("course_", "")
    c = COURSES.get(code)
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("💳 Sotib olish", callback_data=f"buy_{code}"))
    kb.add(types.InlineKeyboardButton("🔙 Ortga", callback_data="back_courses"))
    bot.send_message(call.message.chat.id, f"""📚 <b>{c['name']}</b>

💰 Narx: {c['price']:,} so'm

Bu kursda siz professional darajaga chiqasiz!""", reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data == "back_courses")
def back(call):
    kb = types.InlineKeyboardMarkup(row_width=1)
    for code, c in COURSES.items():
        kb.add(types.InlineKeyboardButton(f"{c['name']} — {c['price']:,} so'm", callback_data=f"course_{code}"))
    bot.send_message(call.message.chat.id, "📚 <b>Kurslar</b>", reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data.startswith("buy_"))
def buy(call):
    code = call.data.replace("buy_", "")
    c = COURSES.get(code)
    states[call.from_user.id] = {"step": "payment", "course": code}
    bot.send_message(call.message.chat.id, f"""💳 <b>To'lov</b>

Karta: <code>{CARD}</code>
💰 Miqdor: <b>{c['price']:,} so'm</b>

📸 Screenshotni yuboring""")

@bot.message_handler(content_types=["photo"])
def payment(message):
    state = states.get(message.from_user.id)
    if not state or state.get("step") != "payment":
        return
    code = state["course"]
    c = COURSES[code]
    username = f"@{message.from_user.username}" if message.from_user.username else str(message.from_user.id)
    kb = types.InlineKeyboardMarkup()
    kb.add(
        types.InlineKeyboardButton("✅ Tasdiqlash", callback_data=f"ok_{message.from_user.id}_{code}"),
        types.InlineKeyboardButton("❌ Rad", callback_data=f"no_{message.from_user.id}")
    )
    bot.send_photo(ADMIN_ID, message.photo[-1].file_id,
        caption=f"📚 <b>Yangi kurs to'lovi</b>\n\n👤 {username}\n🆔 <code>{message.from_user.id}</code>\n{c['name']}\n💰 {c['price']:,} so'm",
        reply_markup=kb)
    states.pop(message.from_user.id, None)
    bot.send_message(message.chat.id, "✅ To'lov yuborildi! Admin tasdiqlaydi.", reply_markup=main_menu())

@bot.callback_query_handler(func=lambda c: c.data.startswith("ok_") or c.data.startswith("no_"))
def decision(call):
    if call.from_user.id != ADMIN_ID:
        return
    if call.data.startswith("ok_"):
        parts = call.data.split("_")
        uid, code = int(parts[1]), parts[2]
        c = COURSES.get(code, {})
        bot.send_message(uid, f"✅ <b>To'lov tasdiqlandi!</b>\n\n📚 {c.get('name','Kurs')} uchun havola:\n{c.get('link','')}")
        bot.answer_callback_query(call.id, "Tasdiqlandi ✅")
    else:
        uid = int(call.data.split("_")[1])
        bot.send_message(uid, "❌ To'lov rad etildi.")
        bot.answer_callback_query(call.id, "Rad etildi ❌")

@bot.message_handler(func=lambda m: m.text in ["📋 Mening kurslarim", "📞 Aloqa"])
def stub(message):
    bot.send_message(message.chat.id, "📞 Admin: @X_VBRAIN" if "Aloqa" in message.text else "ℹ️ Sotib olingan kurslar shu yerda ko'rinadi.")

print("Kurs bot ishga tushdi!")
bot.infinity_polling(skip_pending=True)
