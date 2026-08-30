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
    get_local_date,
)


# =========================================================
# Scheduler Configuration
# =========================================================

# عدد الثواني بين كل عملية فحص.
#
# 30 ثانية مناسبة حتى لا نفوّت وقت الإرسال
# بسبب اختلاف بسيط في وقت التنفيذ.
CHECK_INTERVAL = 30


# =========================================================
# Bot Reference
# =========================================================

_bot = None


def set_bot(bot):
    """
    حفظ كائن البوت لاستخدامه داخل الـ Scheduler.

    يتم استدعاؤها من main.py بعد إنشاء البوت.
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
    إرسال رسالة بأمان.

    إذا حدث خطأ مع مستخدم معين، لا يتوقف الـ Scheduler بالكامل.
    """

    if _bot is None:
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
# Morning Message
# =========================================================

def build_morning_message():
    """
    إنشاء رسالة أذكار الصباح.

    المحتوى التفصيلي سيتم ربطه لاحقًا
    بملف adhkar.py.
    """

    return (
        "🌅 <b>أذكار الصباح</b>\n\n"
        "حان الآن وقت أذكار الصباح.\n"
        "اجعل لسانك رطبًا بذكر الله 🤍"
    )


# =========================================================
# Evening Message
# =========================================================

def build_evening_message():
    """
    إنشاء رسالة أذكار المساء.

    المحتوى التفصيلي سيتم ربطه لاحقًا
    بملف adhkar.py.
    """

    return (
        "🌙 <b>أذكار المساء</b>\n\n"
        "حان الآن وقت أذكار المساء.\n"
        "اجعل لسانك رطبًا بذكر الله 🤍"
    )


# =========================================================
# Check Morning Reminder
# =========================================================

def check_morning_reminder(user):
    """
    فحص ما إذا كان وقت أذكار الصباح قد حان للمستخدم.
    """

    if not ENABLE_MORNING_REMINDER:
        return

    if not user["morning_enabled"]:
        return

    timezone_name = user["timezone"]

    if not timezone_name:
        return

    local_now = get_local_now(timezone_name)

    if local_now is None:
        return

    current_time = local_now.strftime("%H:%M")
    current_date = local_now.strftime("%Y-%m-%d")

    reminder_time = user["morning_time"] or DEFAULT_MORNING_TIME

    # هل حان وقت الإرسال؟
    if current_time != reminder_time:
        return

    # هل تم الإرسال اليوم بالفعل؟
    if user["last_morning_sent"] == current_date:
        return

    message = build_morning_message()

    sent = safe_send_message(
        user["telegram_id"],
        message
    )

    if sent:
        mark_morning_sent(
            user["telegram_id"],
            current_date
        )

        print(
            f"[SCHEDULER] Morning adhkar sent "
            f"to {user['telegram_id']} "
            f"({timezone_name})"
        )


# =========================================================
# Check Evening Reminder
# =========================================================

def check_evening_reminder(user):
    """
    فحص ما إذا كان وقت أذكار المساء قد حان للمستخدم.
    """

    if not ENABLE_EVENING_REMINDER:
        return

    if not user["evening_enabled"]:
        return

    timezone_name = user["timezone"]

    if not timezone_name:
        return

    local_now = get_local_now(timezone_name)

    if local_now is None:
        return

    current_time = local_now.strftime("%H:%M")
    current_date = local_now.strftime("%Y-%m-%d")

    reminder_time = user["evening_time"] or DEFAULT_EVENING_TIME

    # هل حان وقت الإرسال؟
    if current_time != reminder_time:
        return

    # هل تم الإرسال اليوم بالفعل؟
    if user["last_evening_sent"] == current_date:
        return

    message = build_evening_message()

    sent = safe_send_message(
        user["telegram_id"],
        message
    )

    if sent:
        mark_evening_sent(
            user["telegram_id"],
            current_date
        )

        print(
            f"[SCHEDULER] Evening adhkar sent "
            f"to {user['telegram_id']} "
            f"({timezone_name})"
        )


# =========================================================
# Scheduler Cycle
# =========================================================

def scheduler_cycle():
    """
    تنفيذ دورة واحدة من فحص المستخدمين.
    """

    try:
        users = get_reminder_users()

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

    print("[SCHEDULER] Scheduler started.")

    while True:

        try:
            scheduler_cycle()

        except Exception as error:
            print(
                f"[SCHEDULER] Unexpected error: {error}"
            )

        time.sleep(CHECK_INTERVAL)


# =========================================================
# Start Scheduler
# =========================================================

def start_scheduler():
    """
    تشغيل الـ Scheduler في Thread مستقل.
    """

    thread = threading.Thread(
        target=scheduler_worker,
        daemon=True,
        name="adhkar-scheduler"
    )

    thread.start()

    return thread