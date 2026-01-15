import asyncio
import logging
import os
import random
from datetime import datetime, timedelta
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, Command
from aiogram.types import (
    InlineKeyboardButton, 
    InlineKeyboardMarkup,
    FSInputFile
)
from aiogram.utils.keyboard import InlineKeyboardBuilder

import database
import messages
import scheduler

# Load environment variables
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_USERNAMES = messages.ADMIN_USERNAMES  # [@evgenii_sharapov, @SadhuStas]

if not TOKEN:
    print("Error: BOT_TOKEN is not set in .env")

dp = Dispatcher()

# ═══════════════════════════════════════════════════════════════
# УТИЛИТЫ
# ═══════════════════════════════════════════════════════════════

def is_admin(user: types.User) -> bool:
    """Проверка, является ли пользователь админом."""
    return user.username and user.username.lower() in [u.lower() for u in ADMIN_USERNAMES]


async def send_video_note_or_placeholder(bot: Bot, chat_id: int, video_path: str, placeholder: str):
    """Отправка видео-кружка или placeholder текста."""
    if video_path and os.path.exists(video_path):
        await bot.send_video_note(chat_id, FSInputFile(video_path))
    else:
        await bot.send_message(chat_id, placeholder)


async def send_warmup_video(bot: Bot, chat_id: int, video_file_id: str, caption: str, button_text: str = None, button_url: str = None):
    """Отправка прогревочного видео с подписью и кнопкой."""
    keyboard = None
    if button_text and button_url:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=button_text, url=button_url)]
        ])
    
    try:
        if video_file_id:
            await bot.send_video(
                chat_id,
                video_file_id,
                caption=caption,
                reply_markup=keyboard,
                parse_mode="Markdown"
            )
        else:
            # Если видео нет, отправляем только текст
            await bot.send_message(
                chat_id,
                caption,
                reply_markup=keyboard,
                parse_mode="Markdown"
            )
    except Exception as e:
        logging.warning(f"Failed to send warmup video to {chat_id}: {e}")


# ═══════════════════════════════════════════════════════════════
# КОМАНДА /start — ПРИВЕТСТВИЕ
# ═══════════════════════════════════════════════════════════════

@dp.message(CommandStart())
async def cmd_start(message: types.Message, bot: Bot):
    """Приветственное сообщение с видео и кнопкой регистрации."""
    
    # Парсим реферальную ссылку (start_param)
    ref_by = None
    args = message.text.split()
    if len(args) > 1:
        param = args[1]
        if param.startswith("ref_"):
            try:
                ref_by = int(param.replace("ref_", ""))
                # Не записывать себя как реферера
                if ref_by == message.from_user.id:
                    ref_by = None
                else:
                    logging.info(f"User {message.from_user.id} came from referral link of user {ref_by}")
            except ValueError:
                pass
    
    # Сохраняем пользователя с реферером
    await database.add_user(
        message.from_user.id,
        message.from_user.username,
        message.from_user.full_name,
        ref_by=ref_by
    )
    
    # Кнопка регистрации — МГНОВЕННАЯ (Inline)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=messages.REGISTER_BUTTON, 
            callback_data="register_webinar"
        )]
    ])
    
    # Отправляем видео с текстом и кнопкой
    try:
        await bot.send_video(
            message.chat.id,
            messages.VIDEO_1_FILE_ID,
            caption=messages.WELCOME_TEXT,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
    except Exception as e:
        logging.warning(f"Failed to send welcome video: {e}")
        # Fallback на текст
        await message.answer(messages.WELCOME_TEXT, reply_markup=keyboard, parse_mode="Markdown")


# ═══════════════════════════════════════════════════════════════
# УПРАВЛЕНИЕ (RESET)
# ═══════════════════════════════════════════════════════════════

@dp.message(Command("reset"))
async def cmd_reset(message: types.Message):
    """Сброс регистрации (для тестов)."""
    try:
        await database.reset_registration(message.from_user.id)
        await message.reply("🔄 **Регистрация сброшена!**\n\nМожешь попробовать забронировать место заново через /start.", parse_mode="Markdown")
    except Exception as e:
        logging.error(f"Reset error: {e}")
        await message.reply(f"Ошибка при сбросе: {e}")


# ═══════════════════════════════════════════════════════════════
# РЕГИСТРАЦИЯ НА ВЕБИНАР
# ═══════════════════════════════════════════════════════════════

@dp.callback_query(F.data == "register_webinar")
async def handle_registration(callback: types.CallbackQuery, bot: Bot):
    """Обработка нажатия кнопки регистрации."""
    logging.info(f"Button registration attempt by {callback.from_user.username}")
    
    user_id = callback.from_user.id
    
    # Проверяем, не зарегистрирован ли уже
    user = await database.get_user(user_id)
    if user and user.get('has_registered_webinar'):
        await callback.answer("Вы уже записаны на эфир! ✅", show_alert=True)
        try:
            await callback.message.edit_reply_markup(reply_markup=None)
        except:
            pass
        return
    
    # Регистрируем
    await database.set_webinar_registration(user_id)
    await callback.answer("Отлично! Вы записаны! 🎉", show_alert=True)
    
    # Обновляем сообщение
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
        await callback.message.reply("✅ **Место забронировано!**\n\nЖди напоминания перед эфиром 📅", parse_mode="Markdown")
        
        # Предложение подписаться на канал (мягкое)
        channel_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📢 Подписаться на канал", url=messages.CHANNEL_LINK)]
        ])
        await bot.send_message(
            user_id,
            "🔔 **Чтобы не пропустить эфир — подпишись на канал!**\n\n"
            "Там будут напоминания, полезные материалы и анонсы.",
            reply_markup=channel_keyboard,
            parse_mode="Markdown"
        )
    except Exception as e:
        logging.warning(f"Error updating message: {e}")
    
    # Запускаем отложенное подтверждение через 30 секунд
    asyncio.create_task(send_confirmation_delayed(bot, user_id, delay_seconds=30))


