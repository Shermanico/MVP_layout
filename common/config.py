"""
Configuración para el sistema de coordinación multi-dron.
"""
from dataclasses import dataclass
from typing import Dict, Any
import json
import os


@dataclass
class Config:
    """Configuración de la aplicación."""
    # Configuración de mapa
    default_latitude: float = 20.9674  # Mérida, Yucatán, México
    default_longitude: float = -89.5926
    default_zoom: int = 13
    
    # Configuración de drones
    max_drones: int = 10
    telemetry_update_interval: float = 0.5  # segundos
    
    # Configuración de simulación
    use_fake_telemetry: bool = True  # Establecer a False para usar MAVSDK
    fake_drone_count: int = 3
    
    # Almacenamiento
    poi_storage_file: str = "pois.json"
    
    # Configuración de UI
    window_width: int = 1400
    window_height: int = 900
    window_title: str = "Sistema de Coordinación Multi-Dron"
    
    @classmethod
    def load_from_file(cls, path: str = "config.json") -> "Config":
        """Carga la configuración desde un archivo JSON."""
        if os.path.exists(path):
            with open(path, "r") as f:
                data = json.load(f)
                return cls(**data)
        return cls()
    
    def save_to_file(self, path: str = "config.json"):
        """Guarda la configuración en un archivo JSON."""
        data = {
            "default_latitude": self.default_latitude,
            "default_longitude": self.default_longitude,
            "default_zoom": self.default_zoom,
            "max_drones": self.max_drones,
            "telemetry_update_interval": self.telemetry_update_interval,
            "use_fake_telemetry": self.use_fake_telemetry,
            "fake_drone_count": self.fake_drone_count,
            "poi_storage_file": self.poi_storage_file,
            "window_width": self.window_width,
            "window_height": self.window_height,
            "window_title": self.window_title,
        }
        with open(path, "w") as f:
            json.dump(data, f, indent=2)

