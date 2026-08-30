# =========================================================
# Adhkar Companion
# Database Manager
# SQLite User Settings & Reminder Storage
# =========================================================

import os
import re
import sqlite3
from datetime import datetime, timezone

from config import (
    DATABASE_NAME,
    DEFAULT_MORNING_TIME,
    DEFAULT_EVENING_TIME,
)


# =========================================================
# Constants
# =========================================================

TIME_PATTERN = re.compile(r"^(?:[01]\d|2[0-3]):[0-5]\d$")


# =========================================================
# Database Connection
# =========================================================

def get_connection():
    """
    إنشاء اتصال آمن بقاعدة البيانات.

    يتم تفعيل:
    - WAL لتحسين التعامل مع القراءة والكتابة.
    - foreign_keys.
    - row_factory لإرجاع الصفوف كـ sqlite3.Row.
    """

    database_dir = os.path.dirname(
        os.path.abspath(DATABASE_NAME)
    )

    if database_dir:
        os.makedirs(
            database_dir,
            exist_ok=True
        )

    connection = sqlite3.connect(
        DATABASE_NAME,
        timeout=30,
        check_same_thread=False,
    )

    connection.row_factory = sqlite3.Row

    connection.execute("PRAGMA journal_mode=WAL")
    connection.execute("PRAGMA foreign_keys=ON")

    return connection


# =========================================================
# Current UTC Time
# =========================================================

def utc_now():
    """
    الحصول على الوقت الحالي بتوقيت UTC
    بصيغة ISO 8601.
    """

    return datetime.now(
        timezone.utc
    ).isoformat()


# =========================================================
# Validate Time
# =========================================================

def is_valid_time(time_value):
    """
    التحقق من صحة الوقت.

    الصيغة المطلوبة:
        HH:MM

    أمثلة:
        06:00 -> True
        18:30 -> True
        25:00 -> False
        6:00  -> False
    """

    if not time_value:
        return False

    return bool(
        TIME_PATTERN.fullmatch(
            str(time_value).strip()
        )
    )


# =========================================================
# Initialize Database
# =========================================================

def init_database():
    """
    إنشاء قاعدة البيانات والجداول المطلوبة.

    إذا كانت قاعدة البيانات قديمة،
    تتم إضافة الأعمدة الناقصة تلقائيًا.
    """

    with get_connection() as connection:

        cursor = connection.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                telegram_id INTEGER UNIQUE NOT NULL,

                first_name TEXT DEFAULT '',
                username TEXT DEFAULT '',

                timezone TEXT DEFAULT NULL,

                morning_enabled INTEGER DEFAULT 1,
                evening_enabled INTEGER DEFAULT 1,

                morning_time TEXT DEFAULT '06:00',
                evening_time TEXT DEFAULT '18:00',

                last_morning_sent TEXT DEFAULT NULL,
                last_evening_sent TEXT DEFAULT NULL,

                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)

        connection.commit()

        # -------------------------------------------------
        # إصلاح قواعد البيانات القديمة
        # -------------------------------------------------

        cursor.execute("""
            PRAGMA table_info(users)
        """)

        existing_columns = {
            row["name"]
            for row in cursor.fetchall()
        }

        required_columns = {
            "first_name": "TEXT DEFAULT ''",
            "username": "TEXT DEFAULT ''",
            "timezone": "TEXT DEFAULT NULL",
            "morning_enabled": "INTEGER DEFAULT 1",
            "evening_enabled": "INTEGER DEFAULT 1",
            "morning_time": "TEXT DEFAULT '06:00'",
            "evening_time": "TEXT DEFAULT '18:00'",
            "last_morning_sent": "TEXT DEFAULT NULL",
            "last_evening_sent": "TEXT DEFAULT NULL",
            "created_at": "TEXT",
            "updated_at": "TEXT",
        }

        for column, definition in required_columns.items():

            if column not in existing_columns:

                cursor.execute(
                    f"ALTER TABLE users "
                    f"ADD COLUMN {column} {definition}"
                )

        connection.commit()


# =========================================================
# Add / Update User
# =========================================================

