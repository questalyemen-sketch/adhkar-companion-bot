from telebot import types

from config import TIMEZONE_OPTIONS


# =========================================================
# First-Time Timezone Setup
# =========================================================

def timezone_setup_menu():
    """
    قائمة اختيار المنطقة الزمنية عند أول استخدام للبوت.

    لا يمكن للمستخدم الوصول إلى القائمة الرئيسية
    قبل اختيار المنطقة الزمنية.
    """

    keyboard = types.InlineKeyboardMarkup(row_width=2)

    for name, timezone_name in TIMEZONE_OPTIONS:
        keyboard.add(
            types.InlineKeyboardButton(
                name,
                callback_data=f"set_timezone:{timezone_name}"
            )
        )

    return keyboard


# =========================================================
# Timezone Menu
# =========================================================

def timezone_menu():
    """
    قائمة تغيير المنطقة الزمنية من الإعدادات.
    """

    keyboard = types.InlineKeyboardMarkup(row_width=2)

    for name, timezone_name in TIMEZONE_OPTIONS:
        keyboard.add(
            types.InlineKeyboardButton(
                name,
                callback_data=f"set_timezone:{timezone_name}"
            )
        )

    keyboard.add(
        types.InlineKeyboardButton(
            "🔙 رجوع",
            callback_data="settings"
        )
    )

    return keyboard


# =========================================================
# Main Menu
# =========================================================

def main_menu():
    """
    القائمة الرئيسية للبوت.
    """

    keyboard = types.InlineKeyboardMarkup(row_width=2)

    keyboard.add(
        types.InlineKeyboardButton(
            "🌅 أذكار الصباح",
            callback_data="morning"
        ),
        types.InlineKeyboardButton(
            "🌙 أذكار المساء",
            callback_data="evening"
        )
    )

    keyboard.add(
        types.InlineKeyboardButton(
            "🤲 الأدعية",
            callback_data="duas"
        ),
        types.InlineKeyboardButton(
            "🕌 أذكار الصلاة",
            callback_data="prayer"
        )
    )

    keyboard.add(
        types.InlineKeyboardButton(
            "😴 أذكار النوم",
            callback_data="sleep"
        ),
        types.InlineKeyboardButton(
            "📚 جميع الأذكار",
            callback_data="all_adhkar"
        )
    )

    keyboard.add(
        types.InlineKeyboardButton(
            "⏰ إعدادات التذكير",
            callback_data="settings"
        )
    )

    return keyboard


# =========================================================
# Back Button
# =========================================================

def back_button():
    """
    زر العودة إلى القائمة الرئيسية.
    """

    keyboard = types.InlineKeyboardMarkup()

    keyboard.add(
        types.InlineKeyboardButton(
            "🔙 القائمة الرئيسية",
            callback_data="main_menu"
        )
    )

    return keyboard


# =========================================================
# Reminder Settings
# =========================================================

def reminder_settings():
    """
    قائمة إعدادات التذكيرات.
    """

    keyboard = types.InlineKeyboardMarkup(row_width=2)

    keyboard.add(
        types.InlineKeyboardButton(
            "🌅 أذكار الصباح",
            callback_data="morning_settings"
        ),
        types.InlineKeyboardButton(
            "🌙 أذكار المساء",
            callback_data="evening_settings"
        )
    )

    keyboard.add(
        types.InlineKeyboardButton(
            "🌍 المنطقة الزمنية",
            callback_data="timezone"
        )
    )

    keyboard.add(
        types.InlineKeyboardButton(
            "🔙 القائمة الرئيسية",
            callback_data="main_menu"
        )
    )

    return keyboard


# =========================================================
# Morning Settings
# =========================================================

def morning_settings(enabled=True):
    """
    إعدادات أذكار الصباح.

    enabled=True  → التذكير مفعل.
    enabled=False → التذكير متوقف.
    """

    keyboard = types.InlineKeyboardMarkup(row_width=2)

    status = "🟢 مفعل" if enabled else "🔴 متوقف"
    action = "⏸️ إيقاف التذكير" if enabled else "▶️ تشغيل التذكير"

    keyboard.add(
        types.InlineKeyboardButton(
            f"{status}",
            callback_data="morning_status"
        )
    )

    keyboard.add(
        types.InlineKeyboardButton(
            action,
            callback_data="toggle_morning"
        )
    )

    keyboard.add(
        types.InlineKeyboardButton(
            "⏰ تغيير الوقت",
            callback_data="morning_time"
        )
    )

    keyboard.add(
        types.InlineKeyboardButton(
            "🔙 رجوع",
            callback_data="settings"
        )
    )

    return keyboard


