"""
Servicio de aplicación para drones.
Implementa el puerto de entrada IDroneService orquestando casos de uso.
"""
from typing import List, Dict, Any, Callable, Optional
from domain.ports.input.drone_service_port import IDroneService
from application.use_cases.drone.start_drones import StartDronesUseCase
from application.use_cases.drone.stop_drones import StopDronesUseCase
from application.use_cases.drone.get_drone_list import GetDroneListUseCase
from domain.ports.output.drone_repository_port import IDroneRepository


class DroneService(IDroneService):
    """
    Servicio de aplicación para gestión de drones.
    Implementa el puerto de entrada IDroneService.
    """
    
    def __init__(
        self,
        start_drones_use_case: StartDronesUseCase,
        stop_drones_use_case: StopDronesUseCase,
        get_drone_list_use_case: GetDroneListUseCase
    ):
        """
        Inicializa el servicio.
        
        Args:
            start_drones_use_case: Caso de uso para iniciar drones
            stop_drones_use_case: Caso de uso para detener drones
            get_drone_list_use_case: Caso de uso para obtener lista de drones
        """
        self.start_drones_use_case = start_drones_use_case
        self.stop_drones_use_case = stop_drones_use_case
        self.get_drone_list_use_case = get_drone_list_use_case
    
    async def start_drones(self, count: int, update_interval: float = 0.5, callback: Optional[Callable[[Dict[str, Any]], None]] = None) -> None:
        """Inicia múltiples drones."""
        await self.start_drones_use_case.execute(count, update_interval, callback)
    
    async def stop_drones(self) -> None:
        """Detiene todos los drones."""
        await self.stop_drones_use_case.execute()
    
    def get_drone_count(self) -> int:
        """Obtiene el número de drones activos."""
        return self.get_drone_list_use_case.get_count()
    
    def get_drone_list(self) -> List[str]:
        """Obtiene la lista de IDs de drones activos."""
        return self.get_drone_list_use_case.execute()
    
    async def send_command(self, drone_id: str, command: str, **kwargs) -> None:
        """
        Envía un comando a un dron específico.
        
        Nota: Este método requiere acceso directo al repositorio.
        En una implementación más pura, esto sería otro caso de uso.
        """
        # Por ahora, delegamos al repositorio directamente
        # En el futuro, esto debería ser un caso de uso: SendCommandToDroneUseCase
        raise NotImplementedError("Send command will be implemented as a use case")

