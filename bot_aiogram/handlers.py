from aiogram import Router, types
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder
import aiohttp
import logging

from config import API_BASE_URL

logger = logging.getLogger(__name__)
router = Router()

MAX_LEN = 4000


# ---------- utils ----------
def split_message(text: str, max_len: int = MAX_LEN):
    return [text[i:i + max_len] for i in range(0, len(text), max_len)]


# ---------- FSM ----------
class IncidentForm(StatesGroup):
    waiting_for_message = State()
    waiting_for_room = State()


# ---------- /start ----------
@router.message(Command("start"))
async def start_command(message: Message):
    await message.answer(
        "👋 Привет! Я бот для управления инцидентами.\n\n"
        "📋 Команды:\n"
        "/add-incidents — создать инцидент\n"
        "/tasks — активные инциденты\n"
        "/solve — закрыть инцидент\n"
        "/id — мой Telegram ID\n"
        "/cancel — отменить действие"
    )


# ---------- /add-incidents ----------
@router.message(Command("add-incidents"))
async def add_incident_start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("📝 Опишите проблему:")
    await state.set_state(IncidentForm.waiting_for_message)


@router.message(IncidentForm.waiting_for_message)
async def receive_incident_text(message: Message, state: FSMContext):
    text = message.text.strip()
    if not text:
        await message.answer("⚠ Текст не может быть пустым")
        return

    await state.update_data(user_message=text)

    # Получаем кабинеты из Django (используем существующий endpoint)
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{API_BASE_URL}/rooms/bot/") as resp:  # ИСПРАВЛЕНО
                if resp.status != 200:
                    error_text = await resp.text()
                    logger.error(f"Rooms API error: {resp.status} - {error_text}")
                    await message.answer("❌ Не удалось получить список кабинетов")
                    await state.clear()
                    return
                rooms = await resp.json()
    except Exception as e:
        logger.error(f"Error getting rooms: {e}")
        await message.answer("❌ Ошибка соединения с сервером")
        await state.clear()
        return

    if not rooms:
        # Если нет кабинетов, создаем инцидент без кабинета
        await message.answer("ℹ️ Кабинеты не настроены. Создаю инцидент без кабинета...")
        await create_incident_without_room(message, state)
        return

    kb = InlineKeyboardBuilder()
    for room in rooms:
        # Форматируем текст кнопки в зависимости от структуры ответа
        if 'office' in room and isinstance(room['office'], dict):
            office_name = room['office'].get('name', 'Офис')
        elif 'office_name' in room:
            office_name = room['office_name']
        else:
            office_name = 'Офис'
            
        room_number = room.get('room_number', 'N/A')
        button_text = f"🏢 {office_name} - {room_number}"
        
        kb.button(
            text=button_text,
            callback_data=f"room:{room['id']}"
        )
    
    # Добавляем кнопку "Без кабинета"
    kb.button(
        text="⏭ Без кабинета",
        callback_data="room:skip"
    )
    
    kb.adjust(1)

    await message.answer(
        "🏢 Выберите кабинет:",
        reply_markup=kb.as_markup()
    )
    await state.set_state(IncidentForm.waiting_for_room)

async def create_incident_without_room(message: Message, state: FSMContext):
    """Создает инцидент без указания кабинета"""
    data = await state.get_data()
    user_message = data.get("user_message")

    if not user_message:
        await message.answer("❌ Ошибка: текст инцидента потерян")
        await state.clear()
        return

    payload = {
        "telegram_id": message.from_user.id,
        "user_message": user_message,
        # Не передаем room, чтобы Django создал без кабинета
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{API_BASE_URL}/incidents/",  # ИСПРАВЛЕНО: правильный URL
                json=payload
            ) as resp:

                if resp.status != 201:
                    try:
                        error = await resp.json()
                        error_msg = error.get('detail', error.get('error', str(error)))
                    except:
                        error_msg = await resp.text()
                    
                    await message.answer(f"❌ Ошибка API: {error_msg}")
                    await state.clear()
                    return

                incident = await resp.json()

    except Exception as e:
        logger.error(f"Error creating incident: {e}")
        await message.answer("❌ Ошибка соединения с сервером")
        await state.clear()
        return

    await message.answer(
        f"✅ Инцидент создан!\n"
        f"🆔 ID: {incident.get('id', 'N/A')}\n"
        f"📝 {incident.get('user_message', 'N/A')}\n"
        f"📊 Статус: {incident.get('status', 'N/A')}"
    )

    await state.clear()


