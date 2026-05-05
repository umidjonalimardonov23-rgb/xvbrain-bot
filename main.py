import os
import time
import sqlite3
import threading
import telebot
from telebot import types

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
CARD_NUMBER = os.getenv("CARD_NUMBER", "")

WEEK = 7 * 24 * 3600

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
    created_at INTEGER,
    expires_at INTEGER DEFAULT 0,
    reminded INTEGER DEFAULT 0
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

cur.execute("""
CREATE TABLE IF NOT EXISTS sub_payments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER,
    user_id INTEGER,
    amount INTEGER,
    status TEXT,
    created_at INTEGER
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS support_msgs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    message TEXT,
    replied INTEGER DEFAULT 0,
    created_at INTEGER
)
""")

try:
    cur.execute("ALTER TABLE orders ADD COLUMN expires_at INTEGER DEFAULT 0")
except:
    pass
try:
    cur.execute("ALTER TABLE orders ADD COLUMN reminded INTEGER DEFAULT 0")
except:
    pass
try:
    cur.execute("ALTER TABLE users ADD COLUMN referrer_id INTEGER DEFAULT 0")
except:
    pass
try:
    cur.execute("ALTER TABLE users ADD COLUMN ref_count INTEGER DEFAULT 0")
except:
    pass

conn.commit()

states = {}

BOT_TYPES = {
    "shop": {
        "name": "🛒 Shop bot",
        "info": """🛒 <b>Shop bot</b>

Nima qila oladi:
✅ Mahsulot katalogi
✅ Savat
✅ Buyurtma qabul qilish
✅ To'lov screenshot
✅ Admin tasdiqlash
✅ Statistika
✅ Reklama yuborish

Kimga kerak:
Do'kon, online savdo, Free Fire/PUBG sotuvchilar uchun."""
    },
    "smm": {
        "name": "🚀 SMM bot",
        "info": """🚀 <b>SMM bot</b>

Nima qila oladi:
✅ Instagram like
✅ Telegram obunachi
✅ TikTok view
✅ Buyurtma qabul qilish
✅ Balans tizimi
✅ Admin panel
✅ API ulash mumkin

Kimga kerak:
SMM xizmat sotadiganlar uchun."""
    },
    "payment": {
        "name": "💳 To'lov bot",
        "info": """💳 <b>To'lov bot</b>

Nima qila oladi:
✅ Karta raqam chiqaradi
✅ Screenshot qabul qiladi
✅ Adminga yuboradi
✅ Tasdiqlash/rad etish
✅ Mijozga javob beradi

Kimga kerak:
To'lov tekshiradigan xizmatlar uchun."""
    },
    "taxi": {
        "name": "🚕 Taxi bot",
        "info": """🚕 <b>Taxi bot</b>

Nima qila oladi:
✅ Qayerdan/qayerga so'raydi
✅ Telefon raqam oladi
✅ Buyurtmani adminga yuboradi
✅ Guruhga zakaz tashlash mumkin
✅ Statistika

Kimga kerak:
Taxi xizmatlari uchun."""
    },
    "food": {
        "name": "🍔 Food bot",
        "info": """🍔 <b>Food bot</b>

Nima qila oladi:
✅ Menyu ko'rsatadi
✅ Zakaz qabul qiladi
✅ Manzil oladi
✅ Telefon so'raydi
✅ To'lov screenshot
✅ Adminga yuboradi

Kimga kerak:
Kafe, fast food, oshxona uchun."""
    },
    "test": {
        "name": "📝 Test bot",
        "info": """📝 <b>Test bot</b>

Nima qila oladi:
✅ Test savollar
✅ Javob tekshirish
✅ Ball hisoblash
✅ Natija chiqarish
✅ Admin savol qo'shishi mumkin

Kimga kerak:
O'quv markaz va ustozlar uchun."""
    },
    "course": {
        "name": "📚 Kurs bot",
        "info": """📚 <b>Kurs bot</b>

Nima qila oladi:
✅ Darslar ro'yxati
✅ Pullik kurs sotish
✅ To'lov tekshirish
✅ Video/link berish
✅ O'quvchilar bazasi

Kimga kerak:
Online kurs sotadiganlar uchun."""
    },
    "obuna": {
        "name": "👑 Obuna bot",
        "info": """👑 <b>Obuna bot</b>

Nima qila oladi:
✅ Kanalga obuna tekshiradi
✅ Obuna bo'lmasa ishlatmaydi
✅ Majburiy obuna
✅ Reklama yuborish
✅ Kanal rivojlantirish

Kimga kerak:
Kanal egalariga."""
    },
    "ai": {
        "name": "🤖 AI ChatGPT bot",
        "info": """🤖 <b>AI ChatGPT bot</b>

Nima qila oladi:
✅ Savollarga javob beradi
✅ Matn yozadi
✅ Tarjima qiladi
✅ G'oya beradi
✅ API orqali ishlaydi

Kimga kerak:
AI xizmat sotmoqchi bo'lganlar uchun."""
    },
    "zayavka": {
        "name": "📥 Zayavka bot",
        "info": """📥 <b>Zayavka bot</b>

Nima qila oladi:
✅ Mijozdan ism oladi
✅ Telefon oladi
✅ Xizmat turini so'raydi
✅ Arizani adminga yuboradi
✅ Admin javob beradi

Kimga kerak:
Har qanday xizmat ko'rsatuvchi biznes uchun."""
    }
}

TARIFFS = {
    "Start": 25000,
    "Standard": 45000,
    "Pro": 65000,
    "Turbo": 85000,
    "VIP": 110000
}

PRO_STEPS = [
    ("bot_name", "🤖 Botingizning nomini yozing:\n\nMasalan: <code>MyShopBot</code>"),
    ("bot_description", "📝 Bot haqida qisqacha tavsif yozing:\n\nMasalan: <code>Bizning do'kon boti</code>"),
    ("bot_token", "🔑 BotFatherdan olingan bot tokenini yuboring:\n\nMasalan: <code>123456789:ABCDEF...</code>"),
    ("welcome_text", "👋 Foydalanuvchi /start berganda ko'rinadigan xush kelibsiz xabarini yozing:"),
    ("admin_contact", "📞 Admin aloqa (username yoki telefon):\n\nMasalan: <code>@username</code> yoki <code>+998901234567</code>"),
]

REFERRAL_BONUS = 15000

def save_user(message, referrer_id=0):
    cur.execute("SELECT user_id FROM users WHERE user_id=?", (message.from_user.id,))
    if not cur.fetchone():
        cur.execute(
            "INSERT INTO users (user_id, username, balance, created_at, referrer_id) VALUES (?, ?, ?, ?, ?)",
            (message.from_user.id, message.from_user.username, 0, int(time.time()), referrer_id)
        )
        conn.commit()
        # Referal bonus
        if referrer_id and referrer_id != message.from_user.id:
            cur.execute("SELECT user_id FROM users WHERE user_id=?", (referrer_id,))
            if cur.fetchone():
                cur.execute("UPDATE users SET balance = balance + ?, ref_count = ref_count + 1 WHERE user_id=?",
                            (REFERRAL_BONUS, referrer_id))
                conn.commit()
                try:
                    bot.send_message(referrer_id,
                        f"🎉 <b>Referal bonus!</b>\n\n👤 Yangi do'stingiz qo'shildi!\n💰 Balansga <b>{REFERRAL_BONUS:,} so'm</b> qo'shildi!")
                except:
                    pass
    else:
        if message.from_user.username:
            cur.execute("UPDATE users SET username=? WHERE user_id=?",
                        (message.from_user.username, message.from_user.id))
            conn.commit()

