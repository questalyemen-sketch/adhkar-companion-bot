import os
from dotenv import load_dotenv

# تحميل متغيرات البيئة من ملف .env
load_dotenv()


# =========================================================
# Telegram
# =========================================================

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
ADMIN_ID = os.getenv("ADMIN_ID", "")


# =========================================================
# Project
# =========================================================

BOT_NAME = "Adhkar Companion"
BOT_VERSION = "1.0.0"


# =========================================================
# Database
# =========================================================

DATABASE_NAME = "adhkar.db"


# =========================================================
# Default Reminder Settings
# =========================================================

DEFAULT_MORNING_TIME = "06:00"
DEFAULT_EVENING_TIME = "18:00"

DEFAULT_TIMEZONE = "UTC"


# =========================================================
# Application Settings
# =========================================================

ENABLE_MORNING_REMINDER = True
ENABLE_EVENING_REMINDER = True


# =========================================================
# Validation
# =========================================================

if not BOT_TOKEN:
    raise ValueError(
        "BOT_TOKEN is not set. "
        "Please add BOT_TOKEN to your environment variables."
    )