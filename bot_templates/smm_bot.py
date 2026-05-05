import os
import telebot
from telebot import types

BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_TOKEN_HERE")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
CARD = os.getenv("CARD_NUMBER", "0000000000000000")

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")
states = {}

SERVICES = {
    "ig_like": {"name": "❤️ Instagram Like", "price": 5000, "unit": "1000 ta"},
    "tg_sub": {"name": "👥 Telegram Obunachi", "price": 8000, "unit": "1000 ta"},
    "tiktok": {"name": "👁 TikTok View", "price": 3000, "unit": "1000 ta"},
    "yt_view": {"name": "▶️ YouTube View", "price": 4000, "unit": "1000 ta"},
}

def main_menu():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("🚀 Xizmatlar", "💰 Balans")
    kb.row("📋 Buyurtmalarim", "📞 Aloqa")
    return kb

@bot.message_handler(commands=["start"])
def start(message):
    bot.send_message(message.chat.id, "🚀 <b>SMM Bot</b>\n\nSMMga oid xizmatlar 👇", reply_markup=main_menu())

@bot.message_handler(func=lambda m: m.text == "🚀 Xizmatlar")
def services(message):
    kb = types.InlineKeyboardMarkup(row_width=1)
    for code, s in SERVICES.items():
        kb.add(types.InlineKeyboardButton(f"{s['name']} — {s['price']:,} so'm ({s['unit']})", callback_data=f"svc_{code}"))
    bot.send_message(message.chat.id, "🚀 <b>Xizmatlar</b>\n\nBirini tanlang:", reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data.startswith("svc_"))
def choose_service(call):
    code = call.data.replace("svc_", "")
    s = SERVICES.get(code)
    states[call.from_user.id] = {"step": "qty", "service": code}
    bot.send_message(call.message.chat.id, f"""🚀 <b>{s['name']}</b>

💰 Narx: {s['price']:,} so'm / {s['unit']}

Nechta buyurtma berasiz? (ming bilan)\nMasalan: <code>5</code> (5000 ta)""")

@bot.message_handler(func=lambda m: states.get(m.from_user.id, {}).get("step") == "qty")
def get_qty(message):
    try:
        qty = int(message.text.strip())
    except:
        bot.send_message(message.chat.id, "❌ Faqat raqam yozing.")
        return
    state = states[message.from_user.id]
    s = SERVICES[state["service"]]
    total = s["price"] * qty
    states[message.from_user.id] = {"step": "link", "service": state["service"], "qty": qty, "total": total}
    bot.send_message(message.chat.id, f"🔗 Link yuboring (Instagram, Telegram, TikTok va h.k.):")

@bot.message_handler(func=lambda m: states.get(m.from_user.id, {}).get("step") == "link")
def get_link(message):
    state = states[message.from_user.id]
    s = SERVICES[state["service"]]
    states[message.from_user.id] = {"step": "payment", "service": state["service"], "qty": state["qty"], "total": state["total"], "link": message.text}
    bot.send_message(message.chat.id, f"""💳 <b>To'lov</b>

Karta: <code>{CARD}</code>
💰 Miqdor: <b>{state['total']:,} so'm</b>

📸 Screenshotni yuboring""")

@bot.message_handler(content_types=["photo"])
def get_payment(message):
    state = states.get(message.from_user.id)
    if not state or state.get("step") != "payment":
        return
    s = SERVICES[state["service"]]
    username = f"@{message.from_user.username}" if message.from_user.username else str(message.from_user.id)
    kb = types.InlineKeyboardMarkup()
    kb.add(
        types.InlineKeyboardButton("✅ Qabul", callback_data=f"ok_{message.from_user.id}"),
        types.InlineKeyboardButton("❌ Rad", callback_data=f"no_{message.from_user.id}")
    )
    bot.send_photo(ADMIN_ID, message.photo[-1].file_id,
        caption=f"🚀 <b>Yangi SMM buyurtma</b>\n\n👤 {username}\n🆔 <code>{message.from_user.id}</code>\n{s['name']}: {state['qty']}000 ta\n🔗 {state['link']}\n💰 {state['total']:,} so'm",
        reply_markup=kb)
    states.pop(message.from_user.id, None)
    bot.send_message(message.chat.id, "✅ Buyurtma yuborildi! Admin tasdiqlaydi.", reply_markup=main_menu())

@bot.callback_query_handler(func=lambda c: c.data.startswith("ok_") or c.data.startswith("no_"))
def decision(call):
    if call.from_user.id != ADMIN_ID:
        return
    uid = int(call.data.split("_")[1])
    if call.data.startswith("ok_"):
        bot.send_message(uid, "✅ Buyurtmangiz tasdiqlandi! Tez orada bajariladi.")
        bot.answer_callback_query(call.id, "Tasdiqlandi ✅")
    else:
        bot.send_message(uid, "❌ Buyurtma rad etildi.")
        bot.answer_callback_query(call.id, "Rad etildi ❌")

@bot.message_handler(func=lambda m: m.text == "📞 Aloqa")
def contact(message):
    bot.send_message(message.chat.id, "📞 Admin: @X_VBRAIN")

@bot.message_handler(func=lambda m: m.text in ["💰 Balans", "📋 Buyurtmalarim"])
def stub(message):
    bot.send_message(message.chat.id, "ℹ️ Bu bo'lim tez orada tayyor bo'ladi.")

print("SMM bot ishga tushdi!")
bot.infinity_polling(skip_pending=True)
