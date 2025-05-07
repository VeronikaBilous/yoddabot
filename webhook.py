from main import bot, TOKEN
from flask import Flask, request
import telebot
import os

# Отримуємо токен з середовища

app = Flask(__name__)

# Webhook endpoint для Telegram
@app.route(f'/{TOKEN}', methods=['POST'])
def telegram_webhook():
    if request.headers.get('content-type') == 'application/json':
        update = telebot.types.Update.de_json(request.data.decode("utf-8"))
        bot.process_new_updates([update])
    return 'ok', 200

# Простий маршрут для перевірки
@app.route('/')
def index():
    return '✅ Webhook активний!'

# Обробка будь-якого текстового повідомлення
@bot.message_handler(func=lambda message: True)
def echo_all(message):
    bot.reply_to(message, "Привіт! Я працюю через Webhook 😊")

# Коли запускається застосунок, встановлюємо webhook
if __name__ == '__main__':
    bot.remove_webhook()
    bot.set_webhook(url=f'https://yoddabot.onrender.com/{TOKEN}')
    # app.run(host='0.0.0.0', port=8080)