# ---------- room selected ----------
@router.callback_query(lambda c: c.data.startswith("room:"))
async def room_selected(call: types.CallbackQuery, state: FSMContext):
    room_data = call.data.split(":")[1]
    data = await state.get_data()
    user_message = data.get("user_message")

    if not user_message:
        await call.answer("❌ Ошибка: текст инцидента потерян", show_alert=True)
        await state.clear()
        return

    if room_data == "skip":
        # Создаем инцидент без кабинета
        payload = {
            "telegram_id": call.from_user.id,
            "user_message": user_message
        }
        room_id_display = "не указан"
    else:
        room_id = int(room_data)
        payload = {
            "telegram_id": call.from_user.id,
            "user_message": user_message,
            "room": room_id
        }
        room_id_display = room_id

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{API_BASE_URL}/incidents/",  # ИСПРАВЛЕНО: правильный URL
                json=payload
            ) as resp:

                if resp.status != 201:
                    try:
                        error = await resp.json()
                        error_msg = error.get('detail', error.get('error', str(error)))
                    except:
                        error_msg = await resp.text()
                    
                    await call.message.answer(f"❌ Ошибка: {error_msg}")
                    await state.clear()
                    return

                incident = await resp.json()

    except Exception as e:
        logger.error(f"Error creating incident: {e}")
        await call.message.answer("❌ Ошибка соединения")
        await state.clear()
        return

    # Формируем информативное сообщение
    room_info = f"🏢 Кабинет: {room_id_display}\n" if room_data != "skip" else ""
    
    response_text = (
        f"✅ Инцидент создан!\n"
        f"🆔 ID: {incident.get('id', 'N/A')}\n"
        f"📝 {incident.get('user_message', 'N/A')}\n"
        f"{room_info}"
        f"📊 Статус: {incident.get('status', 'N/A')}"
    )

    # Редактируем сообщение с кнопками или отправляем новое
    try:
        await call.message.edit_text(response_text)
    except:
        # Если не удалось отредактировать (например, сообщение слишком старое)
        await call.message.answer(response_text)
        await call.message.delete()

    await state.clear()
    await call.answer()


# ---------- /tasks ----------
@router.message(Command("tasks"))
async def show_tasks(message: Message):
    telegram_id = message.from_user.id

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{API_BASE_URL}/incidents/not-done/",  # ИСПРАВЛЕНО: правильный URL
                params={"telegram_id": telegram_id}
            ) as resp:
                if resp.status == 403 or resp.status == 401:
                    await message.answer("⛔ Нет доступа")
                    return
                elif resp.status != 200:
                    error_text = await resp.text()
                    logger.error(f"Tasks API error: {resp.status} - {error_text}")
                    await message.answer("❌ Ошибка сервера")
                    return
                    
                incidents = await resp.json()
    except Exception as e:
        logger.error(f"Error getting tasks: {e}")
        await message.answer("❌ Ошибка соединения")
        return

    if not incidents:
        await message.answer("✅ Активных инцидентов нет")
        return

    text = "🛠 *Активные инциденты:*\n\n"
    for inc in incidents:
        room_info = f"🏢 {inc.get('room_info', '')}\n" if inc.get('room_info') else ""
        text += (
            f"🆔 *#{inc.get('id', 'N/A')}*\n"
            f"📌 {inc.get('user_message', 'N/A')}\n"
            f"{room_info}"
            f"📊 `{inc.get('status', 'N/A')}`\n\n"
        )

    for part in split_message(text):
        await message.answer(part, parse_mode="Markdown")  # ИСПРАВЛЕНО: Markdown вместо MarkdownV2


# ---------- /solve ----------
@router.message(Command("solve"))
async def solve_menu(message: Message):
    telegram_id = message.from_user.id

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{API_BASE_URL}/incidents/not-done/",  # ИСПРАВЛЕНО: правильный URL
                params={"telegram_id": telegram_id}
            ) as resp:
                if resp.status == 403 or resp.status == 401:
                    await message.answer("⛔ Нет доступа")
                    return
                incidents = await resp.json()
    except Exception as e:
        logger.error(f"Error in solve menu: {e}")
        await message.answer("❌ Ошибка соединения")
        return

    if not incidents:
        await message.answer("✅ Нет активных инцидентов")
        return

    kb = InlineKeyboardBuilder()
    for inc in incidents:
        room_text = f" (🏢{inc.get('room_info', '')})" if inc.get('room_info') else ""
        kb.button(
            text=f"🛠 #{inc['id']}{room_text}",
            callback_data=f"close:{inc['id']}"
        )
    kb.adjust(1)

    await message.answer(
        "Выберите инцидент для закрытия:",
        reply_markup=kb.as_markup()
    )


# ---------- close incident ----------
@router.callback_query(lambda c: c.data.startswith("close:"))
async def close_incident(call: types.CallbackQuery):
    incident_id = call.data.split(":")[1]
    telegram_id = call.from_user.id

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{API_BASE_URL}/incidents/{incident_id}/close/",  # ИСПРАВЛЕНО: правильный URL
                json={"telegram_id": telegram_id}
            ) as resp:
                if resp.status != 200:
                    try:
                        error = await resp.json()
                        error_msg = error.get('detail', error.get('error', str(error)))
                    except:
                        error_msg = await resp.text()
                    await call.answer(f"❌ {error_msg}", show_alert=True)
                    return
                    
                result = await resp.json()
    except Exception as e:
        logger.error(f"Error closing incident: {e}")
        await call.answer("❌ Ошибка соединения", show_alert=True)
        return

    # Редактируем сообщение с кнопками
    try:
        await call.message.edit_text(f"✅ Инцидент #{incident_id} закрыт")
    except:
        await call.message.answer(f"✅ Инцидент #{incident_id} закрыт")
    
    await call.answer()


# ---------- /id ----------
@router.message(Command("id"))
async def my_id(message: Message):
    await message.answer(f"🆔 `{message.from_user.id}`", parse_mode="Markdown")  # ИСПРАВЛЕНО: Markdown вместо MarkdownV2


# ---------- /cancel ----------
@router.message(Command("cancel"))
async def cancel(message: Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        await message.answer("ℹ️ Нет активной операции для отмены")
        return
        
    await state.clear()
    await message.answer("❌ Операция отменена")