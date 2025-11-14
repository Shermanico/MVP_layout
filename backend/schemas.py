"""
Esquemas de datos para telemetría y POIs.
"""
from typing import Dict, Any
from dataclasses import dataclass, asdict
from common.constants import POIType, DroneStatus


@dataclass
class TelemetrySchema:
    """Esquema para telemetría de drones."""
    drone_id: str
    latitude: float
    longitude: float
    altitude: float
    heading: float
    velocity: float
    battery: float
    status: str
    timestamp: float
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte a diccionario."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TelemetrySchema":
        """Crea desde un diccionario."""
        return cls(**data)


@dataclass
class POISchema:
    """Esquema para Punto de Interés."""
    id: str
    latitude: float
    longitude: float
    type: str
    description: str
    timestamp: float
    created_by: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte a diccionario."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "POISchema":
        """Crea desde un diccionario."""
        return cls(**data)
