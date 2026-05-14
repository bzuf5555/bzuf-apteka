import math
from dataclasses import dataclass


@dataclass
class Coordinates:
    lat: float
    lng: float


def haversine_km(p1: Coordinates, p2: Coordinates) -> float:
    """Ikki nuqta orasidagi masofani km da hisoblaydi (Haversine)."""
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
