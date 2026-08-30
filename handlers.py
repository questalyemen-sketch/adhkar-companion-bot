from telebot import TeleBot
from telebot import types

from config import BOT_NAME

from database import (
    add_user,
    get_user,
    has_timezone,
    update_timezone,
    update_morning_settings,
    update_evening_settings,
)

from keyboards import (
    main_menu,
    back_button,
    reminder_settings,
    morning_settings,
    evening_settings,
    timezone_menu,
    time_selection,
    adhkar_navigation,
    dua_navigation,
)

from adhkar import (
    get_morning_adhkar,
    get_evening_adhkar,
    get_sleep_adhkar,
    get_prayer_adhkar,
    get_duas,
)

from timezone_utils import (
    is_valid_timezone,
    get_timezone_display_name,
    get_local_time,
)


# =========================================================
# Bot Reference
# =========================================================

bot = None


def set_bot(bot_instance):
    """
    حفظ كائن البوت لاستخدامه داخل handlers.
    """
    global bot
    bot = bot_instance


# =========================================================
# Temporary User State
# =========================================================

user_states = {}


# =========================================================
# Helpers
# =========================================================

def ensure_user(user):
    """
    التأكد من وجود المستخدم في قاعدة البيانات.
    """

    existing_user = get_user(user.id)

    if existing_user is None:
        add_user(
            telegram_id=user.id,
            first_name=user.first_name or "",
            username=user.username or "",
        )

        existing_user = get_user(user.id)

    return existing_user


def send_main_menu(chat_id):
    """
    إرسال القائمة الرئيسية.
    """

    bot.send_message(
        chat_id,
        (
            f"📿 <b>{BOT_NAME}</b>\n\n"
            "اختر ما تريد من القائمة:"
        ),
        parse_mode="HTML",
        reply_markup=main_menu(),
    )


def send_timezone_setup(chat_id):
    """
    إرسال شاشة اختيار المنطقة الزمنية لأول مرة.
    """

    keyboard = timezone_menu()

    bot.send_message(
        chat_id,
        (
            "🌍 <b>اختر منطقتك الزمنية</b>\n\n"
            "حتى يتمكن البوت من إرسال أذكار الصباح "
            "والمساء تلقائيًا في الوقت الصحيح حسب توقيتك المحلي.\n\n"
            "⚠️ يجب اختيار المنطقة الزمنية قبل تفعيل التذكيرات."
        ),
        parse_mode="HTML",
        reply_markup=keyboard,
    )


def timezone_required(message):
    """
    التأكد من أن المستخدم اختار المنطقة الزمنية.
    """

    user = ensure_user(message.from_user)

    if not user["timezone"]:
        send_timezone_setup(message.chat.id)
        return False

    return True


def callback_timezone_required(call):
    """
    التحقق من المنطقة الزمنية في Callback.
    """

    user = get_user(call.from_user.id)

    if not user:
        add_user(
            telegram_id=call.from_user.id,
            first_name=call.from_user.first_name or "",
            username=call.from_user.username or "",
        )

        user = get_user(call.from_user.id)

    if not user or not user["timezone"]:
        bot.answer_callback_query(
            call.id,
            "🌍 اختر منطقتك الزمنية أولًا.",
            show_alert=True,
        )

        try:
            bot.edit_message_text(
                (
                    "🌍 <b>اختر منطقتك الزمنية أولًا</b>\n\n"
                    "حتى يتمكن البوت من إرسال التذكيرات "
                    "في الوقت الصحيح."
                ),
                call.message.chat.id,
                call.message.message_id,
                parse_mode="HTML",
                reply_markup=timezone_menu(),
            )
        except Exception:
            bot.send_message(
                call.message.chat.id,
                (
                    "🌍 <b>اختر منطقتك الزمنية أولًا</b>"
                ),
                parse_mode="HTML",
                reply_markup=timezone_menu(),
            )

        return False

    return True


def safe_edit_message(
    call,
    text,
    reply_markup=None,
):
    """
    تعديل رسالة Callback بأمان.
    """

    try:
        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            parse_mode="HTML",
            reply_markup=reply_markup,
        )
    except Exception:
        bot.send_message(
            call.message.chat.id,
            text,
            parse_mode="HTML",
            reply_markup=reply_markup,
        )


