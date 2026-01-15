"""
Планировщик напоминаний для бота «Гвозди Просто»

Эфир: Настраивается в messages.WEBINAR_DATE
"""

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime, timedelta
from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import database
import messages
import logging

scheduler = AsyncIOScheduler(timezone="Europe/Moscow")


async def send_reminder(bot: Bot, text: str, only_registered: bool = True):
    """Отправка обычного текстового напоминания."""
    if only_registered:
        users = await database.get_registered_users()
    else:
        users = await database.get_active_users()
    
    count = 0
    for user_id in users:
        try:
            await bot.send_message(user_id, text, parse_mode="Markdown")
            count += 1
        except Exception as e:
            logging.warning(f"Failed to send reminder to {user_id}: {e}")
            await database.update_status(user_id, False)
    
    logging.info(f"Reminder sent to {count} users")


async def send_warmup_job(bot: Bot, video_num: int):
    """Отправка прогревочного видео (1-5)."""
    warmup_data = messages.get_warmup_video(video_num)
    if not warmup_data:
        logging.error(f"Warmup video #{video_num} config not found")
        return

    users = await database.get_registered_users()
    count = 0
    
    # Подготовка кнопки (URL или callback)
    keyboard = None
    if warmup_data.get('button_text'):
        if warmup_data.get('callback_data'):
            # Callback кнопка (вызывает действие в боте)
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text=warmup_data['button_text'], callback_data=warmup_data['callback_data'])]
            ])
        elif warmup_data.get('button_url'):
            # URL кнопка (открывает ссылку)
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text=warmup_data['button_text'], url=warmup_data['button_url'])]
            ])

    for user_id in users:
        try:
            if warmup_data.get('file_id'):
                await bot.send_video(
                    user_id,
                    warmup_data['file_id'],
                    caption=warmup_data['caption'],
                    reply_markup=keyboard,
                    parse_mode="Markdown"
                )
            else:
                await bot.send_message(
                    user_id,
                    warmup_data['caption'],
                    reply_markup=keyboard,
                    parse_mode="Markdown"
                )
            count += 1
        except Exception as e:
            logging.warning(f"Failed to send warmup #{video_num} to {user_id}: {e}")
            await database.update_status(user_id, False)
            
    logging.info(f"Warmup #{video_num} sent to {count} users")




async def send_reminder_with_link(bot: Bot):
    """Отправка напоминания о старте с ссылкой."""
    stream_link = await database.get_stream_link()
    
    if stream_link:
        text = messages.REMINDER_START.format(stream_link=stream_link)
    else:
        text = messages.REMINDER_START_NO_LINK
    
    await send_reminder(bot, text)


async def send_reminder_with_button(bot: Bot, text: str, button_text: str = "🔴 Перейти к эфиру"):
    """Отправка напоминания с кнопкой-ссылкой на эфир."""
    stream_link = await database.get_stream_link()
    
    users = await database.get_registered_users()
    count = 0
    
    # Создаём кнопку с ссылкой
    keyboard = None
    if stream_link:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=button_text, url=stream_link)]
        ])
    
    for user_id in users:
        try:
            await bot.send_message(
                user_id, 
                text, 
                reply_markup=keyboard,
                parse_mode="Markdown"
            )
            count += 1
        except Exception as e:
            logging.warning(f"Failed to send reminder to {user_id}: {e}")
            await database.update_status(user_id, False)
    
    logging.info(f"Reminder with button sent to {count} users")



async def send_post_webinar_offer(bot: Bot, hours_left: int):
    """Отправка пост-эфир предложения с дедлайном и кнопкой оплаты."""
    
    buyers_count = await database.get_buyers_count()
    
    # Вычисляем дедлайн (относительно даты вебинара + 12ч)
    webinar_dt = datetime.strptime(messages.WEBINAR_DATE, "%Y-%m-%d %H:%M:%S")
    deadline_dt = webinar_dt + timedelta(hours=12)
    deadline_str = deadline_dt.strftime("%H:%M")
    
    # Ссылка на оплату
    payment_url = messages.PAYMENT_LINK
    
    if hours_left == 3:
        text = messages.POST_WEBINAR_DEADLINE_3H.format(
            buyers_count=buyers_count,
            deadline=deadline_str
        )
        button_text = "💳 Купить со скидкой"
    elif hours_left == 1:
        text = messages.POST_WEBINAR_DEADLINE_1H.format(
            buyers_count=buyers_count,
            deadline=deadline_str
        )
        button_text = "🔥 Купить сейчас"
    elif hours_left == 0:
        text = messages.POST_WEBINAR_CLOSED
        button_text = None  # Без кнопки, скидка закончилась
    else:
        return
    
    # Создаём кнопку
    keyboard = None
    if button_text and payment_url:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=button_text, url=payment_url)]
        ])
    
    # Отправляем всем зарегистрированным
    users = await database.get_registered_users()
    count = 0
    
    for user_id in users:
        try:
            await bot.send_message(
                user_id, 
                text, 
                reply_markup=keyboard,
                parse_mode="Markdown"
            )
            count += 1
        except Exception as e:
            logging.warning(f"Failed to send deadline reminder to {user_id}: {e}")
            await database.update_status(user_id, False)
    
    logging.info(f"Deadline reminder ({hours_left}h) sent to {count} users")


