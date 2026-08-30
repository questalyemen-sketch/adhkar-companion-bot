# =========================================================
# Adhkar Companion
# Main Bot
# =========================================================

import html
import time

import telebot
from telebot import types

from config import (
    BOT_TOKEN,
    BOT_NAME,
    BOT_VERSION,
    REQUIRE_TIMEZONE_ON_START,
    TIMEZONE_OPTIONS,
    DEFAULT_MORNING_TIME,
    DEFAULT_EVENING_TIME,
)

from database import (
    init_database,
    add_user,
    get_user,
    update_timezone,
    update_morning_settings,
    update_evening_settings,
    toggle_morning,
    toggle_evening,
)

from timezone_utils import (
    is_valid_timezone,
    is_valid_time,
    get_timezone_display_name,
    get_local_time,
)

from adhkar import (
    get_morning_adhkar,
    get_evening_adhkar,
    get_sleep_adhkar,
    get_prayer_adhkar,
    get_duas,
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

from scheduler import (
    set_bot,
    start_scheduler,
)


# =========================================================
# Bot Initialization
# =========================================================

bot = telebot.TeleBot(
    BOT_TOKEN,
    parse_mode="HTML"
)


# =========================================================
# Runtime State
# =========================================================

# تخزين حالة المستخدم مؤقتًا أثناء اختيار بعض الإعدادات.
#
# لا يتم الاعتماد عليها لحفظ البيانات الدائمة.
# البيانات الدائمة محفوظة في SQLite.
user_states = {}


# =========================================================
# Database Initialization
# =========================================================

init_database()


# =========================================================
# Scheduler Initialization
# =========================================================

set_bot(bot)
start_scheduler()


# =========================================================
# Helper: Get User ID
# =========================================================

def get_user_id(message_or_call):
    """
    الحصول على Telegram ID من Message أو CallbackQuery.
    """

    if hasattr(message_or_call, "from_user"):
        return message_or_call.from_user.id

    return None


# =========================================================
# Helper: Register User
# =========================================================

def register_user(user):
    """
    تسجيل المستخدم أو تحديث بياناته.
    """

    if not user:
        return

    telegram_id = user.id

    first_name = (
        user.first_name
        or ""
    )

    username = (
        user.username
        or ""
    )

    add_user(
        telegram_id,
        first_name,
        username
    )


# =========================================================
# Helper: Get Database User
# =========================================================

def get_database_user(telegram_id):
    """
    الحصول على المستخدم من قاعدة البيانات.
    """

    try:
        return get_user(telegram_id)

    except Exception as error:

        print(
            f"[MAIN] Failed to get user "
            f"{telegram_id}: {error}"
        )

        return None


# =========================================================
# Helper: Check Timezone
# =========================================================

def user_needs_timezone(telegram_id):
    """
    تحديد ما إذا كان المستخدم يحتاج إلى اختيار
    المنطقة الزمنية.
    """

    user = get_database_user(
        telegram_id
    )

    if not user:
        return True

    timezone_name = user["timezone"]

    if not timezone_name:
        return True

    return not is_valid_timezone(
        timezone_name
    )


# =========================================================
# Helper: Escape HTML
# =========================================================

def escape_html(value):
    """
    حماية النصوص التي تأتي من المستخدم قبل وضعها
    داخل رسالة HTML.
    """

    return html.escape(
        str(value or "")
    )


# =========================================================
# Helper: Answer Callback
# =========================================================

def answer_callback(
    call,
    text=None,
    show_alert=False
):
    """
    الرد على CallbackQuery بأمان.
    """

    try:

        bot.answer_callback_query(
            call.id,
            text=text,
            show_alert=show_alert
        )

    except Exception as error:

        print(
            f"[MAIN] Callback answer error: {error}"
        )


# =========================================================
# Helper: Edit Message
# =========================================================

def edit_message(
    call,
    text,
    reply_markup=None
):
    """
    تعديل رسالة Inline بأمان.
    """

    try:

        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=text,
            reply_markup=reply_markup,
            parse_mode="HTML"
        )

        return True

    except Exception as error:

        # يحدث أحيانًا عندما تكون الرسالة بنفس النص
        # أو عند وجود تغيير بسيط في حالة Telegram.
        print(
            f"[MAIN] Failed to edit message: {error}"
        )

        return False


