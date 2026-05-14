import math
import re
import datetime
from dataclasses import dataclass

TZ_TASHKENT = datetime.timezone(datetime.timedelta(hours=5))


@dataclass
class Coordinates:
    lat: float
    lng: float


def haversine_km(p1: Coordinates, p2: Coordinates) -> float:
    R = 6371.0
    phi1 = math.radians(p1.lat)
    phi2 = math.radians(p2.lat)
    dphi = math.radians(p2.lat - p1.lat)
    dlam = math.radians(p2.lng - p1.lng)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    return round(2 * R * math.asin(math.sqrt(a)), 2)


def format_distance(km: float) -> str:
    if km < 1.0:
        return f"{int(km * 1000)} m"
    return f"{km:.1f} km"


def is_open_now(working_hours: str) -> tuple[bool, str]:
    """
    Toshkent vaqti (UTC+5) bo'yicha dorixona ochiqligini tekshiradi.
    Returns: (is_open, display_text)
    """
    if not working_hours:
        return True, "?"

    wh = working_hours.strip().lower()
    if wh in ("24/7", "круглосуточно", "doimo", "tungi", "uzluksiz"):
        return True, "24/7 🟢"

    now = datetime.datetime.now(TZ_TASHKENT)

    # Parse "HH:MM-HH:MM" yoki "HH:MM – HH:MM"
    m = re.search(r"(\d{1,2})[:\.](\d{2})\s*[-–]\s*(\d{1,2})[:\.](\d{2})", working_hours)
    if not m:
        return True, working_hours

    oh, om, ch, cm = int(m[1]), int(m[2]), int(m[3]), int(m[4])
    open_min = oh * 60 + om
    close_min = ch * 60 + cm
    now_min = now.hour * 60 + now.minute

    if close_min <= open_min:  # Tungi ish: 22:00-06:00
        is_open = now_min >= open_min or now_min < close_min
    else:
        is_open = open_min <= now_min < close_min

    status = f"{oh:02d}:{om:02d}–{ch:02d}:{cm:02d}"
    indicator = "🟢" if is_open else "🔴"
    return is_open, f"{status} {indicator}"
