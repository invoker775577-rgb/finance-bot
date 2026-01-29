import telebot
import os
import datetime
from dotenv import load_dotenv
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, BotCommand

from src.parser import parse_input
from src.storage import FinanceStorage
from src.visualizer import create_pie_chart

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    raise ValueError("Токен не найден! Проверь .env")

bot = telebot.TeleBot(TOKEN)

def get_user_storage(user_id):
    return FinanceStorage(f"data/{user_id}_finance.csv")

def set_main_menu():
    commands = [
        BotCommand("start", "🏠 Главное меню"),
        BotCommand("stats", "📊 Статистика и лимиты"),
        BotCommand("currency", "💱 Сменить валюту"),
        BotCommand("salary", "💰 Задать зарплату"),
        BotCommand("records", "📋 Список трат"),
        BotCommand("search", "🔍 Поиск"),
        BotCommand("undo", "🔙 Отмена записи"),
        BotCommand("history", "📅 Архив / Excel"),
        BotCommand("reset", "🗑 Сброс данных")
    ]
    bot.set_my_commands(commands)

# --- НОВЫЙ КРУТОЙ СТАРТ ---

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    user_name = message.from_user.first_name
    storage = get_user_storage(message.chat.id)
    cur = storage.get_currency()
    
    text = (
        f"👋 **Привет, {user_name}!**\n\n"
        "Я здесь, чтобы твои деньги не исчезали в никуда. "
        "Я простой, быстрый и не задаю лишних вопросов.\n\n"
        "🚀 **Как пользоваться:**\n"
        "1. **Пиши траты как есть:**\n"
        f"   `Такси 500` или `Обед 1250 бизнес ланч`\n"
        "2. **Следи за лимитом:**\n"
        f"   Задай бюджет `/salary 50000`, и я скажу, сколько можно тратить в день.\n"
        "3. **Анализируй:**\n"
        "   Жми `/stats` — покажу графики и остаток.\n\n"
        f"💱 **Твоя валюта сейчас:** `{cur}`\n"
        "(Чтобы сменить на рубли, динары или евро — жми `/currency`)\n\n"
        "👇 **Меню команд — в кнопке слева внизу.**"
    )
    bot.send_message(message.chat.id, text, parse_mode="Markdown")

# --- СМЕНА ВАЛЮТЫ ---

@bot.message_handler(commands=['currency'])
def change_currency_menu(message):
    markup = InlineKeyboardMarkup()
    # Популярные валюты
    btn1 = InlineKeyboardButton("🇺🇸 USD ($)", callback_data="set_cur_$")
    btn2 = InlineKeyboardButton("🇪🇺 EUR (€)", callback_data="set_cur_€")
    btn3 = InlineKeyboardButton("🇷🇺 RUB (₽)", callback_data="set_cur_₽")
    btn4 = InlineKeyboardButton("🇷🇸 RSD (din)", callback_data="set_cur_din")
    btn5 = InlineKeyboardButton("🇧🇾 BYN (Br)", callback_data="set_cur_Br")
    btn6 = InlineKeyboardButton("🇺🇦 UAH (₴)", callback_data="set_cur_₴")
    
    markup.add(btn1, btn2)
    markup.add(btn3, btn4)
    markup.add(btn5, btn6)
    
    bot.send_message(message.chat.id, "💱 **В чем будем считать деньги?**\nВыберите из списка:", reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data.startswith("set_cur_"))
def callback_set_currency(call):
    # Получаем символ из callback_data (например set_cur_din -> din)
    symbol = call.data.split("_")[2]
    storage = get_user_storage(call.message.chat.id)
    storage.set_currency(symbol)
    
    bot.answer_callback_query(call.id, f"Валюта установлена: {symbol}")
    bot.edit_message_text(f"✅ Готово! Теперь считаем в **{symbol}**.", call.message.chat.id, call.message.message_id, parse_mode="Markdown")

# --- ОСТАЛЬНЫЕ КОМАНДЫ (С УЧЕТОМ ВАЛЮТЫ) ---