def add_user(
    telegram_id,
    first_name="",
    username=""
):
    """
    إضافة مستخدم جديد أو تحديث بيانات مستخدم موجود.

    المستخدم الجديد:
    - timezone = NULL
    - morning_enabled = 1
    - evening_enabled = 1
    - يستخدم أوقات config.py الافتراضية.

    المستخدم الموجود:
    - يتم تحديث الاسم واسم المستخدم فقط.
    - لا يتم تغيير إعداداته.
    """

    now = utc_now()

    morning_time = (
        DEFAULT_MORNING_TIME
        if is_valid_time(DEFAULT_MORNING_TIME)
        else "06:00"
    )

    evening_time = (
        DEFAULT_EVENING_TIME
        if is_valid_time(DEFAULT_EVENING_TIME)
        else "18:00"
    )

    with get_connection() as connection:

        connection.execute("""
            INSERT INTO users (
                telegram_id,
                first_name,
                username,
                timezone,
                morning_enabled,
                evening_enabled,
                morning_time,
                evening_time,
                last_morning_sent,
                last_evening_sent,
                created_at,
                updated_at
            )
            VALUES (
                ?,
                ?,
                ?,
                NULL,
                1,
                1,
                ?,
                ?,
                NULL,
                NULL,
                ?,
                ?
            )

            ON CONFLICT(telegram_id)
            DO UPDATE SET
                first_name = excluded.first_name,
                username = excluded.username,
                updated_at = excluded.updated_at
        """, (
            telegram_id,
            first_name or "",
            username or "",
            morning_time,
            evening_time,
            now,
            now,
        ))

        connection.commit()


# =========================================================
# Get User
# =========================================================

def get_user(telegram_id):
    """
    الحصول على بيانات المستخدم بواسطة Telegram ID.
    """

    with get_connection() as connection:

        cursor = connection.execute("""
            SELECT *
            FROM users
            WHERE telegram_id = ?
        """, (telegram_id,))

        return cursor.fetchone()


# =========================================================
# Check User Exists
# =========================================================

def user_exists(telegram_id):
    """
    التحقق من وجود المستخدم.
    """

    with get_connection() as connection:

        cursor = connection.execute("""
            SELECT 1
            FROM users
            WHERE telegram_id = ?
            LIMIT 1
        """, (telegram_id,))

        return cursor.fetchone() is not None


# =========================================================
# Check Timezone
# =========================================================

def has_timezone(telegram_id):
    """
    التحقق من وجود منطقة زمنية للمستخدم.
    """

    user = get_user(telegram_id)

    if not user:
        return False

    timezone_name = user["timezone"]

    return (
        timezone_name is not None
        and str(timezone_name).strip() != ""
    )


# =========================================================
# Get User Timezone
# =========================================================

def get_user_timezone(telegram_id):
    """
    الحصول على المنطقة الزمنية للمستخدم.
    """

    user = get_user(telegram_id)

    if not user:
        return None

    return user["timezone"]


# =========================================================
# Update Timezone
# =========================================================

def update_timezone(
    telegram_id,
    timezone_name
):
    """
    تحديث المنطقة الزمنية للمستخدم.

    ملاحظة:
    التحقق من صحة المنطقة الزمنية يتم في
    timezone_utils.py قبل استدعاء هذه الدالة.
    """

    if not timezone_name:
        return False

    timezone_name = str(
        timezone_name
    ).strip()

    if not timezone_name:
        return False

    with get_connection() as connection:

        cursor = connection.execute("""
            UPDATE users
            SET
                timezone = ?,
                updated_at = ?
            WHERE telegram_id = ?
        """, (
            timezone_name,
            utc_now(),
            telegram_id,
        ))

        connection.commit()

        return cursor.rowcount > 0


# =========================================================
# Clear Timezone
# =========================================================

def clear_timezone(telegram_id):
    """
    حذف المنطقة الزمنية للمستخدم.

    بعد الحذف لن تعمل التذكيرات التلقائية.
    """

    with get_connection() as connection:

        cursor = connection.execute("""
            UPDATE users
            SET
                timezone = NULL,
                last_morning_sent = NULL,
                last_evening_sent = NULL,
                updated_at = ?
            WHERE telegram_id = ?
        """, (
            utc_now(),
            telegram_id,
        ))

        connection.commit()

        return cursor.rowcount > 0


