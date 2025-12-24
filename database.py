import aiosqlite
import logging
from datetime import datetime

DB_NAME = "sadhu_bot.db"

async def init_db():
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                full_name TEXT,
                registered_at TIMESTAMP,
                is_active BOOLEAN DEFAULT 1,
                has_registered_webinar BOOLEAN DEFAULT 0
            )
        """)
        await db.commit()
    logging.info("Database initialized")

async def add_user(user_id: int, username: str, full_name: str):
    async with aiosqlite.connect(DB_NAME) as db:
        try:
            await db.execute("""
                INSERT OR IGNORE INTO users (user_id, username, full_name, registered_at)
                VALUES (?, ?, ?, ?)
            """, (user_id, username, full_name, datetime.now()))
            # If user existed but was inactive, reactivate
            await db.execute("UPDATE users SET is_active = 1 WHERE user_id = ?", (user_id,))
            await db.commit()
        except Exception as e:
            logging.error(f"Error adding user {user_id}: {e}")

async def set_webinar_registration(user_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("UPDATE users SET has_registered_webinar = 1 WHERE user_id = ?", (user_id,))
        await db.commit()

async def get_active_users():
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT user_id FROM users WHERE is_active = 1") as cursor:
            rows = await cursor.fetchall()
            return [row['user_id'] for row in rows]
            
async def get_registered_users():
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT user_id FROM users WHERE is_active = 1 AND has_registered_webinar = 1") as cursor:
            rows = await cursor.fetchall()
            return [row['user_id'] for row in rows]

async def update_status(user_id: int, is_active: bool):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("UPDATE users SET is_active = ? WHERE user_id = ?", (is_active, user_id))
        await db.commit()
