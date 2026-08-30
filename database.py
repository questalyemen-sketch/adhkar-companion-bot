import sqlite3
from datetime import datetime, timezone

from config import (
    DATABASE_NAME,
    DEFAULT_MORNING_TIME,
    DEFAULT_EVENING_TIME,
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
    بصيغة ISO 8601.
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

            first_name TEXT DEFAULT '',
            username TEXT DEFAULT '',

            -- NULL تعني أن المستخدم لم يختر المنطقة الزمنية بعد
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
    إضافة مستخدم جديد أو تحديث بيانات مستخدم موجود.

    المستخدم الجديد:
    - لا يحصل على منطقة زمنية تلقائيًا.
    - يحصل على أوقات التذكير الافتراضية.
    - يتم تفعيل تذكيرات الصباح والمساء افتراضيًا.

    إذا كان المستخدم موجودًا مسبقًا:
    - يتم تحديث الاسم واسم المستخدم فقط.
    - لا يتم تغيير المنطقة الزمنية أو إعدادات التذكير.
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
        VALUES (?, ?, ?, NULL, 1, 1, ?, ?, ?, ?)

        ON CONFLICT(telegram_id)
        DO UPDATE SET
            first_name = excluded.first_name,
            username = excluded.username,
            updated_at = excluded.updated_at
    """, (
        telegram_id,
        first_name or "",
        username or "",
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
# Check User Exists
# =========================================================

def user_exists(telegram_id):
    """
    التحقق من وجود المستخدم في قاعدة البيانات.
    """

    return get_user(telegram_id) is not None


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

    يعيد:
        اسم المنطقة الزمنية أو None
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

    مثال:
        Asia/Aden
        Africa/Cairo
        Asia/Riyadh
    """

    if not timezone_name:
        return False

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        UPDATE users
        SET
            timezone = ?,
            updated_at = ?
        WHERE telegram_id = ?
    """, (
        timezone_name,
        utc_now(),
        telegram_id
    ))

    updated = cursor.rowcount > 0

    connection.commit()
    connection.close()

    return updated


# =========================================================
# Clear Timezone
# =========================================================

def clear_timezone(telegram_id):
    """
    حذف المنطقة الزمنية للمستخدم.

    بعد ذلك لن يتم إرسال التذكيرات التلقائية
    حتى يختار المستخدم منطقة زمنية جديدة.
    """

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        UPDATE users
        SET
            timezone = NULL,
            updated_at = ?
        WHERE telegram_id = ?
    """, (
        utc_now(),
        telegram_id
    ))

    updated = cursor.rowcount > 0

    connection.commit()
    connection.close()

    return updated


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
        بصيغة HH:MM
    """

    connection = get_connection()
    cursor = connection.cursor()

    updates = []
    values = []

    if enabled is not None:
        updates.append("morning_enabled = ?")
        values.append(int(bool(enabled)))

    if time is not None:
        updates.append("morning_time = ?")
        values.append(time)

    if not updates:
        connection.close()
        return False

    updates.append("updated_at = ?")
    values.append(utc_now())
    values.append(telegram_id)

    query = f"""
        UPDATE users
        SET {", ".join(updates)}
        WHERE telegram_id = ?
    """

    cursor.execute(query, values)

    updated = cursor.rowcount > 0

    connection.commit()
    connection.close()

    return updated


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
        بصيغة HH:MM
    """

    connection = get_connection()
    cursor = connection.cursor()

    updates = []
    values = []

    if enabled is not None:
        updates.append("evening_enabled = ?")
        values.append(int(bool(enabled)))

    if time is not None:
        updates.append("evening_time = ?")
        values.append(time)

    if not updates:
        connection.close()
        return False

    updates.append("updated_at = ?")
    values.append(utc_now())
    values.append(telegram_id)

    query = f"""
        UPDATE users
        SET {", ".join(updates)}
        WHERE telegram_id = ?
    """

    cursor.execute(query, values)

    updated = cursor.rowcount > 0

    connection.commit()
    connection.close()

    return updated


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
    الحصول على المستخدمين المؤهلين للتذكيرات التلقائية.

    الشروط:
    1. المستخدم موجود.
    2. اختار منطقة زمنية.
    3. يوجد تذكير صباح أو مساء مفعّل.
    """

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
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

    users = cursor.fetchall()

    connection.close()

    return users


# =========================================================
# Get Morning Reminder Users
# =========================================================

def get_morning_reminder_users():
    """
    الحصول على المستخدمين الذين لديهم
    تذكير أذكار الصباح مفعّل ومنطقة زمنية محددة.
    """

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT *
        FROM users
        WHERE timezone IS NOT NULL
          AND TRIM(timezone) != ''
          AND morning_enabled = 1
        ORDER BY id ASC
    """)

    users = cursor.fetchall()

    connection.close()

    return users


# =========================================================
# Get Evening Reminder Users
# =========================================================

def get_evening_reminder_users():
    """
    الحصول على المستخدمين الذين لديهم
    تذكير أذكار المساء مفعّل ومنطقة زمنية محددة.
    """

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT *
        FROM users
        WHERE timezone IS NOT NULL
          AND TRIM(timezone) != ''
          AND evening_enabled = 1
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

    date:
        التاريخ المحلي للمستخدم بصيغة YYYY-MM-DD.
    """

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        UPDATE users
        SET
            last_morning_sent = ?,
            updated_at = ?
        WHERE telegram_id = ?
    """, (
        date,
        utc_now(),
        telegram_id
    ))

    updated = cursor.rowcount > 0

    connection.commit()
    connection.close()

    return updated


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
        التاريخ المحلي للمستخدم بصيغة YYYY-MM-DD.
    """

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        UPDATE users
        SET
            last_evening_sent = ?,
            updated_at = ?
        WHERE telegram_id = ?
    """, (
        date,
        utc_now(),
        telegram_id
    ))

    updated = cursor.rowcount > 0

    connection.commit()
    connection.close()

    return updated


# =========================================================
# Get Last Morning Sent
# =========================================================

def get_last_morning_sent(telegram_id):
    """
    الحصول على آخر تاريخ أُرسلت فيه أذكار الصباح.
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
    الحصول على آخر تاريخ أُرسلت فيه أذكار المساء.
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

    updated = cursor.rowcount > 0

    connection.commit()
    connection.close()

    return updated


# =========================================================
# Toggle Morning Reminder
# =========================================================

def toggle_morning(telegram_id):
    """
    تبديل حالة تذكير الصباح.

    يعيد:
        True  إذا أصبح مفعّلًا.
        False إذا أصبح متوقفًا.
        None إذا لم يكن المستخدم موجودًا.
    """

    user = get_user(telegram_id)

    if not user:
        return None

    new_status = 0 if user["morning_enabled"] else 1

    update_morning_settings(
        telegram_id,
        enabled=bool(new_status)
    )

    return bool(new_status)


# =========================================================
# Toggle Evening Reminder
# =========================================================

def toggle_evening(telegram_id):
    """
    تبديل حالة تذكير المساء.

    يعيد:
        True  إذا أصبح مفعّلًا.
        False إذا أصبح متوقفًا.
        None إذا لم يكن المستخدم موجودًا.
    """

    user = get_user(telegram_id)

    if not user:
        return None

    new_status = 0 if user["evening_enabled"] else 1

    update_evening_settings(
        telegram_id,
        enabled=bool(new_status)
    )

    return bool(new_status)