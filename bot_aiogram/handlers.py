from aiogram import types
import aiohttp
import requests
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
API_URL = "http://127.0.0.1:8000/api/incidents/not-done/"
API_URL_ADD = "http://127.0.0.1:8000/api/incidents/add/"
MAX_LEN = 4000

router = Router()
API_URL_ADD = "http://127.0.0.1:8000/api/incidents/"
MAX_LEN = 4000

def split_message(text, max_len=MAX_LEN):
    return [text[i:i+max_len] for i in range(0, len(text), max_len)]

# ----------------- FSM -----------------
class IncidentForm(StatesGroup):
    waiting_for_message = State()

# ----------------- Команда /add-incidents -----------------
@router.message(Command("add-incidents"))
async def add_incident_start(message: Message, state: FSMContext):
    await message.answer("📝 Пожалуйста, напишите текст вашего инцидента:")
    await state.set_state(IncidentForm.waiting_for_message)

# ----------------- Получение текста инцидента -----------------
@router.message(IncidentForm.waiting_for_message)
async def add_incident_receive(message: Message, state: FSMContext):
    user_message = message.text.strip()
    if not user_message:
        await message.answer("⚠ Текст не может быть пустым. Попробуйте снова.")
        return

    data = {
        "telegram_id": message.from_user.id,
        "user_message": user_message
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(API_URL_ADD, json=data) as resp:
                if resp.status == 201:
                    incident = await resp.json()
                    text = (
                        f"✅ Инцидент создан!\n"
                        f"ID: {incident.get('id')}\n"
                        f"Сообщение: {incident.get('user_message')}\n"
                        f"Статус: {incident.get('status')}"
                    )
                    for part in split_message(text):
                        await message.answer(part)
                else:
                    try:
                        error = await resp.json()
                        err_msg = error.get('error', str(error))
                    except:
                        err_msg = await resp.text()
                    for part in split_message(f"❌ Ошибка при создании инцидента: {err_msg}"):
                        await message.answer(part)
    except Exception as e:
        for part in split_message(f"❌ Произошла ошибка при соединении с API: {e}"):
            await message.answer(part)
    await state.clear()

@router.message(Command("tasks"))
async def not_done_tasks(message: Message):
    params = {"telegram_id": message.from_user.id}

    async with aiohttp.ClientSession() as session:
        async with session.get(API_URL, params=params) as resp:

            if resp.status == 403 or resp.status == 401:
                await message.answer("⛔ У вас нет доступа")
                return

            incidents = await resp.json()

    if not incidents:
        await message.answer("✅ Нет активных заявок")
        return

    text = "🛠 *Активные инциденты:*\n\n"

    for i in incidents:
        status_icon = "🆕" if i.get("status") == "new" else "⏳"
        text += (
            f"{status_icon} *#{i.get('id')}*\n"
            f"📌 {i.get('user_message')}\n"
            f"📊 Статус: `{i.get('status')}`\n\n"
        )

    for part in split_message(text):
        await message.answer(part, parse_mode="Markdown")

@router.message(Command("id"))
async def my_id(message: Message):
    await message.answer(f"Ваш Telegram ID: {message.from_user.id}")
