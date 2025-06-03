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

# Дані
tasks = {}
user_states = {}

if os.path.exists("tasks.json"):
    with open("tasks.json", "r", encoding="utf-8") as f:
        tasks = json.load(f)

# Оновлення структури зі списку у словник
for user_id in list(tasks.keys()):
    if isinstance(tasks[user_id], list):
        tasks[user_id] = {"Список": tasks[user_id]}

# Збереження
def save_tasks():
    import shutil
    if os.path.exists("tasks.json"):
        shutil.copy("tasks.json", "tasks_backup.json")  # створення бекапу
    with open("tasks.json", "w", encoding="utf-8") as f:
        json.dump(tasks, f, ensure_ascii=False, indent=4)

# Клавіатура

def power_keyboard():
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(telebot.types.KeyboardButton("\u26a1 Power"))
    return markup

def inline_menu():
    markup = telebot.types.InlineKeyboardMarkup()
    markup.row(
        telebot.types.InlineKeyboardButton("\ud83d\udccb Списки", callback_data="list_lists"),
        telebot.types.InlineKeyboardButton("\u2795 Додати", callback_data="choose_list_for_add")
    )
    markup.row(
        telebot.types.InlineKeyboardButton("\u2705 Завершити", callback_data="choose_list_for_finish"),
        telebot.types.InlineKeyboardButton("\ud83d\uddd1\ufe0f Видалити список", callback_data="delete_list")
    )
    markup.row(
        telebot.types.InlineKeyboardButton("\u2728 Натхнення", callback_data="inspiration"),
        telebot.types.InlineKeyboardButton("\u2139\ufe0f Інструкція", callback_data="instruction")
    )
    return markup

motivational_phrases = [
    "\u2728 Навіть маленький прогрес — це прогрес!",
    "\ud83d\ude80 Ти можеш більше, ніж здається!",
    "\ud83c\udf1f Великий шлях починається з малого кроку!",
    "\ud83d\udd25 Успіх — це справа рішучості.",
    "\ud83d\udca1 Віра в себе творить дива!",
    "\ud83c\udf31 Кожен день — нова можливість.",
    "\ud83d\udd25 Сьогодні твій день для перемог!",
    "\ud83c\udf1f Велика мрія — половина успіху!",
    "\ud83d\udea4 Шлях у тисячу миль починається з одного кроку.",
    "\ud83d\udca5 Найкращий час для дій — зараз!",
    "\ud83e\udde0 Вчись, рости і світ відкриється перед тобою!"
]

morning_mantras = [
    "\ud83c\udf1e Прокинься і згадай: сила в тобі вже є!",
    "\ud83c\udf1f Сьогодні твій день для великих починань!",
    "\ud83d\ude80 Рушай уперед, не озираючись назад."
]

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "\ud83d\udee1\ufe0f Привіт, падаване! Power кнопку шукай, і шлях свій ти знайдеш!", reply_markup=power_keyboard())

@bot.message_handler(func=lambda message: message.text == "\u26a1 Power")
def send_main_menu(message):
    bot.send_message(message.chat.id, "\ud83d\udcc8 Обирай шлях свій:", reply_markup=inline_menu())

