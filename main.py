import telebot
import os
import json
import random
import threading
import schedule
import time
from flask import Flask, request
from dotenv import load_dotenv

# Ініціалізація Flask
app = Flask(__name__)

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

# Оновлення структури
for user_id in list(tasks.keys()):
    if isinstance(tasks[user_id], list):
        tasks[user_id] = {"Список": tasks[user_id]}

def save_tasks():
    import shutil
    if os.path.exists("tasks.json"):
        shutil.copy("tasks.json", "tasks_backup.json")
    with open("tasks.json", "w", encoding="utf-8") as f:
        json.dump(tasks, f, ensure_ascii=False, indent=4)

# Клавіатури
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
    "🌟 Сьогодні ідеальний день для великих кроків!",
    "🏆 Велика мрія — половина успіху!",
    "🛤️ Шлях у тисячу миль починається з одного кроку.",
    "💥 Найкращий час для дій — зараз!",
    "🧠 Вчись, рости і світ відкриється перед тобою!"
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
    user_id = str(call.message.chat.id)
    if user_id not in tasks:
        tasks[user_id] = {}

    try:
        if call.data == "list_lists":
            if not tasks[user_id]:
                bot.send_message(call.message.chat.id, "📭 Списків у тебе ще нема.", reply_markup=power_keyboard())
            else:
                msg = "📋 Твої списки:\n"
                for list_name, items in tasks[user_id].items():
                    sorted_items = sorted(items, key=lambda x: 0 if x.startswith("!") else 1)
                    msg += f"\n🔹 {list_name}:\n" + "\n".join(f"- {item}" for item in sorted_items)
                bot.send_message(call.message.chat.id, msg, reply_markup=power_keyboard())

        elif call.data == "choose_list_for_add":
            markup = telebot.types.InlineKeyboardMarkup()
            for name in tasks[user_id]:
                markup.add(telebot.types.InlineKeyboardButton(name, callback_data=f"add_to:{name}"))
            if len(tasks[user_id]) < 10:
                markup.add(telebot.types.InlineKeyboardButton("➕ Новий список", callback_data="create_new_list"))
            bot.send_message(call.message.chat.id, "➕ Обери список або створи новий:", reply_markup=markup)

        elif call.data.startswith("add_to:"):
            list_name = call.data.split(":")[1]
            user_states[user_id] = f"adding_to:{list_name}"
            bot.send_message(call.message.chat.id, f"📝 Введи завдання через / . Всі будуть додані до списку: {list_name}", reply_markup=power_keyboard())

        elif call.data == "create_new_list":
            user_states[user_id] = "creating_new_list"
            bot.send_message(call.message.chat.id, "📂 Введи назву нового списку:", reply_markup=power_keyboard())

        elif call.data == "choose_list_for_finish":
            if not tasks[user_id]:
                bot.send_message(call.message.chat.id, "📭 Немає списків для завершення.", reply_markup=power_keyboard())
            else:
                markup = telebot.types.InlineKeyboardMarkup()
                for name in tasks[user_id]:
                    markup.add(telebot.types.InlineKeyboardButton(name, callback_data=f"finish_from:{name}"))
                bot.send_message(call.message.chat.id, "✅ Обери список для завершення:", reply_markup=markup)

        elif call.data.startswith("finish_from:"):
            list_name = call.data.split(":")[1]
            user_states[user_id] = f"finishing_from:{list_name}"
            tasks_list = tasks[user_id][list_name]
            if tasks_list:
                msg = f"📋 Завдання у списку {list_name}:\n"
                msg += "\n".join(f"{i+1}. {task}" for i, task in enumerate(tasks_list))
                msg += "\nВведи номери через кому або дефіс (1,2 або 1-3):"
                bot.send_message(call.message.chat.id, msg, reply_markup=power_keyboard())
            else:
                bot.send_message(call.message.chat.id, "📭 Список порожній.", reply_markup=power_keyboard())

        elif call.data == "delete_list":
            if not tasks[user_id]:
                bot.send_message(call.message.chat.id, "📭 Видаляти нічого. Немає списків.", reply_markup=power_keyboard())
            else:
                markup = telebot.types.InlineKeyboardMarkup()
                for name in tasks[user_id]:
                    markup.add(telebot.types.InlineKeyboardButton(f"🗑️ {name}", callback_data=f"delete:{name}"))
                bot.send_message(call.message.chat.id, "🗑️ Обери список для видалення:", reply_markup=markup)

        elif call.data.startswith("delete:"):
            list_name = call.data.split(":")[1]
            if list_name in tasks[user_id]:
                del tasks[user_id][list_name]
                save_tasks()
                bot.send_message(call.message.chat.id, f"🗑️ Список {list_name} видалено.", reply_markup=power_keyboard())
            else:
                bot.send_message(call.message.chat.id, "❌ Список не знайдено.", reply_markup=power_keyboard())

        elif call.data == "inspiration":
            phrase = random.choice(motivational_phrases)
            bot.send_message(call.message.chat.id, phrase, reply_markup=power_keyboard())

        elif call.data == "instruction":
            bot.send_message(call.message.chat.id, "ℹ️ Інструкція:\n⚡ Power — головна кнопка.\n➕ Додай через / кілька завдань.\n✅ Завершуй за номерами.\n📋 Використовуй ! для важливих.\n🗑️ Видаляй зайві списки.\nМаєш максимум 10 списків!", reply_markup=power_keyboard())

        bot.answer_callback_query(call.id)

    except Exception as e:
        print(f"⚠️ Помилка в callback: {call.data}\n{e}")
        bot.send_message(call.message.chat.id, "⚠️ Щось пішло не так. Натисни ⚡ Power.", reply_markup=power_keyboard())

