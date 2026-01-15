import sqlite3
import logging

logging.basicConfig(level=logging.INFO)

DB_NAME = "sadhu_bot.db"

def fix_db():
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        
        # Check if column exists
        cursor.execute("PRAGMA table_info(users)")
        columns = [info[1] for info in cursor.fetchall()]
        
        if 'source' not in columns:
            logging.info("Adding missing column 'source' to users table...")
            cursor.execute("ALTER TABLE users ADD COLUMN source TEXT")
            conn.commit()
            logging.info("Successfully added 'source' column.")
        else:
            logging.info("'source' column already exists.")
            
        conn.close()
    except Exception as e:
        logging.error(f"Database fix failed: {e}")

if __name__ == "__main__":
    fix_db()