def main_menu():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("🤖 Bot yaratish", "⚡️ Pro bot yaratish")
    kb.row("📋 Botlarim", "💰 Hisobim")
    kb.row("💳 Pul kiritish", "🔄 Obuna yangilash")
    kb.row("👥 Referal", "📕 Qo'llanma")
    kb.row("☎️ Qo'llab-quvvatlash")
    return kb

def admin_menu():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("📋 Buyurtmalar", "💳 To'lovlar")
    kb.row("🎁 Bonus pul berish", "👥 Foydalanuvchilar")
    kb.row("📊 Statistika", "📈 Hisobot")
    kb.row("💬 Support xabarlar", "📢 Xabar yuborish")
    kb.row("🔙 Asosiy menyu")
    return kb

def bot_keyboard():
    kb = types.InlineKeyboardMarkup(row_width=2)
    for code, data in BOT_TYPES.items():
        kb.add(types.InlineKeyboardButton(data["name"], callback_data=f"info_{code}"))
    kb.add(types.InlineKeyboardButton("🔙 Ortga", callback_data="back_main"))
    return kb

def tariff_keyboard(bot_code):
    kb = types.InlineKeyboardMarkup(row_width=2)
    for name, price in TARIFFS.items():
        kb.add(types.InlineKeyboardButton(f"{name} — {price:,} so'm", callback_data=f"tariff_{bot_code}_{name}_{price}"))
    kb.add(types.InlineKeyboardButton("🔙 Ortga", callback_data="back_bots"))
    return kb

# ───────────────────────── START ─────────────────────────

@bot.message_handler(commands=["start"])
def start(message):
    ref_id = 0
    parts = message.text.split()
    if len(parts) > 1:
        try:
            ref_id = int(parts[1])
        except:
            pass
    save_user(message, referrer_id=ref_id)
    bot.send_message(message.chat.id, """🤖 <b>X VBrain Builder Bot</b>

Bu bot orqali har xil Telegram botlarga buyurtma berishingiz mumkin.

Pastdagi menyudan foydalaning 👇""", reply_markup=main_menu())

# ───────────────────────── BOT YARATISH ─────────────────────────

@bot.message_handler(func=lambda m: m.text == "🤖 Bot yaratish")
def create_bot(message):
    save_user(message)
    bot.send_message(message.chat.id, "🤖 <b>Bot yaratish</b>\n\nQuyidagi botlardan birini tanlang 👇", reply_markup=bot_keyboard())

@bot.callback_query_handler(func=lambda c: c.data == "back_main")
def back_main(call):
    states.pop(call.from_user.id, None)
    bot.send_message(call.message.chat.id, "🏠 Asosiy menyu", reply_markup=main_menu())

@bot.callback_query_handler(func=lambda c: c.data == "back_bots")
def back_bots(call):
    states.pop(call.from_user.id, None)
    bot.send_message(call.message.chat.id, "🤖 <b>Bot yaratish</b>\n\nQuyidagi botlardan birini tanlang 👇", reply_markup=bot_keyboard())

@bot.callback_query_handler(func=lambda c: c.data.startswith("info_"))
def show_info(call):
    code = call.data.replace("info_", "")
    data = BOT_TYPES.get(code)
    if not data:
        return
    bot.send_message(call.message.chat.id, f"""{data["info"]}

💵 <b>Bot ochish narxi:</b> 200 000 so'm
💰 <b>Oylik tarif:</b> pastdan tanlanadi

Quyidan tarif tanlang 👇""", reply_markup=tariff_keyboard(code))

@bot.callback_query_handler(func=lambda c: c.data.startswith("tariff_"))
def choose_tariff(call):
    parts = call.data.split("_")
    bot_code = parts[1]
    tariff = parts[2]
    price = int(parts[3])

    cur.execute("SELECT balance FROM users WHERE user_id=?", (call.from_user.id,))
    row = cur.fetchone()
    balance = row[0] if row else 0

    if balance < price:
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("💳 Pul kiritish", callback_data="go_deposit"))
        kb.add(types.InlineKeyboardButton("🔙 Ortga", callback_data=f"info_{bot_code}"))
        bot.send_message(call.message.chat.id, f"""❌ <b>Balans yetarli emas.</b>

💰 Balansingiz: <b>{balance:,} so'm</b>
💵 Kerak: <b>{price:,} so'm</b>

Avval pul kiriting 👇""", reply_markup=kb)
        return

    states[call.from_user.id] = {
        "step": "token",
        "bot_code": bot_code,
        "tariff": tariff,
        "price": price
    }

    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("❌ Bekor qilish", callback_data="cancel"))
    bot.send_message(call.message.chat.id, """🔑 BotFatherdan olingan bot tokenini yuboring.

Masalan:
<code>123456789:ABCDEF...</code>

Agar token yo'q bo'lsa, @BotFather dan yangi bot ochib token oling.""", reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data == "go_deposit")
def go_deposit_cb(call):
    states[call.from_user.id] = {"step": "amount"}
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("❌ Bekor qilish", callback_data="cancel"))
    bot.send_message(call.message.chat.id, "💳 Qancha pul kiritmoqchisiz?\n\nMasalan: <code>50000</code>", reply_markup=kb)

BOT_TEMPLATE_FILES = {
    "shop": "bot_templates/shop_bot.py",
    "smm": "bot_templates/smm_bot.py",
    "payment": "bot_templates/payment_bot.py",
    "taxi": "bot_templates/taxi_bot.py",
    "food": "bot_templates/food_bot.py",
    "test": "bot_templates/test_bot.py",
    "course": "bot_templates/course_bot.py",
    "obuna": "bot_templates/obuna_bot.py",
    "ai": "bot_templates/ai_bot.py",
    "zayavka": "bot_templates/zayavka_bot.py",
}

def auto_configure_bot(token, bot_name, bot_code):
    import requests as req
    try:
        commands = [
            {"command": "start", "description": "Botni ishga tushirish"},
        ]
        req.post(f"https://api.telegram.org/bot{token}/setMyCommands",
                 json={"commands": commands}, timeout=10)
        req.post(f"https://api.telegram.org/bot{token}/setMyDescription",
                 json={"description": f"{bot_name} — X VBrain tomonidan yaratilgan"}, timeout=10)
    except:
        pass

