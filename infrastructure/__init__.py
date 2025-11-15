"""
Infraestructura - Configuración y utilidades compartidas.
"""
from infrastructure.config import (
    Config, POIType, DroneStatus, CHANNEL_TELEMETRY, CHANNEL_POI,
    RED, GREEN, BLUE, AMBER, GREY, GREY_200, GREY_300, GREY_600,
    generate_drone_id, normalize_telemetry, create_poi, format_timestamp, clamp_value
)

__all__ = [
    "Config", "POIType", "DroneStatus", "CHANNEL_TELEMETRY", "CHANNEL_POI",
    "RED", "GREEN", "BLUE", "AMBER", "GREY", "GREY_200", "GREY_300", "GREY_600",
    "generate_drone_id", "normalize_telemetry", "create_poi", "format_timestamp", "clamp_value"
]

