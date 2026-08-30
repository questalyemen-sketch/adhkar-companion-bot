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
    timezone_setup_menu,
    timezone_menu,
    reminder_settings,
    morning_settings,
    evening_settings,
    time_selection,
    adhkar_navigation,
    dua_navigation,
    all_adhkar_menu,
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

# تخزين حالة المستخدم مؤقتًا في الذاكرة.
#
# لاحقًا يمكن نقل الحالات التي تحتاج حفظًا دائمًا
# إلى قاعدة البيانات.

user_states = {}


# =========================================================
# Helpers
# =========================================================

def get_user_id(message):
    """
    الحصول على Telegram ID للمستخدم.
    """

    return message.from_user.id


def ensure_user(message):
    """
    التأكد من وجود المستخدم في قاعدة البيانات.
    """

    user = get_user(message.from_user.id)

    if user is None:
        add_user(
            telegram_id=message.from_user.id,
            first_name=message.from_user.first_name or "",
            username=message.from_user.username or "",
        )

        user = get_user(message.from_user.id)

    return user


def timezone_required(message):
    """
    التحقق من أن المستخدم اختار المنطقة الزمنية.

    إذا لم يخترها، تظهر له شاشة الاختيار.
    """

    user = ensure_user(message)

    if not user["timezone"]:
        bot.send_message(
            message.chat.id,
            (
                "🌍 <b>اختر منطقتك الزمنية أولًا</b>\n\n"
                "حتى يتمكن البوت من إرسال أذكار الصباح "
                "والمساء في الوقت الصحيح حسب بلدك."
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

    user = ensure_user(message)

    if not user["timezone"]:
        bot.send_message(
            message.chat.id,
            (
                f"🌙 <b>أهلًا بك في {BOT_NAME}</b>\n\n"
                "📿 هنا يمكنك الوصول إلى أذكار الصباح "
                "والمساء والأدعية والأذكار المختلفة.\n\n"
                "⏰ ولأن البوت سيرسل لك الأذكار تلقائيًا، "
                "نحتاج أولًا إلى معرفة منطقتك الزمنية.\n\n"
                "🌍 <b>اختر منطقتك الزمنية:</b>"
            ),
            parse_mode="HTML",
            reply_markup=timezone_setup_menu(),
        )

        return

    send_main_menu(message.chat.id)


# =========================================================
# Timezone Callback
# =========================================================

def handle_timezone_callback(call):
    """
    معالجة اختيار المنطقة الزمنية.
    """

    timezone_name = call.data.replace(
        "set_timezone:",
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

    try:
        bot.edit_message_text(
            (
                "✅ <b>تم ضبط المنطقة الزمنية بنجاح</b>\n\n"
                f"🌍 المنطقة: <b>{display_name}</b>\n"
                f"🕐 الوقت الحالي: <b>{local_time}</b>\n\n"
                "الآن أصبحت التذكيرات تعمل حسب توقيتك المحلي."
            ),
            call.message.chat.id,
            call.message.message_id,
            parse_mode="HTML",
        )

    except Exception:
        bot.send_message(
            call.message.chat.id,
            (
                "✅ <b>تم ضبط المنطقة الزمنية بنجاح.</b>\n\n"
                f"🌍 المنطقة: <b>{display_name}</b>\n"
                f"🕐 الوقت الحالي: <b>{local_time}</b>"
            ),
            parse_mode="HTML",
        )

    send_main_menu(call.message.chat.id)


# =========================================================
# Main Menu Callback
# =========================================================

def handle_main_menu(call):
    """
    العودة إلى القائمة الرئيسية.
    """

    if not has_timezone(call.from_user.id):
        bot.answer_callback_query(
            call.id,
            "🌍 يجب اختيار المنطقة الزمنية أولًا.",
            show_alert=True
        )

        return

    bot.answer_callback_query(call.id)

    try:
        bot.edit_message_text(
            (
                f"📿 <b>{BOT_NAME}</b>\n\n"
                "اختر ما تريد من القائمة:"
            ),
            call.message.chat.id,
            call.message.message_id,
            parse_mode="HTML",
            reply_markup=main_menu(),
        )

    except Exception:
        send_main_menu(call.message.chat.id)


# =========================================================
# Morning Adhkar
# =========================================================

def handle_morning(call):
    """
    عرض أذكار الصباح.
    """

    if not has_timezone(call.from_user.id):
        bot.answer_callback_query(
            call.id,
            "🌍 اختر منطقتك الزمنية أولًا.",
            show_alert=True
        )
        return

    adhkar = get_morning_adhkar()

    send_adhkar_list(
        call,
        "🌅 أذكار الصباح",
        adhkar,
        "morning"
    )


# =========================================================
# Evening Adhkar
# =========================================================

def handle_evening(call):
    """
    عرض أذكار المساء.
    """

    if not has_timezone(call.from_user.id):
        bot.answer_callback_query(
            call.id,
            "🌍 اختر منطقتك الزمنية أولًا.",
            show_alert=True
        )
        return

    adhkar = get_evening_adhkar()

    send_adhkar_list(
        call,
        "🌙 أذكار المساء",
        adhkar,
        "evening"
    )


# =========================================================
# Sleep Adhkar
# =========================================================

def handle_sleep(call):
    """
    عرض أذكار النوم.
    """

    if not has_timezone(call.from_user.id):
        bot.answer_callback_query(
            call.id,
            "🌍 اختر منطقتك الزمنية أولًا.",
            show_alert=True
        )
        return

    adhkar = get_sleep_adhkar()

    send_adhkar_list(
        call,
        "😴 أذكار النوم",
        adhkar,
        "sleep"
    )


# =========================================================
# Prayer Adhkar
# =========================================================

def handle_prayer(call):
    """
    عرض أذكار الصلاة.
    """

    if not has_timezone(call.from_user.id):
        bot.answer_callback_query(
            call.id,
            "🌍 اختر منطقتك الزمنية أولًا.",
            show_alert=True
        )
        return

    adhkar = get_prayer_adhkar()

    send_adhkar_list(
        call,
        "🕌 أذكار الصلاة",
        adhkar,
        "prayer"
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
    إرسال قائمة الأذكار.
    """

    if not adhkar:
        bot.answer_callback_query(
            call.id,
            "لا توجد أذكار متاحة حاليًا.",
            show_alert=True
        )
        return

    bot.answer_callback_query(call.id)

    message_parts = [
        f"📿 <b>{title}</b>",
        ""
    ]

    for index, item in enumerate(adhkar, start=1):

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
# Duas
# =========================================================

def handle_duas(call):
    """
    عرض الأدعية.
    """

    if not has_timezone(call.from_user.id):
        bot.answer_callback_query(
            call.id,
            "🌍 اختر منطقتك الزمنية أولًا.",
            show_alert=True
        )
        return

    duas = get_duas()

    bot.answer_callback_query(call.id)

    message_parts = [
        "🤲 <b>الأدعية</b>",
        ""
    ]

    for index, dua in enumerate(duas, start=1):

        title = dua.get("title", "دعاء")
        text = dua.get("text", "")

        message_parts.append(
            f"<b>{index}. {title}</b>"
        )

        message_parts.append(text)
        message_parts.append("")

    message = "\n".join(message_parts)

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
    """
    عرض قائمة جميع أقسام الأذكار.
    """

    if not has_timezone(call.from_user.id):
        bot.answer_callback_query(
            call.id,
            "🌍 اختر منطقتك الزمنية أولًا.",
            show_alert=True
        )
        return

    bot.answer_callback_query(call.id)

    try:
        bot.edit_message_text(
            (
                "📚 <b>جميع الأذكار</b>\n\n"
                "اختر القسم الذي تريد:"
            ),
            call.message.chat.id,
            call.message.message_id,
            parse_mode="HTML",
            reply_markup=all_adhkar_menu(),
        )

    except Exception:
        bot.send_message(
            call.message.chat.id,
            (
                "📚 <b>جميع الأذكار</b>\n\n"
                "اختر القسم الذي تريد:"
            ),
            parse_mode="HTML",
            reply_markup=all_adhkar_menu(),
        )


# =========================================================
# Reminder Settings
# =========================================================

def handle_settings(call):
    """
    عرض إعدادات التذكيرات.
    """

    if not has_timezone(call.from_user.id):
        bot.answer_callback_query(
            call.id,
            "🌍 اختر منطقتك الزمنية أولًا.",
            show_alert=True
        )
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
    """
    إعدادات أذكار الصباح.
    """

    if not has_timezone(call.from_user.id):
        bot.answer_callback_query(
            call.id,
            "🌍 اختر منطقتك الزمنية أولًا.",
            show_alert=True
        )
        return

    user = get_user(call.from_user.id)

    bot.answer_callback_query(call.id)

    text = (
        "🌅 <b>إعدادات أذكار الصباح</b>\n\n"
        f"الحالة: "
        f"{'🟢 مفعل' if user['morning_enabled'] else '🔴 متوقف'}\n"
        f"⏰ الوقت: <b>{user['morning_time']}</b>"
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
    """
    إعدادات أذكار المساء.
    """

    if not has_timezone(call.from_user.id):
        bot.answer_callback_query(
            call.id,
            "🌍 اختر منطقتك الزمنية أولًا.",
            show_alert=True
        )
        return

    user = get_user(call.from_user.id)

    bot.answer_callback_query(call.id)

    text = (
        "🌙 <b>إعدادات أذكار المساء</b>\n\n"
        f"الحالة: "
        f"{'🟢 مفعل' if user['evening_enabled'] else '🔴 متوقف'}\n"
        f"⏰ الوقت: <b>{user['evening_time']}</b>"
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
    """
    تشغيل / إيقاف تذكير الصباح.
    """

    user = get_user(call.from_user.id)

    if not user or not user["timezone"]:
        bot.answer_callback_query(
            call.id,
            "🌍 اختر منطقتك الزمنية أولًا.",
            show_alert=True
        )
        return

    new_status = not bool(user["morning_enabled"])

    update_morning_settings(
        call.from_user.id,
        enabled=new_status
    )

    bot.answer_callback_query(
        call.id,
        "✅ تم تحديث إعدادات الصباح."
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
            show_alert=True
        )
        return

    new_status = not bool(user["evening_enabled"])

    update_evening_settings(
        call.from_user.id,
        enabled=new_status
    )

    bot.answer_callback_query(
        call.id,
        "✅ تم تحديث إعدادات المساء."
    )

    handle_evening_settings(call)


# =========================================================
# Morning Time
# =========================================================

def handle_morning_time(call):
    """
    عرض أوقات أذكار الصباح.
    """

    if not has_timezone(call.from_user.id):
        bot.answer_callback_query(
            call.id,
            "🌍 اختر منطقتك الزمنية أولًا.",
            show_alert=True
        )
        return

    bot.answer_callback_query(call.id)

    try:
        bot.edit_message_text(
            (
                "🌅 <b>وقت أذكار الصباح</b>\n\n"
                "اختر الوقت الذي تريد وصول التذكير فيه:"
            ),
            call.message.chat.id,
            call.message.message_id,
            parse_mode="HTML",
            reply_markup=time_selection("morning"),
        )

    except Exception:
        bot.send_message(
            call.message.chat.id,
            (
                "🌅 <b>وقت أذكار الصباح</b>\n\n"
                "اختر الوقت:"
            ),
            parse_mode="HTML",
            reply_markup=time_selection("morning"),
        )


# =========================================================
# Evening Time
# =========================================================

def handle_evening_time(call):
    """
    عرض أوقات أذكار المساء.
    """

    if not has_timezone(call.from_user.id):
        bot.answer_callback_query(
            call.id,
            "🌍 اختر منطقتك الزمنية أولًا.",
            show_alert=True
        )
        return

    bot.answer_callback_query(call.id)

    try:
        bot.edit_message_text(
            (
                "🌙 <b>وقت أذكار المساء</b>\n\n"
                "اختر الوقت الذي تريد وصول التذكير فيه:"
            ),
            call.message.chat.id,
            call.message.message_id,
            parse_mode="HTML",
            reply_markup=time_selection("evening"),
        )

    except Exception:
        bot.send_message(
            call.message.chat.id,
            (
                "🌙 <b>وقت أذكار المساء</b>\n\n"
                "اختر الوقت:"
            ),
            parse_mode="HTML",
            reply_markup=time_selection("evening"),
        )


# =========================================================
# Set Morning Time
# =========================================================

def handle_set_morning_time(call):
    """
    حفظ وقت أذكار الصباح.
    """

    time_value = call.data.replace(
        "morning_set:",
        "",
        1
    )

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
    """
    حفظ وقت أذكار المساء.
    """

    time_value = call.data.replace(
        "evening_set:",
        "",
        1
    )

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

    @bot_instance.message_handler(commands=["start"])
    def start_handler(message):
        handle_start(message)

    # -----------------------------------------------------
    # Callback Queries
    # -----------------------------------------------------

    @bot_instance.callback_query_handler(
        func=lambda call: call.data.startswith("set_timezone:")
    )
    def timezone_callback(call):
        handle_timezone_callback(call)

    @bot_instance.callback_query_handler(
        func=lambda call: call.data == "main_menu"
    )
    def main_menu_callback(call):
        handle_main_menu(call)

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

    @bot_instance.callback_query_handler(
        func=lambda call: call.data == "duas"
    )
    def duas_callback(call):
        handle_duas(call)

    @bot_instance.callback_query_handler(
        func=lambda call: call.data == "all_adhkar"
    )
    def all_adhkar_callback(call):
        handle_all_adhkar(call)

    @bot_instance.callback_query_handler(
        func=lambda call: call.data == "settings"
    )
    def settings_callback(call):
        handle_settings(call)

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

    @bot_instance.callback_query_handler(
        func=lambda call: call.data == "morning_time"
    )
    def morning_time_callback(call):
        handle_morning_time(call)

    @bot_instance.callback_query_handler(
        func=lambda call: call.data == "evening_time"
    )
    def evening_time_callback(call):
        handle_evening_time(call)

    @bot_instance.callback_query_handler(
        func=lambda call: call.data.startswith("morning_set:")
    )
    def set_morning_time_callback(call):
        handle_set_morning_time(call)

    @bot_instance.callback_query_handler(
        func=lambda call: call.data.startswith("evening_set:")
    )
    def set_evening_time_callback(call):
        handle_set_evening_time(call)

    print("[HANDLERS] All handlers registered successfully.")