def send_bot_template(chat_id, bot_code, token, tariff):
    template_path = BOT_TEMPLATE_FILES.get(bot_code)
    if not template_path or not os.path.exists(template_path):
        return
    try:
        with open(template_path, "r", encoding="utf-8") as f:
            content = f.read()
        content = content.replace("YOUR_TOKEN_HERE", token)
        import tempfile
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py",
                                         prefix=f"{bot_code}_bot_",
                                         delete=False, encoding="utf-8") as tmp:
            tmp.write(content)
            tmp_path = tmp.name
        with open(tmp_path, "rb") as f:
            bot.send_document(chat_id, f,
                visible_file_name=f"{bot_code}_bot.py",
                caption=f"""✅ <b>Botingiz tayyor!</b>

📦 Fayl: <code>{bot_code}_bot.py</code>
🔑 Token allaqachon ichiga yozilgan

<b>Ishga tushirish uchun:</b>
1️⃣ Faylni serverga yuklang (Railway, VPS, Replit)
2️⃣ <code>pip install pyTelegramBotAPI</code>
3️⃣ <code>python {bot_code}_bot.py</code>

❓ Yordam: @X_VBRAIN""")
        os.unlink(tmp_path)
    except Exception as e:
        print(f"Template yuborishda xato: {e}")

@bot.message_handler(func=lambda m: states.get(m.from_user.id, {}).get("step") == "token")
def get_token(message):
    if message.text in MENU_BUTTONS:
        states.pop(message.from_user.id, None)
        bot.process_new_messages([message])
        return
    token = message.text.strip()
    state = states.get(message.from_user.id)

    if ":" not in token or len(token) < 25:
        bot.send_message(message.chat.id, "❌ Token noto'g'ri. Qayta yuboring.")
        return

    bot_code = state["bot_code"]
    tariff = state["tariff"]
    price = state["price"]
    bot_name = BOT_TYPES[bot_code]["name"]

    expires_at = int(time.time()) + WEEK

    cur.execute("UPDATE users SET balance = balance - ? WHERE user_id=?", (price, message.from_user.id))
    cur.execute("""
    INSERT INTO orders (user_id, bot_type, tariff, price, token, status, created_at, expires_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (message.from_user.id, bot_name, tariff, price, token, "approved", int(time.time()), expires_at))
    conn.commit()

    order_id = cur.lastrowid
    states.pop(message.from_user.id, None)
    username = f"@{message.from_user.username}" if message.from_user.username else "username yo'q"

    import datetime
    exp_str = datetime.datetime.fromtimestamp(expires_at).strftime("%d.%m.%Y")

    bot.send_message(message.chat.id, f"""⚙️ <b>Bot sozlanmoqda...</b>

🤖 Bot: {bot_name}
💎 Tarif: {tariff}

Bir soniya kuting ⏳""")

    auto_configure_bot(token, bot_name, bot_code)
    send_bot_template(message.chat.id, bot_code, token, tariff)

    bot.send_message(message.chat.id, f"""📅 <b>Obuna ma'lumoti</b>

🤖 Bot: {bot_name}
💎 Tarif: {tariff}
💰 Haftalik to'lov: {price:,} so'm
📅 Tugash sanasi: <b>{exp_str}</b>

⚠️ 1 hafta o'tgach to'lov qilmasangiz bot to'xtaydi.
📲 To'lov uchun: "💳 Obuna yangilash" tugmasini bosing.""")

    bot.send_message(ADMIN_ID, f"""📥 <b>Yangi bot buyurtma #{order_id}</b>

👤 User: {username}
🆔 ID: <code>{message.from_user.id}</code>
🤖 Bot turi: {bot_name}
💎 Tarif: {tariff}
💰 Narx: {price:,} so'm
🔑 Token: <code>{token}</code>
📅 Muddati: {exp_str}
✅ Holat: AVTOMATIK YUBORILDI""")

@bot.callback_query_handler(func=lambda c: c.data.startswith("orderok_") or c.data.startswith("orderno_"))
def order_decision(call):
    if call.from_user.id != ADMIN_ID:
        return bot.answer_callback_query(call.id, "Siz admin emassiz.")

    parts = call.data.rsplit("_", 1)
    action = parts[0]
    order_id = int(parts[1])

    cur.execute("SELECT user_id, bot_type FROM orders WHERE id=?", (order_id,))
    row = cur.fetchone()
    if not row:
        return bot.answer_callback_query(call.id, "Buyurtma topilmadi.")

    user_id, bot_type = row

    if action == "orderok":
        cur.execute("UPDATE orders SET status='approved' WHERE id=?", (order_id,))
        conn.commit()
        bot.send_message(user_id, f"✅ <b>Buyurtmangiz tasdiqlandi!</b>\n\n🤖 Bot: {bot_type}\nAdmin siz bilan tez orada bog'lanadi.")
        bot.answer_callback_query(call.id, "Tasdiqlandi ✅")
    else:
        cur.execute("UPDATE orders SET status='rejected' WHERE id=?", (order_id,))
        conn.commit()
        bot.send_message(user_id, "❌ Buyurtmangiz rad etildi. Qo'shimcha ma'lumot uchun support bilan bog'laning: @X_VBRAIN")
        bot.answer_callback_query(call.id, "Rad etildi ❌")

# ───────────────────────── PRO BOT YARATISH ─────────────────────────

@bot.message_handler(func=lambda m: m.text == "⚡️ Pro bot yaratish")
def pro_bot_start(message):
    save_user(message)
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("🚀 Boshlash", callback_data="pro_start"))
    kb.add(types.InlineKeyboardButton("🔙 Ortga", callback_data="back_main"))
    bot.send_message(message.chat.id, """⚡️ <b>Pro Bot Yaratish</b>

Bu bo'limda siz o'zingizning botingizni <b>to'liq sozlab</b> buyurtma berasiz:

📝 Bot nomi
📋 Tavsif
🔑 Token
👋 Xush kelibsiz xabar
📞 Admin kontakt

💰 <b>Narxi: 150 000 so'm</b>

Tayyor bo'lsangiz, boshlang 👇""", reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data == "pro_start")
def pro_start(call):
    cur.execute("SELECT balance FROM users WHERE user_id=?", (call.from_user.id,))
    row = cur.fetchone()
    balance = row[0] if row else 0

    if balance < 150000:
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("💳 Pul kiritish", callback_data="go_deposit"))
        kb.add(types.InlineKeyboardButton("🔙 Ortga", callback_data="back_main"))
        bot.send_message(call.message.chat.id, f"""❌ <b>Balans yetarli emas.</b>

💰 Balansingiz: <b>{balance:,} so'm</b>
💵 Kerak: <b>150 000 so'm</b>""", reply_markup=kb)
        return

    states[call.from_user.id] = {"step": "pro_bot_name", "pro_data": {}}
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("❌ Bekor qilish", callback_data="cancel"))
    bot.send_message(call.message.chat.id, "⚡️ <b>Pro Bot — 1/5</b>\n\n🤖 Botingizning nomini yozing:\n\nMasalan: <code>MyShopBot</code>", reply_markup=kb)

@bot.message_handler(func=lambda m: states.get(m.from_user.id, {}).get("step") == "pro_bot_name")
def pro_bot_name(message):
    if message.text in MENU_BUTTONS:
        states.pop(message.from_user.id, None)
        bot.process_new_messages([message])
        return
    states[message.from_user.id]["pro_data"]["bot_name"] = message.text.strip()
    states[message.from_user.id]["step"] = "pro_description"
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("❌ Bekor qilish", callback_data="cancel"))
    bot.send_message(message.chat.id, "⚡️ <b>Pro Bot — 2/5</b>\n\n📝 Bot haqida qisqacha tavsif yozing:", reply_markup=kb)

