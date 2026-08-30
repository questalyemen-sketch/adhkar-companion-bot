# =========================================================
# Adhkar Companion
# Automatic Reminder Scheduler
# =========================================================

import threading
import time

from config import (
    DEFAULT_MORNING_TIME,
    DEFAULT_EVENING_TIME,
    ENABLE_MORNING_REMINDER,
    ENABLE_EVENING_REMINDER,
)

from database import (
    get_reminder_users,
    mark_morning_sent,
    mark_evening_sent,
)

from timezone_utils import (
    get_local_now,
)

from adhkar import (
    get_morning_adhkar,
    get_evening_adhkar,
)


# =========================================================
# Scheduler Configuration
# =========================================================

# عدد الثواني بين كل عملية فحص.
#
# 30 ثانية مناسبة للتذكيرات اليومية، وتقلل احتمال
# تفويت وقت الإرسال بسبب تأخر بسيط في التنفيذ.
CHECK_INTERVAL = 30


# =========================================================
# Bot Reference
# =========================================================

_bot = None


def set_bot(bot):
    """
    حفظ كائن البوت لاستخدامه داخل Scheduler.

    يتم استدعاؤها من main.py بعد إنشاء كائن TeleBot.
    """

    global _bot

    _bot = bot


# =========================================================
# Send Message Safely
# =========================================================

def safe_send_message(
    telegram_id,
    text
):
    """
    إرسال رسالة إلى المستخدم بأمان.

    إذا فشل الإرسال لمستخدم واحد، لا يتوقف الـ Scheduler.
    """

    if _bot is None:
        print(
            "[SCHEDULER] Bot instance is not configured."
        )

        return False

    if not text:
        return False

    try:

        _bot.send_message(
            telegram_id,
            text,
            parse_mode="HTML"
        )

        return True

    except Exception as error:

        print(
            f"[SCHEDULER] Failed to send message "
            f"to {telegram_id}: {error}"
        )

        return False


# =========================================================
# Build Adhkar Message
# =========================================================

def build_adhkar_message(
    title,
    adhkar
):
    """
    تحويل قائمة الأذكار إلى رسالة Telegram.

    يتوقع أن يكون كل عنصر بالشكل:

        {
            "text": "...",
            "count": 3
        }

    أو:

        {
            "text": "..."
        }
    """

    if not adhkar:
        return None

    message_parts = [
        f"📿 <b>{title}</b>",
        "",
        "حان الآن وقت الأذكار 🤍",
        "",
    ]

    for index, item in enumerate(
        adhkar,
        start=1
    ):

        if not isinstance(item, dict):
            continue

        text = item.get(
            "text",
            ""
        )

        if not text:
            continue

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

    message_parts.append(
        "🤍 بارك الله في وقتك."
    )

    return "\n".join(message_parts)


# =========================================================
# Morning Message
# =========================================================

def build_morning_message():
    """
    إنشاء رسالة أذكار الصباح من adhkar.py.
    """

    try:

        adhkar = get_morning_adhkar()

        return build_adhkar_message(
            "🌅 أذكار الصباح",
            adhkar
        )

    except Exception as error:

        print(
            f"[SCHEDULER] Failed to build "
            f"morning message: {error}"
        )

        return None


# =========================================================
# Evening Message
# =========================================================

def build_evening_message():
    """
    إنشاء رسالة أذكار المساء من adhkar.py.
    """

    try:

        adhkar = get_evening_adhkar()

        return build_adhkar_message(
            "🌙 أذكار المساء",
            adhkar
        )

    except Exception as error:

        print(
            f"[SCHEDULER] Failed to build "
            f"evening message: {error}"
        )

        return None


# =========================================================
# Check Morning Reminder
# =========================================================

