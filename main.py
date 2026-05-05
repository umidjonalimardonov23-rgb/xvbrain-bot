import os
import time
import sqlite3
import telebot
from telebot import types

BOT_TOKEN = os.getenv("BOT_TOKEN", "TOKEN_BU_YERGA")
ADMIN_ID = int(os.getenv("ADMIN_ID", "123456789"))
CARD_NUMBER = os.getenv("CARD_NUMBER", "8600 0000 0000 0000")

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

conn = sqlite3.connect("xvbrain.db", check_same_thread=False)
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    balance INTEGER DEFAULT 0,
    created_at INTEGER
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    bot_type TEXT,
    tariff TEXT,
    price INTEGER,
    token TEXT,
    status TEXT,
    created_at INTEGER
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS payments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    amount INTEGER,
    status TEXT,
    created_at INTEGER
)
""")
conn.commit()

states = {}

BOT_TYPES = {
    "shop": {
        "name": "🛒 Shop bot",
        "price": 25000,
        "info": """
🛒 <b>Shop bot</b>

Nima qila oladi:
✅ Mahsulot katalogi
✅ Savat
✅ Buyurtma qabul qilish
✅ To‘lov screenshot
✅ Admin tasdiqlash
✅ Statistika
✅ Reklama yuborish

Kimga kerak:
Do‘kon, online savdo, Free Fire/PUBG sotuvchilar uchun.
"""
    },
    "smm": {
        "name": "🚀 SMM bot",
        "price": 30000,
        "info": """
🚀 <b>SMM bot</b>

Nima qila oladi:
✅ Instagram like
✅ Telegram obunachi
✅ TikTok view
✅ Buyurtma qabul qilish
✅ Balans tizimi
✅ Admin panel
✅ API ulash mumkin

Kimga kerak:
SMM xizmat sotadiganlar uchun.
"""
    },
    "payment": {
        "name": "💳 To‘lov bot",
        "price": 20000,
        "info": """
💳 <b>To‘lov bot</b>

Nima qila oladi:
✅ Karta raqam chiqaradi
✅ Screenshot qabul qiladi
✅ Adminga yuboradi
✅ Tasdiqlash/rad etish
✅ Mijozga javob beradi

Kimga kerak:
To‘lov tekshiradigan xizmatlar uchun.
"""
    },
    "taxi": {
        "name": "🚕 Taxi bot",
        "price": 25000,
        "info": """
🚕 <b>Taxi bot</b>

Nima qila oladi:
✅ Qayerdan/qayerga so‘raydi
✅ Telefon raqam oladi
✅ Buyurtmani adminga yuboradi
✅ Guruhga zakaz tashlash mumkin
✅ Statistika

Kimga kerak:
Taxi xizmatlari uchun.
"""
    },
    "food": {
        "name": "🍔 Food bot",
        "price": 30000,
        "info": """
🍔 <b>Food bot</b>

Nima qila oladi:
✅ Menyu ko‘rsatadi
✅ Zakaz qabul qiladi
✅ Manzil oladi
✅ Telefon so‘raydi
✅ To‘lov screenshot
✅ Adminga yuboradi

Kimga kerak:
Kafe, fast food, oshxona uchun.
"""
    },
    "test": {
        "name": "📝 Test bot",
        "price": 25000,
        "info": """
📝 <b>Test bot</b>

Nima qila oladi:
✅ Test savollar
✅ Javob tekshirish
✅ Ball hisoblash
✅ Natija chiqarish
✅ Admin savol qo‘shishi mumkin

Kimga kerak:
O‘quv markaz va ustozlar uchun.
"""
    },
    "course": {
        "name": "📚 Kurs bot",
        "price": 35000,
        "info": """
📚 <b>Kurs bot</b>

Nima qila oladi:
✅ Darslar ro‘yxati
✅ Pullik kurs sotish
✅ To‘lov tekshirish
✅ Video/link berish
✅ O‘quvchilar bazasi

