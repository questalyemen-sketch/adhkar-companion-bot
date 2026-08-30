from telebot import types


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
    """

    keyboard = types.InlineKeyboardMarkup(row_width=2)

    status = "🔴 إيقاف" if enabled else "🟢 تشغيل"

    keyboard.add(
        types.InlineKeyboardButton(
            f"{status}",
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
    """

    keyboard = types.InlineKeyboardMarkup(row_width=2)

    status = "🔴 إيقاف" if enabled else "🟢 تشغيل"

    keyboard.add(
        types.InlineKeyboardButton(
            f"{status}",
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
# Timezone Menu
# =========================================================

def timezone_menu():
    """
    قائمة المناطق الزمنية الشائعة.
    """

    keyboard = types.InlineKeyboardMarkup(row_width=2)

    timezones = [
        ("🇾🇪 اليمن", "tz_Asia/Aden"),
        ("🇪🇬 مصر", "tz_Africa/Cairo"),
        ("🇸🇦 السعودية", "tz_Asia/Riyadh"),
        ("🇦🇪 الإمارات", "tz_Asia/Dubai"),
        ("🇯🇴 الأردن", "tz_Asia/Amman"),
        ("🇮🇶 العراق", "tz_Asia/Baghdad"),
        ("🇰🇼 الكويت", "tz_Asia/Kuwait"),
        ("🇶🇦 قطر", "tz_Asia/Qatar"),
        ("🇧🇭 البحرين", "tz_Asia/Bahrain"),
        ("🇴🇲 عُمان", "tz_Asia/Muscat"),
        ("🇲🇦 المغرب", "tz_Africa/Casablanca"),
        ("🇩🇿 الجزائر", "tz_Africa/Algiers"),
        ("🇹🇳 تونس", "tz_Africa/Tunis"),
        ("🇬🇧 بريطانيا", "tz_Europe/London"),
        ("🇫🇷 فرنسا", "tz_Europe/Paris"),
        ("🇩🇪 ألمانيا", "tz_Europe/Berlin"),
        ("🇺🇸 أمريكا", "tz_America/New_York"),
        ("🇨🇦 كندا", "tz_America/Toronto"),
    ]

    for name, callback in timezones:
        keyboard.add(
            types.InlineKeyboardButton(
                name,
                callback_data=callback
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
    قائمة اختيار الوقت.

    prefix:
        morning
        evening
    """

    keyboard = types.InlineKeyboardMarkup(row_width=3)

    times = [
        "05:00",
        "05:30",
        "06:00",
        "06:30",
        "07:00",
        "07:30",
        "08:00",
        "17:00",
        "17:30",
        "18:00",
        "18:30",
        "19:00",
        "19:30",
        "20:00",
    ]

    for time in times:
        keyboard.add(
            types.InlineKeyboardButton(
                time,
                callback_data=f"{prefix}_set_{time}"
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