@bot.message_handler(commands=['salary'])
def set_salary(message):
    storage = get_user_storage(message.chat.id)
    cur = storage.get_currency()
    try:
        args = message.text.split()
        if len(args) < 2:
            bot.reply_to(message, f"⚠️ Пример: `/salary 50000`", parse_mode="Markdown")
            return
        amount = float(args[1].replace(",", "."))
        storage.set_budget(amount)
        bot.reply_to(message, f"✅ Бюджет на месяц: **{amount:,.0f} {cur}**", parse_mode="Markdown")
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
    storage = get_user_storage(message.chat.id)
    cur = storage.get_currency()
    
    if len(args) < 2:
        bot.reply_to(message, "🔍 Пример: `/search такси`", parse_mode="Markdown")
        return
    
    query = args[1]
    results = storage.search_records(query)
    
    if not results:
        bot.reply_to(message, "Ничего не найдено.")
        return
        
    text = f"🔎 **Поиск '{query}':**\n"
    total = 0
    for r in results:
        date_str = r['date'].strftime("%d.%m")
        note = f" ({r['note']})" if r['note'] else ""
        text += f"{date_str} | {r['category']} | {r['amount']} {cur}{note}\n"
        total += r['amount']
        
    text += f"\nИтого: **{total} {cur}**"
    bot.send_message(message.chat.id, text, parse_mode="Markdown")

@bot.message_handler(commands=['records'])
def show_records(message):
    storage = get_user_storage(message.chat.id)
    cur = storage.get_currency()
    records = storage.get_last_records(10)
    if not records:
        bot.send_message(message.chat.id, "Список пуст.")
        return
        
    text = f"📋 **Последние операции ({cur}):**\n"
    for r in records:
        date_str = r['date'].strftime("%d.%m %H:%M")
        note = f" _{r['note']}_" if r['note'] else ""
        text += f"`{date_str}` | {r['category']} | {r['amount']} {cur}{note}\n"
        
    bot.send_message(message.chat.id, text, parse_mode="Markdown")

@bot.message_handler(commands=['stats'])
def send_stats(message):
    user_id = message.chat.id
    storage = get_user_storage(user_id)
    cur = storage.get_currency() # Узнаем валюту
    now = datetime.datetime.now()
    
    stats = storage.get_stats_by_month(now.year, now.month)
    budget_data = storage.get_budget_status()
    
    if not stats:
        bot.send_message(user_id, "Нет данных за текущий месяц.")
        return

    try:
        # Передаем валюту в генератор графика
        chart_file = create_pie_chart(stats, currency_symbol=cur)
        
        spent = budget_data['spent']
        budget = budget_data['budget']
        rem = budget_data['remaining']
        daily = budget_data['daily_limit']
        
        caption = f"📊 **{now.strftime('%m.%Y')}**\n"
        caption += f"Расход: **{spent:,.2f} {cur}**\n"
        
        if budget > 0:
            caption += f"Бюджет: {budget:,.0f} {cur}\n"
            if rem > 0:
                caption += f"Остаток: **{rem:,.2f} {cur}**\n"
                caption += f"Лимит на день: **{daily:,.2f} {cur}**"
            else:
                caption += f"Перерасход: **{abs(rem):,.2f} {cur}** 😱"
                
        bot.send_photo(user_id, photo=chart_file, caption=caption, parse_mode="Markdown")
    except Exception as e:
        print(f"Error stats: {e}")
        bot.send_message(user_id, "Ошибка построения отчета.")

# --- КНОПКИ СБРОСА И ИСТОРИИ ---

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
    if call.data.startswith("set_cur_"): return # Это обрабатывается в другом месте

    user_id = call.message.chat.id
    storage = get_user_storage(user_id)
    cur = storage.get_currency()
    
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
                bot.send_photo(user_id, create_pie_chart(stats, cur), caption=f"Отчет за {m}.{y}")
            else:
                bot.answer_callback_query(call.id, "Пусто.")
            bot.answer_callback_query(call.id)
        except: pass

# --- ОБРАБОТКА СООБЩЕНИЙ ---

@bot.message_handler(content_types=['text'])
def process_expense(message):
    try:
        data = parse_input(message.text)
        storage = get_user_storage(message.chat.id)
        cur = storage.get_currency()
        
        storage.add_expense(data['category'], data['amount'], data['note'])
        
        status = storage.get_budget_status()
        note_text = f" ({data['note']})" if data['note'] else ""
        
        reply = f"✅ {data['category']}: {data['amount']} {cur}{note_text}\n"
        
        if status['budget'] > 0:
            if status['remaining'] > 0:
                reply += f"Остаток: {status['remaining']:,.0f} {cur} (Лимит/день: {status['daily_limit']:,.0f})"
            else:
                reply += f"Перерасход: {abs(status['remaining']):,.0f} {cur}"
        
        bot.reply_to(message, reply)
        
    except ValueError:
        bot.reply_to(message, "Не понял. Пиши так: `Такси 500`", parse_mode="Markdown")
    except Exception as e:
        print(f"Error: {e}")
        bot.reply_to(message, "Ошибка записи.")

def run_bot():
    print("Бот запущен. Обновляю меню...")
    set_main_menu()
    bot.infinity_polling()

