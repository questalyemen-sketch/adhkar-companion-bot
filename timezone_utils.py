from datetime import datetime, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


# =========================================================
# Timezone Validation
# =========================================================

def is_valid_timezone(timezone_name):
    """
    التحقق من صحة اسم المنطقة الزمنية.

    أمثلة:
        Asia/Aden      -> True
        Asia/Riyadh    -> True
        Invalid/Zone   -> False
        None           -> False
    """

    if not isinstance(timezone_name, str):
        return False

    timezone_name = timezone_name.strip()

    if not timezone_name:
        return False

    try:
        ZoneInfo(timezone_name)
        return True

    except (ZoneInfoNotFoundError, ValueError):
        return False


# =========================================================
# Get Timezone
# =========================================================

def get_timezone(timezone_name):
    """
    الحصول على كائن ZoneInfo للمنطقة الزمنية.

    يعيد:
        ZoneInfo
    أو:
        None إذا كانت المنطقة غير صحيحة.
    """

    if not is_valid_timezone(timezone_name):
        return None

    try:
        return ZoneInfo(timezone_name)

    except (ZoneInfoNotFoundError, ValueError):
        return None


# =========================================================
# Get Current UTC Time
# =========================================================

def get_utc_now():
    """
    الحصول على الوقت الحالي بتوقيت UTC.
    """

    return datetime.now(timezone.utc)


# =========================================================
# Get Current Local Time
# =========================================================

def get_local_now(timezone_name):
    """
    الحصول على الوقت الحالي حسب المنطقة الزمنية للمستخدم.

    مثال:
        Asia/Aden
        Asia/Riyadh
        Africa/Cairo
    """

    tz = get_timezone(timezone_name)

    if tz is None:
        return None

    return datetime.now(tz)


# =========================================================
# Get Current Local Date
# =========================================================

def get_local_date(timezone_name):
    """
    الحصول على تاريخ اليوم حسب توقيت المستخدم.

    النتيجة:
        YYYY-MM-DD
    """

    local_time = get_local_now(timezone_name)

    if local_time is None:
        return None

    return local_time.strftime("%Y-%m-%d")


# =========================================================
# Get Current Local Time
# =========================================================

def get_local_time(timezone_name):
    """
    الحصول على الوقت المحلي بصيغة HH:MM.
    """

    local_time = get_local_now(timezone_name)

    if local_time is None:
        return None

    return local_time.strftime("%H:%M")


# =========================================================
# Validate Time
# =========================================================

def is_valid_time(time_value):
    """
    التحقق من صحة الوقت بصيغة HH:MM.

    أمثلة:
        06:00 -> True
        18:30 -> True
        25:00 -> False
        6:00  -> False
    """

    if not isinstance(time_value, str):
        return False

    time_value = time_value.strip()

    if len(time_value) != 5:
        return False

    if time_value[2] != ":":
        return False

    hour = time_value[:2]
    minute = time_value[3:]

    if not (hour.isdigit() and minute.isdigit()):
        return False

    hour = int(hour)
    minute = int(minute)

    return (
        0 <= hour <= 23
        and 0 <= minute <= 59
    )


# =========================================================
# Convert UTC To Local Time
# =========================================================

def utc_to_local(utc_datetime, timezone_name):
    """
    تحويل وقت UTC إلى الوقت المحلي للمستخدم.

    إذا كان datetime بدون timezone،
    يتم اعتباره UTC.
    """

    tz = get_timezone(timezone_name)

    if tz is None:
        return None

    if not isinstance(utc_datetime, datetime):
        return None

    if utc_datetime.tzinfo is None:
        utc_datetime = utc_datetime.replace(
            tzinfo=timezone.utc
        )

    return utc_datetime.astimezone(tz)


# =========================================================
# Compare Local Time
# =========================================================

def is_time_match(
    timezone_name,
    target_time
):
    """
    التحقق مما إذا كان الوقت الحالي للمستخدم
    يطابق وقت التذكير.

    target_time:
        HH:MM

    مثال:
        is_time_match("Asia/Aden", "06:00")
    """

    if not is_valid_timezone(timezone_name):
        return False

    if not is_valid_time(target_time):
        return False

    current_time = get_local_time(timezone_name)

    if current_time is None:
        return False

    return current_time == target_time


# =========================================================
# Get UTC Offset
# =========================================================