# =========================================================
# Timezone Menu
# =========================================================

def send_timezone_menu_callback(call):
    """
    عرض قائمة المناطق الزمنية.
    """

    bot.answer_callback_query(call.id)

    safe_edit_message(
        call,
        (
            "🌍 <b>المنطقة الزمنية</b>\n\n"
            "اختر المنطقة الزمنية الخاصة بك:"
        ),
        timezone_menu(),
    )


# =========================================================
# /start
# =========================================================

def handle_start(message):
    """
    معالجة أمر /start.
    """

    user = ensure_user(message.from_user)

    if not user["timezone"]:
        bot.send_message(
            message.chat.id,
            (
                f"🌙 <b>أهلًا بك في {BOT_NAME}</b>\n\n"
                "📿 ستجد هنا أذكار الصباح والمساء "
                "والأدعية وأذكار الصلاة والنوم.\n\n"
                "⏰ يستطيع البوت إرسال أذكار الصباح والمساء "
                "تلقائيًا حسب توقيتك المحلي.\n\n"
                "🌍 <b>لكن قبل ذلك اختر منطقتك الزمنية:</b>"
            ),
            parse_mode="HTML",
            reply_markup=timezone_menu(),
        )

        return

    send_main_menu(message.chat.id)


# =========================================================
# Timezone Callback
# =========================================================

def handle_timezone_callback(call):
    """
    معالجة اختيار المنطقة الزمنية.

    keyboards.py يستخدم:
        tz_Asia/Aden
        tz_Africa/Cairo
        ...
    """

    timezone_name = call.data.replace(
        "tz_",
        "",
        1,
    )

    if not is_valid_timezone(timezone_name):
        bot.answer_callback_query(
            call.id,
            "❌ المنطقة الزمنية غير صالحة.",
            show_alert=True,
        )
        return

    update_timezone(
        call.from_user.id,
        timezone_name,
    )

    display_name = get_timezone_display_name(
        timezone_name
    )

    local_time = get_local_time(
        timezone_name
    )

    bot.answer_callback_query(
        call.id,
        "✅ تم حفظ منطقتك الزمنية.",
    )

    safe_edit_message(
        call,
        (
            "✅ <b>تم ضبط المنطقة الزمنية بنجاح</b>\n\n"
            f"🌍 المنطقة: <b>{display_name}</b>\n"
            f"🕐 الوقت المحلي الآن: <b>{local_time}</b>\n\n"
            "⏰ أصبحت التذكيرات تعمل حسب توقيتك المحلي.\n\n"
            "يمكنك الآن استخدام جميع أقسام البوت."
        ),
        main_menu(),
    )


# =========================================================
# Main Menu
# =========================================================

def handle_main_menu(call):
    """
    العودة إلى القائمة الرئيسية.
    """

    if not callback_timezone_required(call):
        return

    bot.answer_callback_query(call.id)

    safe_edit_message(
        call,
        (
            f"📿 <b>{BOT_NAME}</b>\n\n"
            "اختر ما تريد من القائمة:"
        ),
        main_menu(),
    )


# =========================================================
# Morning Adhkar
# =========================================================

def handle_morning(call):
    """
    عرض أذكار الصباح.
    """

    if not callback_timezone_required(call):
        return

    adhkar = get_morning_adhkar()

    send_adhkar_list(
        call,
        "🌅 أذكار الصباح",
        adhkar,
        "morning",
    )


# =========================================================
# Evening Adhkar
# =========================================================

def handle_evening(call):
    """
    عرض أذكار المساء.
    """

    if not callback_timezone_required(call):
        return

    adhkar = get_evening_adhkar()

    send_adhkar_list(
        call,
        "🌙 أذكار المساء",
        adhkar,
        "evening",
    )


# =========================================================
# Sleep Adhkar
# =========================================================

def handle_sleep(call):
    """
    عرض أذكار النوم.
    """

    if not callback_timezone_required(call):
        return

    adhkar = get_sleep_adhkar()

    send_adhkar_list(
        call,
        "😴 أذكار النوم",
        adhkar,
        "sleep",
    )