# =========================================================
# Helper: Send Main Menu
# =========================================================

def send_main_menu(
    chat_id,
    first_name=""
):
    """
    إرسال القائمة الرئيسية.
    """

    safe_name = escape_html(
        first_name
    )

    if safe_name:

        text = (
            f"👋 أهلًا بك {safe_name}\n\n"
            f"📿 <b>{BOT_NAME}</b>\n"
            f"نسخة {BOT_VERSION}\n\n"
            "اختر ما تريد من القائمة:"
        )

    else:

        text = (
            f"📿 <b>{BOT_NAME}</b>\n\n"
            "اختر ما تريد من القائمة:"
        )

    bot.send_message(
        chat_id,
        text,
        reply_markup=main_menu()
    )


# =========================================================
# Helper: Timezone Setup Message
# =========================================================

def send_timezone_setup(
    chat_id,
    first_time=True
):
    """
    إرسال واجهة اختيار المنطقة الزمنية.
    """

    if first_time:

        text = (
            "🌍 <b>مرحبًا بك في Adhkar Companion</b>\n\n"
            "حتى أتمكن من إرسال أذكار الصباح "
            "والمساء في الوقت الصحيح، يجب أولًا "
            "تحديد منطقتك الزمنية.\n\n"
            "اختر موقعك من القائمة:"
        )

        keyboard = timezone_setup_menu()

    else:

        text = (
            "🌍 <b>تغيير المنطقة الزمنية</b>\n\n"
            "اختر منطقتك الزمنية الجديدة:"
        )

        keyboard = timezone_menu()

    bot.send_message(
        chat_id,
        text,
        reply_markup=keyboard
    )


# =========================================================
# Helper: Build Adhkar Text
# =========================================================

def build_adhkar_text(
    title,
    items,
    introduction=""
):
    """
    بناء رسالة أذكار من قائمة الأذكار.
    """

    if not items:

        return (
            f"<b>{escape_html(title)}</b>\n\n"
            "لا توجد أذكار متاحة حاليًا."
        )

    parts = [
        f"📿 <b>{escape_html(title)}</b>",
        ""
    ]

    if introduction:

        parts.extend([
            introduction,
            ""
        ])

    for index, item in enumerate(
        items,
        start=1
    ):

        if not isinstance(
            item,
            dict
        ):
            continue

        item_title = item.get(
            "title",
            ""
        )

        text = item.get(
            "text",
            ""
        )

        count = item.get(
            "count"
        )

        if item_title:

            parts.append(
                f"🔹 <b>{escape_html(item_title)}</b>"
            )

        if text:

            parts.append(
                escape_html(text)
            )

        if count:

            parts.append(
                f"🔁 العدد: <b>{count}</b>"
            )

        parts.append("")

    parts.append(
        "🤍 تقبل الله منك."
    )

    return "\n".join(parts)


# =========================================================
# Helper: Send Adhkar
# =========================================================

