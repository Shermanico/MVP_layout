"""
Funciones utilitarias para el sistema de coordinación multi-dron.
"""
import json
import time
from typing import Dict, Any, Optional
from datetime import datetime


def generate_drone_id(index: int) -> str:
    """Genera un ID único de dron."""
    return f"DRONE_{index:03d}"


def normalize_telemetry(raw_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normaliza los datos de telemetría en una estructura JSON limpia.
    Preserva campos específicos de Matrice 300 RTK si están presentes.
    
    Args:
        raw_data: Datos de telemetría crudos de MAVSDK o generador falso
        
    Returns:
        Diccionario de telemetría normalizado
    """
    normalized = {
        "drone_id": raw_data.get("drone_id", "UNKNOWN"),
        "latitude": float(raw_data.get("latitude", 0.0)),
        "longitude": float(raw_data.get("longitude", 0.0)),
        "altitude": float(raw_data.get("altitude", 0.0)),
        "heading": float(raw_data.get("heading", 0.0)),
        "velocity": float(raw_data.get("velocity", 0.0)),
        "battery": float(raw_data.get("battery", 100.0)),
        "status": raw_data.get("status", "idle"),
        "timestamp": raw_data.get("timestamp", time.time()),
    }
    
    # Preservar campos específicos de Matrice 300 RTK si están presentes
    if "vertical_speed" in raw_data:
        normalized["vertical_speed"] = float(raw_data.get("vertical_speed", 0.0))
    if "rtk_fix" in raw_data:
        normalized["rtk_fix"] = raw_data.get("rtk_fix", False)
    if "max_speed" in raw_data:
        normalized["max_speed"] = float(raw_data.get("max_speed", 23.0))
    if "max_altitude" in raw_data:
        normalized["max_altitude"] = float(raw_data.get("max_altitude", 5000.0))
    if "flight_time_remaining" in raw_data:
        normalized["flight_time_remaining"] = float(raw_data.get("flight_time_remaining", 0.0))
    
    return normalized


def create_poi(
    latitude: float,
    longitude: float,
    poi_type: str,
    description: str = "",
    created_by: str = "user"
) -> Dict[str, Any]:
    """
    Crea un diccionario de POI.
    
    Args:
        latitude: Latitud del POI
        longitude: Longitud del POI
        poi_type: Tipo de POI (hazard, target, checkpoint, etc.)
        description: Descripción opcional
        created_by: ID de usuario/dispositivo que creó el POI
        
    Returns:
        Diccionario de POI
    """
    return {
        "id": f"poi_{int(time.time() * 1000)}",
        "latitude": float(latitude),
        "longitude": float(longitude),
        "type": poi_type,
        "description": description,
        "timestamp": time.time(),
        "created_by": created_by,
    }


def format_timestamp(timestamp: float) -> str:
    """Formatea un timestamp Unix a una cadena legible."""
    return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")


def clamp_value(value: float, min_val: float, max_val: float) -> float:
    """Limita un valor entre min y max."""
    return max(min_val, min(max_val, value))