# =========================================================
# Prayer Adhkar
# =========================================================

def handle_prayer(call):
    """
    عرض أذكار الصلاة.
    """

    if not callback_timezone_required(call):
        return

    adhkar = get_prayer_adhkar()

    send_adhkar_list(
        call,
        "🕌 أذكار الصلاة",
        adhkar,
        "prayer",
    )


# =========================================================
# Send Adhkar List
# =========================================================

def send_adhkar_list(
    call,
    title,
    adhkar,
    category,
):
    """
    إرسال قائمة الأذكار.
    """

    if not adhkar:
        bot.answer_callback_query(
            call.id,
            "لا توجد أذكار متاحة حاليًا.",
            show_alert=True,
        )
        return

    bot.answer_callback_query(call.id)

    message_parts = [
        f"📿 <b>{title}</b>",
        "",
    ]

    for index, item in enumerate(
        adhkar,
        start=1,
    ):
        text = item.get("text", "")
        count = item.get("count")

        message_parts.append(
            f"<b>{index}.</b> {text}"
        )

        if count:
            message_parts.append(
                f"🔁 العدد: <b>{count}</b>"
            )

        message_parts.append("")

    message = "\n".join(message_parts)

    safe_edit_message(
        call,
        message,
        adhkar_navigation(category),
    )


# =========================================================
# Duas
# =========================================================

def handle_duas(call):
    """
    عرض الأدعية.
    """

    if not callback_timezone_required(call):
        return

    duas = get_duas()

    bot.answer_callback_query(call.id)

    message_parts = [
        "🤲 <b>الأدعية</b>",
        "",
    ]

    for index, dua in enumerate(
        duas,
        start=1,
    ):
        title = dua.get(
            "title",
            "دعاء",
        )

        text = dua.get(
            "text",
            "",
        )

        message_parts.append(
            f"<b>{index}. {title}</b>"
        )

        message_parts.append(text)
        message_parts.append("")

    message = "\n".join(message_parts)

    safe_edit_message(
        call,
        message,
        dua_navigation(),
    )


# =========================================================
# All Adhkar
# =========================================================

def handle_all_adhkar(call):
    """
    عرض جميع أقسام الأذكار.

    لا نعتمد على all_adhkar_menu()
    لأنها غير موجودة في keyboards.py الحالي.
    """

    if not callback_timezone_required(call):
        return

    bot.answer_callback_query(call.id)

    keyboard = types.InlineKeyboardMarkup(
        row_width=2
    )

    keyboard.add(
        types.InlineKeyboardButton(
            "🌅 أذكار الصباح",
            callback_data="morning",
        ),
        types.InlineKeyboardButton(
            "🌙 أذكار المساء",
            callback_data="evening",
        ),
    )

    keyboard.add(
        types.InlineKeyboardButton(
            "🕌 أذكار الصلاة",
            callback_data="prayer",
        ),
        types.InlineKeyboardButton(
            "😴 أذكار النوم",
            callback_data="sleep",
        ),
    )

    keyboard.add(
        types.InlineKeyboardButton(
            "🤲 الأدعية",
            callback_data="duas",
        ),
    )

    keyboard.add(
        types.InlineKeyboardButton(
            "🔙 القائمة الرئيسية",
            callback_data="main_menu",
        ),
    )

    safe_edit_message(
        call,
        (
            "📚 <b>جميع الأذكار</b>\n\n"
            "اختر القسم الذي تريد:"
        ),
        keyboard,
    )


# =========================================================
# Reminder Settings
# =========================================================

