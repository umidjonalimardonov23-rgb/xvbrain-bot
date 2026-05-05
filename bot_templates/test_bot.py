import os
import telebot
from telebot import types

BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_TOKEN_HERE")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

# Savollar ro'yxati — admin qo'shishi mumkin
QUESTIONS = [
    {"q": "Python nima?", "options": ["Dasturlash tili", "Ilон", "Brauzer", "OS"], "correct": 0},
    {"q": "HTML nima?", "options": ["Protokol", "Til", "Brauzer", "Server"], "correct": 1},
    {"q": "Bot nima?", "options": ["Odam", "Avtomatik dastur", "Telefon", "Kamera"], "correct": 1},
]

states = {}

def main_menu():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("📝 Testni boshlash")
    kb.row("🏆 Natijam", "📞 Aloqa")
    return kb

@bot.message_handler(commands=["start"])
def start(message):
    bot.send_message(message.chat.id, "📝 <b>Test Bot</b>\n\nBilimingizni sinab ko'ring! 👇", reply_markup=main_menu())

@bot.message_handler(func=lambda m: m.text == "📝 Testni boshlash")
def begin_test(message):
    states[message.from_user.id] = {"q": 0, "correct": 0}
    send_question(message.chat.id, message.from_user.id)

def send_question(chat_id, user_id):
    state = states.get(user_id)
    if state is None:
        return
    idx = state["q"]
    if idx >= len(QUESTIONS):
        correct = state["correct"]
        total = len(QUESTIONS)
        states.pop(user_id, None)
        bot.send_message(chat_id, f"""🏆 <b>Test tugadi!</b>

✅ To'g'ri: {correct}/{total}
📊 Ball: {int(correct/total*100)}%

{'🎉 Ajoyib!' if correct == total else '💪 Yaxshi urinish!'}""", reply_markup=main_menu())
        return
    q = QUESTIONS[idx]
    kb = types.InlineKeyboardMarkup(row_width=1)
    for i, opt in enumerate(q["options"]):
        kb.add(types.InlineKeyboardButton(opt, callback_data=f"ans_{i}"))
    bot.send_message(chat_id, f"❓ <b>Savol {idx+1}/{len(QUESTIONS)}</b>\n\n{q['q']}", reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data.startswith("ans_"))
def answer(call):
    state = states.get(call.from_user.id)
    if not state:
        return
    idx = state["q"]
    q = QUESTIONS[idx]
    chosen = int(call.data.replace("ans_", ""))
    if chosen == q["correct"]:
        state["correct"] += 1
        bot.answer_callback_query(call.id, "✅ To'g'ri!")
    else:
        bot.answer_callback_query(call.id, f"❌ Noto'g'ri! To'g'ri: {q['options'][q['correct']]}")
    state["q"] += 1
    send_question(call.message.chat.id, call.from_user.id)

@bot.message_handler(func=lambda m: m.text in ["🏆 Natijam", "📞 Aloqa"])
def stub(message):
    bot.send_message(message.chat.id, "📞 Admin: @X_VBRAIN" if "Aloqa" in message.text else "Hali test o'tkazilmagan.")

print("Test bot ishga tushdi!")
bot.infinity_polling(skip_pending=True)
