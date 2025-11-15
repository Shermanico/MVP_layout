"""
Puerto de salida para repositorio de telemetría.
"""
from abc import ABC, abstractmethod
from typing import Dict
from domain.entities.telemetry import Telemetry


class ITelemetryRepository(ABC):
    """Puerto para repositorio de telemetría."""
    
    @abstractmethod
    def update(self, telemetry: Telemetry) -> None:
        """Actualiza la telemetría de un dron."""
        pass
    
    @abstractmethod
    def get_all(self) -> Dict[str, Telemetry]:
        """Obtiene toda la telemetría."""
        pass
    
    @abstractmethod
    def get_by_drone_id(self, drone_id: str) -> Telemetry:
        """Obtiene telemetría por ID de dron."""
        pass