@bot.message_handler(func=lambda message: True)
def handle_text(message):
    user_id = str(message.chat.id)
    text = message.text.strip()

    if user_id not in user_states:
        bot.send_message(message.chat.id, "⚡ Натисни Power, мудрості набудеш!", reply_markup=power_keyboard())
        return

    state = user_states[user_id]

    if state == "creating_new_list":
        if text in tasks[user_id]:
            bot.send_message(message.chat.id, "⚠️ Такий список вже існує.", reply_markup=power_keyboard())
        elif len(tasks[user_id]) >= 10:
            bot.send_message(message.chat.id, "⚠️ Досягнуто максимуму списків (10).", reply_markup=power_keyboard())
        else:
            tasks[user_id][text] = []
            save_tasks()
            bot.send_message(message.chat.id, f"📂 Створено список: {text}", reply_markup=power_keyboard())
        user_states.pop(user_id)

    elif state.startswith("adding_to:"):
        list_name = state.split(":")[1]
        entries = [entry.strip() for entry in text.split("/") if entry.strip()]
        tasks[user_id][list_name].extend(entries)
        save_tasks()
        bot.send_message(message.chat.id, f"✅ Додано {len(entries)} завдань у список {list_name}.", reply_markup=power_keyboard())
        user_states.pop(user_id)

    elif state.startswith("finishing_from:"):
        list_name = state.split(":")[1]
        try:
            indices = set()
            parts = text.split(',')
            for part in parts:
                if '-' in part:
                    a, b = map(int, part.split('-'))
                    indices.update(range(a, b+1))
                else:
                    indices.add(int(part))
            indices = sorted(indices, reverse=True)
            completed = []
            for i in indices:
                if 1 <= i <= len(tasks[user_id][list_name]):
                    completed.append(tasks[user_id][list_name].pop(i - 1))
            save_tasks()
            if completed:
                bot.send_message(message.chat.id, "✅ Завершено:\n" + "\n".join(f"- {x}" for x in completed), reply_markup=power_keyboard())
            else:
                bot.send_message(message.chat.id, "⚠️ Нічого не завершено.", reply_markup=power_keyboard())
        except:
            bot.send_message(message.chat.id, "⚠️ Помилка у форматі номерів. Перевір.", reply_markup=power_keyboard())
        user_states.pop(user_id)

# Натхнення
def morning_greeting():
    phrase = random.choice(morning_mantras)
    bot.send_message(CHAT_ID, f"💥 Доброго ранку, падаване! {phrase}", reply_markup=power_keyboard())

# Webhook для Render
@app.route(f"/{TOKEN}", methods=['POST'])
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
    return '⚡ Webhook активний. YoddaBot на зв’язку!'

# Запуск для Render
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    schedule.every().day.at("10:00").do(morning_greeting)
    threading.Thread(target=lambda: [schedule.run_pending() or time.sleep(60)]).start()
    app.run(host='0.0.0.0', port=port)
