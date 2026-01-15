import sqlite3
import logging

logging.basicConfig(level=logging.INFO)

DB_NAME = "sadhu_bot.db"

def fix_db():
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        
        # Get existing columns
        cursor.execute("PRAGMA table_info(users)")
        columns = [info[1] for info in cursor.fetchall()]
        
        logging.info(f"Existing columns: {columns}")
        
        # Columns to add
        columns_to_add = [
            ("registered_webinar_at", "TIMESTAMP"),
            ("attended_webinar", "BOOLEAN DEFAULT 0"),
            ("purchased_course", "BOOLEAN DEFAULT 0"),
            ("payment_id", "TEXT")
        ]
        
        for col_name, col_type in columns_to_add:
            if col_name not in columns:
                logging.info(f"Adding missing column '{col_name}'...")
                try:
                    cursor.execute(f"ALTER TABLE users ADD COLUMN {col_name} {col_type}")
                    logging.info(f"Successfully added '{col_name}'.")
                except Exception as e:
                    logging.error(f"Failed to add '{col_name}': {e}")
            else:
                logging.info(f"Column '{col_name}' already exists.")
            
        conn.commit()
        conn.close()
        logging.info("Database migration completed.")
        
    except Exception as e:
        logging.error(f"Database fix failed: {e}")

if __name__ == "__main__":
    fix_db()