def handle_settings(call):
    """
    عرض إعدادات التذكيرات.
    """

    if not callback_timezone_required(call):
        return

    bot.answer_callback_query(call.id)

    user = get_user(call.from_user.id)

    timezone_name = user["timezone"]

    display_name = get_timezone_display_name(
        timezone_name
    )

    morning_status = (
        "🟢 مفعل"
        if user["morning_enabled"]
        else "🔴 متوقف"
    )

    evening_status = (
        "🟢 مفعل"
        if user["evening_enabled"]
        else "🔴 متوقف"
    )

    text = (
        "⏰ <b>إعدادات التذكير</b>\n\n"
        f"🌍 المنطقة الزمنية: <b>{display_name}</b>\n\n"
        f"🌅 أذكار الصباح: {morning_status}\n"
        f"⏰ الوقت: <b>{user['morning_time']}</b>\n\n"
        f"🌙 أذكار المساء: {evening_status}\n"
        f"⏰ الوقت: <b>{user['evening_time']}</b>\n\n"
        "اختر الإعداد الذي تريد تغييره:"
    )

    safe_edit_message(
        call,
        text,
        reminder_settings(),
    )


# =========================================================
# Morning Settings
# =========================================================

def handle_morning_settings(call):
    """
    إعدادات أذكار الصباح.
    """

    if not callback_timezone_required(call):
        return

    user = get_user(call.from_user.id)

    bot.answer_callback_query(call.id)

    text = (
        "🌅 <b>إعدادات أذكار الصباح</b>\n\n"
        f"الحالة: "
        f"{'🟢 مفعل' if user['morning_enabled'] else '🔴 متوقف'}\n"
        f"⏰ الوقت: <b>{user['morning_time']}</b>"
    )

    safe_edit_message(
        call,
        text,
        morning_settings(
            bool(user["morning_enabled"])
        ),
    )


# =========================================================
# Evening Settings
# =========================================================

def handle_evening_settings(call):
    """
    إعدادات أذكار المساء.
    """

    if not callback_timezone_required(call):
        return

    user = get_user(call.from_user.id)

    bot.answer_callback_query(call.id)

    text = (
        "🌙 <b>إعدادات أذكار المساء</b>\n\n"
        f"الحالة: "
        f"{'🟢 مفعل' if user['evening_enabled'] else '🔴 متوقف'}\n"
        f"⏰ الوقت: <b>{user['evening_time']}</b>"
    )

    safe_edit_message(
        call,
        text,
        evening_settings(
            bool(user["evening_enabled"])
        ),
    )


# =========================================================
# Toggle Morning
# =========================================================

def handle_toggle_morning(call):
    """
    تشغيل / إيقاف تذكير الصباح.
    """

    user = get_user(call.from_user.id)

    if not user or not user["timezone"]:
        bot.answer_callback_query(
            call.id,
            "🌍 اختر منطقتك الزمنية أولًا.",
            show_alert=True,
        )
        return

    new_status = not bool(
        user["morning_enabled"]
    )

    update_morning_settings(
        call.from_user.id,
        enabled=new_status,
    )

    bot.answer_callback_query(
        call.id,
        "✅ تم تحديث إعدادات الصباح.",
    )

    handle_morning_settings(call)


# =========================================================
# Toggle Evening
# =========================================================

def handle_toggle_evening(call):
    """
    تشغيل / إيقاف تذكير المساء.
    """

    user = get_user(call.from_user.id)

    if not user or not user["timezone"]:
        bot.answer_callback_query(
            call.id,
            "🌍 اختر منطقتك الزمنية أولًا.",
            show_alert=True,
        )
        return

    new_status = not bool(
        user["evening_enabled"]
    )

    update_evening_settings(
        call.from_user.id,
        enabled=new_status,
    )

    bot.answer_callback_query(
        call.id,
        "✅ تم تحديث إعدادات المساء.",
    )

    handle_evening_settings(call)


# =========================================================
# Timezone Settings
# =========================================================

def handle_timezone_settings(call):
    """
    تغيير المنطقة الزمنية من الإعدادات.
    """

    bot.answer_callback_query(call.id)

    safe_edit_message(
        call,
        (
            "🌍 <b>تغيير المنطقة الزمنية</b>\n\n"
            "اختر منطقتك الزمنية الجديدة:"
        ),
        timezone_menu(),
    )


# =========================================================
# Morning Time
# =========================================================

def handle_morning_time(call):
    """
    عرض أوقات أذكار الصباح.
    """

    if not callback_timezone_required(call):
        return

    bot.answer_callback_query(call.id)

    safe_edit_message(
        call,
        (
            "🌅 <b>وقت أذكار الصباح</b>\n\n"
            "اختر الوقت الذي تريد وصول التذكير فيه:"
        ),
        time_selection("morning"),
    )


