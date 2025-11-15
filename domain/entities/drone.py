"""
Entidad de dron.
"""
from dataclasses import dataclass
from typing import Optional
from domain.entities.telemetry import Telemetry


@dataclass
class Drone:
    """Entidad de dron."""
    drone_id: str
    current_telemetry: Optional[Telemetry] = None
    
    def update_telemetry(self, telemetry: Telemetry) -> None:
        """Actualiza la telemetría del dron."""
        self.current_telemetry = telemetry

