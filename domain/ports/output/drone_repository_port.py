"""
Puerto de salida para repositorio de drones.
"""
from abc import ABC, abstractmethod
from typing import List, Callable, Optional, Dict, Any
from domain.entities.drone import Drone
from domain.entities.telemetry import Telemetry


class IDroneRepository(ABC):
    """Puerto para repositorio de drones."""
    
    @abstractmethod
    async def start_drones(self, count: int, update_interval: float, callback: Optional[Callable[[Dict[str, Any]], None]] = None) -> List[Drone]:
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

