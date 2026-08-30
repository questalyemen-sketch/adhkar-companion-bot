import sqlite3
from datetime import datetime
from config import DATABASE_NAME


# =========================================================
# Database Connection
# =========================================================

def get_connection():
    """
    إنشاء اتصال بقاعدة البيانات.
    """
    connection = sqlite3.connect(DATABASE_NAME)
    connection.row_factory = sqlite3.Row
    return connection


# =========================================================
# Initialize Database
# =========================================================

def init_database():
    """
    إنشاء الجداول المطلوبة إذا لم تكن موجودة.
    """

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER UNIQUE NOT NULL,
            first_name TEXT,
            username TEXT,

            timezone TEXT DEFAULT 'UTC',

            morning_enabled INTEGER DEFAULT 1,
            evening_enabled INTEGER DEFAULT 1,

            morning_time TEXT DEFAULT '06:00',
            evening_time TEXT DEFAULT '18:00',

            last_morning_sent TEXT,
            last_evening_sent TEXT,

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
    """

    now = datetime.utcnow().isoformat()

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO users (
            telegram_id,
            first_name,
            username,
            created_at,
            updated_at
        )
        VALUES (?, ?, ?, ?, ?)

        ON CONFLICT(telegram_id)
        DO UPDATE SET
            first_name = excluded.first_name,
            username = excluded.username,
            updated_at = excluded.updated_at
    """, (
        telegram_id,
        first_name,
        username,
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
    الحصول على بيانات مستخدم.
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
# Update Timezone
# =========================================================

def update_timezone(telegram_id, timezone):
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
        timezone,
        datetime.utcnow().isoformat(),
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
            datetime.utcnow().isoformat(),
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
            datetime.utcnow().isoformat(),
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
            datetime.utcnow().isoformat(),
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
            datetime.utcnow().isoformat(),
            telegram_id
        ))

    connection.commit()
    connection.close()


# =========================================================
# Get All Reminder Users
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
# Mark Morning As Sent
# =========================================================

def mark_morning_sent(telegram_id, date):
    """
    تسجيل أن أذكار الصباح أُرسلت للمستخدم في هذا التاريخ.
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
        datetime.utcnow().isoformat(),
        telegram_id
    ))

    connection.commit()
    connection.close()


# =========================================================
# Mark Evening As Sent
# =========================================================

def mark_evening_sent(telegram_id, date):
    """
    تسجيل أن أذكار المساء أُرسلت للمستخدم في هذا التاريخ.
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
        datetime.utcnow().isoformat(),
        telegram_id
    ))

    connection.commit()
    connection.close()