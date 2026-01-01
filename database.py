import aiosqlite
import logging
from datetime import datetime
from typing import Optional, List, Tuple

DB_NAME = "sadhu_bot.db"


async def init_db():
    """Инициализация базы данных с расширенной схемой."""
    async with aiosqlite.connect(DB_NAME) as db:
        # Основная таблица пользователей
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                full_name TEXT,
                registered_at TIMESTAMP,
                is_active BOOLEAN DEFAULT 1,
                has_registered_webinar BOOLEAN DEFAULT 0,
                registered_webinar_at TIMESTAMP,
                attended_webinar BOOLEAN DEFAULT 0,
                purchased_course BOOLEAN DEFAULT 0,
                payment_id TEXT,
                source TEXT,
                ref_by INTEGER
            )
        """)
        
        # Миграция: добавляем ref_by если не существует
        try:
            await db.execute("ALTER TABLE users ADD COLUMN ref_by INTEGER")
            await db.commit()
            logging.info("Added ref_by column to users table")
        except:
            pass  # Колонка уже существует
        
        # Таблица рекомендаций для розыгрыша
        await db.execute("""
            CREATE TABLE IF NOT EXISTS referrals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                referrer_id INTEGER,
                friend_username TEXT,
                created_at TIMESTAMP,
                FOREIGN KEY (referrer_id) REFERENCES users(user_id)
            )
        """)
        
        # Таблица настроек (ссылка на эфир и т.д.)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """)
        
        # Таблица логов практики (для трекера 21 дня)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS practice_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                practice_date DATE,
                duration_seconds INTEGER DEFAULT 0,
                created_at TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id),
                UNIQUE(user_id, practice_date)
            )
        """)
        
        # Счётчик покупок (для social proof)
        await db.execute("""
            INSERT OR IGNORE INTO settings (key, value) VALUES ('buyers_count', '50')
        """)
        
        await db.commit()
    logging.info("Database initialized with extended schema")


# ═══════════════════════════════════════════════════════════════
# ПОЛЬЗОВАТЕЛИ
# ═══════════════════════════════════════════════════════════════

async def add_user(user_id: int, username: str, full_name: str, source: str = None, ref_by: int = None):
    """Добавление нового пользователя с опциональным реферером."""
    async with aiosqlite.connect(DB_NAME) as db:
        try:
            await db.execute("""
                INSERT OR IGNORE INTO users (user_id, username, full_name, registered_at, source, ref_by)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (user_id, username, full_name, datetime.now(), source, ref_by))
            # Реактивация если был неактивен
            await db.execute("UPDATE users SET is_active = 1 WHERE user_id = ?", (user_id,))
            await db.commit()
            
            # Логируем успешный реферал
            if ref_by:
                logging.info(f"User {user_id} registered via referral from {ref_by}")
        except Exception as e:
            logging.error(f"Error adding user {user_id}: {e}")


async def count_user_referrals(user_id: int) -> int:
    """Подсчёт успешных рефералов (зарегистрированных на вебинар)."""
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("""
            SELECT COUNT(*) FROM users 
            WHERE ref_by = ? AND has_registered_webinar = 1
        """, (user_id,)) as cursor:
            result = await cursor.fetchone()
            return result[0] if result else 0


async def get_user_referral_info(user_id: int) -> dict:
    """Получение информации о рефералах пользователя для Mini App."""
    referral_count = await count_user_referrals(user_id)
    user = await get_user(user_id)
    
    return {
        "user_id": user_id,
        "username": user.get("username") if user else None,
        "full_name": user.get("full_name") if user else None,
        "is_registered": user.get("has_registered_webinar", False) if user else False,
        "referrals": referral_count,
        "target_referrals": 2,
        "in_raffle": referral_count >= 2
    }


async def get_user(user_id: int) -> Optional[dict]:
    """Получение данных пользователя."""
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None


async def set_webinar_registration(user_id: int):
    """Регистрация на вебинар."""
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
            UPDATE users 
            SET has_registered_webinar = 1, registered_webinar_at = ?
            WHERE user_id = ?
        """, (datetime.now(), user_id))
        await db.commit()


async def set_attended_webinar(user_id: int):
    """Отметка о посещении вебинара."""
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("UPDATE users SET attended_webinar = 1 WHERE user_id = ?", (user_id,))
        await db.commit()


async def set_purchased(user_id: int, payment_id: str = None):
    """Отметка о покупке курса."""
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
            UPDATE users SET purchased_course = 1, payment_id = ? WHERE user_id = ?
        """, (payment_id, user_id))
        await db.commit()
        # Увеличиваем счётчик покупок
        await increment_buyers_count()


async def get_active_users() -> List[int]:
    """Получение всех активных пользователей."""
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT user_id FROM users WHERE is_active = 1") as cursor:
            rows = await cursor.fetchall()
            return [row['user_id'] for row in rows]


async def get_registered_users() -> List[int]:
    """Получение записавшихся на вебинар."""
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("""
            SELECT user_id FROM users 
            WHERE is_active = 1 AND has_registered_webinar = 1
        """) as cursor:
            rows = await cursor.fetchall()
            return [row['user_id'] for row in rows]


async def update_status(user_id: int, is_active: bool):
    """Обновление статуса активности."""
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("UPDATE users SET is_active = ? WHERE user_id = ?", (is_active, user_id))
        await db.commit()


# ═══════════════════════════════════════════════════════════════
# РОЗЫГРЫШ (рекомендации)
# ═══════════════════════════════════════════════════════════════

