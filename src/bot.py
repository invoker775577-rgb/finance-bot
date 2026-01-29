import telebot
import os
import datetime
from dotenv import load_dotenv
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, BotCommand

from src.parser import parse_input
from src.storage import FinanceStorage
from src.visualizer import create_pie_chart

# 1. Загрузка окружения
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    raise ValueError("Токен не найден! Проверь .env")

bot = telebot.TeleBot(TOKEN)

def get_user_storage(user_id):
    return FinanceStorage(f"data/{user_id}_finance.csv")

# --- ГЛАВНАЯ ФИШКА: НАСТРОЙКА КНОПКИ MENU ---
def set_main_menu():
    """Создает синюю кнопку Menu слева внизу"""
    commands = [
        BotCommand("stats", "📊 Статистика и бюджет"),
        BotCommand("records", "📋 Последние 10 трат"),
        BotCommand("salary", "💰 Установить бюджет"),
        BotCommand("history", "📅 История / Excel"),
        BotCommand("search", "🔍 Поиск по базе"),
        BotCommand("undo", "🔙 Отмена записи"),
        BotCommand("reset", "🗑 Сброс данных"),
        BotCommand("help", "ℹ️ Помощь")
    ]
    bot.set_my_commands(commands)

# --- КОМАНДЫ ---

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    text = (
        "**FinBot v3.0**\n\n"
        "**Добавить трату:**\n"
        "`Категория Сумма [Комментарий]`\n"
        "Пример: `Такси 500` или `Обед 12.50 бизнес-ланч`\n\n"
        "👇 **Все команды теперь в кнопке Menu слева внизу.**"
    )
    bot.send_message(message.chat.id, text, parse_mode="Markdown")

@bot.message_handler(commands=['salary'])
def set_salary(message):
    try:
        args = message.text.split()
        if len(args) < 2:
            bot.reply_to(message, "Формат: `/salary 2000`", parse_mode="Markdown")
            return
        amount = float(args[1].replace(",", "."))
        get_user_storage(message.chat.id).set_budget(amount)
        bot.reply_to(message, f"✅ Бюджет на месяц: **{amount} $**", parse_mode="Markdown")
    except ValueError:
        bot.reply_to(message, "Ошибка: сумма должна быть числом.")

@bot.message_handler(commands=['undo'])
def undo_last(message):
    if get_user_storage(message.chat.id).delete_last_expense():
        bot.reply_to(message, "↩️ Последняя запись удалена.")
    else:
        bot.reply_to(message, "Нет записей для удаления.")

@bot.message_handler(commands=['search'])
def search_expenses(message):
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        bot.reply_to(message, "Формат: `/search текст`", parse_mode="Markdown")
        return
    
    query = args[1]
    results = get_user_storage(message.chat.id).search_records(query)
    
    if not results:
        bot.reply_to(message, "Ничего не найдено.")
        return
        
    text = f"🔎 **Поиск '{query}':**\n"
    total = 0
    for r in results:
        date_str = r['date'].strftime("%d.%m")
        note = f" ({r['note']})" if r['note'] else ""
        text += f"{date_str} | {r['category']} | {r['amount']} ${note}\n"
        total += r['amount']
        
    text += f"\nИтого: **{total} $**"
    bot.send_message(message.chat.id, text, parse_mode="Markdown")

@bot.message_handler(commands=['records'])
def show_records(message):
    records = get_user_storage(message.chat.id).get_last_records(10)
    if not records:
        bot.send_message(message.chat.id, "Список пуст.")
        return
        
    text = "📋 **Последние операции:**\n"
    for r in records:
        date_str = r['date'].strftime("%d.%m %H:%M")
        note = f" _{r['note']}_" if r['note'] else ""
        text += f"`{date_str}` | {r['category']} | {r['amount']} ${note}\n"
        
    bot.send_message(message.chat.id, text, parse_mode="Markdown")

