import telebot
import os
import json
import random
import threading
import schedule
import time
from flask import Flask, request
from dotenv import load_dotenv

# Завантаження змінних середовища
load_dotenv()
TOKEN = os.getenv('TOKEN')
CHAT_ID = int(os.getenv('CHAT_ID'))
bot = telebot.TeleBot(TOKEN)

# Flask app
app = Flask(__name__)

@app.route(f'/{TOKEN}', methods=['POST'])
def receive_update():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
    return 'ok', 200

@app.route('/')
def index():
    return "✅ Webhook активний!"

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
    "🌟 Великий шлях починається з малого кроку!",
    "🔥 Успіх — це справа рішучості.",
    "💡 Віра в себе творить дива!",
    "🌱 Кожен день — нова можливість.",
    "🔥 Сьогодні твій день для перемог!",
    "🏆 Велика мрія — половина успіху!"
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

# ... [❗ Твій існуючий обробник callback_query_handler сюди вставляєш без змін]
# ... [❗ Твій обробник message_handler також вставляєш сюди без змін]

def morning_greeting():
    phrase = random.choice(morning_mantras)
    bot.send_message(CHAT_ID, f"💥 Доброго ранку, падаване! {phrase}", reply_markup=power_keyboard())

schedule.every().day.at("10:00").do(morning_greeting)

# Фоновий планувальник
def run_scheduler():
    while True:
        schedule.run_pending()
        time.sleep(60)

threading.Thread(target=run_scheduler).start()

# 👉 Встановлення webhook і запуск Flask
if __name__ == "__main__":
    bot.remove_webhook()
    bot.set_webhook(url='https://yoddabot.onrender.com/' + TOKEN)
    app.run(host="0.0.0.0", port=8080)