def send_adhkar(
    chat_id,
    title,
    items,
    keyboard
):
    """
    إرسال الأذكار للمستخدم.
    """

    text = build_adhkar_text(
        title,
        items
    )

    # Telegram لديه حد لطول الرسالة.
    # نقسم الرسالة إذا كانت طويلة جدًا.
    max_length = 4000

    if len(text) <= max_length:

        bot.send_message(
            chat_id,
            text,
            reply_markup=keyboard
        )

        return

    # -----------------------------------------------------
    # تقسيم الرسالة الطويلة
    # -----------------------------------------------------

    chunks = []

    current = ""

    for line in text.splitlines(
        keepends=True
    ):

        if len(current) + len(line) > max_length:

            if current:

                chunks.append(
                    current
                )

            current = line

        else:

            current += line

    if current:

        chunks.append(
            current
        )

    for index, chunk in enumerate(
        chunks
    ):

        if index == len(chunks) - 1:

            bot.send_message(
                chat_id,
                chunk,
                reply_markup=keyboard
            )

        else:

            bot.send_message(
                chat_id,
                chunk
            )


# =========================================================
# Helper: Show Adhkar In Callback
# =========================================================

def show_adhkar_callback(
    call,
    title,
    items,
    keyboard
):
    """
    عرض الأذكار من خلال Callback.
    """

    text = build_adhkar_text(
        title,
        items
    )

    max_length = 4000

    if len(text) <= max_length:

        edit_message(
            call,
            text,
            keyboard
        )

        return

    # إذا كانت الرسالة طويلة جدًا،
    # نحذف الرسالة الحالية ثم نرسل الرسالة على أجزاء.
    try:

        bot.delete_message(
            call.message.chat.id,
            call.message.message_id
        )

    except Exception:
        pass

    send_adhkar(
        call.message.chat.id,
        title,
        items,
        keyboard
    )


# =========================================================
# /start
# =========================================================

@bot.message_handler(
    commands=["start"]
)
def start_command(message):
    """
    نقطة الدخول الرئيسية للبوت.
    """

    try:

        register_user(
            message.from_user
        )

        telegram_id = (
            message.from_user.id
        )

        if (
            REQUIRE_TIMEZONE_ON_START
            and user_needs_timezone(
                telegram_id
            )
        ):

            send_timezone_setup(
                message.chat.id,
                first_time=True
            )

            return

        send_main_menu(
            message.chat.id,
            message.from_user.first_name
        )

    except Exception as error:

        print(
            f"[MAIN] /start error: {error}"
        )

        bot.send_message(
            message.chat.id,
            "❌ حدث خطأ مؤقت. حاول مرة أخرى."
        )


# =========================================================
# /menu
# =========================================================

@bot.message_handler(
    commands=["menu"]
)
def menu_command(message):
    """
    فتح القائمة الرئيسية.
    """

    try:

        register_user(
            message.from_user
        )

        telegram_id = (
            message.from_user.id
        )

        if (
            REQUIRE_TIMEZONE_ON_START
            and user_needs_timezone(
                telegram_id
            )
        ):

            send_timezone_setup(
                message.chat.id,
                first_time=True
            )

            return

        send_main_menu(
            message.chat.id,
            message.from_user.first_name
        )

    except Exception as error:

        print(
            f"[MAIN] /menu error: {error}"
        )


# =========================================================
# Main Menu Callback
# =========================================================

@bot.callback_query_handler(
    func=lambda call:
        call.data == "main_menu"
)
def callback_main_menu(call):

    answer_callback(
        call
    )

    try:

        user = call.from_user

        register_user(
            user
        )

        db_user = get_database_user(
            user.id
        )

        if (
            REQUIRE_TIMEZONE_ON_START
            and (
                not db_user
                or not db_user["timezone"]
            )
        ):

            edit_message(
                call,
                (
                    "🌍 يجب تحديد منطقتك الزمنية "
                    "أولًا حتى تعمل التذكيرات."
                ),
                timezone_setup_menu()
            )

            return

        text = (
            f"📿 <b>{BOT_NAME}</b>\n\n"
            "اختر ما تريد:"
        )

        edit_message(
            call,
            text,
            main_menu()
        )

    except Exception as error:

        print(
            f"[MAIN] main menu error: {error}"
        )


# =========================================================
# Morning Adhkar
# =========================================================