# =========================================================
# Evening Settings
# =========================================================

def evening_settings(enabled=True):
    """
    إعدادات أذكار المساء.

    enabled=True  → التذكير مفعل.
    enabled=False → التذكير متوقف.
    """

    keyboard = types.InlineKeyboardMarkup(row_width=2)

    status = "🟢 مفعل" if enabled else "🔴 متوقف"
    action = "⏸️ إيقاف التذكير" if enabled else "▶️ تشغيل التذكير"

    keyboard.add(
        types.InlineKeyboardButton(
            f"{status}",
            callback_data="evening_status"
        )
    )

    keyboard.add(
        types.InlineKeyboardButton(
            action,
            callback_data="toggle_evening"
        )
    )

    keyboard.add(
        types.InlineKeyboardButton(
            "⏰ تغيير الوقت",
            callback_data="evening_time"
        )
    )

    keyboard.add(
        types.InlineKeyboardButton(
            "🔙 رجوع",
            callback_data="settings"
        )
    )

    return keyboard


# =========================================================
# Time Selection
# =========================================================

def time_selection(prefix):
    """
    قائمة اختيار وقت التذكير.

    prefix:
        morning
        evening
    """

    keyboard = types.InlineKeyboardMarkup(row_width=3)

    if prefix == "morning":
        times = [
            "05:00",
            "05:30",
            "06:00",
            "06:30",
            "07:00",
            "07:30",
            "08:00",
            "08:30",
            "09:00",
        ]

    elif prefix == "evening":
        times = [
            "16:00",
            "16:30",
            "17:00",
            "17:30",
            "18:00",
            "18:30",
            "19:00",
            "19:30",
            "20:00",
            "20:30",
            "21:00",
        ]

    else:
        times = [
            "06:00",
            "18:00",
        ]

    for time in times:
        keyboard.add(
            types.InlineKeyboardButton(
                time,
                callback_data=f"{prefix}_set:{time}"
            )
        )

    keyboard.add(
        types.InlineKeyboardButton(
            "🔙 رجوع",
            callback_data=f"{prefix}_settings"
        )
    )

    return keyboard


# =========================================================
# Adhkar Navigation
# =========================================================

def adhkar_navigation(category):
    """
    أزرار التنقل داخل قسم الأذكار.
    """

    keyboard = types.InlineKeyboardMarkup(row_width=2)

    keyboard.add(
        types.InlineKeyboardButton(
            "📿 ذكر آخر",
            callback_data=f"{category}_next"
        )
    )

    keyboard.add(
        types.InlineKeyboardButton(
            "🔙 القائمة الرئيسية",
            callback_data="main_menu"
        )
    )

    return keyboard


# =========================================================
# Dua Navigation
# =========================================================

def dua_navigation():
    """
    أزرار التنقل داخل قسم الأدعية.
    """

    keyboard = types.InlineKeyboardMarkup(row_width=2)

    keyboard.add(
        types.InlineKeyboardButton(
            "🤲 دعاء آخر",
            callback_data="duas_next"
        )
    )

    keyboard.add(
        types.InlineKeyboardButton(
            "🔙 القائمة الرئيسية",
            callback_data="main_menu"
        )
    )

    return keyboard


# =========================================================
# All Adhkar Menu
# =========================================================

def all_adhkar_menu():
    """
    قائمة جميع أقسام الأذكار.
    """

    keyboard = types.InlineKeyboardMarkup(row_width=2)

    keyboard.add(
        types.InlineKeyboardButton(
            "🌅 أذكار الصباح",
            callback_data="morning"
        ),
        types.InlineKeyboardButton(
            "🌙 أذكار المساء",
            callback_data="evening"
        )
    )

    keyboard.add(
        types.InlineKeyboardButton(
            "🕌 أذكار الصلاة",
            callback_data="prayer"
        ),
        types.InlineKeyboardButton(
            "😴 أذكار النوم",
            callback_data="sleep"
        )
    )

    keyboard.add(
        types.InlineKeyboardButton(
            "🤲 الأدعية",
            callback_data="duas"
        )
    )

    keyboard.add(
        types.InlineKeyboardButton(
            "🔙 القائمة الرئيسية",
            callback_data="main_menu"
        )
    )

    return keyboard