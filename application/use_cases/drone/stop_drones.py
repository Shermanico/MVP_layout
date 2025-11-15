"""
Caso de uso: Detener drones.
"""
from domain.ports.output.drone_repository_port import IDroneRepository


class StopDronesUseCase:
    """Caso de uso para detener todos los drones."""
    
    def __init__(self, drone_repository: IDroneRepository):
        """
        Inicializa el caso de uso.
        
        Args:
            drone_repository: Repositorio de drones (puerto de salida)
        """
        self.drone_repository = drone_repository
    
    async def execute(self) -> None:
        """Ejecuta el caso de uso."""
        await self.drone_repository.stop_drones()

