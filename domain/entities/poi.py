"""
Entidad de Punto de Interés.
"""
from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class POI:
    """Entidad de Punto de Interés."""
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
    def from_dict(cls, data: Dict[str, Any]) -> "POI":
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

