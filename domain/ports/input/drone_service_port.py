"""
Puerto de entrada para servicio de drones.
Define los casos de uso relacionados con drones.
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any
from app.dtos import TelemetryDTO


class IDroneService(ABC):
    """Puerto de entrada para operaciones con drones."""
    
    @abstractmethod
    async def start_drones(self, count: int) -> None:
        """Inicia múltiples drones."""
        pass
    
    @abstractmethod
    async def stop_drones(self) -> None:
        """Detiene todos los drones."""
        pass
    
    @abstractmethod
    def get_drone_count(self) -> int:
        """Obtiene el número de drones activos."""
        pass
    
    @abstractmethod
    def get_drone_list(self) -> List[str]:
        """Obtiene la lista de IDs de drones activos."""
        pass
    
    @abstractmethod
    async def send_command(self, drone_id: str, command: str, **kwargs) -> None:
        """Envía un comando a un dron específico."""
        pass