Kimga kerak:
Online kurs sotadiganlar uchun.
"""
    },
    "obuna": {
        "name": "👑 Obuna bot",
        "price": 20000,
        "info": """
👑 <b>Obuna bot</b>

Nima qila oladi:
✅ Kanalga obuna tekshiradi
✅ Obuna bo‘lmasa ishlatmaydi
✅ Majburiy obuna
✅ Reklama yuborish
✅ Kanal rivojlantirish

Kimga kerak:
Kanal egalariga.
"""
    },
    "ai": {
        "name": "🤖 AI ChatGPT bot",
        "price": 40000,
        "info": """
🤖 <b>AI ChatGPT bot</b>

Nima qila oladi:
✅ Savollarga javob beradi
✅ Matn yozadi
✅ Tarjima qiladi
✅ G‘oya beradi
✅ API orqali ishlaydi

Kimga kerak:
AI xizmat sotmoqchi bo‘lganlar uchun.
"""
    },
    "zayavka": {
        "name": "📥 Zayavka bot",
        "price": 25000,
        "info": """
📥 <b>Zayavka bot</b>

Nima qila oladi:
✅ Mijozdan ism oladi
✅ Telefon oladi
✅ Xizmat turini so‘raydi
✅ Arizani adminga yuboradi
✅ Admin javob beradi

Kimga kerak:
Har qanday xizmat ko‘rsatuvchi biznes uchun.
"""
    }
}

TARIFFS = {
    "Start": 25000,
    "Standard": 45000,
    "Pro": 65000,
    "Turbo": 85000,
    "VIP": 110000
}

def save_user(message):
    cur.execute("SELECT user_id FROM users WHERE user_id=?", (message.from_user.id,))
    if not cur.fetchone():
        cur.execute(
            "INSERT INTO users (user_id, username, created_at) VALUES (?, ?, ?)",
            (message.from_user.id, message.from_user.username, int(time.time()))
        )
        conn.commit()

def main_menu():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("🤖 Bot yaratish", "📋 Botlarim")
    kb.row("💳 Pul kiritish", "💰 Hisobim")
    kb.row("👥 Referal", "📕 Qo‘llanma")
    kb.row("☎️ Qo‘llab-quvvatlash")
    return kb

def bot_keyboard():
    kb = types.InlineKeyboardMarkup(row_width=2)
    for code, data in BOT_TYPES.items():
        kb.add(types.InlineKeyboardButton(data["name"], callback_data=f"info_{code}"))
    return kb

def tariff_keyboard(bot_code):
    kb = types.InlineKeyboardMarkup(row_width=2)
    for name, price in TARIFFS.items():
        kb.add(types.InlineKeyboardButton(f"{name} — {price} so‘m", callback_data=f"tariff_{bot_code}_{name}_{price}"))
    kb.add(types.InlineKeyboardButton("❌ Bekor qilish", callback_data="cancel"))
    return kb

@bot.message_handler(commands=["start"])
def start(message):
    save_user(message)
    bot.send_message(message.chat.id, """
🤖 <b>X VBrain Builder Bot</b>

Bu bot orqali har xil Telegram botlarga buyurtma berishingiz mumkin.

Pastdagi menyudan foydalaning 👇
""", reply_markup=main_menu())

@bot.message_handler(func=lambda m: m.text == "🤖 Bot yaratish")
def create_bot(message):
    save_user(message)
    bot.send_message(message.chat.id, """
🤖 <b>Bot yaratish</b>

Quyidagi botlardan birini tanlang 👇
""", reply_markup=bot_keyboard())

@bot.callback_query_handler(func=lambda c: c.data.startswith("info_"))
def show_info(call):
    code = call.data.replace("info_", "")
    data = BOT_TYPES.get(code)

    if not data:
        return

    bot.send_message(call.message.chat.id, f"""
{data["info"]}