@dp.message(F.web_app_data)
async def handle_web_app_data(message: types.Message, bot: Bot):
    """Обработка данных из Mini App."""
    import json
    data = message.web_app_data.data
    logging.info(f"Web App data from {message.from_user.username}: {data}")
    
    try:
        json_data = json.loads(data)
        action = json_data.get('action')
        
        if action == 'register_webinar':
            user_id = message.from_user.id
            
            # Регистрируем в БД
            await database.set_webinar_registration(user_id)
            
            # Мгновенное подтверждение
            await message.reply("✅ **Место забронировано!**\n\nЖди напоминания перед эфиром 📅", parse_mode="Markdown")
            
            # Отправляем видео 2 через 30 секунд
            asyncio.create_task(send_confirmation_delayed(bot, user_id, delay_seconds=30))
            
    except Exception as e:
        logging.error(f"Failed to process Web App data: {e}")

async def send_confirmation_delayed(bot: Bot, user_id: int, delay_seconds: int = 300):
    """Отправка подтверждения через delay_seconds секунд."""
    await asyncio.sleep(delay_seconds)
    
    try:
        # Кнопка для открытия Mini App на дашборде
        from aiogram.types import WebAppInfo
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text="🎁 Участвовать в розыгрыше", 
                web_app=WebAppInfo(url="https://mini-app-sharapovs-projects.vercel.app")
            )]
        ])
        
        # Отправляем видео #2 с текстом и кнопкой
        await bot.send_video(
            user_id,
            messages.VIDEO_2_FILE_ID,
            caption=messages.WARMUP_2_TEXT,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
    except Exception as e:
        logging.warning(f"Failed to send confirmation to {user_id}: {e}")


# ═══════════════════════════════════════════════════════════════
# РОЗЫГРЫШ — РЕКОМЕНДАЦИИ ДРУЗЕЙ
# ═══════════════════════════════════════════════════════════════

@dp.callback_query(F.data == "start_recommend")
async def start_recommend(callback: types.CallbackQuery):
    """Начало процесса рекомендации."""
    await callback.answer()
    await callback.message.answer(messages.RECOMMEND_INTRO, parse_mode="Markdown")


@dp.message(Command("recommend"))
async def cmd_recommend_start(message: types.Message):
    """Команда /recommend — начало ввода рекомендаций."""
    # Проверяем, есть ли уже рекомендации
    existing = await database.get_user_referrals(message.from_user.id)
    if existing:
        await message.answer(
            messages.RECOMMEND_ALREADY.format(friends="\n".join(existing)),
            parse_mode="Markdown"
        )
        return
    
    await message.answer(messages.RECOMMEND_INTRO, parse_mode="Markdown")


@dp.message(F.text.startswith("@"))
async def handle_recommendation(message: types.Message):
    """Обработка ввода рекомендаций (@friend1 @friend2)."""
    
    user_id = message.from_user.id
    
    # Проверяем, есть ли уже рекомендации
    existing = await database.get_user_referrals(user_id)
    if existing:
        await message.answer(
            messages.RECOMMEND_ALREADY.format(friends="\n".join(existing)),
            parse_mode="Markdown"
        )
        return
    
    # Парсим юзернеймы
    text = message.text.strip()
    usernames = [u.strip() for u in text.split() if u.startswith("@")]
    
    if len(usernames) < 2:
        await message.answer(messages.RECOMMEND_ERROR, parse_mode="Markdown")
        return
    
    # Берём первые 2
    friends = usernames[:2]
    
    # Сохраняем
    success = await database.add_referrals(user_id, friends)
    
    if success:
        await message.answer(
            messages.RECOMMEND_SUCCESS.format(friends="\n".join(friends)),
            parse_mode="Markdown"
        )
    else:
        existing = await database.get_user_referrals(user_id)
        await message.answer(
            messages.RECOMMEND_ALREADY.format(friends="\n".join(existing)),
            parse_mode="Markdown"
        )


# ═══════════════════════════════════════════════════════════════
# АДМИН-КОМАНДЫ
# ═══════════════════════════════════════════════════════════════

@dp.message(Command("raffle"))
async def cmd_raffle(message: types.Message):
    """Розыгрыш доски среди участников."""
    if not is_admin(message.from_user):
        return
    
    participants = await database.get_raffle_participants()
    
    if not participants:
        await message.answer(messages.RAFFLE_NO_PARTICIPANTS)
        return
    
    # Случайный выбор
    winner = random.choice(participants)
    winner_id, winner_username, winner_name = winner
    
    await message.answer(
        messages.RAFFLE_WINNER.format(
            winner_name=winner_name or "Участник",
            winner_username=winner_username or winner_id
        ),
        parse_mode="Markdown"
    )


@dp.message(Command("stats"))
async def cmd_stats(message: types.Message):
    """Статистика бота (только для админа)."""
    if not is_admin(message.from_user):
        return
    
    stats = await database.get_stats()
    
    await message.answer(
        messages.STATS_MESSAGE.format(**stats),
        parse_mode="Markdown"
    )


@dp.message(Command("set_stream_link"))
async def cmd_set_stream_link(message: types.Message):
    """Установка ссылки на эфир (только для админа)."""
    if not is_admin(message.from_user):
        return
    
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("❌ Использование: `/set_stream_link https://...`", parse_mode="Markdown")
        return
    
    link = parts[1].strip()
    await database.set_stream_link(link)
    await message.answer(f"✅ Ссылка на эфир установлена:\n{link}")


@dp.message(Command("broadcast"))
async def cmd_broadcast(message: types.Message, bot: Bot):
    """Массовая рассылка (только для админа)."""
    if not is_admin(message.from_user):
        return
    
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("❌ Использование: `/broadcast Текст сообщения`", parse_mode="Markdown")
        return
    
    text = parts[1]
    users = await database.get_active_users()
    count = 0
    
    for user_id in users:
        try:
            await bot.send_message(user_id, text, parse_mode="Markdown")
            count += 1
            await asyncio.sleep(0.05)  # Антифлуд
        except Exception as e:
            logging.warning(f"Broadcast failed for {user_id}: {e}")
            await database.update_status(user_id, False)
    
    await message.answer(messages.BROADCAST_CONFIRM.format(count=count))


@dp.message(Command("debug"))
async def cmd_debug(message: types.Message):
    """Получение file_id из пересланных видео (только для админа)."""
    if not is_admin(message.from_user):
        return
    
    await message.answer(
        "🔧 **Режим отладки**\n\n"
        "Перешли мне видео — я верну его `file_id`.\n\n"
        "Этот ID используй для прогрев-серии.",
        parse_mode="Markdown"
    )


@dp.message(F.video | F.video_note | F.document)
async def handle_video_debug(message: types.Message):
    """Обработка любых файлов для получения file_id."""
    # Логгируем попытку для отладки
    logging.info(f"Received file from {message.from_user.username} (ID: {message.from_user.id})")
    
    if not is_admin(message.from_user):
        logging.warning(f"Access denied for {message.from_user.username}")
        # Можно временно включить ответ для всех, чтобы проверить
        return
    
    file_id = None
    file_type = "Неизвестно"
    file_size = 0
    duration = 0
    
    if message.video:
        file_id = message.video.file_id
        file_type = "Video (Видео)"
        file_size = message.video.file_size
        duration = message.video.duration
    elif message.video_note:
        file_id = message.video_note.file_id
        file_type = "Video Note (Кружок)"
        file_size = message.video_note.file_size
        duration = message.video_note.duration
    elif message.document:
        file_id = message.document.file_id
        file_type = f"Document ({message.document.mime_type})"
        file_size = message.document.file_size
    
    if file_id:
        await message.reply(
            f"📹 **File Info:**\n\n"
            f"**Type:** {file_type}\n"
            f"**File ID:** `{file_id}`\n\n"
            f"📏 Размер: {file_size // 1024} KB\n"
            f"⏱ Длительность: {duration} сек",
            parse_mode="Markdown"
        )
    else:
        await message.reply("❌ Не удалось извлечь file_id. Попробуй другое видео.")


@dp.message(Command("test_warmup"))
async def cmd_test_warmup(message: types.Message, bot: Bot):
    """Тестовая отправка прогревочных видео (только для админа)."""
    if not is_admin(message.from_user):
        return
    
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer(
            "❌ Использование: `/test_warmup 1-5`\n\n"
            "Где номер — это номер видео (1-5)",
            parse_mode="Markdown"
        )
        return
    
    try:
        video_num = int(parts[1])
        if video_num < 1 or video_num > 5:
            raise ValueError
    except ValueError:
        await message.answer("❌ Укажи номер от 1 до 5")
        return
    
    # Получаем данные прогрева
    warmup_data = messages.get_warmup_video(video_num)
    
    if not warmup_data:
        await message.answer(f"❌ Видео #{video_num} не настроено")
        return
    
    await send_warmup_video(
        bot,
        message.chat.id,
        warmup_data.get('file_id'),
        warmup_data['caption'],
        warmup_data.get('button_text'),
        warmup_data.get('button_url')
    )
    
    await message.answer(f"✅ Отправлено видео #{video_num}")


@dp.message(Command("test_scenario"))
async def cmd_test_scenario(message: types.Message, bot: Bot):
    """Запуск ускоренного тестового режима."""
    if not is_admin(message.from_user):
        return
    
    await message.answer(
        "⚠️ **ЗАПУСК ТЕСТОВОГО РЕЖИМА**\n\n"
        "Интервал: 1 минута\n"
        "Последовательность:\n"
        "1. Видео #1 (через 1 мин)\n"
        "2. Видео #2 (через 2 мин)\n"
        "3. Видео #3 (через 3 мин)\n"
        "4. Видео #4 (через 4 мин)\n"
        "5. СТАРТ ЭФИРА (через 5 мин)\n"
        "6. Оффер (через 6 мин)\n\n"
        "⏳ Жди уведомления...",
        parse_mode="Markdown"
    )
    
    await scheduler.start_test_schedule(bot)


@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    """Список команд."""
    help_text = """
📋 **Доступные команды:**

👤 **Для всех:**
/start — Начать
/recommend — Участвовать в розыгрыше доски

👨‍💼 **Для админа:**
/stats — Статистика бота
/raffle — Провести розыгрыш
/set_stream_link — Установить ссылку на эфир
/broadcast — Массовая рассылка
/debug — Получить file_id видео
/test_warmup N — Тест прогревочного видео
/test_scenario — ЗАПУСК ТЕСТОВОГО РЕЖИМА (1 мин шаг)
"""
    await message.answer(help_text, parse_mode="Markdown")


# ═══════════════════════════════════════════════════════════════
# НЕИЗВЕСТНЫЕ КОМАНДЫ
# ═══════════════════════════════════════════════════════════════

@dp.message()
async def handle_unknown(message: types.Message):
    """Обработка неизвестных сообщений."""
    # Пропускаем сообщения, начинающиеся с @
    if message.text and message.text.startswith("@"):
        return
    
    await message.answer(messages.UNKNOWN_COMMAND, parse_mode="Markdown")


# ═══════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════

async def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # Initialize DB
    await database.init_db()
    
    # Initialize Bot
    if TOKEN:
        bot = Bot(token=TOKEN)
        
        # Setup Scheduler for reminders
        scheduler.setup_scheduler(bot)
        
        # Start API server for Mini App
        import api
        api_port = int(os.getenv('PORT', 8080))
        api_runner = await api.start_api_server(host='0.0.0.0', port=api_port)
        
        logging.info("Bot and API server starting...")
        
        try:
            await dp.start_polling(bot)
        finally:
            # Cleanup API server on exit
            await api_runner.cleanup()
    else:
        logging.warning("BOT_TOKEN not found. Bot will not start polling.")


if __name__ == "__main__":
    asyncio.run(main())