# =========================================================
# Update Morning Settings
# =========================================================

def update_morning_settings(
    telegram_id,
    enabled=None,
    time=None
):
    """
    تحديث إعدادات أذكار الصباح.

    enabled:
        True  = تشغيل
        False = إيقاف

    time:
        HH:MM
    """

    updates = []
    values = []

    if enabled is not None:

        updates.append(
            "morning_enabled = ?"
        )

        values.append(
            int(bool(enabled))
        )

    if time is not None:

        time = str(time).strip()

        if not is_valid_time(time):
            return False

        updates.append(
            "morning_time = ?"
        )

        values.append(time)

        # عند تغيير الوقت نسمح بإرسال التذكير
        # مرة أخرى في الموعد الجديد.
        updates.append(
            "last_morning_sent = NULL"
        )

    if not updates:
        return False

    updates.append(
        "updated_at = ?"
    )

    values.append(
        utc_now()
    )

    values.append(
        telegram_id
    )

    query = f"""
        UPDATE users
        SET {", ".join(updates)}
        WHERE telegram_id = ?
    """

    with get_connection() as connection:

        cursor = connection.execute(
            query,
            values
        )

        connection.commit()

        return cursor.rowcount > 0


# =========================================================
# Update Evening Settings
# =========================================================

def update_evening_settings(
    telegram_id,
    enabled=None,
    time=None
):
    """
    تحديث إعدادات أذكار المساء.

    enabled:
        True  = تشغيل
        False = إيقاف

    time:
        HH:MM
    """

    updates = []
    values = []

    if enabled is not None:

        updates.append(
            "evening_enabled = ?"
        )

        values.append(
            int(bool(enabled))
        )

    if time is not None:

        time = str(time).strip()

        if not is_valid_time(time):
            return False

        updates.append(
            "evening_time = ?"
        )

        values.append(time)

        updates.append(
            "last_evening_sent = NULL"
        )

    if not updates:
        return False

    updates.append(
        "updated_at = ?"
    )

    values.append(
        utc_now()
    )

    values.append(
        telegram_id
    )

    query = f"""
        UPDATE users
        SET {", ".join(updates)}
        WHERE telegram_id = ?
    """

    with get_connection() as connection:

        cursor = connection.execute(
            query,
            values
        )

        connection.commit()

        return cursor.rowcount > 0


# =========================================================
# Get All Users
# =========================================================

def get_all_users():
    """
    الحصول على جميع المستخدمين.
    """

    with get_connection() as connection:

        cursor = connection.execute("""
            SELECT *
            FROM users
            ORDER BY id ASC
        """)

        return cursor.fetchall()


# =========================================================
# Get Reminder Users
# =========================================================

def get_reminder_users():
    """
    الحصول على المستخدمين المؤهلين للتذكيرات.
    """

    with get_connection() as connection:

        cursor = connection.execute("""
            SELECT *
            FROM users
            WHERE timezone IS NOT NULL
              AND TRIM(timezone) != ''
              AND (
                  morning_enabled = 1
                  OR evening_enabled = 1
              )
            ORDER BY id ASC
        """)

        return cursor.fetchall()


# =========================================================
# Get Morning Reminder Users
# =========================================================

def get_morning_reminder_users():
    """
    المستخدمون الذين لديهم تذكير صباحي مفعّل.
    """

    with get_connection() as connection:

        cursor = connection.execute("""
            SELECT *
            FROM users
            WHERE timezone IS NOT NULL
              AND TRIM(timezone) != ''
              AND morning_enabled = 1
            ORDER BY id ASC
        """)

        return cursor.fetchall()


# =========================================================
# Get Evening Reminder Users
# =========================================================

def get_evening_reminder_users():
    """
    المستخدمون الذين لديهم تذكير مسائي مفعّل.
    """

    with get_connection() as connection:

        cursor = connection.execute("""
            SELECT *
            FROM users
            WHERE timezone IS NOT NULL
              AND TRIM(timezone) != ''
              AND evening_enabled = 1
            ORDER BY id ASC
        """)

        return cursor.fetchall()


# =========================================================
# Mark Morning As Sent
# =========================================================