@bot.callback_query_handler(
    func=lambda call:
        call.data == "morning"
)
def callback_morning(call):

    answer_callback(
        call
    )

    try:

        items = get_morning_adhkar()

        show_adhkar_callback(
            call,
            "🌅 أذكار الصباح",
            items,
            adhkar_navigation("morning")
        )

    except Exception as error:

        print(
            f"[MAIN] Morning error: {error}"
        )


# =========================================================
# Evening Adhkar
# =========================================================

@bot.callback_query_handler(
    func=lambda call:
        call.data == "evening"
)
def callback_evening(call):

    answer_callback(
        call
    )

    try:

        items = get_evening_adhkar()

        show_adhkar_callback(
            call,
            "🌙 أذكار المساء",
            items,
            adhkar_navigation("evening")
        )

    except Exception as error:

        print(
            f"[MAIN] Evening error: {error}"
        )


# =========================================================
# Sleep Adhkar
# =========================================================

@bot.callback_query_handler(
    func=lambda call:
        call.data == "sleep"
)
def callback_sleep(call):

    answer_callback(
        call
    )

    try:

        items = get_sleep_adhkar()

        show_adhkar_callback(
            call,
            "😴 أذكار النوم",
            items,
            adhkar_navigation("sleep")
        )

    except Exception as error:

        print(
            f"[MAIN] Sleep error: {error}"
        )


# =========================================================
# Prayer Adhkar
# =========================================================

@bot.callback_query_handler(
    func=lambda call:
        call.data == "prayer"
)
def callback_prayer(call):

    answer_callback(
        call
    )

    try:

        items = get_prayer_adhkar()

        show_adhkar_callback(
            call,
            "🕌 أذكار الصلاة",
            items,
            adhkar_navigation("prayer")
        )

    except Exception as error:

        print(
            f"[MAIN] Prayer error: {error}"
        )


# =========================================================
# Duas
# =========================================================

@bot.callback_query_handler(
    func=lambda call:
        call.data == "duas"
)
def callback_duas(call):

    answer_callback(
        call
    )

    try:

        items = get_duas()

        show_adhkar_callback(
            call,
            "🤲 الأدعية",
            items,
            dua_navigation()
        )

    except Exception as error:

        print(
            f"[MAIN] Duas error: {error}"
        )


# =========================================================
# All Adhkar
# =========================================================

@bot.callback_query_handler(
    func=lambda call:
        call.data == "all_adhkar"
)
def callback_all_adhkar(call):

    answer_callback(
        call
    )

    try:

        edit_message(
            call,
            (
                "📚 <b>جميع الأذكار</b>\n\n"
                "اختر القسم الذي تريد فتحه:"
            ),
            all_adhkar_menu()
        )

    except Exception as error:

        print(
            f"[MAIN] All adhkar error: {error}"
        )


# =========================================================
# Next Adhkar
# =========================================================

@bot.callback_query_handler(
    func=lambda call:
        call.data.endswith("_next")
)
def callback_next_adhkar(call):

    answer_callback(
        call
    )

    try:

        category = call.data[:-5]

        if category == "morning":

            items = get_morning_adhkar()

            title = "🌅 أذكار الصباح"

            keyboard = adhkar_navigation(
                "morning"
            )

        elif category == "evening":

            items = get_evening_adhkar()

            title = "🌙 أذكار المساء"

            keyboard = adhkar_navigation(
                "evening"
            )

        elif category == "sleep":

            items = get_sleep_adhkar()

            title = "😴 أذكار النوم"

            keyboard = adhkar_navigation(
                "sleep"
            )

        elif category == "prayer":

            items = get_prayer_adhkar()

            title = "🕌 أذكار الصلاة"

            keyboard = adhkar_navigation(
                "prayer"
            )

        elif category == "duas":

            items = get_duas()

            title = "🤲 الأدعية"

            keyboard = dua_navigation()

        else:

            return

        show_adhkar_callback(
            call,
            title,
            items,
            keyboard
        )

    except Exception as error:

        print(
            f"[MAIN] Next adhkar error: {error}"
        )


