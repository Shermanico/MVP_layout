"""
Caso de uso: Iniciar drones.
"""
from domain.ports.output.drone_repository_port import IDroneRepository


class StartDronesUseCase:
    """Caso de uso para iniciar múltiples drones."""
    
    def __init__(self, drone_repository: IDroneRepository):
        """
        Inicializa el caso de uso.
        
        Args:
            drone_repository: Repositorio de drones (puerto de salida)
        """
        self.drone_repository = drone_repository
    
    async def execute(self, count: int, update_interval: float = 0.5, callback=None) -> None:
        """
        Ejecuta el caso de uso.
        
        Args:
            count: Número de drones a iniciar
            update_interval: Intervalo de actualización en segundos
            callback: Callback opcional para actualizaciones de telemetría
        """
        # Validación de negocio
        if count <= 0:
            raise ValueError("El número de drones debe ser mayor a 0")
        
        if count > 10:
            raise ValueError("No se pueden iniciar más de 10 drones simultáneamente")
        
        # Delegar al repositorio (puerto de salida)
        await self.drone_repository.start_drones(count, update_interval, callback)