def mark_morning_sent(
    telegram_id,
    date
):
    """
    تسجيل تاريخ إرسال أذكار الصباح.

    date:
        YYYY-MM-DD
    """

    if not date:
        return False

    with get_connection() as connection:

        cursor = connection.execute("""
            UPDATE users
            SET
                last_morning_sent = ?,
                updated_at = ?
            WHERE telegram_id = ?
        """, (
            date,
            utc_now(),
            telegram_id,
        ))

        connection.commit()

        return cursor.rowcount > 0


# =========================================================
# Mark Evening As Sent
# =========================================================

def mark_evening_sent(
    telegram_id,
    date
):
    """
    تسجيل تاريخ إرسال أذكار المساء.

    date:
        YYYY-MM-DD
    """

    if not date:
        return False

    with get_connection() as connection:

        cursor = connection.execute("""
            UPDATE users
            SET
                last_evening_sent = ?,
                updated_at = ?
            WHERE telegram_id = ?
        """, (
            date,
            utc_now(),
            telegram_id,
        ))

        connection.commit()

        return cursor.rowcount > 0


# =========================================================
# Get Last Morning Sent
# =========================================================

def get_last_morning_sent(telegram_id):
    """
    الحصول على آخر تاريخ لإرسال أذكار الصباح.
    """

    user = get_user(telegram_id)

    if not user:
        return None

    return user["last_morning_sent"]


# =========================================================
# Get Last Evening Sent
# =========================================================

def get_last_evening_sent(telegram_id):
    """
    الحصول على آخر تاريخ لإرسال أذكار المساء.
    """

    user = get_user(telegram_id)

    if not user:
        return None

    return user["last_evening_sent"]


# =========================================================
# Reset Reminder History
# =========================================================

def reset_reminder_history(telegram_id):
    """
    إعادة ضبط سجل إرسال الأذكار.
    """

    with get_connection() as connection:

        cursor = connection.execute("""
            UPDATE users
            SET
                last_morning_sent = NULL,
                last_evening_sent = NULL,
                updated_at = ?
            WHERE telegram_id = ?
        """, (
            utc_now(),
            telegram_id,
        ))

        connection.commit()

        return cursor.rowcount > 0


# =========================================================
# Toggle Morning Reminder
# =========================================================

def toggle_morning(telegram_id):
    """
    تبديل حالة تذكير الصباح.

    يعيد:
        True  = أصبح مفعّلًا
        False = أصبح متوقفًا
        None  = المستخدم غير موجود
    """

    user = get_user(telegram_id)

    if not user:
        return None

    new_status = not bool(
        user["morning_enabled"]
    )

    if update_morning_settings(
        telegram_id,
        enabled=new_status
    ):
        return new_status

    return None


# =========================================================
# Toggle Evening Reminder
# =========================================================

def toggle_evening(telegram_id):
    """
    تبديل حالة تذكير المساء.

    يعيد:
        True  = أصبح مفعّلًا
        False = أصبح متوقفًا
        None  = المستخدم غير موجود
    """

    user = get_user(telegram_id)

    if not user:
        return None

    new_status = not bool(
        user["evening_enabled"]
    )

    if update_evening_settings(
        telegram_id,
        enabled=new_status
    ):
        return new_status

    return None


# =========================================================
# Get Users By Timezone
# =========================================================

def get_users_by_timezone(timezone_name):
    """
    الحصول على جميع المستخدمين الذين
    يستخدمون منطقة زمنية محددة.
    """

    if not timezone_name:
        return []

    with get_connection() as connection:

        cursor = connection.execute("""
            SELECT *
            FROM users
            WHERE timezone = ?
            ORDER BY id ASC
        """, (
            timezone_name,
        ))

        return cursor.fetchall()


# =========================================================
# Cleanup / Close
# =========================================================

def vacuum_database():
    """
    تحسين قاعدة البيانات وتنظيف المساحة غير المستخدمة.

    يمكن تشغيلها يدويًا عند الحاجة.
    """

    with get_connection() as connection:
        connection.execute("VACUUM")


# =========================================================
# Module Test
# =========================================================

if __name__ == "__main__":

    print("[DATABASE] Initializing database...")

    init_database()

    print("[DATABASE] Database initialized successfully.")