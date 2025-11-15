"""
Data Transfer Objects (DTOs).
Objetos de transferencia de datos entre capas.
"""
from dataclasses import dataclass
from typing import Dict, Any, Optional


@dataclass
class TelemetryDTO:
    """DTO para telemetría de dron."""
    drone_id: str
    latitude: float
    longitude: float
    altitude: float
    heading: float
    velocity: float
    battery: float
    status: str
    timestamp: float
    vertical_speed: Optional[float] = None
    rtk_fix: Optional[bool] = None
    max_speed: Optional[float] = None
    max_altitude: Optional[float] = None
    flight_time_remaining: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte a diccionario."""
        data = {
            "drone_id": self.drone_id,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "altitude": self.altitude,
            "heading": self.heading,
            "velocity": self.velocity,
            "battery": self.battery,
            "status": self.status,
            "timestamp": self.timestamp,
        }
        if self.vertical_speed is not None:
            data["vertical_speed"] = self.vertical_speed
        if self.rtk_fix is not None:
            data["rtk_fix"] = self.rtk_fix
        if self.max_speed is not None:
            data["max_speed"] = self.max_speed
        if self.max_altitude is not None:
            data["max_altitude"] = self.max_altitude
        if self.flight_time_remaining is not None:
            data["flight_time_remaining"] = self.flight_time_remaining
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TelemetryDTO":
        """Crea desde un diccionario."""
        return cls(
            drone_id=data.get("drone_id", "UNKNOWN"),
            latitude=float(data.get("latitude", 0.0)),
            longitude=float(data.get("longitude", 0.0)),
            altitude=float(data.get("altitude", 0.0)),
            heading=float(data.get("heading", 0.0)),
            velocity=float(data.get("velocity", 0.0)),
            battery=float(data.get("battery", 100.0)),
            status=data.get("status", "idle"),
            timestamp=float(data.get("timestamp", 0.0)),
            vertical_speed=data.get("vertical_speed"),
            rtk_fix=data.get("rtk_fix"),
            max_speed=data.get("max_speed"),
            max_altitude=data.get("max_altitude"),
            flight_time_remaining=data.get("flight_time_remaining"),
        )


@dataclass
class POIDTO:
    """DTO para Punto de Interés."""
    id: str
    latitude: float
    longitude: float
    type: str
    description: str
    timestamp: float
    created_by: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte a diccionario."""
        return {
            "id": self.id,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "type": self.type,
            "description": self.description,
            "timestamp": self.timestamp,
            "created_by": self.created_by,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "POIDTO":
        """Crea desde un diccionario."""
        return cls(
            id=data.get("id", ""),
            latitude=float(data.get("latitude", 0.0)),
            longitude=float(data.get("longitude", 0.0)),
            type=data.get("type", "other"),
            description=data.get("description", ""),
            timestamp=float(data.get("timestamp", 0.0)),
            created_by=data.get("created_by", "user"),
        )