@bot.message_handler(commands=['stats'])
def send_stats(message):
    user_id = message.chat.id
    storage = get_user_storage(user_id)
    now = datetime.datetime.now()
    
    stats = storage.get_stats_by_month(now.year, now.month)
    budget_data = storage.get_budget_status()
    
    if not stats:
        bot.send_message(user_id, "Нет данных за текущий месяц.")
        return

    try:
        chart_file = create_pie_chart(stats)
        
        spent = budget_data['spent']
        budget = budget_data['budget']
        rem = budget_data['remaining']
        daily = budget_data['daily_limit']
        
        caption = f"📊 **{now.strftime('%m.%Y')}**\n"
        caption += f"Расход: **{spent} $**\n"
        
        if budget > 0:
            caption += f"Бюджет: {budget} $\n"
            if rem > 0:
                caption += f"Остаток: **{rem:.2f} $**\n"
                caption += f"Лимит на день: **{daily:.2f} $**"
            else:
                caption += f"Перерасход: **{abs(rem):.2f} $**"
                
        bot.send_photo(user_id, photo=chart_file, caption=caption, parse_mode="Markdown")
    except Exception:
        bot.send_message(user_id, "Ошибка построения отчета.")

# --- UI КНОПКИ ---

@bot.message_handler(commands=['reset'])
def ask_reset(message):
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🗑 Удалить всё", callback_data="reset_confirm"))
    markup.add(InlineKeyboardButton("Отмена", callback_data="reset_cancel"))
    bot.send_message(message.chat.id, "Подтвердите полный сброс:", reply_markup=markup)

@bot.message_handler(commands=['history'])
def show_history_menu(message):
    markup = InlineKeyboardMarkup()
    year = datetime.datetime.now().year
    months = {1:"Янв", 2:"Фев", 3:"Мар", 4:"Апр", 5:"Май", 6:"Июн", 7:"Июл", 8:"Авг", 9:"Сен", 10:"Окт", 11:"Ноя", 12:"Дек"}
    
    buttons = [InlineKeyboardButton(name, callback_data=f"stats_{year}_{num}") for num, name in months.items()]
    markup.add(*buttons[:4], *buttons[4:8], *buttons[8:])
    markup.add(InlineKeyboardButton("📥 Скачать CSV", callback_data="download_all"))

    bot.send_message(message.chat.id, "Выберите месяц:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    user_id = call.message.chat.id
    storage = get_user_storage(user_id)
    
    if call.data == "reset_confirm":
        storage.reset_data()
        bot.delete_message(user_id, call.message.message_id)
        bot.send_message(user_id, "База очищена.")
    elif call.data == "reset_cancel":
        bot.delete_message(user_id, call.message.message_id)
    elif call.data == "download_all":
        try:
            with open(storage.filename, "rb") as f:
                bot.send_document(user_id, f, caption="История операций")
        except: 
            bot.answer_callback_query(call.id, "Нет данных.")
    elif call.data.startswith("stats_"):
        try:
            _, y, m = call.data.split("_")
            stats = storage.get_stats_by_month(int(y), int(m))
            if stats:
                bot.send_photo(user_id, create_pie_chart(stats), caption=f"Отчет за {m}.{y}")
            else:
                bot.answer_callback_query(call.id, "Пусто.")
            bot.answer_callback_query(call.id)
        except: pass

@bot.message_handler(content_types=['text'])
def process_expense(message):
    try:
        data = parse_input(message.text)
        storage = get_user_storage(message.chat.id)
        storage.add_expense(data['category'], data['amount'], data['note'])
        
        status = storage.get_budget_status()
        note_text = f" ({data['note']})" if data['note'] else ""
        
        reply = f"✅ {data['category']}: {data['amount']} ${note_text}\n"
        
        if status['budget'] > 0:
            if status['remaining'] > 0:
                reply += f"Остаток: {status['remaining']:.2f} $ (Лимит/день: {status['daily_limit']:.2f})"
            else:
                reply += f"Перерасход: {abs(status['remaining']):.2f} $"
        
        bot.reply_to(message, reply)
        
    except ValueError:
        bot.reply_to(message, "Ошибка формата. Пример: `Такси 500`", parse_mode="Markdown")
    except Exception:
        bot.reply_to(message, "Ошибка записи.")

def run_bot():
    print("Бот запущен. Обновляю меню команд...")
    set_main_menu() # <--- ВОТ ЭТА МАГИЧЕСКАЯ СТРОЧКА СОЗДАЕТ МЕНЮ
    bot.infinity_polling()