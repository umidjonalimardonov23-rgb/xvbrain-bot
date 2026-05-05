import os
import telebot
from telebot import types

BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_TOKEN_HERE")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
CARD = os.getenv("CARD_NUMBER", "0000000000000000")

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")
states = {}

def main_menu():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("💳 To'lov qilish")
    kb.row("📞 Aloqa")
    return kb

@bot.message_handler(commands=["start"])
def start(message):
    bot.send_message(message.chat.id, "💳 <b>To'lov Bot</b>\n\nTo'lov qilish uchun tugmani bosing 👇", reply_markup=main_menu())

@bot.message_handler(func=lambda m: m.text == "💳 To'lov qilish")
def pay(message):
    states[message.from_user.id] = {"step": "amount"}
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("❌ Bekor qilish", callback_data="cancel"))
    bot.send_message(message.chat.id, "💰 Qancha to'lamoqchisiz? (so'mda)\n\nMasalan: <code>50000</code>", reply_markup=kb)

@bot.message_handler(func=lambda m: states.get(m.from_user.id, {}).get("step") == "amount")
def get_amount(message):
    if message.text == "💳 To'lov qilish" or message.text == "📞 Aloqa":
        states.pop(message.from_user.id, None)
        bot.process_new_messages([message])
        return
    try:
        amount = int(message.text.replace(" ", "").replace(",", ""))
    except:
        bot.send_message(message.chat.id, "❌ Faqat raqam yozing.")
        return
    states[message.from_user.id] = {"step": "screenshot", "amount": amount}
    bot.send_message(message.chat.id, f"""💳 <b>To'lov</b>

Karta: <code>{CARD}</code>
💰 Miqdor: <b>{amount:,} so'm</b>

📸 To'lov screenshotini yuboring""")

@bot.message_handler(content_types=["photo"])
def get_screenshot(message):
    state = states.get(message.from_user.id)
    if not state or state.get("step") != "screenshot":
        return
    amount = state["amount"]
    username = f"@{message.from_user.username}" if message.from_user.username else str(message.from_user.id)
    kb = types.InlineKeyboardMarkup()
    kb.add(
        types.InlineKeyboardButton("✅ Tasdiqlash", callback_data=f"ok_{message.from_user.id}_{amount}"),
        types.InlineKeyboardButton("❌ Rad etish", callback_data=f"no_{message.from_user.id}")
    )
    bot.send_photo(ADMIN_ID, message.photo[-1].file_id,
        caption=f"💳 <b>Yangi to'lov</b>\n\n👤 {username}\n🆔 <code>{message.from_user.id}</code>\n💰 {amount:,} so'm",
        reply_markup=kb)
    states.pop(message.from_user.id, None)
    bot.send_message(message.chat.id, "✅ To'lov adminga yuborildi!", reply_markup=main_menu())

@bot.callback_query_handler(func=lambda c: c.data.startswith("ok_") or c.data.startswith("no_"))
def decision(call):
    if call.from_user.id != ADMIN_ID:
        return
    if call.data.startswith("ok_"):
        parts = call.data.split("_")
        uid, amount = int(parts[1]), parts[2]
        bot.send_message(uid, f"✅ <b>To'lov tasdiqlandi!</b>\n\n💰 {int(amount):,} so'm qabul qilindi.")
        bot.answer_callback_query(call.id, "Tasdiqlandi ✅")
    else:
        uid = int(call.data.split("_")[1])
        bot.send_message(uid, "❌ To'lov rad etildi. Support: @X_VBRAIN")
        bot.answer_callback_query(call.id, "Rad etildi ❌")

@bot.callback_query_handler(func=lambda c: c.data == "cancel")
def cancel(call):
    states.pop(call.from_user.id, None)
    bot.send_message(call.message.chat.id, "❌ Bekor qilindi.", reply_markup=main_menu())

@bot.message_handler(func=lambda m: m.text == "📞 Aloqa")
def contact(message):
    bot.send_message(message.chat.id, "📞 Admin: @X_VBRAIN")

print("To'lov bot ishga tushdi!")
bot.infinity_polling(skip_pending=True)
