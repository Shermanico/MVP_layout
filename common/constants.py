"""
Constantes utilizadas en toda la aplicación.
"""
from enum import Enum


class POIType(str, Enum):
    """Tipos de Puntos de Interés."""
    HAZARD = "hazard"
    TARGET = "target"
    CHECKPOINT = "checkpoint"
    LANDING_ZONE = "landing_zone"
    OTHER = "other"


class DroneStatus(str, Enum):
    """Estados de estado del dron."""
    IDLE = "idle"
    ARMED = "armed"
    TAKEOFF = "takeoff"
    FLYING = "flying"
    LANDING = "landing"
    ERROR = "error"


# Nombres de canales Pub/Sub para Flet
CHANNEL_TELEMETRY = "telemetry"
CHANNEL_POI = "poi"
CHANNEL_DRONE_LIST = "drone_list"
CHANNEL_EVENT_LOG = "event_log"

# Nombres de campos de telemetría
TELEMETRY_FIELDS = [
    "drone_id",
    "latitude",
    "longitude",
    "altitude",
    "heading",
    "velocity",
    "battery",
    "status",
    "timestamp",
]

