import os
import telebot
from telebot import types

BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_TOKEN_HERE")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

PRODUCTS = {
    "mahsulot1": {"name": "Mahsulot 1", "price": 50000, "desc": "Mahsulot tavsifi"},
    "mahsulot2": {"name": "Mahsulot 2", "price": 75000, "desc": "Mahsulot tavsifi"},
    "mahsulot3": {"name": "Mahsulot 3", "price": 100000, "desc": "Mahsulot tavsifi"},
}

CARD = os.getenv("CARD_NUMBER", "0000000000000000")
orders = {}

def main_menu():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("🛒 Katalog", "📋 Buyurtmalarim")
    kb.row("📞 Aloqa")
    return kb

@bot.message_handler(commands=["start"])
def start(message):
    bot.send_message(message.chat.id, """👋 <b>Xush kelibsiz!</b>

Do'konimizga xush kelibsiz. Quyidagi menyudan foydalaning 👇""", reply_markup=main_menu())

@bot.message_handler(func=lambda m: m.text == "🛒 Katalog")
def catalog(message):
    kb = types.InlineKeyboardMarkup(row_width=1)
    for code, p in PRODUCTS.items():
        kb.add(types.InlineKeyboardButton(f"{p['name']} — {p['price']:,} so'm", callback_data=f"buy_{code}"))
    bot.send_message(message.chat.id, "🛒 <b>Katalog</b>\n\nMahsulotni tanlang:", reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data.startswith("buy_"))
def buy(call):
    code = call.data.replace("buy_", "")
    p = PRODUCTS.get(code)
    if not p:
        return
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("✅ Buyurtma berish", callback_data=f"order_{code}"))
    kb.add(types.InlineKeyboardButton("🔙 Ortga", callback_data="back_catalog"))
    bot.send_message(call.message.chat.id, f"""📦 <b>{p['name']}</b>

📝 {p['desc']}
💰 Narx: <b>{p['price']:,} so'm</b>

Buyurtma bermoqchimisiz?""", reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data == "back_catalog")
def back_catalog(call):
    kb = types.InlineKeyboardMarkup(row_width=1)
    for code, p in PRODUCTS.items():
        kb.add(types.InlineKeyboardButton(f"{p['name']} — {p['price']:,} so'm", callback_data=f"buy_{code}"))
    bot.send_message(call.message.chat.id, "🛒 <b>Katalog</b>\n\nMahsulotni tanlang:", reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data.startswith("order_"))
def order(call):
    code = call.data.replace("order_", "")
    p = PRODUCTS.get(code)
    orders[call.from_user.id] = {"product": code, "step": "waiting_payment"}
    bot.send_message(call.message.chat.id, f"""💳 <b>To'lov</b>

Karta raqamiga pul o'tkazing:
<code>{CARD}</code>

💰 Miqdor: <b>{p['price']:,} so'm</b>

📸 To'lov screenshotini yuboring""")

@bot.message_handler(content_types=["photo"])
def payment_photo(message):
    state = orders.get(message.from_user.id)
    if not state or state.get("step") != "waiting_payment":
        return
    p = PRODUCTS[state["product"]]
    username = f"@{message.from_user.username}" if message.from_user.username else str(message.from_user.id)
    kb = types.InlineKeyboardMarkup()
    kb.add(
        types.InlineKeyboardButton("✅ Tasdiqlash", callback_data=f"ok_{message.from_user.id}_{state['product']}"),
        types.InlineKeyboardButton("❌ Rad etish", callback_data=f"no_{message.from_user.id}")
    )
    bot.send_photo(ADMIN_ID, message.photo[-1].file_id,
        caption=f"📦 <b>Yangi buyurtma</b>\n\n👤 {username}\n🆔 <code>{message.from_user.id}</code>\n📦 {p['name']}\n💰 {p['price']:,} so'm",
        reply_markup=kb)
    orders.pop(message.from_user.id, None)
    bot.send_message(message.chat.id, "✅ To'lov yuborildi! Admin tasdiqlaydi.", reply_markup=main_menu())

@bot.callback_query_handler(func=lambda c: c.data.startswith("ok_") or c.data.startswith("no_"))
def admin_decision(call):
    if call.from_user.id != ADMIN_ID:
        return
    if call.data.startswith("ok_"):
        _, uid, code = call.data.split("_")
        p = PRODUCTS.get(code)
        bot.send_message(int(uid), f"✅ <b>Buyurtmangiz tasdiqlandi!</b>\n\n📦 {p['name'] if p else 'Mahsulot'}\n\nTez orada yetkazamiz!")
        bot.answer_callback_query(call.id, "Tasdiqlandi ✅")
    else:
        uid = call.data.split("_")[1]
        bot.send_message(int(uid), "❌ To'lov rad etildi. Qayta urinib ko'ring.")
        bot.answer_callback_query(call.id, "Rad etildi ❌")

@bot.message_handler(func=lambda m: m.text == "📋 Buyurtmalarim")
def my_orders(message):
    bot.send_message(message.chat.id, "📋 Buyurtmalaringiz admin tomonidan ko'rib chiqilmoqda.")

@bot.message_handler(func=lambda m: m.text == "📞 Aloqa")
def contact(message):
    bot.send_message(message.chat.id, "📞 Admin: @X_VBRAIN")

print("Shop bot ishga tushdi!")
bot.infinity_polling(skip_pending=True)