@bot.message_handler(func=lambda m: states.get(m.from_user.id, {}).get("step") == "pro_description")
def pro_description(message):
    if message.text in MENU_BUTTONS:
        states.pop(message.from_user.id, None)
        bot.process_new_messages([message])
        return
    states[message.from_user.id]["pro_data"]["description"] = message.text.strip()
    states[message.from_user.id]["step"] = "pro_token"
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("❌ Bekor qilish", callback_data="cancel"))
    bot.send_message(message.chat.id, "⚡️ <b>Pro Bot — 3/5</b>\n\n🔑 BotFather tokenini yuboring:\n\nMasalan: <code>123456789:ABCDEF...</code>", reply_markup=kb)

@bot.message_handler(func=lambda m: states.get(m.from_user.id, {}).get("step") == "pro_token")
def pro_token(message):
    if message.text in MENU_BUTTONS:
        states.pop(message.from_user.id, None)
        bot.process_new_messages([message])
        return
    token = message.text.strip()
    if ":" not in token or len(token) < 25:
        bot.send_message(message.chat.id, "❌ Token noto'g'ri. Qayta yuboring.")
        return
    states[message.from_user.id]["pro_data"]["token"] = token
    states[message.from_user.id]["step"] = "pro_welcome"
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("❌ Bekor qilish", callback_data="cancel"))
    bot.send_message(message.chat.id, "⚡️ <b>Pro Bot — 4/5</b>\n\n👋 /start bosganda ko'rinadigan xush kelibsiz xabarni yozing:", reply_markup=kb)

@bot.message_handler(func=lambda m: states.get(m.from_user.id, {}).get("step") == "pro_welcome")
def pro_welcome(message):
    if message.text in MENU_BUTTONS:
        states.pop(message.from_user.id, None)
        bot.process_new_messages([message])
        return
    states[message.from_user.id]["pro_data"]["welcome"] = message.text.strip()
    states[message.from_user.id]["step"] = "pro_contact"
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("❌ Bekor qilish", callback_data="cancel"))
    bot.send_message(message.chat.id, "⚡️ <b>Pro Bot — 5/5</b>\n\n📞 Admin aloqa (username yoki telefon):\n\nMasalan: <code>@username</code>", reply_markup=kb)

@bot.message_handler(func=lambda m: states.get(m.from_user.id, {}).get("step") == "pro_contact")
def pro_contact(message):
    if message.text in MENU_BUTTONS:
        states.pop(message.from_user.id, None)
        bot.process_new_messages([message])
        return
    state = states.get(message.from_user.id)
    pro_data = state["pro_data"]
    pro_data["contact"] = message.text.strip()

    cur.execute("UPDATE users SET balance = balance - 150000 WHERE user_id=?", (message.from_user.id,))
    cur.execute("""
    INSERT INTO orders (user_id, bot_type, tariff, price, token, status, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (message.from_user.id, f"⚡️ Pro: {pro_data['bot_name']}", "Pro", 150000, pro_data["token"], "pending", int(time.time())))
    conn.commit()

    order_id = cur.lastrowid
    states.pop(message.from_user.id, None)
    username = f"@{message.from_user.username}" if message.from_user.username else "username yo'q"

    kb = types.InlineKeyboardMarkup()
    kb.add(
        types.InlineKeyboardButton("✅ Tasdiqlash", callback_data=f"orderok_{order_id}"),
        types.InlineKeyboardButton("❌ Rad etish", callback_data=f"orderno_{order_id}")
    )

    bot.send_message(ADMIN_ID, f"""⚡️ <b>Yangi PRO bot buyurtma #{order_id}</b>

👤 User: {username}
🆔 ID: <code>{message.from_user.id}</code>

🤖 Bot nomi: {pro_data['bot_name']}
📝 Tavsif: {pro_data['description']}
🔑 Token: <code>{pro_data['token']}</code>
👋 Welcome xabar: {pro_data['welcome']}
📞 Kontakt: {pro_data['contact']}

💰 Narx: 150 000 so'm
Holat: ⏳ kutilmoqda""", reply_markup=kb)

    bot.send_message(message.chat.id, f"""✅ <b>Pro bot buyurtmangiz qabul qilindi!</b>

🤖 Bot nomi: {pro_data['bot_name']}
💰 To'landi: 150 000 so'm

Admin tekshiradi va botingizni to'liq sozlab beradi. ⏳""", reply_markup=main_menu())

# ───────────────────────── BOTLARIM ─────────────────────────

@bot.message_handler(func=lambda m: m.text == "📋 Botlarim")
def my_bots(message):
    import datetime
    cur.execute("""SELECT id, bot_type, tariff, price, status, expires_at
                   FROM orders WHERE user_id=? ORDER BY id DESC""", (message.from_user.id,))
    rows = cur.fetchall()

    if not rows:
        bot.send_message(message.chat.id, "📭 Sizda hali bot yo'q.\n\n🤖 Bot yaratish uchun menyudan foydalaning.")
        return

    now = int(time.time())
    text = "📋 <b>Mening botlarim</b>\n\n"
    for r in rows:
        oid, btype, tariff, price, status, expires_at = r
        if status == "approved":
            if expires_at and expires_at > 0:
                qoldi = expires_at - now
                if qoldi <= 0:
                    st = "❌ Muddati tugagan"
                elif qoldi <= 2 * 24 * 3600:
                    h = qoldi // 3600
                    st = f"⚠️ {h} soat qoldi"
                else:
                    d = qoldi // 86400
                    exp_str = datetime.datetime.fromtimestamp(expires_at).strftime("%d.%m.%Y")
                    st = f"✅ Aktiv — {exp_str} gacha ({d} kun)"
            else:
                st = "✅ Aktiv"
        elif status == "expired":
            st = "❌ To'xtatilgan (obuna tugagan)"
        elif status == "pending":
            st = "⏳ Kutilmoqda"
        elif status == "rejected":
            st = "🚫 Rad etilgan"
        else:
            st = status

        text += f"🆔 <b>#{oid}</b> — {btype}\n"
        text += f"💎 {tariff} | 💰 {price:,} so'm/hafta\n"
        text += f"📌 {st}\n"
        if expires_at and expires_at > 0 and status in ("approved", "expired"):
            if expires_at < now:
                kb_renew = types.InlineKeyboardMarkup()
                kb_renew.add(types.InlineKeyboardButton("🔄 Obuna yangilash", callback_data=f"subrenew_{oid}"))
        text += "\n"

    bot.send_message(message.chat.id, text)

# ───────────────────────── PUL KIRITISH ─────────────────────────

@bot.message_handler(func=lambda m: m.text == "💳 Pul kiritish")
def deposit(message):
    states[message.from_user.id] = {"step": "amount"}
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("❌ Bekor qilish", callback_data="cancel"))
    bot.send_message(message.chat.id, "💳 Qancha pul kiritmoqchisiz?\n\nMasalan: <code>50000</code>", reply_markup=kb)

MENU_BUTTONS = [
    "🤖 Bot yaratish", "⚡️ Pro bot yaratish", "📋 Botlarim", "💰 Hisobim",
    "💳 Pul kiritish", "👥 Referal", "📕 Qo'llanma", "☎️ Qo'llab-quvvatlash",
    "📋 Buyurtmalar", "💳 To'lovlar", "🎁 Bonus pul berish", "👥 Foydalanuvchilar",
    "📊 Statistika", "📢 Xabar yuborish", "🔙 Asosiy menyu"
]

