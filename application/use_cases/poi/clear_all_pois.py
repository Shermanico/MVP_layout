"""
Caso de uso: Limpiar todos los POIs.
"""
from domain.ports.output.poi_repository_port import IPOIRepository


class ClearAllPOIsUseCase:
    """Caso de uso para eliminar todos los POIs."""
    
    def __init__(self, poi_repository: IPOIRepository):
        """
        Inicializa el caso de uso.
        
        Args:
            poi_repository: Repositorio de POIs (puerto de salida)
        """
        self.poi_repository = poi_repository
    
    def execute(self) -> None:
        """Ejecuta el caso de uso."""
        self.poi_repository.clear_all()