# =========================================================
# Settings
# =========================================================

@bot.callback_query_handler(
    func=lambda call:
        call.data == "settings"
)
def callback_settings(call):

    answer_callback(
        call
    )

    try:

        user = get_database_user(
            call.from_user.id
        )

        if not user:

            register_user(
                call.from_user
            )

            user = get_database_user(
                call.from_user.id
            )

        timezone_name = (
            user["timezone"]
            if user
            else None
        )

        if timezone_name:

            timezone_display = (
                get_timezone_display_name(
                    timezone_name
                )
            )

            timezone_line = (
                f"🌍 المنطقة: "
                f"<b>{escape_html(timezone_display)}</b>"
            )

        else:

            timezone_line = (
                "🌍 المنطقة: <b>غير محددة</b>"
            )

        text = (
            "⚙️ <b>إعدادات التذكير</b>\n\n"
            f"{timezone_line}\n\n"
            "اختر الإعداد الذي تريد تغييره:"
        )

        edit_message(
            call,
            text,
            reminder_settings()
        )

    except Exception as error:

        print(
            f"[MAIN] Settings error: {error}"
        )


# =========================================================
# Timezone Menu
# =========================================================

@bot.callback_query_handler(
    func=lambda call:
        call.data == "timezone"
)
def callback_timezone(call):

    answer_callback(
        call
    )

    try:

        edit_message(
            call,
            (
                "🌍 <b>اختيار المنطقة الزمنية</b>\n\n"
                "اختر المنطقة الزمنية التي تستخدمها:"
            ),
            timezone_menu()
        )

    except Exception as error:

        print(
            f"[MAIN] Timezone menu error: {error}"
        )


# =========================================================
# Set Timezone
# =========================================================

@bot.callback_query_handler(
    func=lambda call:
        call.data.startswith(
            "set_timezone:"
        )
)
def callback_set_timezone(call):

    timezone_name = (
        call.data.split(
            ":",
            1
        )[1]
    )

    if not is_valid_timezone(
        timezone_name
    ):

        answer_callback(
            call,
            "❌ المنطقة الزمنية غير صالحة.",
            True
        )

        return

    try:

        success = update_timezone(
            call.from_user.id,
            timezone_name
        )

        if not success:

            answer_callback(
                call,
                "❌ تعذر حفظ المنطقة الزمنية.",
                True
            )

            return

        display_name = (
            get_timezone_display_name(
                timezone_name
            )
        )

        local_time = get_local_time(
            timezone_name
        )

        answer_callback(
            call,
            "✅ تم حفظ المنطقة الزمنية."
        )

        text = (
            "✅ <b>تم تحديد المنطقة الزمنية</b>\n\n"
            f"🌍 المنطقة: "
            f"<b>{escape_html(display_name)}</b>\n"
            f"🕐 الوقت المحلي الآن: "
            f"<b>{escape_html(local_time)}</b>\n\n"
            "أصبحت التذكيرات مرتبطة بتوقيتك المحلي."
        )

        edit_message(
            call,
            text,
            main_menu()
        )

    except Exception as error:

        print(
            f"[MAIN] Set timezone error: {error}"
        )

        answer_callback(
            call,
            "❌ حدث خطأ أثناء حفظ المنطقة.",
            True
        )


# =========================================================
# Morning Settings
# =========================================================