@bot.message_handler(func=lambda m: states.get(m.from_user.id, {}).get("step") == "amount")
def amount_handler(message):
    if message.text in MENU_BUTTONS:
        states.pop(message.from_user.id, None)
        bot.process_new_messages([message])
        return
    try:
        amount_value = int(message.text.replace(" ", "").replace(",", ""))
    except:
        bot.send_message(message.chat.id, "❌ Faqat raqam yozing. Masalan: <code>50000</code>")
        return

    if amount_value < 1000:
        bot.send_message(message.chat.id, "❌ Minimal miqdor: 1 000 so'm")
        return

    states[message.from_user.id] = {"step": "payment_photo", "amount": amount_value}
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("❌ Bekor qilish", callback_data="cancel"))
    bot.send_message(message.chat.id, f"""💳 <b>To'lov qiling</b>

Karta:
<code>{CARD_NUMBER}</code>

💰 Miqdor: <b>{amount_value:,} so'm</b>

📸 To'lov screenshotini yuboring 👇""", reply_markup=kb)

@bot.message_handler(content_types=["photo"])
def payment_photo(message):
    state = states.get(message.from_user.id)
    if not state or state.get("step") != "payment_photo":
        return

    amount_value = state["amount"]
    username = f"@{message.from_user.username}" if message.from_user.username else "username yo'q"

    cur.execute("INSERT INTO payments (user_id, amount, status, created_at) VALUES (?, ?, ?, ?)",
                (message.from_user.id, amount_value, "pending", int(time.time())))
    conn.commit()
    pay_id = cur.lastrowid

    kb = types.InlineKeyboardMarkup()
    kb.add(
        types.InlineKeyboardButton("✅ Tasdiqlash", callback_data=f"payok_{pay_id}"),
        types.InlineKeyboardButton("❌ Rad etish", callback_data=f"payno_{pay_id}")
    )

    bot.send_photo(ADMIN_ID, message.photo[-1].file_id, caption=f"""💳 <b>Yangi to'lov #{pay_id}</b>

👤 User: {username}
🆔 ID: <code>{message.from_user.id}</code>
💰 Miqdor: {amount_value:,} so'm""", reply_markup=kb)

    states.pop(message.from_user.id, None)
    bot.send_message(message.chat.id, "✅ To'lov adminga yuborildi. Tasdiqlanishini kuting. ⏳", reply_markup=main_menu())

@bot.callback_query_handler(func=lambda c: c.data.startswith("payok_") or c.data.startswith("payno_"))
def pay_decision(call):
    if call.from_user.id != ADMIN_ID:
        return bot.answer_callback_query(call.id, "Siz admin emassiz.")

    parts = call.data.rsplit("_", 1)
    action = parts[0]
    pay_id = int(parts[1])

    cur.execute("SELECT user_id, amount, status FROM payments WHERE id=?", (pay_id,))
    row = cur.fetchone()
    if not row:
        return bot.answer_callback_query(call.id, "To'lov topilmadi.")

    user_id, amount_value, status = row
    if status != "pending":
        return bot.answer_callback_query(call.id, "Bu to'lov avval tekshirilgan.")

    if action == "payok":
        cur.execute("UPDATE users SET balance = balance + ? WHERE user_id=?", (amount_value, user_id))
        cur.execute("UPDATE payments SET status='approved' WHERE id=?", (pay_id,))
        conn.commit()
        bot.send_message(user_id, f"✅ <b>To'lov tasdiqlandi!</b>\n\n💰 Balansga <b>{amount_value:,} so'm</b> qo'shildi.")
        bot.answer_callback_query(call.id, "Tasdiqlandi ✅")
    else:
        cur.execute("UPDATE payments SET status='rejected' WHERE id=?", (pay_id,))
        conn.commit()
        bot.send_message(user_id, "❌ To'lovingiz rad etildi. Support: @X_VBRAIN")
        bot.answer_callback_query(call.id, "Rad etildi ❌")

# ───────────────────────── HISOBIM ─────────────────────────

@bot.message_handler(func=lambda m: m.text == "💰 Hisobim")
def account(message):
    cur.execute("SELECT balance FROM users WHERE user_id=?", (message.from_user.id,))
    row = cur.fetchone()
    balance = row[0] if row else 0
    cur.execute("SELECT COUNT(*) FROM orders WHERE user_id=?", (message.from_user.id,))
    orders_count = cur.fetchone()[0]

    bot.send_message(message.chat.id, f"""💰 <b>Hisobim</b>

🆔 ID: <code>{message.from_user.id}</code>
💵 Balans: <b>{balance:,} so'm</b>
🤖 Buyurtmalar: {orders_count} ta""")

# ───────────────────────── REFERAL ─────────────────────────

@bot.message_handler(func=lambda m: m.text == "👥 Referal")
def referal(message):
    try:
        username = bot.get_me().username
    except:
        username = "XVBrainBuilderBot"
    link = f"https://t.me/{username}?start={message.from_user.id}"
    cur.execute("SELECT ref_count FROM users WHERE user_id=?", (message.from_user.id,))
    row = cur.fetchone()
    ref_count = row[0] if row and row[0] else 0

    bot.send_message(message.chat.id, f"""👥 <b>Referal tizimi</b>

🔗 Sizning linkingiz:
<code>{link}</code>

👆 Linkni nusxalab do'stlaringizga yuboring!

📊 Taklif qilganlaringiz: <b>{ref_count} kishi</b>
💰 Har bir do'st uchun: <b>{REFERRAL_BONUS:,} so'm</b> bonus

🎁 Do'st siz orqali ro'yxatdan o'tsa — balansga avtomatik bonus qo'shiladi!""")

# ───────────────────────── QO'LLANMA ─────────────────────────

@bot.message_handler(func=lambda m: m.text == "📕 Qo'llanma")
def guide(message):
    bot.send_message(message.chat.id, """📕 <b>Qo'llanma</b>

<b>Oddiy bot buyurtma:</b>
1️⃣ Pul kiriting
2️⃣ "🤖 Bot yaratish" ga kiring
3️⃣ Bot turini tanlang
4️⃣ Tarif tanlang
5️⃣ BotFather token yuboring
6️⃣ Admin tasdiqlaydi va botingiz tayyorlanadi

<b>Pro bot buyurtma:</b>
1️⃣ "⚡️ Pro bot yaratish" ga kiring
2️⃣ Barcha ma'lumotlarni kiriting
3️⃣ Admin sizga maxsus bot tayyorlab beradi

Support: @X_VBRAIN""")

# ───────────────────────── SUPPORT CHAT ─────────────────────────

@bot.message_handler(func=lambda m: m.text == "☎️ Qo'llab-quvvatlash")
def support(message):
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("💬 Xabar yuborish", callback_data="support_write"))
    bot.send_message(message.chat.id, """☎️ <b>Qo'llab-quvvatlash</b>

📩 @X_VBRAIN orqali murojaat qilishingiz mumkin.

Yoki pastdagi tugma orqali to'g'ridan-to'g'ri xabar yuboring 👇""", reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data == "support_write")
def support_write(call):
    states[call.from_user.id] = {"step": "support_msg"}
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("❌ Bekor qilish", callback_data="cancel"))
    bot.send_message(call.message.chat.id, "💬 <b>Xabaringizni yozing:</b>\n\nAdmin iloji boricha tez javob beradi ⏰", reply_markup=kb)

