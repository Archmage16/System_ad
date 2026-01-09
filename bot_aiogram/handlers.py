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

def split_message(text: str, max_len: int = MAX_LEN) -> list:
    """Разбивает длинный текст на части."""
    return [text[i:i+max_len] for i in range(0, len(text), max_len)]

# ----------------- FSM States -----------------
class IncidentForm(StatesGroup):
    waiting_for_message = State()
    waiting_for_cabinet = State()

# ----------------- Команда /start -----------------
@router.message(Command("start"))
async def start_command(message: Message):
    """Приветственное сообщение."""
    text = (
        "👋 Привет! Я бот для управления инцидентами.\n\n"
        "📋 Доступные команды:\n"
        "/start - Показать это сообщение\n"
        "/add-incidents - Создать новый инцидент\n"
        "/tasks - Мои активные инциденты\n"
        "/solve - Закрыть инцидент (для исполнителей)\n"
        "/id - Показать мой Telegram ID\n"
        "/cancel - Отменить текущую операцию"
    )
    await message.answer(text)

# ----------------- Команда /add-incidents -----------------
@router.message(Command("add-incidents"))
async def add_incident_start(message: Message, state: FSMContext):
    """Начало создания инцидента."""
    await message.answer("📝 Пожалуйста, напишите текст вашего инцидента:")
    await state.set_state(IncidentForm.waiting_for_message)

# ----------------- Получение текста инцидента -----------------
@router.message(IncidentForm.waiting_for_message)
async def add_incident_receive(message: Message, state: FSMContext):
    """Получаем текст инцидента."""
    user_message = message.text.strip()
    if not user_message:
        await message.answer("⚠ Текст не может быть пустым. Попробуйте снова.")
        return
    
    await state.update_data(user_message=user_message)
    await message.answer("🏢 Теперь укажите номер кабинета (или '-' если не требуется):")
    await state.set_state(IncidentForm.waiting_for_cabinet)

# ----------------- Получение кабинета и отправка -----------------
@router.message(IncidentForm.waiting_for_cabinet)
async def add_incident_cabinet(message: Message, state: FSMContext):
    """Получаем кабинет и отправляем данные в API."""
    cabinet = message.text.strip()
    
    # Получаем сохранённые данные
    data = await state.get_data()
    user_message = data.get('user_message', '')
    
    # Обработка кабинета
    if cabinet.lower() in ('-', 'нет', 'не требуется', ''):
        cabinet = ''
    
    # Формируем данные для API
    api_data = {
        "telegram_id": message.from_user.id,
        "user_message": user_message,
        "cabinet": cabinet
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{API_BASE_URL}/incidents/", 
                json=api_data
            ) as resp:
                
                if resp.status == 201:
                    incident = await resp.json()
                    
                    # Формируем ответ
                    cabinet_info = f"🏢 Кабинет: {incident.get('cabinet', 'не указан')}\n" if incident.get('cabinet') else ""
                    
                    text = (
                        f"✅ Инцидент создан!\n"
                        f"🆔 ID: {incident.get('id')}\n"
                        f"📝 Сообщение: {incident.get('user_message')}\n"
                        f"{cabinet_info}"
                        f"📊 Статус: {incident.get('status')}"
                    )
                    
                    for part in split_message(text):
                        await message.answer(part)
                    
                else:
                    error_data = await resp.json()
                    error_msg = error_data.get('detail', str(error_data))
                    await message.answer(f"❌ Ошибка: {error_msg}")
                    
    except Exception as e:
        logger.error(f"Ошибка при создании инцидента: {e}")
        await message.answer(f"❌ Ошибка соединения: {e}")
    
    finally:
        await state.clear()