def check_morning_reminder(user):
    """
    فحص تذكير أذكار الصباح لمستخدم واحد.
    """

    if not ENABLE_MORNING_REMINDER:
        return

    if not user["morning_enabled"]:
        return

    timezone_name = user["timezone"]

    if not timezone_name:
        return

    local_now = get_local_now(
        timezone_name
    )

    if local_now is None:
        return

    current_time = local_now.strftime(
        "%H:%M"
    )

    current_date = local_now.strftime(
        "%Y-%m-%d"
    )

    reminder_time = (
        user["morning_time"]
        or DEFAULT_MORNING_TIME
    )

    # -----------------------------------------------------
    # لم يصل وقت التذكير بعد
    # -----------------------------------------------------

    if current_time != reminder_time:
        return

    # -----------------------------------------------------
    # تم الإرسال اليوم بالفعل
    # -----------------------------------------------------

    if user["last_morning_sent"] == current_date:
        return

    # -----------------------------------------------------
    # بناء الرسالة
    # -----------------------------------------------------

    message = build_morning_message()

    if not message:
        print(
            f"[SCHEDULER] Morning message is empty "
            f"for {user['telegram_id']}"
        )

        return

    # -----------------------------------------------------
    # إرسال الرسالة
    # -----------------------------------------------------

    sent = safe_send_message(
        user["telegram_id"],
        message
    )

    # -----------------------------------------------------
    # تسجيل الإرسال فقط إذا نجح
    # -----------------------------------------------------

    if sent:

        mark_morning_sent(
            user["telegram_id"],
            current_date
        )

        print(
            f"[SCHEDULER] Morning adhkar sent "
            f"to {user['telegram_id']} "
            f"at {current_time} "
            f"({timezone_name})"
        )


# =========================================================
# Check Evening Reminder
# =========================================================

def check_evening_reminder(user):
    """
    فحص تذكير أذكار المساء لمستخدم واحد.
    """

    if not ENABLE_EVENING_REMINDER:
        return

    if not user["evening_enabled"]:
        return

    timezone_name = user["timezone"]

    if not timezone_name:
        return

    local_now = get_local_now(
        timezone_name
    )

    if local_now is None:
        return

    current_time = local_now.strftime(
        "%H:%M"
    )

    current_date = local_now.strftime(
        "%Y-%m-%d"
    )

    reminder_time = (
        user["evening_time"]
        or DEFAULT_EVENING_TIME
    )

    # -----------------------------------------------------
    # لم يصل وقت التذكير بعد
    # -----------------------------------------------------

    if current_time != reminder_time:
        return

    # -----------------------------------------------------
    # تم الإرسال اليوم بالفعل
    # -----------------------------------------------------

    if user["last_evening_sent"] == current_date:
        return

    # -----------------------------------------------------
    # بناء الرسالة
    # -----------------------------------------------------

    message = build_evening_message()

    if not message:
        print(
            f"[SCHEDULER] Evening message is empty "
            f"for {user['telegram_id']}"
        )

        return

    # -----------------------------------------------------
    # إرسال الرسالة
    # -----------------------------------------------------

    sent = safe_send_message(
        user["telegram_id"],
        message
    )

    # -----------------------------------------------------
    # تسجيل الإرسال فقط إذا نجح
    # -----------------------------------------------------

    if sent:

        mark_evening_sent(
            user["telegram_id"],
            current_date
        )

        print(
            f"[SCHEDULER] Evening adhkar sent "
            f"to {user['telegram_id']} "
            f"at {current_time} "
            f"({timezone_name})"
        )


# =========================================================
# Scheduler Cycle
# =========================================================

def scheduler_cycle():
    """
    تنفيذ دورة واحدة من فحص جميع المستخدمين.
    """

    try:

        users = get_reminder_users()

        if not users:
            return

        for user in users:

            try:

                check_morning_reminder(user)
                check_evening_reminder(user)

            except Exception as error:

                print(
                    f"[SCHEDULER] Error processing "
                    f"user {user['telegram_id']}: {error}"
                )

    except Exception as error:

        print(
            f"[SCHEDULER] Database error: {error}"
        )


# =========================================================
# Scheduler Worker
# =========================================================

def scheduler_worker():
    """
    العامل الرئيسي للـ Scheduler.

    يعمل في Thread مستقل حتى لا يمنع
    Telegram polling من العمل.
    """

    print(
        "[SCHEDULER] Scheduler started."
    )

    while True:

        try:

            scheduler_cycle()

        except Exception as error:

            print(
                f"[SCHEDULER] Unexpected error: {error}"
            )

        time.sleep(
            CHECK_INTERVAL
        )


# =========================================================
# Start Scheduler
# =========================================================

def start_scheduler():
    """
    تشغيل Scheduler في Thread مستقل.

    يعيد كائن Thread حتى يستطيع main.py
    الاحتفاظ به عند الحاجة.
    """

    thread = threading.Thread(
        target=scheduler_worker,
        daemon=True,
        name="adhkar-scheduler"
    )

    thread.start()

    return thread