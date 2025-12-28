from aiogram import types
import requests
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
API_URL = "http://127.0.0.1:8000/api/incidents/not-done/"

router = Router()
@router.message(Command("tasks"))
async def not_done_tasks(message: Message):
    API_URL = "http://127.0.0.1:8000/api/incidents/not-done/"
    params = {"telegram_id": message.from_user.id}
    r = requests.get(API_URL, params=params)

    if r.status_code == 403:
        await message.answer(f"⛔ У вас нет доступа {r.json().get('error')}")
        return
    
    incidents = r.json()  # используем ответ с фильтром по Telegram ID

    if not incidents:
        await message.answer("✅ Нет активных заявок")
        return

    text = "🛠 *Активные инциденты:*\n\n"

    for i in incidents:
        # Проверяем, что i — словарь
        if isinstance(i, dict):
            status_icon = "🆕" if i.get('status') == 'new' else "⏳"
            text += (
                f"{status_icon} *#{i.get('id')}*\n"
                f"📌 {i.get('user_message')}\n"
                f"📊 Статус: `{i.get('status')}`\n\n"
            )
        else:
            # Если что-то пошло не так, просто выводим строку
            text += f"{i}\n\n"

    await message.answer(text, parse_mode="Markdown")

@router.message(Command("id"))
async def my_id(message: Message):
    await message.answer(f"Ваш Telegram ID: {message.from_user.id}")