@bot.callback_query_handler(func=lambda call: True)
def handle_inline_buttons(call):
    user_id = str(call.message.chat.id)
    if user_id not in tasks:
        tasks[user_id] = {}

    try:
        if call.data == "list_lists":
            if not tasks[user_id]:
                bot.send_message(call.message.chat.id, "\ud83d\udcdc Списків у тебе ще нема.", reply_markup=power_keyboard())
            else:
                msg = "\ud83d\udccb Твої списки:\n"
                for list_name, items in tasks[user_id].items():
                    sorted_items = sorted(items, key=lambda x: 0 if x.startswith("!") else 1)
                    msg += f"\n\ud83d\udd39 {list_name}:\n" + "\n".join(f"- {item}" for item in sorted_items)
                bot.send_message(call.message.chat.id, msg, reply_markup=power_keyboard())

        elif call.data == "choose_list_for_add":
            markup = telebot.types.InlineKeyboardMarkup()
            for name in tasks[user_id]:
                markup.add(telebot.types.InlineKeyboardButton(name, callback_data=f"add_to:{name}"))
            if len(tasks[user_id]) < 10:
                markup.add(telebot.types.InlineKeyboardButton("\u2795 Новий список", callback_data="create_new_list"))
            bot.send_message(call.message.chat.id, "\u2795 Обери список або створи новий:", reply_markup=markup)

        elif call.data.startswith("add_to:"):
            list_name = call.data.split(":")[1]
            user_states[user_id] = f"adding_to:{list_name}"
            bot.send_message(call.message.chat.id, f"\ud83d\udcdd Введи завдання через / . Всі будуть додані до списку: {list_name}", reply_markup=power_keyboard())

        elif call.data == "create_new_list":
            user_states[user_id] = "creating_new_list"
            bot.send_message(call.message.chat.id, "\ud83d\udcc2 Введи назву нового списку:", reply_markup=power_keyboard())

        elif call.data == "choose_list_for_finish":
            if not tasks[user_id]:
                bot.send_message(call.message.chat.id, "\ud83d\udcdc Немає списків для завершення.", reply_markup=power_keyboard())
            else:
                markup = telebot.types.InlineKeyboardMarkup()
                for name in tasks[user_id]:
                    markup.add(telebot.types.InlineKeyboardButton(name, callback_data=f"finish_from:{name}"))
                bot.send_message(call.message.chat.id, "\u2705 Обери список для завершення:", reply_markup=markup)

        elif call.data.startswith("finish_from:"):
            list_name = call.data.split(":")[1]
            user_states[user_id] = f"completing_from:{list_name}"
            tasks_list = tasks[user_id][list_name]
            if tasks_list:
                msg = f"\ud83d\udccb Завдання у списку {list_name}:\n"
                msg += "\n".join(f"{i+1}. {task}" for i, task in enumerate(tasks_list))
                msg += "\nВведи номери через кому або дефіс (1,2 або 1-3):"
                bot.send_message(call.message.chat.id, msg, reply_markup=power_keyboard())
            else:
                bot.send_message(call.message.chat.id, "\ud83d\udcdc Список порожній.", reply_markup=power_keyboard())

        elif call.data == "delete_list":
            if not tasks[user_id]:
                bot.send_message(call.message.chat.id, "\ud83d\udcdc Видаляти нічого. Немає списків.", reply_markup=power_keyboard())
            else:
                markup = telebot.types.InlineKeyboardMarkup()
                for name in tasks[user_id]:
                    markup.add(telebot.types.InlineKeyboardButton(f"\ud83d\uddd1\ufe0f {name}", callback_data=f"delete:{name}"))
                bot.send_message(call.message.chat.id, "\ud83d\uddd1\ufe0f Обери список для видалення:", reply_markup=markup)

        elif call.data.startswith("delete:"):
            list_name = call.data.split(":")[1]
            if list_name in tasks[user_id]:
                del tasks[user_id][list_name]
                save_tasks()
                bot.send_message(call.message.chat.id, f"\ud83d\uddd1\ufe0f Список {list_name} видалено.", reply_markup=power_keyboard())
            else:
                bot.send_message(call.message.chat.id, "\u274c Список не знайдено.", reply_markup=power_keyboard())

        elif call.data == "inspiration":
            phrase = random.choice(motivational_phrases)
            bot.send_message(call.message.chat.id, phrase, reply_markup=power_keyboard())

        elif call.data == "instruction":
            bot.send_message(call.message.chat.id, "\u2139\ufe0f Інструкція:\n\u26a1 Power — головна кнопка.\n\u2795 Додай через / кілька завдань.\n\u2705 Завершуй за номерами.\n\ud83d\udccb Використовуй ! для важливих.\n\ud83d\uddd1\ufe0f Видаляй зайві списки.\nМаєш максимум 10 списків!", reply_markup=power_keyboard())

        bot.answer_callback_query(call.id)

    except Exception as e:
        print(f"\u26a0\ufe0f Помилка в callback: {call.data}\n{e}")
        bot.send_message(call.message.chat.id, "\u26a0\ufe0f Щось пішло не так. Натисни \u26a1 Power.", reply_markup=power_keyboard())

@bot.message_handler(func=lambda message: True)
def handle_text(message):
    user_id = str(message.chat.id)
    text = message.text.strip()

    if user_id not in user_states:
        bot.send_message(message.chat.id, "\u26a1 Натисни Power, мудрості набудеш!", reply_markup=power_keyboard())
        return

    state = user_states[user_id]

    if state == "creating_new_list":
        if text in tasks[user_id]:
            bot.send_message(message.chat.id, "\u26a0\ufe0f Такий список вже існує.", reply_markup=power_keyboard())
        elif len(tasks[user_id]) >= 10:
            bot.send_message(message.chat.id, "\u26a0\ufe0f Досягнуто максимуму списків (10).", reply_markup=power_keyboard())
        else:
            tasks[user_id][text] = []
            save_tasks()
            bot.send_message(message.chat.id, f"\ud83d\udcc2 Створено список: {text}", reply_markup=power_keyboard())
        user_states.pop(user_id)

    elif state.startswith("adding_to:"):
        list_name = state.split(":")[1]
        if "/" in text:
            items = [item.strip() for item in text.split("/")]
        else:
            items = [text.strip()]

        tasks[user_id][list_name].extend(items)
        save_tasks()
        bot.send_message(message.chat.id, f"\u2705 Додано до списку «{list_name}»: {', '.join(items)}", reply_markup=power_keyboard())
        user_states.pop(user_id)

    elif state.startswith("completing_from:"):
        list_name = state.split(":")[1]
        try:
            indexes = [int(i) - 1 for i in text.replace(" ", "").replace("-", ",").split(",")]
            indexes = sorted(set(indexes), reverse=True)
            for i in indexes:
                if 0 <= i < len(tasks[user_id][list_name]):
                    del tasks[user_id][list_name][i]
            save_tasks()
            bot.send_message(message.chat.id, f"\u2705 Завдання завершено у списку {list_name}.", reply_markup=power_keyboard())
        except Exception as e:
            bot.send_message(message.chat.id, "\u274c Помилка завершення. Спробуй ще раз.", reply_markup=power_keyboard())
        user_states.pop(user_id)

# --- Flask Webhook endpoint ---
app = Flask(__name__)

@app.route(f'/{TOKEN}', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return 'OK', 200
    else:
        return 'Invalid content type', 403

@app.route('/')
def index():
    return '\u26a1 Webhook активний. YoddaBot на зв’язку!'

# Запуск Flask-сервера для Render
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
