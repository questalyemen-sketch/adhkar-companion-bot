import sqlite3
from datetime import datetime, timezone

from config import (
    DATABASE_NAME,
    DEFAULT_MORNING_TIME,
    DEFAULT_EVENING_TIME,
    DEFAULT_TIMEZONE,
)


# =========================================================
# Database Connection
# =========================================================

def get_connection():
    """
    إنشاء اتصال بقاعدة البيانات.
    """

    connection = sqlite3.connect(
        DATABASE_NAME,
        timeout=30
    )

    connection.row_factory = sqlite3.Row

    return connection


# =========================================================
# Current UTC Time
# =========================================================

def utc_now():
    """
    الحصول على الوقت الحالي بتوقيت UTC
    بصيغة ISO.
    """

    return datetime.now(timezone.utc).isoformat()


# =========================================================
# Initialize Database
# =========================================================

def init_database():
    """
    إنشاء قاعدة البيانات والجداول المطلوبة.
    """

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            telegram_id INTEGER UNIQUE NOT NULL,

            first_name TEXT,
            username TEXT,

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
    connection.close()


# =========================================================
# Add / Update User
# =========================================================

def add_user(
    telegram_id,
    first_name="",
    username=""
):
    """
    إضافة مستخدم جديد أو تحديث بياناته.

    المستخدم الجديد لا يحصل على منطقة زمنية تلقائيًا.
    يجب عليه اختيارها عند أول استخدام.
    """

    now = utc_now()

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO users (
            telegram_id,
            first_name,
            username,
            timezone,
            morning_enabled,
            evening_enabled,
            morning_time,
            evening_time,
            created_at,
            updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)

        ON CONFLICT(telegram_id)
        DO UPDATE SET
            first_name = excluded.first_name,
            username = excluded.username,
            updated_at = excluded.updated_at
    """, (
        telegram_id,
        first_name,
        username,
        DEFAULT_TIMEZONE,
        1,
        1,
        DEFAULT_MORNING_TIME,
        DEFAULT_EVENING_TIME,
        now,
        now
    ))

    connection.commit()
    connection.close()


# =========================================================
# Get User
# =========================================================

def get_user(telegram_id):
    """
    الحصول على بيانات مستخدم بواسطة Telegram ID.
    """

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT *
        FROM users
        WHERE telegram_id = ?
    """, (telegram_id,))

    user = cursor.fetchone()

    connection.close()

    return user


# =========================================================
# Check Timezone
# =========================================================

def has_timezone(telegram_id):
    """
    التحقق مما إذا كان المستخدم قد اختار
    منطقة زمنية أم لا.
    """

    user = get_user(telegram_id)

    if not user:
        return False

    return bool(user["timezone"])


# =========================================================
# Update Timezone
# =========================================================

def update_timezone(
    telegram_id,
    timezone_name
):
    """
    تحديث المنطقة الزمنية للمستخدم.
    """

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        UPDATE users
        SET timezone = ?,
            updated_at = ?
        WHERE telegram_id = ?
    """, (
        timezone_name,
        utc_now(),
        telegram_id
    ))

    connection.commit()
    connection.close()


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
    """

    connection = get_connection()
    cursor = connection.cursor()

    if enabled is not None:
        cursor.execute("""
            UPDATE users
            SET morning_enabled = ?,
                updated_at = ?
            WHERE telegram_id = ?
        """, (
            int(enabled),
            utc_now(),
            telegram_id
        ))

    if time is not None:
        cursor.execute("""
            UPDATE users
            SET morning_time = ?,
                updated_at = ?
            WHERE telegram_id = ?
        """, (
            time,
            utc_now(),
            telegram_id
        ))

    connection.commit()
    connection.close()


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
    """

    connection = get_connection()
    cursor = connection.cursor()

    if enabled is not None:
        cursor.execute("""
            UPDATE users
            SET evening_enabled = ?,
                updated_at = ?
            WHERE telegram_id = ?
        """, (
            int(enabled),
            utc_now(),
            telegram_id
        ))

    if time is not None:
        cursor.execute("""
            UPDATE users
            SET evening_time = ?,
                updated_at = ?
            WHERE telegram_id = ?
        """, (
            time,
            utc_now(),
            telegram_id
        ))

    connection.commit()
    connection.close()


# =========================================================
# Get All Users
# =========================================================

def get_all_users():
    """
    الحصول على جميع المستخدمين.
    """

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT *
        FROM users
        ORDER BY id ASC
    """)

    users = cursor.fetchall()

    connection.close()

    return users


# =========================================================
# Get Reminder Users
# =========================================================

def get_reminder_users():
    """
    الحصول على المستخدمين الذين:
    1. اختاروا منطقة زمنية.
    2. لديهم تذكير صباح أو مساء مفعّل.
    """

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT *
        FROM users
        WHERE timezone IS NOT NULL
          AND (
              morning_enabled = 1
              OR evening_enabled = 1
          )
        ORDER BY id ASC
    """)

    users = cursor.fetchall()

    connection.close()

    return users


# =========================================================
# Mark Morning As Sent
# =========================================================

def mark_morning_sent(
    telegram_id,
    date
):
    """
    تسجيل تاريخ إرسال أذكار الصباح.
    """

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        UPDATE users
        SET last_morning_sent = ?,
            updated_at = ?
        WHERE telegram_id = ?
    """, (
        date,
        utc_now(),
        telegram_id
    ))

    connection.commit()
    connection.close()


# =========================================================
# Mark Evening As Sent
# =========================================================

def mark_evening_sent(
    telegram_id,
    date
):
    """
    تسجيل تاريخ إرسال أذكار المساء.
    """

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        UPDATE users
        SET last_evening_sent = ?,
            updated_at = ?
        WHERE telegram_id = ?
    """, (
        date,
        utc_now(),
        telegram_id
    ))

    connection.commit()
    connection.close()


# =========================================================
# Reset Reminder History
# =========================================================

def reset_reminder_history(telegram_id):
    """
    إعادة ضبط سجل إرسال الأذكار للمستخدم.
    """

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        UPDATE users
        SET
            last_morning_sent = NULL,
            last_evening_sent = NULL,
            updated_at = ?
        WHERE telegram_id = ?
    """, (
        utc_now(),
        telegram_id
    ))

    connection.commit()
    connection.close()