async def add_referrals(referrer_id: int, friends: List[str]) -> bool:
    """Добавление рекомендаций друзей."""
    async with aiosqlite.connect(DB_NAME) as db:
        # Проверяем, не добавлял ли уже
        async with db.execute(
            "SELECT COUNT(*) FROM referrals WHERE referrer_id = ?", (referrer_id,)
        ) as cursor:
            count = (await cursor.fetchone())[0]
            if count > 0:
                return False  # Уже участвует
        
        # Добавляем рекомендации
        for friend in friends:
            await db.execute("""
                INSERT INTO referrals (referrer_id, friend_username, created_at)
                VALUES (?, ?, ?)
            """, (referrer_id, friend.strip().lstrip('@'), datetime.now()))
        await db.commit()
        return True


async def get_user_referrals(user_id: int) -> List[str]:
    """Получение рекомендаций пользователя."""
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute(
            "SELECT friend_username FROM referrals WHERE referrer_id = ?", (user_id,)
        ) as cursor:
            rows = await cursor.fetchall()
            return [f"@{row[0]}" for row in rows]


async def get_raffle_participants() -> List[Tuple[int, str, str]]:
    """Получение участников розыгрыша (с 2+ рекомендациями)."""
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("""
            SELECT u.user_id, u.username, u.full_name, COUNT(r.id) as ref_count
            FROM users u
            JOIN referrals r ON u.user_id = r.referrer_id
            WHERE u.is_active = 1
            GROUP BY u.user_id
            HAVING ref_count >= 2
        """) as cursor:
            rows = await cursor.fetchall()
            return [(row['user_id'], row['username'], row['full_name']) for row in rows]


# ═══════════════════════════════════════════════════════════════
# НАСТРОЙКИ
# ═══════════════════════════════════════════════════════════════

async def get_setting(key: str) -> Optional[str]:
    """Получение настройки."""
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT value FROM settings WHERE key = ?", (key,)) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else None


async def set_setting(key: str, value: str):
    """Установка настройки."""
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
            INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)
        """, (key, value))
        await db.commit()


async def get_stream_link() -> Optional[str]:
    """Получение ссылки на эфир."""
    return await get_setting('stream_link')


async def set_stream_link(link: str):
    """Установка ссылки на эфир."""
    await set_setting('stream_link', link)


async def get_buyers_count() -> int:
    """Получение количества покупателей."""
    value = await get_setting('buyers_count')
    return int(value) if value else 50


async def increment_buyers_count():
    """Увеличение счётчика покупателей."""
    current = await get_buyers_count()
    await set_setting('buyers_count', str(current + 1))


# ═══════════════════════════════════════════════════════════════
# СТАТИСТИКА
# ═══════════════════════════════════════════════════════════════

async def get_stats() -> dict:
    """Получение статистики для админ-панели."""
    async with aiosqlite.connect(DB_NAME) as db:
        stats = {}
        
        # Всего пользователей
        async with db.execute("SELECT COUNT(*) FROM users WHERE is_active = 1") as cursor:
            stats['total_users'] = (await cursor.fetchone())[0]
        
        # Записались на вебинар
        async with db.execute("""
            SELECT COUNT(*) FROM users WHERE is_active = 1 AND has_registered_webinar = 1
        """) as cursor:
            stats['registered'] = (await cursor.fetchone())[0]
        
        # Участников розыгрыша
        async with db.execute("""
            SELECT COUNT(DISTINCT referrer_id) FROM referrals
        """) as cursor:
            stats['raffle_participants'] = (await cursor.fetchone())[0]
        
        # Купили курс
        async with db.execute("""
            SELECT COUNT(*) FROM users WHERE purchased_course = 1
        """) as cursor:
            stats['buyers'] = (await cursor.fetchone())[0]
        
        # Конверсия
        if stats['total_users'] > 0:
            stats['conversion'] = round(stats['registered'] / stats['total_users'] * 100, 1)
        else:
            stats['conversion'] = 0
        
        return stats


# ═══════════════════════════════════════════════════════════════
# ТРЕКЕР ПРАКТИКИ (21 ДЕНЬ)
# ═══════════════════════════════════════════════════════════════

async def save_practice_log(user_id: int, practice_date: str, duration_seconds: int = 0):
    """Сохранение записи о практике."""
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
            INSERT OR REPLACE INTO practice_logs (user_id, practice_date, duration_seconds, created_at)
            VALUES (?, ?, ?, ?)
        """, (user_id, practice_date, duration_seconds, datetime.now()))
        await db.commit()
        logging.info(f"Practice log saved for user {user_id}: {practice_date}, {duration_seconds}s")


async def get_practice_logs(user_id: int) -> List[dict]:
    """Получение всех записей о практике пользователя."""
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("""
            SELECT practice_date, duration_seconds, created_at 
            FROM practice_logs 
            WHERE user_id = ?
            ORDER BY practice_date ASC
        """, (user_id,)) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]


async def get_completed_days(user_id: int) -> List[int]:
    """Получение списка завершённых дней (1-21) для трекера."""
    logs = await get_practice_logs(user_id)
    
    if not logs:
        return []
    
    # Считаем дни от первой практики
    first_date = datetime.strptime(logs[0]['practice_date'], '%Y-%m-%d').date()
    completed_days = []
    
    for log in logs:
        log_date = datetime.strptime(log['practice_date'], '%Y-%m-%d').date()
        day_number = (log_date - first_date).days + 1
        if 1 <= day_number <= 21:
            completed_days.append(day_number)
    
    return completed_days


async def reset_practice_tracker(user_id: int):
    """Сброс трекера практики для пользователя."""
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("DELETE FROM practice_logs WHERE user_id = ?", (user_id,))
        await db.commit()
        logging.info(f"Practice tracker reset for user {user_id}")