@bot.callback_query_handler(
    func=lambda call:
        call.data == "morning_settings"
)
def callback_morning_settings(call):

    answer_callback(
        call
    )

    try:

        user = get_database_user(
            call.from_user.id
        )

        if not user:

            register_user(
                call.from_user
            )

            user = get_database_user(
                call.from_user.id
            )

        enabled = bool(
            user["morning_enabled"]
        )

        current_time = (
            user["morning_time"]
            or DEFAULT_MORNING_TIME
        )

        text = (
            "🌅 <b>إعدادات أذكار الصباح</b>\n\n"
            f"الحالة: "
            f"<b>{'🟢 مفعّل' if enabled else '🔴 متوقف'}</b>\n"
            f"⏰ وقت التذكير: "
            f"<b>{escape_html(current_time)}</b>"
        )

        edit_message(
            call,
            text,
            morning_settings(enabled)
        )

    except Exception as error:

        print(
            f"[MAIN] Morning settings error: {error}"
        )


# =========================================================
# Evening Settings
# =========================================================

@bot.callback_query_handler(
    func=lambda call:
        call.data == "evening_settings"
)
def callback_evening_settings(call):

    answer_callback(
        call
    )

    try:

        user = get_database_user(
            call.from_user.id
        )

        if not user:

            register_user(
                call.from_user
            )

            user = get_database_user(
                call.from_user.id
            )

        enabled = bool(
            user["evening_enabled"]
        )

        current_time = (
            user["evening_time"]
            or DEFAULT_EVENING_TIME
        )

        text = (
            "🌙 <b>إعدادات أذكار المساء</b>\n\n"
            f"الحالة: "
            f"<b>{'🟢 مفعّل' if enabled else '🔴 متوقف'}</b>\n"
            f"⏰ وقت التذكير: "
            f"<b>{escape_html(current_time)}</b>"
        )

        edit_message(
            call,
            text,
            evening_settings(enabled)
        )

    except Exception as error:

        print(
            f"[MAIN] Evening settings error: {error}"
        )


# =========================================================
# Toggle Morning
# =========================================================

@bot.callback_query_handler(
    func=lambda call:
        call.data == "toggle_morning"
)
def callback_toggle_morning(call):

    try:

        new_status = toggle_morning(
            call.from_user.id
        )

        if new_status is None:

            answer_callback(
                call,
                "❌ المستخدم غير موجود.",
                True
            )

            return

        answer_callback(
            call,
            (
                "🟢 تم تشغيل تذكير الصباح."
                if new_status
                else
                "🔴 تم إيقاف تذكير الصباح."
            )
        )

        user = get_database_user(
            call.from_user.id
        )

        current_time = (
            user["morning_time"]
            or DEFAULT_MORNING_TIME
        )

        text = (
            "🌅 <b>إعدادات أذكار الصباح</b>\n\n"
            f"الحالة: "
            f"<b>{'🟢 مفعّل' if new_status else '🔴 متوقف'}</b>\n"
            f"⏰ وقت التذكير: "
            f"<b>{escape_html(current_time)}</b>"
        )

        edit_message(
            call,
            text,
            morning_settings(
                new_status
            )
        )

    except Exception as error:

        print(
            f"[MAIN] Toggle morning error: {error}"
        )

        answer_callback(
            call,
            "❌ حدث خطأ.",
            True
        )


# =========================================================
# Toggle Evening
# =========================================================

@bot.callback_query_handler(
    func=lambda call:
        call.data == "toggle_evening"
)
def callback_toggle_evening(call):

    try:

        new_status = toggle_evening(
            call.from_user.id
        )

        if new_status is None:

            answer_callback(
                call,
                "❌ المستخدم غير موجود.",
                True
            )

            return

        answer_callback(
            call,
            (
                "🟢 تم تشغيل تذكير المساء."
                if new_status
                else
                "🔴 تم إيقاف تذكير المساء."
            )
        )

        user = get_database_user(
            call.from_user.id
        )

        current_time = (
            user["evening_time"]
            or DEFAULT_EVENING_TIME
        )

        text = (
            "🌙 <b>إعدادات أذكار المساء</b>\n\n"
            f"الحالة: "
            f"<b>{'🟢 مفعّل' if new_status else '🔴 متوقف'}</b>\n"
            f"⏰ وقت التذكير: "
            f"<b>{escape_html(current_time)}</b>"
        )

        edit_message(
            call,
            text,
            evening_settings(
                new_status
            )
        )

    except Exception as error:

        print(
            f"[MAIN] Toggle evening error: {error}"
        )

        answer_callback(
            call,
            "❌ حدث خطأ.",
            True
        )


