from datetime import datetime, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


# =========================================================
# Timezone Validation
# =========================================================

def is_valid_timezone(timezone_name):
    """
    التحقق من صحة اسم المنطقة الزمنية.

    مثال:
        Asia/Aden      -> True
        Asia/Riyadh    -> True
        Invalid/Zone   -> False
    """

    if not timezone_name:
        return False

    try:
        ZoneInfo(timezone_name)
        return True

    except ZoneInfoNotFoundError:
        return False


# =========================================================
# Get Timezone
# =========================================================

def get_timezone(timezone_name):
    """
    الحصول على كائن ZoneInfo للمنطقة الزمنية.

    يعيد None إذا كانت المنطقة غير صحيحة.
    """

    if not is_valid_timezone(timezone_name):
        return None

    try:
        return ZoneInfo(timezone_name)

    except ZoneInfoNotFoundError:
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
# Get Current Local Time String
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
# Convert UTC To Local Time
# =========================================================

def utc_to_local(utc_datetime, timezone_name):
    """
    تحويل وقت UTC إلى الوقت المحلي للمستخدم.
    """

    tz = get_timezone(timezone_name)

    if tz is None:
        return None

    if utc_datetime.tzinfo is None:
        utc_datetime = utc_datetime.replace(tzinfo=timezone.utc)

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

    target_time يجب أن يكون:
        HH:MM

    مثال:
        is_time_match("Asia/Aden", "06:00")
    """

    current_time = get_local_time(timezone_name)

    if current_time is None:
        return False

    return current_time == target_time


# =========================================================
# Get UTC Offset
# =========================================================

def get_utc_offset(timezone_name):
    """
    الحصول على فرق التوقيت عن UTC.

    مثال تقريبي:
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
    """

    local_time = get_local_now(timezone_name)

    if local_time is None:
        return None

    return local_time.strftime(time_format)


# =========================================================
# Get Timezone Display Name
# =========================================================

def get_timezone_display_name(timezone_name):
    """
    تحويل اسم المنطقة الزمنية إلى اسم مناسب للعرض.
    """

    timezone_names = {
        "Asia/Aden": "🇾🇪 اليمن",
        "Asia/Riyadh": "🇸🇦 السعودية",
        "Asia/Dubai": "🇦🇪 الإمارات",
        "Asia/Muscat": "🇴🇲 عُمان",
        "Asia/Qatar": "🇶🇦 قطر",
        "Asia/Bahrain": "🇧🇭 البحرين",
        "Asia/Kuwait": "🇰🇼 الكويت",
        "Asia/Baghdad": "🇮🇶 العراق",
        "Asia/Amman": "🇯🇴 الأردن",
        "Asia/Beirut": "🇱🇧 لبنان",

        "Africa/Cairo": "🇪🇬 مصر",
        "Africa/Tripoli": "🇱🇾 ليبيا",
        "Africa/Tunis": "🇹🇳 تونس",
        "Africa/Algiers": "🇩🇿 الجزائر",
        "Africa/Casablanca": "🇲🇦 المغرب",
        "Africa/Khartoum": "🇸🇩 السودان",

        "Europe/London": "🇬🇧 بريطانيا",
        "Europe/Paris": "🇫🇷 فرنسا",
        "Europe/Berlin": "🇩🇪 ألمانيا",
        "Europe/Istanbul": "🇹🇷 تركيا",

        "America/New_York": "🇺🇸 أمريكا - نيويورك",
        "America/Toronto": "🇨🇦 كندا - تورنتو",
    }

    return timezone_names.get(
        timezone_name,
        timezone_name
    )


# =========================================================
# Get Timezone Information
# =========================================================

def get_timezone_info(timezone_name):
    """
    الحصول على معلومات كاملة عن المنطقة الزمنية.
    """

    if not is_valid_timezone(timezone_name):
        return None

    return {
        "name": timezone_name,
        "display_name": get_timezone_display_name(timezone_name),
        "current_time": get_local_time(timezone_name),
        "current_date": get_local_date(timezone_name),
        "utc_offset": get_utc_offset(timezone_name),
    }