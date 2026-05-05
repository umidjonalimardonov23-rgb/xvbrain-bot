import os
import telebot
from telebot import types

BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_TOKEN_HERE")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
CARD = os.getenv("CARD_NUMBER", "0000000000000000")

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

MENU = {
    "burger": {"name": "🍔 Burger", "price": 25000},
    "pizza": {"name": "🍕 Pizza", "price": 45000},
    "lavash": {"name": "🌯 Lavash", "price": 18000},
    "donerr": {"name": "🥙 Doner", "price": 22000},
    "ichimlik": {"name": "🥤 Ichimlik", "price": 8000},
}

orders = {}
states = {}

def main_menu():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("🍽 Menyu", "🛒 Savatim")
    kb.row("📞 Aloqa")
    return kb

@bot.message_handler(commands=["start"])
def start(message):
    bot.send_message(message.chat.id, "🍔 <b>Xush kelibsiz!</b>\n\nTaom buyurtma qiling 👇", reply_markup=main_menu())

@bot.message_handler(func=lambda m: m.text == "🍽 Menyu")
def show_menu(message):
    kb = types.InlineKeyboardMarkup(row_width=1)
    for code, item in MENU.items():
        kb.add(types.InlineKeyboardButton(f"{item['name']} — {item['price']:,} so'm", callback_data=f"add_{code}"))
    bot.send_message(message.chat.id, "🍽 <b>Menyu</b>\n\nTaom tanlang:", reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data.startswith("add_"))
def add_to_cart(call):
    code = call.data.replace("add_", "")
    item = MENU.get(code)
    if not item:
        return
    if call.from_user.id not in orders:
        orders[call.from_user.id] = []
    orders[call.from_user.id].append(code)
    bot.answer_callback_query(call.id, f"✅ {item['name']} savatga qo'shildi!")

@bot.message_handler(func=lambda m: m.text == "🛒 Savatim")
def cart(message):
    cart_items = orders.get(message.from_user.id, [])
    if not cart_items:
        bot.send_message(message.chat.id, "🛒 Savat bo'sh.")
        return
    total = 0
    text = "🛒 <b>Savatim</b>\n\n"
    for code in cart_items:
        item = MENU[code]
        text += f"• {item['name']} — {item['price']:,} so'm\n"
        total += item['price']
    text += f"\n💰 Jami: <b>{total:,} so'm</b>"
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("✅ Buyurtma berish", callback_data="checkout"))
    kb.add(types.InlineKeyboardButton("🗑 Tozalash", callback_data="clear_cart"))
    bot.send_message(message.chat.id, text, reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data == "clear_cart")
def clear_cart(call):
    orders.pop(call.from_user.id, None)
    bot.send_message(call.message.chat.id, "🗑 Savat tozalandi.", reply_markup=main_menu())

@bot.callback_query_handler(func=lambda c: c.data == "checkout")
def checkout(call):
    states[call.from_user.id] = {"step": "address"}
    bot.send_message(call.message.chat.id, "📍 Manzilni yozing:")

@bot.message_handler(func=lambda m: states.get(m.from_user.id, {}).get("step") == "address")
def get_address(message):
    states[message.from_user.id] = {"step": "phone", "address": message.text}
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    kb.add(types.KeyboardButton("📞 Raqamni yuborish", request_contact=True))
    bot.send_message(message.chat.id, "📞 Telefon raqamingiz?", reply_markup=kb)

@bot.message_handler(content_types=["contact"])
def get_phone(message):
    state = states.get(message.from_user.id)
    if not state or state.get("step") != "phone":
        return
    cart_items = orders.get(message.from_user.id, [])
    total = sum(MENU[c]['price'] for c in cart_items)
    items_text = "\n".join(f"• {MENU[c]['name']}" for c in cart_items)
    username = f"@{message.from_user.username}" if message.from_user.username else "yo'q"

    bot.send_message(ADMIN_ID, f"""🍔 <b>Yangi buyurtma</b>

👤 {username} | <code>{message.from_user.id}</code>
📞 {message.contact.phone_number}
📍 {state['address']}

{items_text}

💰 Jami: {total:,} so'm""")

    orders.pop(message.from_user.id, None)
    states.pop(message.from_user.id, None)
    bot.send_message(message.chat.id, f"""✅ <b>Buyurtma qabul qilindi!</b>

💰 Jami: {total:,} so'm

To'lov: <code>{CARD}</code>
Screenshotni adminga yuboring.""", reply_markup=main_menu())

@bot.message_handler(func=lambda m: m.text == "📞 Aloqa")
def contact(message):
    bot.send_message(message.chat.id, "📞 Admin: @X_VBRAIN")

print("Food bot ishga tushdi!")
bot.infinity_polling(skip_pending=True)