# =========================================================
# Morning Time Selection
# =========================================================

@bot.callback_query_handler(
    func=lambda call:
        call.data == "morning_time"
)
def callback_morning_time(call):

    answer_callback(
        call
    )

    try:

        edit_message(
            call,
            (
                "⏰ <b>وقت أذكار الصباح</b>\n\n"
                "اختر الوقت الذي تريد وصول التذكير فيه:"
            ),
            time_selection("morning")
        )

    except Exception as error:

        print(
            f"[MAIN] Morning time menu error: {error}"
        )


# =========================================================
# Evening Time Selection
# =========================================================

@bot.callback_query_handler(
    func=lambda call:
        call.data == "evening_time"
)
def callback_evening_time(call):

    answer_callback(
        call
    )

    try:

        edit_message(
            call,
            (
                "⏰ <b>وقت أذكار المساء</b>\n\n"
                "اختر الوقت الذي تريد وصول التذكير فيه:"
            ),
            time_selection("evening")
        )

    except Exception as error:

        print(
            f"[MAIN] Evening time menu error: {error}"
        )


# =========================================================
# Set Morning Time
# =========================================================

@bot.callback_query_handler(
    func=lambda call:
        call.data.startswith(
            "morning_set:"
        )
)
def callback_set_morning_time(call):

    time_value = (
        call.data.split(
            ":",
            1
        )[1]
    )

    if not is_valid_time(
        time_value
    ):

        answer_callback(
            call,
            "❌ الوقت غير صالح.",
            True
        )

        return

    try:

        success = update_morning_settings(
            call.from_user.id,
            time=time_value
        )

        if not success:

            answer_callback(
                call,
                "❌ تعذر حفظ الوقت.",
                True
            )

            return

        answer_callback(
            call,
            f"✅ تم ضبط التذكير على {time_value}"
        )

        user = get_database_user(
            call.from_user.id
        )

        enabled = bool(
            user["morning_enabled"]
        )

        text = (
            "🌅 <b>إعدادات أذكار الصباح</b>\n\n"
            f"الحالة: "
            f"<b>{'🟢 مفعّل' if enabled else '🔴 متوقف'}</b>\n"
            f"⏰ وقت التذكير: "
            f"<b>{escape_html(time_value)}</b>"
        )

        edit_message(
            call,
            text,
            morning_settings(
                enabled
            )
        )

    except Exception as error:

        print(
            f"[MAIN] Set morning time error: {error}"
        )

        answer_callback(
            call,
            "❌ حدث خطأ أثناء حفظ الوقت.",
            True
        )


# =========================================================
# Set Evening Time
# =========================================================

@bot.callback_query_handler(
    func=lambda call:
        call.data.startswith(
            "evening_set:"
        )
)
def callback_set_evening_time(call):

    time_value = (
        call.data.split(
            ":",
            1
        )[1]
    )

    if not is_valid_time(
        time_value
    ):

        answer_callback(
            call,
            "❌ الوقت غير صالح.",
            True
        )

        return

    try:

        success = update_evening_settings(
            call.from_user.id,
            time=time_value
        )

        if not success:

            answer_callback(
                call,
                "❌ تعذر حفظ الوقت.",
                True
            )

            return

        answer_callback(
            call,
            f"✅ تم ضبط التذكير على {time_value}"
        )

        user = get_database_user(
            call.from_user.id
        )

        enabled = bool(
            user["evening_enabled"]
        )

        text = (
            "🌙 <b>إعدادات أذكار المساء</b>\n\n"
            f"الحالة: "
            f"<b>{'🟢 مفعّل' if enabled else '🔴 متوقف'}</b>\n"
            f"⏰ وقت التذكير: "
            f"<b>{escape_html(time_value)}</b>"
        )

        edit_message(
            call,
            text,
            evening_settings(
                enabled
            )
        )

    except Exception as error:

        print(
            f"[MAIN] Set evening time error: {error}"
        )

        answer_callback(
            call,
            "❌ حدث خطأ أثناء حفظ الوقت.",
            True
        )