@bot.message_handler(func=lambda m: states.get(m.from_user.id, {}).get("step") == "support_msg")
def support_msg_handler(message):
    if message.text in MENU_BUTTONS:
        states.pop(message.from_user.id, None)
        bot.process_new_messages([message])
        return
    state = states.pop(message.from_user.id, {})
    username = f"@{message.from_user.username}" if message.from_user.username else str(message.from_user.id)

    cur.execute("INSERT INTO support_msgs (user_id, message, created_at) VALUES (?,?,?)",
                (message.from_user.id, message.text, int(time.time())))
    conn.commit()
    msg_id = cur.lastrowid

    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(f"↩️ Javob berish", callback_data=f"sreply_{message.from_user.id}_{msg_id}"))
    bot.send_message(ADMIN_ID, f"""💬 <b>Support xabar #{msg_id}</b>

👤 {username}
🆔 <code>{message.from_user.id}</code>

📝 {message.text}""", reply_markup=kb)

    bot.send_message(message.chat.id, "✅ Xabaringiz adminga yuborildi! Javob kelishini kuting ⏳", reply_markup=main_menu())

@bot.callback_query_handler(func=lambda c: c.data.startswith("sreply_"))
def support_reply_start(call):
    if call.from_user.id != ADMIN_ID:
        return
    parts = call.data.split("_")
    target_uid = int(parts[1])
    msg_id = int(parts[2])
    states[call.from_user.id] = {"step": "sreply", "target_uid": target_uid, "msg_id": msg_id}
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("❌ Bekor qilish", callback_data="cancel_admin"))
    bot.send_message(call.message.chat.id, f"✏️ User <code>{target_uid}</code> ga javob yozing:", reply_markup=kb)

@bot.message_handler(func=lambda m: states.get(m.from_user.id, {}).get("step") == "sreply" and m.from_user.id == ADMIN_ID)
def support_reply_send(message):
    state = states.pop(message.from_user.id, {})
    target_uid = state["target_uid"]
    msg_id = state.get("msg_id")
    try:
        bot.send_message(target_uid, f"📩 <b>Admin javobi:</b>\n\n{message.text}")
        cur.execute("UPDATE support_msgs SET replied=1 WHERE id=?", (msg_id,))
        conn.commit()
        bot.send_message(message.chat.id, "✅ Javob yuborildi!", reply_markup=admin_menu())
    except:
        bot.send_message(message.chat.id, "❌ Xabar yuborishda xato.", reply_markup=admin_menu())

# ───────────────────────── CANCEL ─────────────────────────

@bot.callback_query_handler(func=lambda c: c.data == "cancel")
def cancel(call):
    states.pop(call.from_user.id, None)
    bot.send_message(call.message.chat.id, "❌ Bekor qilindi.", reply_markup=main_menu())

# ───────────────────────── ADMIN PANEL ─────────────────────────

@bot.message_handler(commands=["admin"])
def admin_panel_cmd(message):
    if message.from_user.id != ADMIN_ID:
        return bot.send_message(message.chat.id, "❌ Siz admin emassiz.")
    show_admin_menu(message.chat.id)

def show_admin_menu(chat_id):
    cur.execute("SELECT COUNT(*) FROM users")
    users = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM orders WHERE status='pending'")
    pending_orders = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM payments WHERE status='pending'")
    pending_payments = cur.fetchone()[0]

    bot.send_message(chat_id, f"""🛠 <b>Admin Panel</b>

👥 Foydalanuvchilar: {users}
📋 Kutilayotgan buyurtmalar: {pending_orders}
💳 Kutilayotgan to'lovlar: {pending_payments}

Quyidagi bo'limlardan birini tanlang 👇""", reply_markup=admin_menu())

@bot.message_handler(func=lambda m: m.text == "🔙 Asosiy menyu" and m.from_user.id == ADMIN_ID)
def admin_back_main(message):
    states.pop(message.from_user.id, None)
    bot.send_message(message.chat.id, "🏠 Asosiy menyu", reply_markup=main_menu())

@bot.message_handler(func=lambda m: m.text == "📊 Statistika" and m.from_user.id == ADMIN_ID)
def admin_stats(message):
    cur.execute("SELECT COUNT(*) FROM users")
    users = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM orders")
    all_orders = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM orders WHERE status='approved'")
    approved = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM orders WHERE status='pending'")
    pending = cur.fetchone()[0]
    cur.execute("SELECT SUM(amount) FROM payments WHERE status='approved'")
    total_income = cur.fetchone()[0] or 0
    cur.execute("SELECT SUM(balance) FROM users")
    total_balance = cur.fetchone()[0] or 0

    bot.send_message(message.chat.id, f"""📊 <b>Statistika</b>

👥 Jami foydalanuvchilar: {users}
🤖 Jami buyurtmalar: {all_orders}
✅ Tasdiqlangan: {approved}
⏳ Kutilayotgan: {pending}

💰 Jami tushum: {total_income:,} so'm
💵 Barcha balanslar: {total_balance:,} so'm""")

@bot.message_handler(func=lambda m: m.text == "📋 Buyurtmalar" and m.from_user.id == ADMIN_ID)
def admin_orders(message):
    cur.execute("SELECT id, user_id, bot_type, tariff, price, status FROM orders WHERE status='pending' ORDER BY id DESC LIMIT 10")
    rows = cur.fetchall()

    if not rows:
        bot.send_message(message.chat.id, "📭 Kutilayotgan buyurtmalar yo'q.")
        return

    for r in rows:
        kb = types.InlineKeyboardMarkup()
        kb.add(
            types.InlineKeyboardButton("✅ Tasdiqlash", callback_data=f"orderok_{r[0]}"),
            types.InlineKeyboardButton("❌ Rad etish", callback_data=f"orderno_{r[0]}")
        )
        bot.send_message(message.chat.id, f"""📋 <b>Buyurtma #{r[0]}</b>

🆔 User ID: <code>{r[1]}</code>
🤖 Bot: {r[2]}
💎 Tarif: {r[3]}
💰 Narx: {r[4]:,} so'm
📌 Holat: ⏳ kutilmoqda""", reply_markup=kb)

@bot.message_handler(func=lambda m: m.text == "💳 To'lovlar" and m.from_user.id == ADMIN_ID)
def admin_payments(message):
    cur.execute("SELECT id, user_id, amount FROM payments WHERE status='pending' ORDER BY id DESC LIMIT 10")
    rows = cur.fetchall()

    if not rows:
        bot.send_message(message.chat.id, "📭 Kutilayotgan to'lovlar yo'q.")
        return

    for r in rows:
        kb = types.InlineKeyboardMarkup()
        kb.add(
            types.InlineKeyboardButton("✅ Tasdiqlash", callback_data=f"payok_{r[0]}"),
            types.InlineKeyboardButton("❌ Rad etish", callback_data=f"payno_{r[0]}")
        )
        bot.send_message(message.chat.id, f"""💳 <b>To'lov #{r[0]}</b>

🆔 User ID: <code>{r[1]}</code>
💰 Miqdor: {r[2]:,} so'm
📌 Holat: ⏳ kutilmoqda""", reply_markup=kb)