💵 <b>Bot ochish narxi:</b> 200 000 so‘m
💰 <b>Oylik tarif:</b> pastdan tanlanadi

Quyidan tarif tanlang 👇
""", reply_markup=tariff_keyboard(code))

@bot.callback_query_handler(func=lambda c: c.data.startswith("tariff_"))
def choose_tariff(call):
    _, bot_code, tariff, price = call.data.split("_")
    price = int(price)

    cur.execute("SELECT balance FROM users WHERE user_id=?", (call.from_user.id,))
    row = cur.fetchone()
    balance = row[0] if row else 0

    if balance < price:
        bot.send_message(call.message.chat.id, f"""
❌ Balans yetarli emas.

💰 Balans: {balance} so‘m
💵 Kerak: {price} so‘m

Avval “💳 Pul kiritish” qiling.
""")
        return

    states[call.from_user.id] = {
        "step": "token",
        "bot_code": bot_code,
        "tariff": tariff,
        "price": price
    }

    bot.send_message(call.message.chat.id, """
🔑 Endi BotFatherdan olingan bot tokenini yuboring.

Masalan:
<code>123456789:ABCDEF...</code>

Agar token yo‘q bo‘lsa, @BotFather dan yangi bot ochib token oling.
""")

@bot.message_handler(func=lambda m: states.get(m.from_user.id, {}).get("step") == "token")
def get_token(message):
    token = message.text.strip()
    state = states.get(message.from_user.id)

    if ":" not in token or len(token) < 25:
        bot.send_message(message.chat.id, "❌ Token noto‘g‘ri. Qayta yuboring.")
        return

    bot_code = state["bot_code"]
    tariff = state["tariff"]
    price = state["price"]
    bot_name = BOT_TYPES[bot_code]["name"]

    cur.execute("UPDATE users SET balance = balance - ? WHERE user_id=?", (price, message.from_user.id))
    cur.execute("""
    INSERT INTO orders (user_id, bot_type, tariff, price, token, status, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        message.from_user.id,
        bot_name,
        tariff,
        price,
        token,
        "pending",
        int(time.time())
    ))
    conn.commit()

    order_id = cur.lastrowid
    states.pop(message.from_user.id, None)

    username = f"@{message.from_user.username}" if message.from_user.username else "username yo‘q"

    kb = types.InlineKeyboardMarkup()
    kb.add(
        types.InlineKeyboardButton("✅ Tasdiqlash", callback_data=f"orderok_{order_id}"),
        types.InlineKeyboardButton("❌ Rad etish", callback_data=f"orderno_{order_id}")
    )

    bot.send_message(ADMIN_ID, f"""
📥 <b>Yangi bot buyurtma #{order_id}</b>

👤 User: {username}
🆔 ID: <code>{message.from_user.id}</code>

🤖 Bot turi: {bot_name}
💎 Tarif: {tariff}
💰 Narx: {price} so‘m

🔑 Token:
<code>{token}</code>

Holat: kutilmoqda
""", reply_markup=kb)

    bot.send_message(message.chat.id, f"""
✅ Buyurtma qabul qilindi!

🤖 Bot: {bot_name}
💎 Tarif: {tariff}
💰 Narx: {price} so‘m

Admin tekshiradi va botingizni tayyorlab beradi.
""")

