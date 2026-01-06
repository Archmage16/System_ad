import asyncio
import logging
import requests

from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message
from aiogram import types
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import BOT_TOKEN
from handlers import router

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def start(message: Message):
    await message.answer("Привет! Бот запущен 🚀")


@router.message(Command("solve"))
async def incidents_handler(message: types.Message):
    telegram_id = message.from_user.id

    r = requests.get(
        "http://127.0.0.1:8000/api/incidents/not-done/",
        params={"telegram_id": telegram_id}
    )

    incidents = r.json()

    if not incidents:
        await message.answer("✅ Активных инцидентов нет")
        return

    builder = InlineKeyboardBuilder()

    for inc in incidents:
        builder.button(
            text=f"🛠 Incident #{inc['id']}",
            callback_data=f"close:{inc['id']}"
        )

    builder.adjust(1)  # по одной кнопке в строке

    await message.answer(
        "Выбери инцидент:",
        reply_markup=builder.as_markup()
    )
@router.callback_query(lambda c: c.data.startswith("close:"))
async def close_incident(call: types.CallbackQuery):
    incident_id = call.data.split(":")[1]
    telegram_id = call.from_user.id

    r = requests.post(
        f"http://127.0.0.1:8000/api/incidents/{incident_id}/close/",
        json={"telegram_id": telegram_id}
    )

    if r.status_code == 200:
        await call.message.edit_text(f"✅ Incident #{incident_id} закрыт")
    else:
        await call.answer("❌ Ошибка", show_alert=True)


async def main():
    dp.include_router(router)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
