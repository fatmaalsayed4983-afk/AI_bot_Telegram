import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
    
    # Admin IDs comma-separated parsing
    admin_ids_raw = os.getenv("ADMIN_IDS", "")
    ADMIN_IDS = [int(x.strip()) for x in admin_ids_raw.split(",") if x.strip().isdigit()]

    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

    # Gemini API Keys
    GEMINI_API_KEYS = [
        os.getenv("GEMINI_API_KEY_1", ""),
        os.getenv("GEMINI_API_KEY_2", ""),
        os.getenv("GEMINI_API_KEY_3", ""),
        os.getenv("GEMINI_API_KEY_4", ""),
    ]

    GEMINI_API_KEYS = [
        key for key in GEMINI_API_KEYS
        if key
    ]

    # المفتاح الأساسي - للتوافق مع أي جزء قديم من المشروع
    (
        GEMINI_API_KEYS[0]
        if GEMINI_API_KEYS
        else ""
    )

    DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "auto")
    MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", "10"))

    ENABLE_MEMORY = os.getenv("ENABLE_MEMORY", "True").lower() == "true"
    ENABLE_WEB_SEARCH = os.getenv("ENABLE_WEB_SEARCH", "True").lower() == "true"
    ENABLE_VOICE = os.getenv("ENABLE_VOICE", "False").lower() == "true"
    ENABLE_IMAGE_GENERATION = os.getenv("ENABLE_IMAGE_GENERATION", "True").lower() == "true"

    # DB path configuration
    DB_PATH = "data/assistant_database.db"
    TEMP_DIR = "temp"
