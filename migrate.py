"""
Migrate existing database.db to add phone_number column to users table.
Safe to run multiple times.
"""
import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), "database.db")

if not os.path.exists(db_path):
    print("database.db not found, skipping migration (will be auto-created on bot start).")
else:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    # Check if column already exists
    cursor.execute("PRAGMA table_info(users)")
    cols = [row[1] for row in cursor.fetchall()]
    if "phone_number" not in cols:
        cursor.execute("ALTER TABLE users ADD COLUMN phone_number TEXT")
        conn.commit()
        print("✅ Migration complete: phone_number column added.")
    else:
        print("ℹ️  phone_number column already exists, nothing to do.")
    conn.close()