def setup_scheduler(bot: Bot):
    """Настройка расписания напоминаний."""
    
    webinar_dt = datetime.strptime(messages.WEBINAR_DATE, "%Y-%m-%d %H:%M:%S")
    
    logging.info(f"Setting up scheduler for Webinar: {webinar_dt}")
    
    # ═══════════════════════════════════════════════════════════════
    # ПРОГРЕВ-СЕРИЯ
    # ═══════════════════════════════════════════════════════════════
    
    # Видео 1: За 5 дней (Анонс)
    scheduler.add_job(
        send_warmup_job, 'date', run_date=webinar_dt - timedelta(days=5),
        args=[bot, 1], id='warmup_1', replace_existing=True
    )
    
    # Видео 2: За 3 дня (Вовлечение)
    scheduler.add_job(
        send_warmup_job, 'date', run_date=webinar_dt - timedelta(days=3),
        args=[bot, 2], id='warmup_2', replace_existing=True
    )
    
    # Видео 3: За 1 день (Завтра) — ЗАМЕНЯЕТ старый REMINDER_24H
    scheduler.add_job(
        send_warmup_job, 'date', run_date=webinar_dt - timedelta(days=1),
        args=[bot, 3], id='warmup_3', replace_existing=True
    )
    
    # Видео 4: За 1 час — ЗАМЕНЯЕТ старый REMINDER_1H
    scheduler.add_job(
        send_warmup_job, 'date', run_date=webinar_dt - timedelta(hours=1),
        args=[bot, 4], id='warmup_4', replace_existing=True
    )
    
    # За 5 минут — напоминание с кнопкой
    scheduler.add_job(
        send_reminder_with_button, 'date', run_date=webinar_dt - timedelta(minutes=5),
        args=[bot, messages.REMINDER_5MIN, "🔴 Перейти к эфиру"], 
        id='reminder_5min', replace_existing=True
    )
    
    # СТАРТ ЭФИРА (без изменений)
    scheduler.add_job(
        send_reminder_with_link, 'date', run_date=webinar_dt,
        args=[bot], id='reminder_start', replace_existing=True
    )
    
    # Через 7 минут — напоминание "эфир в разгаре"
    scheduler.add_job(
        send_reminder_with_button, 'date', run_date=webinar_dt + timedelta(minutes=7),
        args=[bot, messages.REMINDER_7MIN, "📺 Подключиться сейчас"], 
        id='reminder_7min', replace_existing=True
    )
    
    # ═══════════════════════════════════════════════════════════════
    # ПОСТ-ЭФИР (ПРОДАЖА)
    # ═══════════════════════════════════════════════════════════════
    
    # Видео 5: Через 1.5 часа (Скидка 20%) — ЗАМЕНЯЕТ старый оффер 12ч
    scheduler.add_job(
        send_warmup_job, 'date', run_date=webinar_dt + timedelta(minutes=90),
        args=[bot, 5], id='warmup_5', replace_existing=True
    )
    
    # Дедлайны (вычисляем от конца скидки, который через 12ч после конца эфира ~14ч после старта)
    # Скидка действует 12 часов ПОСЛЕ ЭФИРА. Эфир ~1.5-2 часа.
    # Допустим отсчет 12 часов начинается с момента отправки Видео 5 (start + 1.5h)
    
    offer_start_dt = webinar_dt + timedelta(minutes=90)
    offer_end_dt = offer_start_dt + timedelta(hours=12)
    
    # Дедлайн 3 часа до конца
    scheduler.add_job(
        send_post_webinar_offer, 'date', run_date=offer_end_dt - timedelta(hours=3),
        args=[bot, 3], id='deadline_3h', replace_existing=True
    )
    
    # Дедлайн 1 час до конца
    scheduler.add_job(
        send_post_webinar_offer, 'date', run_date=offer_end_dt - timedelta(hours=1),
        args=[bot, 1], id='deadline_1h', replace_existing=True
    )
    
    # Закрытие
    scheduler.add_job(
        send_post_webinar_offer, 'date', run_date=offer_end_dt,
        args=[bot, 0], id='offer_closed', replace_existing=True
    )
    
    scheduler.start()
    logging.info("Scheduler started with webinar reminders for 2026-01-05 19:00 MSK")


async def start_test_schedule(bot: Bot):
    """Запуск ТЕСТОВОГО расписания (шаг 1 минута)."""
    scheduler.remove_all_jobs()
    logging.info("⚠️ STARTING TEST SCHEDULE ⚠️")
    
    now = datetime.now()
    
    # 1. Анонс (через 1 мин)
    scheduler.add_job(send_warmup_job, 'date', run_date=now + timedelta(minutes=1), args=[bot, 1], id='test_w1')
    
    # 2. Вовлечение (через 2 мин)
    scheduler.add_job(send_warmup_job, 'date', run_date=now + timedelta(minutes=2), args=[bot, 2], id='test_w2')
    
    # 3. Завтра эфир (через 3 мин)
    scheduler.add_job(send_warmup_job, 'date', run_date=now + timedelta(minutes=3), args=[bot, 3], id='test_w3')
    
    # 4. Через час (через 4 мин)
    scheduler.add_job(send_warmup_job, 'date', run_date=now + timedelta(minutes=4), args=[bot, 4], id='test_w4')
    
    # 5. СТАРТ ЭФИРА (через 5 мин)
    scheduler.add_job(send_reminder_with_link, 'date', run_date=now + timedelta(minutes=5), args=[bot], id='test_start')
    
    # 6. Оффер после эфира (через 6 мин)
    scheduler.add_job(send_warmup_job, 'date', run_date=now + timedelta(minutes=6), args=[bot, 5], id='test_w5')
    
    logging.info("Test schedule set: 6 steps, 1 min interval")


def get_scheduled_jobs():
    """Получение списка запланированных задач (для отладки)."""
    jobs = []
    for job in scheduler.get_jobs():
        jobs.append({
            'id': job.id,
            'next_run': job.next_run_time.strftime("%Y-%m-%d %H:%M:%S")
        })
    return jobs