# =========================================================
# Evening Time
# =========================================================

def handle_evening_time(call):
    """
    عرض أوقات أذكار المساء.
    """

    if not callback_timezone_required(call):
        return

    bot.answer_callback_query(call.id)

    safe_edit_message(
        call,
        (
            "🌙 <b>وقت أذكار المساء</b>\n\n"
            "اختر الوقت الذي تريد وصول التذكير فيه:"
        ),
        time_selection("evening"),
    )


# =========================================================
# Set Morning Time
# =========================================================

def handle_set_morning_time(call):
    """
    حفظ وقت أذكار الصباح.

    keyboards.py يستخدم:
        morning_set_06:00
    """

    time_value = call.data.replace(
        "morning_set_",
        "",
        1,
    )

    if not is_valid_time_format(time_value):
        bot.answer_callback_query(
            call.id,
            "❌ الوقت غير صالح.",
            show_alert=True,
        )
        return

    update_morning_settings(
        call.from_user.id,
        time=time_value,
    )

    bot.answer_callback_query(
        call.id,
        f"✅ تم ضبط وقت الصباح على {time_value}",
    )

    handle_morning_settings(call)


# =========================================================
# Set Evening Time
# =========================================================

def handle_set_evening_time(call):
    """
    حفظ وقت أذكار المساء.

    keyboards.py يستخدم:
        evening_set_18:00
    """

    time_value = call.data.replace(
        "evening_set_",
        "",
        1,
    )

    if not is_valid_time_format(time_value):
        bot.answer_callback_query(
            call.id,
            "❌ الوقت غير صالح.",
            show_alert=True,
        )
        return

    update_evening_settings(
        call.from_user.id,
        time=time_value,
    )

    bot.answer_callback_query(
        call.id,
        f"✅ تم ضبط وقت المساء على {time_value}",
    )

    handle_evening_settings(call)


# =========================================================
# Time Validation
# =========================================================

def is_valid_time_format(value):
    """
    التحقق من أن الوقت بصيغة HH:MM.
    """

    if not value:
        return False

    try:
        hour, minute = value.split(":")

        hour = int(hour)
        minute = int(minute)

        return (
            0 <= hour <= 23
            and 0 <= minute <= 59
        )

    except (
        ValueError,
        AttributeError,
    ):
        return False


# =========================================================
# Adhkar Next
# =========================================================

def handle_adhkar_next(call):
    """
    زر ذكر آخر.

    حاليًا يعيد عرض القائمة نفسها.
    يمكن تطويره لاحقًا ليعرض ذكرًا واحدًا
    في كل ضغطة مع عداد للتقدم.
    """

    category = call.data.replace(
        "_next",
        "",
        1,
    )

    categories = {
        "morning": (
            "🌅 أذكار الصباح",
            get_morning_adhkar(),
        ),
        "evening": (
            "🌙 أذكار المساء",
            get_evening_adhkar(),
        ),
        "sleep": (
            "😴 أذكار النوم",
            get_sleep_adhkar(),
        ),
        "prayer": (
            "🕌 أذكار الصلاة",
            get_prayer_adhkar(),
        ),
    }

    if category not in categories:
        bot.answer_callback_query(
            call.id,
            "❌ القسم غير موجود.",
            show_alert=True,
        )
        return

    title, adhkar = categories[category]

    send_adhkar_list(
        call,
        title,
        adhkar,
        category,
    )


# =========================================================
# Dua Next
# =========================================================

def handle_dua_next(call):
    """
    زر دعاء آخر.
    """

    handle_duas(call)


# =========================================================
# Register Handlers
# =========================================================

