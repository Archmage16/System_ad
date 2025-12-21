import os
from dotenv import load_dotenv

load_dotenv(dotenv_path=".env")

BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не найден. Проверь файл .env")
