import sqlite3
import os
import time
from app.core.config import Config

class DBManager:
    def __init__(self):
        os.makedirs(os.path.dirname(Config.DB_PATH), exist_ok=True)
        self.conn = sqlite3.connect(Config.DB_PATH, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.init_db()

    def init_db(self):
        cursor = self.conn.cursor()
        
        # Users system
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                telegram_id INTEGER PRIMARY KEY,
                username TEXT,
                role TEXT DEFAULT 'user',
                credits INTEGER DEFAULT 100,
                daily_usage INTEGER DEFAULT 0,
                is_active INTEGER DEFAULT 1,
                created_at INTEGER
            )
        ''')
        
        # Conversations table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS conversations (
                conversation_id TEXT PRIMARY KEY,
                telegram_id INTEGER,
                title TEXT,
                created_at INTEGER,
                updated_at INTEGER
            )
        ''')
        
        # Chat History messages
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                message_id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id TEXT,
                role TEXT,
                content TEXT,
                timestamp INTEGER
            )
        ''')
        
        # Long term memories
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS memories (
                memory_id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER,
                memory_text TEXT,
                created_at INTEGER
            )
        ''')
        
        # Settings per user
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                telegram_id INTEGER PRIMARY KEY,
                default_model TEXT DEFAULT 'auto',
                enable_voice INTEGER DEFAULT 0,
                web_search_enabled INTEGER DEFAULT 1
            )
        ''')
        
        # Log consumption
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS usage_logs (
                log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER,
                action TEXT,
                tokens INTEGER DEFAULT 0,
                timestamp INTEGER
            )
        ''')
        
        self.conn.commit()

    # User commands
    def get_or_create_user(self, telegram_id, username):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,))
        user = cursor.fetchone()
        if not user:
            role = 'admin' if telegram_id in Config.ADMIN_IDS else 'user'
            cursor.execute(
                "INSERT INTO users (telegram_id, username, role, credits, daily_usage, is_active, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (telegram_id, username, role, 100, 0, 1, int(time.time()))
            )
            # Default settings
            cursor.execute(
                "INSERT OR IGNORE INTO settings (telegram_id, default_model, enable_voice, web_search_enabled) VALUES (?, ?, ?, ?)",
                (telegram_id, 'auto', 0, 1)
            )
            self.conn.commit()
            cursor.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,))
            user = cursor.fetchone()
        return user

    def update_credits(self, telegram_id, amount):
        cursor = self.conn.cursor()
        cursor.execute("UPDATE users SET credits = credits + ? WHERE telegram_id = ?", (amount, telegram_id))
        self.conn.commit()

    def log_usage(self, telegram_id, action, tokens):
        cursor = self.conn.cursor()
        cursor.execute("INSERT INTO usage_logs (telegram_id, action, tokens, timestamp) VALUES (?, ?, ?, ?)",
                       (telegram_id, action, tokens, int(time.time())))
        cursor.execute("UPDATE users SET daily_usage = daily_usage + ? WHERE telegram_id = ?", (tokens, telegram_id))
        self.conn.commit()

    # Conversation Logic
    def create_conversation(self, conversation_id, telegram_id, title):
        cursor = self.conn.cursor()
        now = int(time.time())
        cursor.execute(
            "INSERT INTO conversations (conversation_id, telegram_id, title, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
            (conversation_id, telegram_id, title, now, now)
        )
        self.conn.commit()

    def get_user_conversations(self, telegram_id):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM conversations WHERE telegram_id = ? ORDER BY updated_at DESC", (telegram_id,))
        return cursor.fetchall()

    def get_messages(self, conversation_id):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM messages WHERE conversation_id = ? ORDER BY timestamp ASC", (conversation_id,))
        return cursor.fetchall()

    def add_message(self, conversation_id, role, content):
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO messages (conversation_id, role, content, timestamp) VALUES (?, ?, ?, ?)",
            (conversation_id, role, content, int(time.time()))
        )
        # Update conversation timestamp
        cursor.execute("UPDATE conversations SET updated_at = ? WHERE conversation_id = ?", (int(time.time()), conversation_id))
        self.conn.commit()

    def clear_conversation(self, conversation_id):
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM messages WHERE conversation_id = ?", (conversation_id,))
        self.conn.commit()

    def delete_conversation(self, conversation_id):
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM conversations WHERE conversation_id = ?", (conversation_id,))
        cursor.execute("DELETE FROM messages WHERE conversation_id = ?", (conversation_id,))
        self.conn.commit()

    # Settings handling
    def get_settings(self, telegram_id):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM settings WHERE telegram_id = ?", (telegram_id,))
        row = cursor.fetchone()
        if not row:
            cursor.execute(
                "INSERT OR IGNORE INTO settings (telegram_id, default_model, enable_voice, web_search_enabled) VALUES (?, ?, ?, ?)",
                (telegram_id, 'auto', 0, 1)
            )
            self.conn.commit()
            cursor.execute("SELECT * FROM settings WHERE telegram_id = ?", (telegram_id,))
            row = cursor.fetchone()
        return row

    def update_setting(self, telegram_id, key, value):
        cursor = self.conn.cursor()
        cursor.execute(f"UPDATE settings SET {key} = ? WHERE telegram_id = ?", (value, telegram_id))
        self.conn.commit()

    # Memory management
    def add_memory(self, telegram_id, text):
        cursor = self.conn.cursor()
        cursor.execute("INSERT INTO memories (telegram_id, memory_text, created_at) VALUES (?, ?, ?)", 
                       (telegram_id, text, int(time.time())))
        self.conn.commit()

    def get_memories(self, telegram_id):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM memories WHERE telegram_id = ? ORDER BY created_at DESC", (telegram_id,))
        return cursor.fetchall()

    def delete_memory(self, memory_id):
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM memories WHERE memory_id = ?", (memory_id,))
        self.conn.commit()

    def clear_all_memories(self, telegram_id):
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM memories WHERE telegram_id = ?", (telegram_id,))
        self.conn.commit()

    # System Admin Stats
    def get_system_stats(self):
        cursor = self.conn.cursor()
        stats = {}
        cursor.execute("SELECT COUNT(*) FROM users")
        stats['total_users'] = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM conversations")
        stats['total_conversations'] = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM messages")
        stats['total_messages'] = cursor.fetchone()[0]
        cursor.execute("SELECT SUM(tokens) FROM usage_logs")
        stats['total_tokens'] = cursor.fetchone()[0] or 0
        return stats

    def get_all_users_admin(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM users")
        return cursor.fetchall()
