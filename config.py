import os
from dotenv import load_dotenv


# =========================================================
# Load Environment Variables
# =========================================================

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
# Reminder Settings
# =========================================================

# أوقات التذكير الافتراضية
DEFAULT_MORNING_TIME = "06:00"
DEFAULT_EVENING_TIME = "18:00"

# لا يتم تحديد منطقة زمنية افتراضية.
# يجب على المستخدم اختيار منطقته الزمنية عند أول استخدام.
DEFAULT_TIMEZONE = None


# =========================================================
# Reminder Status
# =========================================================

ENABLE_MORNING_REMINDER = True
ENABLE_EVENING_REMINDER = True


# =========================================================
# Timezone Settings
# =========================================================

# يجب على المستخدم اختيار المنطقة الزمنية عند أول تشغيل.
#
# القيمة المحفوظة في قاعدة البيانات ستكون اسم IANA
# مثل:
# Asia/Aden
# Africa/Cairo
# Asia/Riyadh
#
# ويمكن إضافة مناطق أخرى لاحقًا.

TIMEZONE_OPTIONS = [
    ("🇾🇪 اليمن", "Asia/Aden"),
    ("🇸🇦 السعودية", "Asia/Riyadh"),
    ("🇦🇪 الإمارات", "Asia/Dubai"),
    ("🇴🇲 عُمان", "Asia/Muscat"),
    ("🇶🇦 قطر", "Asia/Qatar"),
    ("🇧🇭 البحرين", "Asia/Bahrain"),
    ("🇰🇼 الكويت", "Asia/Kuwait"),
    ("🇮🇶 العراق", "Asia/Baghdad"),
    ("🇯🇴 الأردن", "Asia/Amman"),
    ("🇱🇧 لبنان", "Asia/Beirut"),
    ("🇪🇬 مصر", "Africa/Cairo"),
    ("🇱🇾 ليبيا", "Africa/Tripoli"),
    ("🇹🇳 تونس", "Africa/Tunis"),
    ("🇩🇿 الجزائر", "Africa/Algiers"),
    ("🇲🇦 المغرب", "Africa/Casablanca"),
    ("🇸🇩 السودان", "Africa/Khartoum"),
    ("🇬🇧 بريطانيا", "Europe/London"),
    ("🇫🇷 فرنسا", "Europe/Paris"),
    ("🇩🇪 ألمانيا", "Europe/Berlin"),
    ("🇹🇷 تركيا", "Europe/Istanbul"),
    ("🇺🇸 أمريكا - نيويورك", "America/New_York"),
    ("🇨🇦 كندا - تورنتو", "America/Toronto"),
]


# =========================================================
# Registration Settings
# =========================================================

# يجب تحديد المنطقة الزمنية قبل تفعيل التذكيرات.
REQUIRE_TIMEZONE_ON_START = True


# =========================================================
# Validation
# =========================================================

if not BOT_TOKEN:
    raise ValueError(
        "BOT_TOKEN is not set. "
        "Please add BOT_TOKEN to your environment variables."
    )