def get_utc_offset(timezone_name):
    """
    الحصول على فرق التوقيت الحالي عن UTC.

    مثال:
        Asia/Aden -> UTC+03:00
    """

    local_time = get_local_now(timezone_name)

    if local_time is None:
        return None

    offset = local_time.utcoffset()

    if offset is None:
        return None

    total_seconds = int(offset.total_seconds())

    sign = "+" if total_seconds >= 0 else "-"

    total_seconds = abs(total_seconds)

    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60

    return f"UTC{sign}{hours:02d}:{minutes:02d}"


# =========================================================
# Format Local Time
# =========================================================

def format_local_time(
    timezone_name,
    time_format="%H:%M"
):
    """
    تنسيق الوقت المحلي للمستخدم.

    مثال:
        format_local_time("Asia/Aden")
        -> 06:15
    """

    local_time = get_local_now(timezone_name)

    if local_time is None:
        return None

    return local_time.strftime(time_format)


# =========================================================
# Timezone Display Names
# =========================================================

TIMEZONE_NAMES = {

    # -----------------------------------------------------
    # Arabian Peninsula
    # -----------------------------------------------------

    "Asia/Aden": "🇾🇪 اليمن",
    "Asia/Riyadh": "🇸🇦 السعودية",
    "Asia/Dubai": "🇦🇪 الإمارات",
    "Asia/Muscat": "🇴🇲 عُمان",
    "Asia/Qatar": "🇶🇦 قطر",
    "Asia/Bahrain": "🇧🇭 البحرين",
    "Asia/Kuwait": "🇰🇼 الكويت",

    # -----------------------------------------------------
    # Middle East
    # -----------------------------------------------------

    "Asia/Baghdad": "🇮🇶 العراق",
    "Asia/Amman": "🇯🇴 الأردن",
    "Asia/Beirut": "🇱🇧 لبنان",
    "Asia/Damascus": "🇸🇾 سوريا",
    "Asia/Jerusalem": "🇵🇸 فلسطين",
    "Europe/Istanbul": "🇹🇷 تركيا",

    # -----------------------------------------------------
    # North Africa
    # -----------------------------------------------------

    "Africa/Cairo": "🇪🇬 مصر",
    "Africa/Tripoli": "🇱🇾 ليبيا",
    "Africa/Tunis": "🇹🇳 تونس",
    "Africa/Algiers": "🇩🇿 الجزائر",
    "Africa/Casablanca": "🇲🇦 المغرب",
    "Africa/Khartoum": "🇸🇩 السودان",

    # -----------------------------------------------------
    # Europe
    # -----------------------------------------------------

    "Europe/London": "🇬🇧 بريطانيا",
    "Europe/Paris": "🇫🇷 فرنسا",
    "Europe/Berlin": "🇩🇪 ألمانيا",

    # -----------------------------------------------------
    # North America
    # -----------------------------------------------------

    "America/New_York": "🇺🇸 أمريكا - نيويورك",
    "America/Toronto": "🇨🇦 كندا - تورنتو",
}


# =========================================================
# Get Timezone Display Name
# =========================================================

def get_timezone_display_name(timezone_name):
    """
    تحويل اسم المنطقة الزمنية إلى اسم مناسب للعرض.
    """

    if not timezone_name:
        return None

    return TIMEZONE_NAMES.get(
        timezone_name,
        timezone_name
    )


# =========================================================
# Get Available Timezones
# =========================================================

def get_available_timezones():
    """
    الحصول على المناطق الزمنية المتاحة في واجهة البوت.

    النتيجة:
        قائمة من tuples:
        [
            ("🇾🇪 اليمن", "Asia/Aden"),
            ...
        ]
    """

    return [
        (display_name, timezone_name)
        for timezone_name, display_name
        in TIMEZONE_NAMES.items()
    ]


# =========================================================
# Get Timezone Information
# =========================================================

def get_timezone_info(timezone_name):
    """
    الحصول على معلومات كاملة عن المنطقة الزمنية.

    يعيد:
        {
            "name": ...,
            "display_name": ...,
            "current_time": ...,
            "current_date": ...,
            "utc_offset": ...
        }

    أو None إذا كانت المنطقة غير صحيحة.
    """

    if not is_valid_timezone(timezone_name):
        return None

    return {
        "name": timezone_name,
        "display_name": get_timezone_display_name(
            timezone_name
        ),
        "current_time": get_local_time(
            timezone_name
        ),
        "current_date": get_local_date(
            timezone_name
        ),
        "utc_offset": get_utc_offset(
            timezone_name
        ),
    }