@bot.callback_query_handler(func=lambda c: c.data.startswith("orderok_") or c.data.startswith("orderno_"))
def order_decision(call):
    if call.from_user.id != ADMIN_ID:
        return bot.answer_callback_query(call.id, "Siz admin emassiz.")

    action, order_id = call.data.split("_")
    order_id = int(order_id)

    cur.execute("SELECT user_id, bot_type FROM orders WHERE id=?", (order_id,))
    row = cur.fetchone()

    if not row:
        return bot.answer_callback_query(call.id, "Buyurtma topilmadi.")

    user_id, bot_type = row

    if action == "orderok":
        cur.execute("UPDATE orders SET status='approved' WHERE id=?", (order_id,))
        conn.commit()
        bot.send_message(user_id, f"✅ Buyurtmangiz tasdiqlandi!\n\n🤖 Bot: {bot_type}\nAdmin siz bilan bog‘lanadi.")
        bot.answer_callback_query(call.id, "Tasdiqlandi ✅")
    else:
        cur.execute("UPDATE orders SET status='rejected' WHERE id=?", (order_id,))
        conn.commit()
        bot.send_message(user_id, "❌ Buyurtmangiz rad etildi. Support bilan bog‘laning.")
        bot.answer_callback_query(call.id, "Rad etildi ❌")

@bot.message_handler(func=lambda m: m.text == "📋 Botlarim")
def my_bots(message):
    cur.execute("SELECT id, bot_type, tariff, price, status FROM orders WHERE user_id=? ORDER BY id DESC", (message.from_user.id,))
    rows = cur.fetchall()

    if not rows:
        bot.send_message(message.chat.id, "📭 Sizda hali bot yo‘q.")
        return

    text = "📋 <b>Mening botlarim</b>\n\n"
    for r in rows:
        text += f"🆔 #{r[0]}\n🤖 {r[1]}\n💎 Tarif: {r[2]}\n💰 Narx: {r[3]} so‘m\n📌 Holat: {r[4]}\n\n"

    bot.send_message(message.chat.id, text)

@bot.message_handler(func=lambda m: m.text == "💳 Pul kiritish")
def deposit(message):
    states[message.from_user.id] = {"step": "amount"}
    bot.send_message(message.chat.id, "💳 Qancha pul kiritmoqchisiz?\n\nMasalan: 50000")

@bot.message_handler(func=lambda m: states.get(m.from_user.id, {}).get("step") == "amount")
def amount(message):
    try:
        amount_value = int(message.text)
    except:
        bot.send_message(message.chat.id, "❌ Faqat raqam yozing. Masalan: 50000")
        return

    states[message.from_user.id] = {
        "step": "payment_photo",
        "amount": amount_value
    }

    bot.send_message(message.chat.id, f"""
💳 <b>To‘lov qiling</b>

Karta:
<code>{CARD_NUMBER}</code>

💰 Miqdor: <b>{amount_value} so‘m</b>

📸 To‘lov screenshotini yuboring.
""")

@bot.message_handler(content_types=["photo"])
def payment_photo(message):
    state = states.get(message.from_user.id)

    if not state or state.get("step") != "payment_photo":
        return

    amount_value = state["amount"]
    username = f"@{message.from_user.username}" if message.from_user.username else "username yo‘q"

    cur.execute("""
    INSERT INTO payments (user_id, amount, status, created_at)
    VALUES (?, ?, ?, ?)
    """, (message.from_user.id, amount_value, "pending", int(time.time())))
    conn.commit()

    pay_id = cur.lastrowid

    kb = types.InlineKeyboardMarkup()
    kb.add(
        types.InlineKeyboardButton("✅ Tasdiqlash", callback_data=f"payok_{pay_id}"),
        types.InlineKeyboardButton("❌ Rad etish", callback_data=f"payno_{pay_id}")
    )

    bot.send_photo(
        ADMIN_ID,
        message.photo[-1].file_id,
        caption=f"""
💳 <b>Yangi to‘lov #{pay_id}</b>

👤 User: {username}
🆔 ID: <code>{message.from_user.id}</code>
💰 Miqdor: {amount_value} so‘m
""",
        reply_markup=kb
    )

    states.pop(message.from_user.id, None)
    bot.send_message(message.chat.id, "✅ To‘lov adminga yuborildi. Tasdiqlanishini kuting.")

