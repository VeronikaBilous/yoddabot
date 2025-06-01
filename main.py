import telebot
import os
import json
import random
import threading
import schedule
import time
from dotenv import load_dotenv
from flask import Flask, request
from keep_alive import keep_alive

# Завантаження змінних середовища
load_dotenv()
TOKEN = os.getenv('TOKEN')
CHAT_ID = int(os.getenv('CHAT_ID'))
bot = telebot.TeleBot(TOKEN)

# Видалення старого webhook та створення нового
bot.remove_webhook()
time.sleep(1)
bot.set_webhook(url=f"https://yoddabot.onrender.com/{TOKEN}")

app = Flask(__name__)

@app.route(f"/{TOKEN}", methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        update = telebot.types.Update.de_json(request.data.decode('utf-8'))
        bot.process_new_updates([update])
        return 'ok', 200

@app.route('/')
def index():
    return 'Webhook active! 🚀', 200

# Дані
tasks = {}
user_states = {}

if os.path.exists("tasks.json"):
    with open("tasks.json", "r", encoding="utf-8") as f:
        tasks = json.load(f)

for user_id in list(tasks.keys()):
    if isinstance(tasks[user_id], list):
        tasks[user_id] = {"Список": tasks[user_id]}

def save_tasks():
    import shutil
    if os.path.exists("tasks.json"):
        shutil.copy("tasks.json", "tasks_backup.json")
    with open("tasks.json", "w", encoding="utf-8") as f:
        json.dump(tasks, f, ensure_ascii=False, indent=4)

def power_keyboard():
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(telebot.types.KeyboardButton("⚡ Power"))
    return markup

def inline_menu():
    markup = telebot.types.InlineKeyboardMarkup()
    markup.row(
        telebot.types.InlineKeyboardButton("📋 Списки", callback_data="list_lists"),
        telebot.types.InlineKeyboardButton("➕ Додати", callback_data="choose_list_for_add")
    )
    markup.row(
        telebot.types.InlineKeyboardButton("✅ Завершити", callback_data="choose_list_for_finish"),
        telebot.types.InlineKeyboardButton("🗑️ Видалити список", callback_data="delete_list")
    )
    markup.row(
        telebot.types.InlineKeyboardButton("✨ Натхнення", callback_data="inspiration"),
        telebot.types.InlineKeyboardButton("ℹ️ Інструкція", callback_data="instruction")
    )
    return markup

motivational_phrases = [
    "✨ Навіть маленький прогрес — це прогрес!",
    "🚀 Ти можеш більше, ніж здається!",
    "🌟 Великий шлях починається з малого кроку!"
]

morning_mantras = [
    "🌞 Прокинься і згадай: сила в тобі вже є!",
    "🌟 Сьогодні твій день для великих починань!",
    "🚀 Рушай уперед, не озираючись назад."
]

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "🛡️ Привіт, падаване! Power кнопку шукай, і шлях свій ти знайдеш!", reply_markup=power_keyboard())

@bot.message_handler(func=lambda message: message.text == "⚡ Power")
def send_main_menu(message):
    bot.send_message(message.chat.id, "📈 Обирай шлях свій:", reply_markup=inline_menu())

@bot.callback_query_handler(func=lambda call: True)
def handle_inline_buttons(call):
    print(f"Callback: {call.data}")  # DEBUG
    # ... (сюди встав логіку обробки кнопок з попереднього коду)
    bot.answer_callback_query(call.id)

# Функція натхнення зранку
def morning_greeting():
    phrase = random.choice(morning_mantras)
    bot.send_message(CHAT_ID, f"💥 Доброго ранку, падаване! {phrase}", reply_markup=power_keyboard())

# Запуск окремого потоку для натхнення
schedule.every().day.at("10:00").do(morning_greeting)
threading.Thread(target=lambda: [schedule.run_pending() or time.sleep(60)]).start()

# Старт Flask
if __name__ == '__main__':
    keep_alive()
    app.run(host="0.0.0.0", port=8080)