# =========================================================
# Status Buttons
# =========================================================

@bot.callback_query_handler(
    func=lambda call:
        call.data == "morning_status"
)
def callback_morning_status(call):

    user = get_database_user(
        call.from_user.id
    )

    if not user:

        answer_callback(
            call,
            "❌ تعذر العثور على إعداداتك.",
            True
        )

        return

    enabled = bool(
        user["morning_enabled"]
    )

    time_value = (
        user["morning_time"]
        or DEFAULT_MORNING_TIME
    )

    answer_callback(
        call,
        (
            f"🌅 الصباح: "
            f"{'مفعّل' if enabled else 'متوقف'}\n"
            f"⏰ {time_value}"
        ),
        True
    )


@bot.callback_query_handler(
    func=lambda call:
        call.data == "evening_status"
)
def callback_evening_status(call):

    user = get_database_user(
        call.from_user.id
    )

    if not user:

        answer_callback(
            call,
            "❌ تعذر العثور على إعداداتك.",
            True
        )

        return

    enabled = bool(
        user["evening_enabled"]
    )

    time_value = (
        user["evening_time"]
        or DEFAULT_EVENING_TIME
    )

    answer_callback(
        call,
        (
            f"🌙 المساء: "
            f"{'مفعّل' if enabled else 'متوقف'}\n"
            f"⏰ {time_value}"
        ),
        True
    )


# =========================================================
# Unknown Text Handler
# =========================================================

@bot.message_handler(
    content_types=[
        "text"
    ]
)
def unknown_text(message):
    """
    التعامل مع الرسائل النصية التي لا تطابق أمرًا معروفًا.
    """

    try:

        register_user(
            message.from_user
        )

        telegram_id = (
            message.from_user.id
        )

        if (
            REQUIRE_TIMEZONE_ON_START
            and user_needs_timezone(
                telegram_id
            )
        ):

            bot.send_message(
                message.chat.id,
                (
                    "🌍 قبل استخدام البوت، "
                    "اختر منطقتك الزمنية أولًا:"
                ),
                reply_markup=timezone_setup_menu()
            )

            return

        bot.send_message(
            message.chat.id,
            (
                "📿 استخدم القائمة لاختيار القسم "
                "الذي تريده."
            ),
            reply_markup=main_menu()
        )

    except Exception as error:

        print(
            f"[MAIN] Unknown message error: {error}"
        )


# =========================================================
# Error-Protected Polling
# =========================================================

def run_bot():
    """
    تشغيل Telegram polling مع إعادة المحاولة
    في حال حدوث خطأ مؤقت.
    """

    print(
        "========================================"
    )

    print(
        f"📿 {BOT_NAME}"
    )

    print(
        f"📦 Version: {BOT_VERSION}"
    )

    print(
        "🚀 Bot starting..."
    )

    print(
        "========================================"
    )

    while True:

        try:

            print(
                "[MAIN] Starting Telegram polling..."
            )

            bot.infinity_polling(
                skip_pending=True,
                timeout=30,
                long_polling_timeout=30
            )

        except KeyboardInterrupt:

            print(
                "[MAIN] Bot stopped by user."
            )

            break

        except Exception as error:

            print(
                f"[MAIN] Polling error: {error}"
            )

            print(
                "[MAIN] Restarting polling in 5 seconds..."
            )

            time.sleep(5)


# =========================================================
# Entry Point
# =========================================================

if __name__ == "__main__":

    run_bot()