from src.bot import run_bot
from keep_alive import keep_alive  # <--- 1. Импортируем нашу обманку

if __name__ == "__main__":
    keep_alive()  # <--- 2. Запускаем веб-сервер перед ботом
    run_bot()     # <--- 3. Запускаем самого бота