# =========================================================
# Adhkar Companion
# Telegram Bot Handlers
# =========================================================

from telebot import TeleBot, types

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
    timezone_menu,
    reminder_settings,
    morning_settings,
    evening_settings,
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
    حفظ كائن البوت لاستخدامه داخل الدوال.
    """

    global bot
    bot = bot_instance


# =========================================================
# Temporary User State
# =========================================================

user_states = {}


# =========================================================
# Helper Keyboards
# =========================================================

def timezone_setup_menu():
    """
    قائمة اختيار المنطقة الزمنية عند أول دخول.
    """

    return timezone_menu()


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


# =========================================================
# User Helpers
# =========================================================

def ensure_user(user):
    """
    التأكد من وجود المستخدم في قاعدة البيانات.
    """

    telegram_id = user.id

    existing_user = get_user(telegram_id)

    if existing_user is None:

        add_user(
            telegram_id=telegram_id,
            first_name=user.first_name or "",
            username=user.username or "",
        )

        existing_user = get_user(telegram_id)

    return existing_user


def ensure_callback_user(call):
    """
    التأكد من وجود المستخدم عند الضغط على زر.
    """

    return ensure_user(call.from_user)


def timezone_required(message):
    """
    التأكد من أن المستخدم اختار المنطقة الزمنية.

    إذا لم يخترها، يتم عرض شاشة الاختيار.
    """

    user = ensure_user(message.from_user)

    if not user["timezone"]:

        bot.send_message(
            message.chat.id,
            (
                "🌍 <b>اختر منطقتك الزمنية أولًا</b>\n\n"
                "حتى يتمكن البوت من إرسال أذكار الصباح "
                "والمساء تلقائيًا في الوقت الصحيح حسب توقيتك المحلي.\n\n"
                "⬇️ اختر منطقتك من القائمة:"
            ),
            parse_mode="HTML",
            reply_markup=timezone_setup_menu(),
        )

        return False

    return True


def callback_timezone_required(call):
    """
    التحقق من المنطقة الزمنية عند استخدام الأزرار.
    """

    user = ensure_callback_user(call)

    if not user["timezone"]:

        bot.answer_callback_query(
            call.id,
            "🌍 اختر منطقتك الزمنية أولًا.",
            show_alert=True
        )

        try:
            bot.edit_message_text(
                (
                    "🌍 <b>اختر منطقتك الزمنية أولًا</b>\n\n"
                    "حتى يتم إرسال التذكيرات في وقتها الصحيح."
                ),
                call.message.chat.id,
                call.message.message_id,
                parse_mode="HTML",
                reply_markup=timezone_setup_menu(),
            )

        except Exception:
            bot.send_message(
                call.message.chat.id,
                (
                    "🌍 <b>اختر منطقتك الزمنية أولًا</b>\n\n"
                    "حتى يتم إرسال التذكيرات في وقتها الصحيح."
                ),
                parse_mode="HTML",
                reply_markup=timezone_setup_menu(),
            )

        return False

    return True


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
                "📿 هذا البوت يساعدك على المحافظة على "
                "أذكار الصباح والمساء والأذكار والأدعية.\n\n"
                "⏰ سيقوم البوت بإرسال أذكار الصباح والمساء "
                "تلقائيًا حسب توقيتك المحلي.\n\n"
                "لذلك نحتاج أولًا إلى تحديد منطقتك الزمنية.\n\n"
                "🌍 <b>اختر منطقتك الزمنية:</b>"
            ),
            parse_mode="HTML",
            reply_markup=timezone_setup_menu(),
        )

        return

    timezone_name = user["timezone"]
    local_time = get_local_time(timezone_name)
    display_name = get_timezone_display_name(timezone_name)

    bot.send_message(
        message.chat.id,
        (
            f"📿 <b>مرحبًا بك مجددًا في {BOT_NAME}</b>\n\n"
            f"🌍 المنطقة الزمنية: <b>{display_name}</b>\n"
            f"🕐 الوقت المحلي: <b>{local_time}</b>\n\n"
            "اختر ما تريد:"
        ),
        parse_mode="HTML",
        reply_markup=main_menu(),
    )


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
        1
    )

    if not is_valid_timezone(timezone_name):

        bot.answer_callback_query(
            call.id,
            "❌ المنطقة الزمنية غير صالحة.",
            show_alert=True
        )

        return

    # التأكد من وجود المستخدم
    ensure_callback_user(call)

    # حفظ المنطقة الزمنية
    update_timezone(
        call.from_user.id,
        timezone_name
    )

    display_name = get_timezone_display_name(
        timezone_name
    )

    local_time = get_local_time(
        timezone_name
    )

    bot.answer_callback_query(
        call.id,
        "✅ تم حفظ منطقتك الزمنية."
    )

    text = (
        "✅ <b>تم ضبط المنطقة الزمنية بنجاح</b>\n\n"
        f"🌍 المنطقة: <b>{display_name}</b>\n"
        f"🕐 الوقت المحلي: <b>{local_time}</b>\n\n"
        "⏰ سيتم إرسال أذكار الصباح والمساء "
        "حسب توقيتك المحلي.\n\n"
        "يمكنك تغيير أوقات التذكير لاحقًا من الإعدادات."
    )

    try:

        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            parse_mode="HTML",
            reply_markup=main_menu(),
        )

    except Exception:

        bot.send_message(
            call.message.chat.id,
            text,
            parse_mode="HTML",
            reply_markup=main_menu(),
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

    text = (
        f"📿 <b>{BOT_NAME}</b>\n\n"
        "اختر ما تريد من القائمة:"
    )

    try:

        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            parse_mode="HTML",
            reply_markup=main_menu(),
        )

    except Exception:

        send_main_menu(
            call.message.chat.id
        )


# =========================================================
# Send Adhkar List
# =========================================================

def send_adhkar_list(
    call,
    title,
    adhkar,
    category
):
    """
    عرض قائمة الأذكار كاملة.
    """

    if not adhkar:

        bot.answer_callback_query(
            call.id,
            "❌ لا توجد أذكار متاحة حاليًا.",
            show_alert=True
        )

        return

    bot.answer_callback_query(call.id)

    message_parts = [
        f"📿 <b>{title}</b>",
        "",
    ]

    for index, item in enumerate(
        adhkar,
        start=1
    ):

        text = item.get(
            "text",
            ""
        )

        count = item.get(
            "count"
        )

        message_parts.append(
            f"<b>{index}.</b> {text}"
        )

        if count:

            message_parts.append(
                f"🔁 العدد: <b>{count}</b>"
            )

        message_parts.append("")

    message = "\n".join(
        message_parts
    )

    try:

        bot.edit_message_text(
            message,
            call.message.chat.id,
            call.message.message_id,
            parse_mode="HTML",
            reply_markup=adhkar_navigation(category),
        )

    except Exception:

        bot.send_message(
            call.message.chat.id,
            message,
            parse_mode="HTML",
            reply_markup=adhkar_navigation(category),
        )


# =========================================================
# Morning
# =========================================================

def handle_morning(call):

    if not callback_timezone_required(call):
        return

    send_adhkar_list(
        call,
        "🌅 أذكار الصباح",
        get_morning_adhkar(),
        "morning"
    )


# =========================================================
# Evening
# =========================================================

def handle_evening(call):

    if not callback_timezone_required(call):
        return

    send_adhkar_list(
        call,
        "🌙 أذكار المساء",
        get_evening_adhkar(),
        "evening"
    )


# =========================================================
# Sleep
# =========================================================

def handle_sleep(call):

    if not callback_timezone_required(call):
        return

    send_adhkar_list(
        call,
        "😴 أذكار النوم",
        get_sleep_adhkar(),
        "sleep"
    )


# =========================================================
# Prayer
# =========================================================

def handle_prayer(call):

    if not callback_timezone_required(call):
        return

    send_adhkar_list(
        call,
        "🕌 أذكار الصلاة",
        get_prayer_adhkar(),
        "prayer"
    )


# =========================================================
# Duas
# =========================================================

def handle_duas(call):

    if not callback_timezone_required(call):
        return

    duas = get_duas()

    if not duas:

        bot.answer_callback_query(
            call.id,
            "❌ لا توجد أدعية متاحة حاليًا.",
            show_alert=True
        )

        return

    bot.answer_callback_query(call.id)

    message_parts = [
        "🤲 <b>الأدعية</b>",
        "",
    ]

    for index, dua in enumerate(
        duas,
        start=1
    ):

        title = dua.get(
            "title",
            "دعاء"
        )

        text = dua.get(
            "text",
            ""
        )

        message_parts.append(
            f"<b>{index}. {title}</b>"
        )

        message_parts.append(text)
        message_parts.append("")

    message = "\n".join(
        message_parts
    )

    try:

        bot.edit_message_text(
            message,
            call.message.chat.id,
            call.message.message_id,
            parse_mode="HTML",
            reply_markup=dua_navigation(),
        )

    except Exception:

        bot.send_message(
            call.message.chat.id,
            message,
            parse_mode="HTML",
            reply_markup=dua_navigation(),
        )


# =========================================================
# All Adhkar
# =========================================================

def handle_all_adhkar(call):

    if not callback_timezone_required(call):
        return

    bot.answer_callback_query(call.id)

    text = (
        "📚 <b>جميع الأذكار</b>\n\n"
        "اختر القسم الذي تريد:"
    )

    try:

        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            parse_mode="HTML",
            reply_markup=all_adhkar_menu(),
        )

    except Exception:

        bot.send_message(
            call.message.chat.id,
            text,
            parse_mode="HTML",
            reply_markup=all_adhkar_menu(),
        )


# =========================================================
# Reminder Settings
# =========================================================

def handle_settings(call):

    if not callback_timezone_required(call):
        return

    user = get_user(
        call.from_user.id
    )

    if not user:
        bot.answer_callback_query(
            call.id,
            "❌ حدث خطأ في بيانات المستخدم.",
            show_alert=True
        )
        return

    bot.answer_callback_query(call.id)

    timezone_name = user["timezone"]

    display_name = get_timezone_display_name(
        timezone_name
    )

    local_time = get_local_time(
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
        f"🌍 المنطقة الزمنية: <b>{display_name}</b>\n"
        f"🕐 الوقت المحلي الآن: <b>{local_time}</b>\n\n"
        f"🌅 أذكار الصباح: {morning_status}\n"
        f"⏰ الوقت: <b>{user['morning_time']}</b>\n\n"
        f"🌙 أذكار المساء: {evening_status}\n"
        f"⏰ الوقت: <b>{user['evening_time']}</b>\n\n"
        "اختر الإعداد الذي تريد تغييره:"
    )

    try:

        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            parse_mode="HTML",
            reply_markup=reminder_settings(),
        )

    except Exception:

        bot.send_message(
            call.message.chat.id,
            text,
            parse_mode="HTML",
            reply_markup=reminder_settings(),
        )


# =========================================================
# Morning Settings
# =========================================================

def handle_morning_settings(call):

    if not callback_timezone_required(call):
        return

    user = get_user(
        call.from_user.id
    )

    if not user:
        return

    bot.answer_callback_query(call.id)

    status = (
        "🟢 مفعل"
        if user["morning_enabled"]
        else "🔴 متوقف"
    )

    text = (
        "🌅 <b>إعدادات أذكار الصباح</b>\n\n"
        f"الحالة: {status}\n"
        f"⏰ وقت الإرسال: <b>{user['morning_time']}</b>\n\n"
        "يمكنك تشغيل أو إيقاف التذكير "
        "أو تغيير وقت الإرسال."
    )

    try:

        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            parse_mode="HTML",
            reply_markup=morning_settings(
                bool(user["morning_enabled"])
            ),
        )

    except Exception:

        bot.send_message(
            call.message.chat.id,
            text,
            parse_mode="HTML",
            reply_markup=morning_settings(
                bool(user["morning_enabled"])
            ),
        )


# =========================================================
# Evening Settings
# =========================================================

def handle_evening_settings(call):

    if not callback_timezone_required(call):
        return

    user = get_user(
        call.from_user.id
    )

    if not user:
        return

    bot.answer_callback_query(call.id)

    status = (
        "🟢 مفعل"
        if user["evening_enabled"]
        else "🔴 متوقف"
    )

    text = (
        "🌙 <b>إعدادات أذكار المساء</b>\n\n"
        f"الحالة: {status}\n"
        f"⏰ وقت الإرسال: <b>{user['evening_time']}</b>\n\n"
        "يمكنك تشغيل أو إيقاف التذكير "
        "أو تغيير وقت الإرسال."
    )

    try:

        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            parse_mode="HTML",
            reply_markup=evening_settings(
                bool(user["evening_enabled"])
            ),
        )

    except Exception:

        bot.send_message(
            call.message.chat.id,
            text,
            parse_mode="HTML",
            reply_markup=evening_settings(
                bool(user["evening_enabled"])
            ),
        )


# =========================================================
# Toggle Morning
# =========================================================

def handle_toggle_morning(call):

    user = get_user(
        call.from_user.id
    )

    if not user or not user["timezone"]:

        bot.answer_callback_query(
            call.id,
            "🌍 اختر منطقتك الزمنية أولًا.",
            show_alert=True
        )

        return

    new_status = not bool(
        user["morning_enabled"]
    )

    update_morning_settings(
        call.from_user.id,
        enabled=new_status
    )

    bot.answer_callback_query(
        call.id,
        (
            "🟢 تم تشغيل تذكير الصباح."
            if new_status
            else "🔴 تم إيقاف تذكير الصباح."
        )
    )

    handle_morning_settings(call)


# =========================================================
# Toggle Evening
# =========================================================

def handle_toggle_evening(call):

    user = get_user(
        call.from_user.id
    )

    if not user or not user["timezone"]:

        bot.answer_callback_query(
            call.id,
            "🌍 اختر منطقتك الزمنية أولًا.",
            show_alert=True
        )

        return

    new_status = not bool(
        user["evening_enabled"]
    )

    update_evening_settings(
        call.from_user.id,
        enabled=new_status
    )

    bot.answer_callback_query(
        call.id,
        (
            "🟢 تم تشغيل تذكير المساء."
            if new_status
            else "🔴 تم إيقاف تذكير المساء."
        )
    )

    handle_evening_settings(call)


# =========================================================
# Morning Time
# =========================================================

def handle_morning_time(call):

    if not callback_timezone_required(call):
        return

    bot.answer_callback_query(call.id)

    text = (
        "🌅 <b>وقت أذكار الصباح</b>\n\n"
        "اختر الوقت الذي تريد وصول التذكير فيه:"
    )

    try:

        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            parse_mode="HTML",
            reply_markup=time_selection("morning"),
        )

    except Exception:

        bot.send_message(
            call.message.chat.id,
            text,
            parse_mode="HTML",
            reply_markup=time_selection("morning"),
        )


# =========================================================
# Evening Time
# =========================================================

def handle_evening_time(call):

    if not callback_timezone_required(call):
        return

    bot.answer_callback_query(call.id)

    text = (
        "🌙 <b>وقت أذكار المساء</b>\n\n"
        "اختر الوقت الذي تريد وصول التذكير فيه:"
    )

    try:

        bot.edit_message_text(
            text,
            call.message.chat.id,
            call.message.message_id,
            parse_mode="HTML",
            reply_markup=time_selection("evening"),
        )

    except Exception:

        bot.send_message(
            call.message.chat.id,
            text,
            parse_mode="HTML",
            reply_markup=time_selection("evening"),
        )


# =========================================================
# Set Morning Time
# =========================================================

def handle_set_morning_time(call):

    # keyboards.py:
    # morning_set_06:00

    time_value = call.data.replace(
        "morning_set_",
        "",
        1
    )

    if not is_valid_time_value(time_value):

        bot.answer_callback_query(
            call.id,
            "❌ وقت غير صالح.",
            show_alert=True
        )

        return

    update_morning_settings(
        call.from_user.id,
        time=time_value
    )

    bot.answer_callback_query(
        call.id,
        f"✅ تم ضبط وقت الصباح على {time_value}"
    )

    handle_morning_settings(call)


# =========================================================
# Set Evening Time
# =========================================================

def handle_set_evening_time(call):

    # keyboards.py:
    # evening_set_18:00

    time_value = call.data.replace(
        "evening_set_",
        "",
        1
    )

    if not is_valid_time_value(time_value):

        bot.answer_callback_query(
            call.id,
            "❌ وقت غير صالح.",
            show_alert=True
        )

        return

    update_evening_settings(
        call.from_user.id,
        time=time_value
    )

    bot.answer_callback_query(
        call.id,
        f"✅ تم ضبط وقت المساء على {time_value}"
    )

    handle_evening_settings(call)


# =========================================================
# Validate Time
# =========================================================

def is_valid_time_value(time_value):
    """
    التحقق من صيغة HH:MM.
    """

    try:

        hours, minutes = time_value.split(":")

        hours = int(hours)
        minutes = int(minutes)

        return (
            0 <= hours <= 23
            and 0 <= minutes <= 59
        )

    except (
        ValueError,
        AttributeError
    ):

        return False


# =========================================================
# Navigation: Next Adhkar
# =========================================================

def handle_adhkar_next(call):
    """
    زر ذكر آخر.

    في النسخة الحالية نعيد عرض القائمة نفسها.
    ويمكن لاحقًا تطويره إلى نظام ذكر واحد
    مع عداد وتقدم المستخدم.
    """

    category = call.data.replace(
        "_next",
        "",
        1
    )

    if category == "morning":
        handle_morning(call)

    elif category == "evening":
        handle_evening(call)

    elif category == "sleep":
        handle_sleep(call)

    elif category == "prayer":
        handle_prayer(call)

    else:

        bot.answer_callback_query(
            call.id,
            "❌ قسم غير معروف.",
            show_alert=True
        )


# =========================================================
# Next Dua
# =========================================================

def handle_dua_next(call):
    """
    عرض الأدعية مرة أخرى.
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

    # -----------------------------------------------------
    # /start
    # -----------------------------------------------------

    @bot_instance.message_handler(
        commands=["start"]
    )
    def start_handler(message):

        handle_start(message)

    # -----------------------------------------------------
    # Timezone
    # -----------------------------------------------------

    @bot_instance.callback_query_handler(
        func=lambda call:
        call.data.startswith("tz_")
    )
    def timezone_callback(call):

        handle_timezone_callback(call)

    # -----------------------------------------------------
    # Main Menu
    # -----------------------------------------------------

    @bot_instance.callback_query_handler(
        func=lambda call:
        call.data == "main_menu"
    )
    def main_menu_callback(call):

        handle_main_menu(call)

    # -----------------------------------------------------
    # Morning
    # -----------------------------------------------------

    @bot_instance.callback_query_handler(
        func=lambda call:
        call.data == "morning"
    )
    def morning_callback(call):

        handle_morning(call)

    # -----------------------------------------------------
    # Evening
    # -----------------------------------------------------

    @bot_instance.callback_query_handler(
        func=lambda call:
        call.data == "evening"
    )
    def evening_callback(call):

        handle_evening(call)

    # -----------------------------------------------------
    # Sleep
    # -----------------------------------------------------

    @bot_instance.callback_query_handler(
        func=lambda call:
        call.data == "sleep"
    )
    def sleep_callback(call):

        handle_sleep(call)

    # -----------------------------------------------------
    # Prayer
    # -----------------------------------------------------

    @bot_instance.callback_query_handler(
        func=lambda call:
        call.data == "prayer"
    )
    def prayer_callback(call):

        handle_prayer(call)

    # -----------------------------------------------------
    # Duas
    # -----------------------------------------------------

    @bot_instance.callback_query_handler(
        func=lambda call:
        call.data == "duas"
    )
    def duas_callback(call):

        handle_duas(call)

    # -----------------------------------------------------
    # All Adhkar
    # -----------------------------------------------------

    @bot_instance.callback_query_handler(
        func=lambda call:
        call.data == "all_adhkar"
    )
    def all_adhkar_callback(call):

        handle_all_adhkar(call)

    # -----------------------------------------------------
    # Settings
    # -----------------------------------------------------

    @bot_instance.callback_query_handler(
        func=lambda call:
        call.data == "settings"
    )
    def settings_callback(call):

        handle_settings(call)

    # -----------------------------------------------------
    # Morning Settings
    # -----------------------------------------------------

    @bot_instance.callback_query_handler(
        func=lambda call:
        call.data == "morning_settings"
    )
    def morning_settings_callback(call):

        handle_morning_settings(call)

    # -----------------------------------------------------
    # Evening Settings
    # -----------------------------------------------------

    @bot_instance.callback_query_handler(
        func=lambda call:
        call.data == "evening_settings"
    )
    def evening_settings_callback(call):

        handle_evening_settings(call)

    # -----------------------------------------------------
    # Toggle Morning
    # -----------------------------------------------------

    @bot_instance.callback_query_handler(
        func=lambda call:
        call.data == "toggle_morning"
    )
    def toggle_morning_callback(call):

        handle_toggle_morning(call)

    # -----------------------------------------------------
    # Toggle Evening
    # -----------------------------------------------------

    @bot_instance.callback_query_handler(
        func=lambda call:
        call.data == "toggle_evening"
    )
    def toggle_evening_callback(call):

        handle_toggle_evening(call)

    # -----------------------------------------------------
    # Morning Time
    # -----------------------------------------------------

    @bot_instance.callback_query_handler(
        func=lambda call:
        call.data == "morning_time"
    )
    def morning_time_callback(call):

        handle_morning_time(call)

    # -----------------------------------------------------
    # Evening Time
    # -----------------------------------------------------

    @bot_instance.callback_query_handler(
        func=lambda call:
        call.data == "evening_time"
    )
    def evening_time_callback(call):

        handle_evening_time(call)

    # -----------------------------------------------------
    # Set Morning Time
    # -----------------------------------------------------

    @bot_instance.callback_query_handler(
        func=lambda call:
        call.data.startswith("morning_set_")
    )
    def set_morning_time_callback(call):

        handle_set_morning_time(call)

    # -----------------------------------------------------
    # Set Evening Time
    # -----------------------------------------------------

    @bot_instance.callback_query_handler(
        func=lambda call:
        call.data.startswith("evening_set_")
    )
    def set_evening_time_callback(call):

        handle_set_evening_time(call)

    # -----------------------------------------------------
    # Next Adhkar
    # -----------------------------------------------------

    @bot_instance.callback_query_handler(
        func=lambda call:
        call.data.endswith("_next")
        and call.data.split("_")[0]
        in (
            "morning",
            "evening",
            "sleep",
            "prayer",
        )
    )
    def next_adhkar_callback(call):

        handle_adhkar_next(call)

    # -----------------------------------------------------
    # Next Dua
    # -----------------------------------------------------

    @bot_instance.callback_query_handler(
        func=lambda call:
        call.data == "duas_next"
    )
    def next_dua_callback(call):

        handle_dua_next(call)

    print(
        "[HANDLERS] All handlers registered successfully."
    )