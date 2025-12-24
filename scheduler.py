from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiogram import Bot
import database
import logging

scheduler = AsyncIOScheduler()

async def send_webinar_reminder(bot: Bot, text: str):
    """Sends a reminder to all registered users."""
    users = await database.get_registered_users()
    count = 0
    for user_id in users:
        try:
            await bot.send_message(user_id, text)
            count += 1
        except Exception as e:
            # Check for block
            logging.warning(f"Failed to send to {user_id}: {e}")
            await database.update_status(user_id, False)
    logging.info(f"Broadcast finished. Sent to {count} users.")

def setup_scheduler(bot: Bot):
    # Example: Webinar every Sunday at 18:00
    
    # 1. Reminder 1 hour before (Sunday 17:00)
    scheduler.add_job(
        send_webinar_reminder,
        'cron',
        day_of_week='sun',
        hour=17,
        minute=0,
        args=[bot, "🔔 Напоминание: Вебинар по гвоздестоянию начнется через 1 час!"]
    )
    
    # 2. Start (Sunday 18:00)
    scheduler.add_job(
        send_webinar_reminder,
        'cron',
        day_of_week='sun',
        hour=18,
        minute=0,
        args=[bot, "🔴 Мы начинаем! Подключайся к эфиру: [Ссылка на вебинар]"]
    )
    
    scheduler.start()