@bot.message_handler(func=lambda m: m.text == "👥 Foydalanuvchilar" and m.from_user.id == ADMIN_ID)
def admin_users(message):
    cur.execute("SELECT user_id, username, balance, created_at FROM users ORDER BY created_at DESC LIMIT 15")
    rows = cur.fetchall()

    if not rows:
        bot.send_message(message.chat.id, "📭 Foydalanuvchilar yo'q.")
        return

    text = "👥 <b>So'nggi foydalanuvchilar</b>\n\n"
    for r in rows:
        uname = f"@{r[1]}" if r[1] else "yo'q"
        text += f"🆔 <code>{r[0]}</code> | {uname} | 💰 {r[2]:,} so'm\n"

    bot.send_message(message.chat.id, text)

@bot.message_handler(func=lambda m: m.text == "🎁 Bonus pul berish" and m.from_user.id == ADMIN_ID)
def admin_bonus(message):
    states[message.from_user.id] = {"step": "bonus_id"}
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("❌ Bekor qilish", callback_data="cancel_admin"))
    bot.send_message(message.chat.id, "🎁 <b>Bonus pul berish</b>\n\nUser ID raqamini yozing:\n\nMasalan: <code>123456789</code>", reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data == "cancel_admin")
def cancel_admin(call):
    states.pop(call.from_user.id, None)
    show_admin_menu(call.message.chat.id)

@bot.message_handler(func=lambda m: states.get(m.from_user.id, {}).get("step") == "bonus_id")
def bonus_get_id(message):
    if message.text in MENU_BUTTONS:
        states.pop(message.from_user.id, None)
        bot.process_new_messages([message])
        return
    try:
        target_id = int(message.text.strip())
    except:
        bot.send_message(message.chat.id, "❌ Noto'g'ri ID. Qayta yuboring.")
        return

    cur.execute("SELECT user_id, username FROM users WHERE user_id=?", (target_id,))
    row = cur.fetchone()
    if not row:
        bot.send_message(message.chat.id, "❌ Bu ID da foydalanuvchi topilmadi.")
        return

    states[message.from_user.id] = {"step": "bonus_amount", "target_id": target_id, "target_username": row[1]}
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("❌ Bekor qilish", callback_data="cancel_admin"))
    uname = f"@{row[1]}" if row[1] else str(target_id)
    bot.send_message(message.chat.id, f"🎁 <b>{uname}</b> ga necha so'm bonus berasiz?\n\nMasalan: <code>50000</code>", reply_markup=kb)

@bot.message_handler(func=lambda m: states.get(m.from_user.id, {}).get("step") == "bonus_amount")
def bonus_give(message):
    if message.text in MENU_BUTTONS:
        states.pop(message.from_user.id, None)
        bot.process_new_messages([message])
        return
    try:
        bonus = int(message.text.replace(" ", "").replace(",", ""))
    except:
        bot.send_message(message.chat.id, "❌ Faqat raqam yozing. Masalan: <code>50000</code>")
        return

    state = states.pop(message.from_user.id, {})
    target_id = state["target_id"]
    target_username = state.get("target_username")

    cur.execute("UPDATE users SET balance = balance + ? WHERE user_id=?", (bonus, target_id))
    conn.commit()

    uname = f"@{target_username}" if target_username else str(target_id)
    bot.send_message(message.chat.id, f"✅ <b>{uname}</b> ga <b>{bonus:,} so'm</b> bonus berildi!", reply_markup=admin_menu())
    try:
        bot.send_message(target_id, f"🎁 <b>Sizga bonus!</b>\n\n💰 Balansga <b>{bonus:,} so'm</b> qo'shildi!\n\nX VBrain adminidan sovg'a 🎉")
    except:
        pass

@bot.message_handler(func=lambda m: m.text == "📢 Xabar yuborish" and m.from_user.id == ADMIN_ID)
def admin_broadcast_start(message):
    states[message.from_user.id] = {"step": "broadcast"}
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("❌ Bekor qilish", callback_data="cancel_admin"))
    bot.send_message(message.chat.id, "📢 <b>Reklama / Xabar yuborish</b>\n\nBarcha foydalanuvchilarga yuboriladigan xabarni yozing:", reply_markup=kb)

@bot.message_handler(func=lambda m: states.get(m.from_user.id, {}).get("step") == "broadcast")
def admin_broadcast(message):
    if message.text in MENU_BUTTONS:
        states.pop(message.from_user.id, None)
        bot.process_new_messages([message])
        return
    states.pop(message.from_user.id, None)
    cur.execute("SELECT user_id FROM users")
    users = cur.fetchall()

    sent = 0
    failed = 0
    for (uid,) in users:
        try:
            bot.send_message(uid, f"📢 <b>X VBrain xabari:</b>\n\n{message.text}")
            sent += 1
        except:
            failed += 1

    bot.send_message(message.chat.id, f"✅ Xabar yuborildi!\n\n✅ Muvaffaqiyatli: {sent}\n❌ Yuborilmadi: {failed}", reply_markup=admin_menu())

# ───────────────────────── OBUNA YANGILASH ─────────────────────────

MENU_BUTTONS.append("🔄 Obuna yangilash")