# ----------------- Команда /tasks -----------------
@router.message(Command("tasks"))
async def not_done_tasks(message: Message):
    """Показать активные инциденты пользователя."""
    telegram_id = message.from_user.id
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{API_BASE_URL}/incidents/not-done/",
                params={"telegram_id": telegram_id}
            ) as resp:
                
                if resp.status == 403 or resp.status == 401:
                    await message.answer("⛔ У вас нет доступа")
                    return
                
                incidents = await resp.json()
                
    except Exception as e:
        logger.error(f"Ошибка при получении задач: {e}")
        await message.answer(f"❌ Ошибка: {e}")
        return
    
    if not incidents:
        await message.answer("✅ Нет активных заявок")
        return
    
    text = "🛠 *Активные инциденты:*\n\n"
    
    for incident in incidents:
        status_icon = "🆕" if incident.get("status") == "new" else "⏳"
        cabinet_info = f"🏢 Кабинет: {incident.get('cabinet')}\n" if incident.get('cabinet') else ""
        
        text += (
            f"{status_icon} *#{incident.get('id')}*\n"
            f"📌 {incident.get('user_message')}\n"
            f"{cabinet_info}"
            f"📊 Статус: `{incident.get('status')}`\n"
            f"📅 Создан: {incident.get('created_at', '')}\n\n"
        )
    
    for part in split_message(text):
        await message.answer(part, parse_mode="Markdown")

# ----------------- Команда /solve -----------------
@router.message(Command("solve"))
async def incidents_handler(message: types.Message):
    """Показать инциденты для закрытия."""
    telegram_id = message.from_user.id
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{API_BASE_URL}/incidents/not-done/",
                params={"telegram_id": telegram_id}
            ) as resp:
                
                incidents = await resp.json()
                
    except Exception as e:
        logger.error(f"Ошибка при получении инцидентов: {e}")
        await message.answer(f"❌ Ошибка: {e}")
        return
    
    if not incidents:
        await message.answer("✅ Активных инцидентов нет")
        return
    
    builder = InlineKeyboardBuilder()
    
    for inc in incidents:
        # Формируем текст кнопки с краткой информацией
        cabinet_text = f" | 🏢{inc.get('cabinet')}" if inc.get('cabinet') else ""
        button_text = f"🛠 #{inc['id']}{cabinet_text}"
        
        builder.button(
            text=button_text,
            callback_data=f"close:{inc['id']}"
        )
    
    builder.adjust(1)
    
    await message.answer(
        "📋 Выберите инцидент для закрытия:",
        reply_markup=builder.as_markup()
    )

# ----------------- Обработка закрытия инцидента -----------------
@router.callback_query(lambda c: c.data.startswith("close:"))
async def close_incident(call: types.CallbackQuery):
    """Закрыть выбранный инцидент."""
    incident_id = call.data.split(":")[1]
    telegram_id = call.from_user.id
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{API_BASE_URL}/incidents/{incident_id}/close/",
                json={"telegram_id": telegram_id}
            ) as resp:
                
                if resp.status == 200:
                    await call.message.edit_text(f"✅ Инцидент #{incident_id} закрыт")
                    await call.answer()
                else:
                    error_data = await resp.json()
                    error_msg = error_data.get('detail', 'Неизвестная ошибка')
                    await call.answer(f"❌ Ошибка: {error_msg}", show_alert=True)
                    
    except Exception as e:
        logger.error(f"Ошибка при закрытии инцидента: {e}")
        await call.answer("❌ Ошибка соединения", show_alert=True)

# ----------------- Команда /id -----------------
@router.message(Command("id"))
async def my_id(message: Message):
    """Показать Telegram ID."""
    await message.answer(f"🆔 Ваш Telegram ID: `{message.from_user.id}`", parse_mode="Markdown")

# ----------------- Команда /cancel -----------------
    @router.message(Command("cancel"))
    async def cancel_handler(message: Message, state: FSMContext):
        """Отменить текущую операцию."""
        current_state = await state.get_state()
        if current_state is None:
            await message.answer("ℹ️ Нет активных операций для отмены.")
            return
        
        await state.clear()
        await message.answer("❌ Операция отменена.")