@bot.callback_query_handler(func=lambda c: c.data.startswith("payok_") or c.data.startswith("payno_"))
def pay_decision(call):
    if call.from_user.id != ADMIN_ID:
        return bot.answer_callback_query(call.id, "Siz admin emassiz.")

    action, pay_id = call.data.split("_")
    pay_id = int(pay_id)

    cur.execute("SELECT user_id, amount, status FROM payments WHERE id=?", (pay_id,))
    row = cur.fetchone()

    if not row:
        return bot.answer_callback_query(call.id, "To‘lov topilmadi.")

    user_id, amount_value, status = row

    if status != "pending":
        return bot.answer_callback_query(call.id, "Bu to‘lov avval tekshirilgan.")

    if action == "payok":
        cur.execute("UPDATE users SET balance = balance + ? WHERE user_id=?", (amount_value, user_id))
        cur.execute("UPDATE payments SET status='approved' WHERE id=?", (pay_id,))
        conn.commit()
        bot.send_message(user_id, f"✅ To‘lov tasdiqlandi!\n\n💰 Balansga {amount_value} so‘m qo‘shildi.")
        bot.answer_callback_query(call.id, "Tasdiqlandi ✅")
    else:
        cur.execute("UPDATE payments SET status='rejected' WHERE id=?", (pay_id,))
        conn.commit()
        bot.send_message(user_id, "❌ To‘lov rad etildi.")
        bot.answer_callback_query(call.id, "Rad etildi ❌")

@bot.message_handler(func=lambda m: m.text == "💰 Hisobim")
def account(message):
    cur.execute("SELECT balance FROM users WHERE user_id=?", (message.from_user.id,))
    row = cur.fetchone()
    balance = row[0] if row else 0

    bot.send_message(message.chat.id, f"""
💰 <b>Hisobim</b>

🆔 ID: <code>{message.from_user.id}</code>
💵 Balans: <b>{balance} so‘m</b>
""")

@bot.message_handler(func=lambda m: m.text == "👥 Referal")
def referal(message):
    username = bot.get_me().username
    link = f"https://t.me/{username}?start={message.from_user.id}"

    bot.send_message(message.chat.id, f"""
👥 <b>Referal</b>

Sizning linkingiz:
{link}

Do‘stlaringizni chaqiring 🔥
""")

@bot.message_handler(func=lambda m: m.text == "📕 Qo‘llanma")
def guide(message):
    bot.send_message(message.chat.id, """
📕 <b>Qo‘llanma</b>

1️⃣ Pul kiriting
2️⃣ Bot yaratish bo‘limiga kiring
3️⃣ Bot turini tanlang
4️⃣ Tarif tanlang
5️⃣ BotFather token yuboring
6️⃣ Admin tasdiqlaydi
7️⃣ Bot tayyorlanadi

Support: @X_VBRAIN
""")

@bot.message_handler(func=lambda m: m.text == "☎️ Qo‘llab-quvvatlash")
def support(message):
    bot.send_message(message.chat.id, "☎️ Qo‘llab-quvvatlash: @X_VBRAIN")

@bot.callback_query_handler(func=lambda c: c.data == "cancel")
def cancel(call):
    states.pop(call.from_user.id, None)
    bot.send_message(call.message.chat.id, "❌ Bekor qilindi.", reply_markup=main_menu())

@bot.message_handler(commands=["admin"])
def admin_panel(message):
    if message.from_user.id != ADMIN_ID:
        return bot.send_message(message.chat.id, "❌ Siz admin emassiz.")

    cur.execute("SELECT COUNT(*) FROM users")
    users = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM orders")
    orders = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM payments WHERE status='pending'")
    payments = cur.fetchone()[0]

    bot.send_message(message.chat.id, f"""
🛠 <b>Admin panel</b>

👥 Users: {users}
🤖 Buyurtmalar: {orders}
💳 Kutilayotgan to‘lovlar: {payments}
""")

print("X VBrain Builder Bot ishga tushdi...")
bot.infinity_polling(skip_pending=True)