@bot.message_handler(func=lambda m: m.text == "🔄 Obuna yangilash")
def sub_renew_menu(message):
    import datetime
    cur.execute("""SELECT id, bot_type, tariff, price, expires_at, status
                   FROM orders WHERE user_id=? AND status IN ('approved','expired')
                   ORDER BY id DESC""", (message.from_user.id,))
    rows = cur.fetchall()
    if not rows:
        bot.send_message(message.chat.id, "📭 Sizda hali bot yo'q.")
        return

    text = "🔄 <b>Obuna yangilash</b>\n\nBotingizni tanlang:\n\n"
    kb = types.InlineKeyboardMarkup(row_width=1)
    now = int(time.time())
    for r in rows:
        oid, btype, tariff, price, expires_at, status = r
        if expires_at:
            exp_str = datetime.datetime.fromtimestamp(expires_at).strftime("%d.%m.%Y")
            qoldi = max(0, (expires_at - now) // 3600)
            if status == "expired" or expires_at < now:
                label = f"❌ #{oid} {btype} — MUDDATI O'TGAN"
            elif qoldi <= 48:
                label = f"⚠️ #{oid} {btype} — {qoldi} soat qoldi"
            else:
                label = f"✅ #{oid} {btype} — {exp_str} gacha"
        else:
            label = f"#{oid} {btype}"
        kb.add(types.InlineKeyboardButton(
            f"{label} | {price:,} so'm/hafta",
            callback_data=f"subrenew_{oid}"
        ))
    bot.send_message(message.chat.id, "🔄 <b>Qaysi bot obunasini yangilamoqchisiz?</b>", reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data.startswith("subrenew_"))
def sub_renew_choose(call):
    order_id = int(call.data.replace("subrenew_", ""))
    cur.execute("SELECT bot_type, tariff, price FROM orders WHERE id=? AND user_id=?",
                (order_id, call.from_user.id))
    row = cur.fetchone()
    if not row:
        return bot.answer_callback_query(call.id, "Buyurtma topilmadi.")
    btype, tariff, price = row
    states[call.from_user.id] = {"step": "sub_photo", "order_id": order_id, "price": price, "btype": btype}
    bot.send_message(call.message.chat.id, f"""💳 <b>Obuna to'lovi</b>

🤖 Bot: {btype}
💎 Tarif: {tariff}
💰 Miqdor: <b>{price:,} so'm</b>

Karta:
<code>{CARD_NUMBER}</code>

📸 To'lov screenshotini yuboring 👇""")

@bot.message_handler(func=lambda m: states.get(m.from_user.id, {}).get("step") == "sub_photo",
                     content_types=["photo"])
def sub_payment_photo(message):
    state = states.get(message.from_user.id)
    if not state or state.get("step") != "sub_photo":
        return
    order_id = state["order_id"]
    price = state["price"]
    btype = state["btype"]
    username = f"@{message.from_user.username}" if message.from_user.username else str(message.from_user.id)

    cur.execute("INSERT INTO sub_payments (order_id, user_id, amount, status, created_at) VALUES (?,?,?,?,?)",
                (order_id, message.from_user.id, price, "pending", int(time.time())))
    conn.commit()
    sub_id = cur.lastrowid

    kb = types.InlineKeyboardMarkup()
    kb.add(
        types.InlineKeyboardButton("✅ Tasdiqlash", callback_data=f"subok_{sub_id}_{order_id}_{message.from_user.id}"),
        types.InlineKeyboardButton("❌ Rad etish", callback_data=f"subno_{sub_id}_{message.from_user.id}")
    )
    bot.send_photo(ADMIN_ID, message.photo[-1].file_id,
        caption=f"""🔄 <b>Obuna to'lovi #{sub_id}</b>

👤 {username}
🆔 <code>{message.from_user.id}</code>
🤖 {btype}
💰 {price:,} so'm
🆔 Buyurtma: #{order_id}""", reply_markup=kb)

    states.pop(message.from_user.id, None)
    bot.send_message(message.chat.id, "✅ To'lov adminga yuborildi. Tasdiqlanishini kuting ⏳", reply_markup=main_menu())

@bot.callback_query_handler(func=lambda c: c.data.startswith("subok_") or c.data.startswith("subno_"))
def sub_decision(call):
    if call.from_user.id != ADMIN_ID:
        return bot.answer_callback_query(call.id, "Siz admin emassiz.")

    import datetime
    parts = call.data.split("_")

    if call.data.startswith("subok_"):
        sub_id, order_id, user_id = int(parts[1]), int(parts[2]), int(parts[3])
        cur.execute("SELECT amount FROM sub_payments WHERE id=?", (sub_id,))
        row = cur.fetchone()
        if not row:
            return bot.answer_callback_query(call.id, "To'lov topilmadi.")

        cur.execute("SELECT expires_at FROM orders WHERE id=?", (order_id,))
        orow = cur.fetchone()
        now = int(time.time())
        current_exp = orow[0] if orow and orow[0] else now
        new_exp = max(current_exp, now) + WEEK

        cur.execute("UPDATE orders SET expires_at=?, status='approved', reminded=0 WHERE id=?", (new_exp, order_id))
        cur.execute("UPDATE sub_payments SET status='approved' WHERE id=?", (sub_id,))
        conn.commit()

        exp_str = datetime.datetime.fromtimestamp(new_exp).strftime("%d.%m.%Y")
        bot.send_message(user_id, f"✅ <b>Obuna tasdiqlandi!</b>\n\n📅 Yangi muddat: <b>{exp_str}</b> gacha\n\nBotingiz yana 1 hafta ishlaydi! 🎉")
        bot.answer_callback_query(call.id, f"Tasdiqlandi ✅ — {exp_str} gacha uzaytirildi")
    else:
        sub_id, user_id = int(parts[1]), int(parts[2])
        cur.execute("UPDATE sub_payments SET status='rejected' WHERE id=?", (sub_id,))
        conn.commit()
        bot.send_message(user_id, "❌ Obuna to'lovi rad etildi. Support: @X_VBRAIN")
        bot.answer_callback_query(call.id, "Rad etildi ❌")

# ───────────────────────── SUBSCRIPTION SCHEDULER ─────────────────────────

def subscription_scheduler():
    import datetime
    while True:
        try:
            now = int(time.time())

            # 2 kun qoldi — eslatma yuborish
            warn_from = now + 2 * 24 * 3600
            warn_to = now + 2 * 24 * 3600 + 3600
            cur.execute("""SELECT id, user_id, bot_type, tariff, price, expires_at
                           FROM orders
                           WHERE status='approved'
                           AND expires_at > ? AND expires_at <= ?
                           AND reminded=0""", (now, warn_from))
            soon = cur.fetchall()
            for row in soon:
                oid, uid, btype, tariff, price, exp in row:
                    try:
                        import datetime as dt
                        exp_str = dt.datetime.fromtimestamp(exp).strftime("%d.%m.%Y %H:%M")
                        kb = types.InlineKeyboardMarkup()
                        kb.add(types.InlineKeyboardButton("💳 Obuna yangilash", callback_data=f"subrenew_{oid}"))
                        bot.send_message(uid, f"""⚠️ <b>Obuna muddati tugayapti!</b>

🤖 Bot: {btype}
📅 Tugash: <b>{exp_str}</b>
💰 To'lov: {price:,} so'm

To'lov qilmasangiz bot to'xtab qoladi! ⏰""", reply_markup=kb)
                        cur.execute("UPDATE orders SET reminded=1 WHERE id=?", (oid,))
                        conn.commit()
                    except Exception as e:
                        print(f"Eslatma yuborishda xato {uid}: {e}")

            # Muddati o'tganlar — to'xtatish
            cur.execute("""SELECT id, user_id, bot_type
                           FROM orders
                           WHERE status='approved' AND expires_at > 0 AND expires_at < ?""", (now,))
            expired = cur.fetchall()
            for row in expired:
                oid, uid, btype = row
                try:
                    cur.execute("UPDATE orders SET status='expired' WHERE id=?", (oid,))
                    conn.commit()
                    kb = types.InlineKeyboardMarkup()
                    kb.add(types.InlineKeyboardButton("🔄 Obuna yangilash", callback_data=f"subrenew_{oid}"))
                    bot.send_message(uid, f"""❌ <b>Bot to'xtatildi!</b>

🤖 {btype} — obuna muddati tugadi.

To'lov qilib obunani yangilang 👇""", reply_markup=kb)
                    bot.send_message(ADMIN_ID, f"🔴 Buyurtma #{oid} ({btype}) muddati tugadi. User: {uid}")
                except Exception as e:
                    print(f"Expire xato {uid}: {e}")

        except Exception as e:
            print(f"Scheduler xato: {e}")

        time.sleep(3600)  # Har soatda tekshiradi

scheduler_thread = threading.Thread(target=subscription_scheduler, daemon=True)
scheduler_thread.start()

try:
    bot.set_my_commands([
        types.BotCommand("/start", "Botni ishga tushirish"),
        types.BotCommand("/admin", "Admin panel"),
    ])
except Exception as e:
    print(f"Komandalar o'rnatilmadi: {e}")

print("X VBrain Builder Bot ishga tushdi...")
bot.infinity_polling(skip_pending=True)
