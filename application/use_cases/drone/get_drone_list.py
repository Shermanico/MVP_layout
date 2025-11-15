"""
Caso de uso: Obtener lista de drones.
"""
from typing import List
from domain.ports.output.drone_repository_port import IDroneRepository


class GetDroneListUseCase:
    """Caso de uso para obtener la lista de drones activos."""
    
    def __init__(self, drone_repository: IDroneRepository):
        """
        Inicializa el caso de uso.
        
        Args:
            drone_repository: Repositorio de drones (puerto de salida)
        """
        self.drone_repository = drone_repository
    
    def execute(self) -> List[str]:
        """
        Ejecuta el caso de uso.
        
        Returns:
            Lista de IDs de drones activos
        """
        return self.drone_repository.get_drone_list()
    
    def get_count(self) -> int:
        """
        Obtiene el número de drones activos.
        
        Returns:
            Número de drones activos
        """
        return self.drone_repository.get_drone_count()

