import os
import requests
import telebot
from telebot import types

BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_TOKEN_HERE")
OPENAI_KEY = os.getenv("OPENAI_KEY", "")  # OpenAI API kalitingizni qo'shing

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")
histories = {}

def main_menu():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("🤖 Savol berish", "🗑 Tarixni tozalash")
    kb.row("📞 Aloqa")
    return kb

def ask_gpt(user_id, text):
    if user_id not in histories:
        histories[user_id] = []
    histories[user_id].append({"role": "user", "content": text})
    try:
        resp = requests.post("https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {OPENAI_KEY}", "Content-Type": "application/json"},
            json={"model": "gpt-3.5-turbo", "messages": [{"role": "system", "content": "Siz foydali AI yordamchisiz. O'zbek tilida javob bering."}] + histories[user_id][-10:]},
            timeout=30)
        answer = resp.json()["choices"][0]["message"]["content"]
        histories[user_id].append({"role": "assistant", "content": answer})
        return answer
    except Exception as e:
        return f"❌ Xatolik yuz berdi: {e}"

@bot.message_handler(commands=["start"])
def start(message):
    bot.send_message(message.chat.id, "🤖 <b>AI ChatBot</b>\n\nSavolingizni yozing, javob beraman! 👇", reply_markup=main_menu())

@bot.message_handler(func=lambda m: m.text == "🗑 Tarixni tozalash")
def clear(message):
    histories.pop(message.from_user.id, None)
    bot.send_message(message.chat.id, "✅ Tarix tozalandi!")

@bot.message_handler(func=lambda m: m.text == "📞 Aloqa")
def contact(message):
    bot.send_message(message.chat.id, "📞 Admin: @X_VBRAIN")

@bot.message_handler(func=lambda m: m.text not in ["🤖 Savol berish", "🗑 Tarixni tozalash", "📞 Aloqa"])
def chat(message):
    bot.send_chat_action(message.chat.id, "typing")
    reply = ask_gpt(message.from_user.id, message.text)
    bot.send_message(message.chat.id, reply)

print("AI bot ishga tushdi!")
bot.infinity_polling(skip_pending=True)