def register_handlers(bot_instance: TeleBot):
    """
    تسجيل جميع أوامر ورسائل وأزرار البوت.
    """

    set_bot(bot_instance)

    # =====================================================
    # /start
    # =====================================================

    @bot_instance.message_handler(
        commands=["start"]
    )
    def start_handler(message):
        handle_start(message)

    # =====================================================
    # Timezone
    # =====================================================

    @bot_instance.callback_query_handler(
        func=lambda call: call.data.startswith("tz_")
    )
    def timezone_callback(call):
        handle_timezone_callback(call)

    # =====================================================
    # Main Menu
    # =====================================================

    @bot_instance.callback_query_handler(
        func=lambda call: call.data == "main_menu"
    )
    def main_menu_callback(call):
        handle_main_menu(call)

    # =====================================================
    # Adhkar
    # =====================================================

    @bot_instance.callback_query_handler(
        func=lambda call: call.data == "morning"
    )
    def morning_callback(call):
        handle_morning(call)

    @bot_instance.callback_query_handler(
        func=lambda call: call.data == "evening"
    )
    def evening_callback(call):
        handle_evening(call)

    @bot_instance.callback_query_handler(
        func=lambda call: call.data == "sleep"
    )
    def sleep_callback(call):
        handle_sleep(call)

    @bot_instance.callback_query_handler(
        func=lambda call: call.data == "prayer"
    )
    def prayer_callback(call):
        handle_prayer(call)

    # =====================================================
    # Duas
    # =====================================================

    @bot_instance.callback_query_handler(
        func=lambda call: call.data == "duas"
    )
    def duas_callback(call):
        handle_duas(call)

    # =====================================================
    # All Adhkar
    # =====================================================

    @bot_instance.callback_query_handler(
        func=lambda call: call.data == "all_adhkar"
    )
    def all_adhkar_callback(call):
        handle_all_adhkar(call)

    # =====================================================
    # Settings
    # =====================================================

    @bot_instance.callback_query_handler(
        func=lambda call: call.data == "settings"
    )
    def settings_callback(call):
        handle_settings(call)

    @bot_instance.callback_query_handler(
        func=lambda call: call.data == "timezone"
    )
    def timezone_settings_callback(call):
        handle_timezone_settings(call)

    @bot_instance.callback_query_handler(
        func=lambda call: call.data == "morning_settings"
    )
    def morning_settings_callback(call):
        handle_morning_settings(call)

    @bot_instance.callback_query_handler(
        func=lambda call: call.data == "evening_settings"
    )
    def evening_settings_callback(call):
        handle_evening_settings(call)

    # =====================================================
    # Toggle
    # =====================================================

    @bot_instance.callback_query_handler(
        func=lambda call: call.data == "toggle_morning"
    )
    def toggle_morning_callback(call):
        handle_toggle_morning(call)

    @bot_instance.callback_query_handler(
        func=lambda call: call.data == "toggle_evening"
    )
    def toggle_evening_callback(call):
        handle_toggle_evening(call)

    # =====================================================
    # Morning Time
    # =====================================================

    @bot_instance.callback_query_handler(
        func=lambda call: call.data == "morning_time"
    )
    def morning_time_callback(call):
        handle_morning_time(call)

    @bot_instance.callback_query_handler(
        func=lambda call: call.data.startswith("morning_set_")
    )
    def set_morning_time_callback(call):
        handle_set_morning_time(call)

    # =====================================================
    # Evening Time
    # =====================================================

    @bot_instance.callback_query_handler(
        func=lambda call: call.data == "evening_time"
    )
    def evening_time_callback(call):
        handle_evening_time(call)

    @bot_instance.callback_query_handler(
        func=lambda call: call.data.startswith("evening_set_")
    )
    def set_evening_time_callback(call):
        handle_set_evening_time(call)

    # =====================================================
    # Adhkar Navigation
    # =====================================================

    @bot_instance.callback_query_handler(
        func=lambda call: call.data.endswith("_next")
        and call.data.split("_")[0]
        in (
            "morning",
            "evening",
            "sleep",
            "prayer",
        )
    )
    def adhkar_next_callback(call):
        handle_adhkar_next(call)

    # =====================================================
    # Dua Navigation
    # =====================================================

    @bot_instance.callback_query_handler(
        func=lambda call: call.data == "duas_next"
    )
    def dua_next_callback(call):
        handle_dua_next(call)

    print(
        "[HANDLERS] All handlers registered successfully."
    )