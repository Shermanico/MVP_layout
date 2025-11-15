"""
Caso de uso: Eliminar POI.
"""
from domain.ports.output.poi_repository_port import IPOIRepository


class DeletePOIUseCase:
    """Caso de uso para eliminar un POI."""
    
    def __init__(self, poi_repository: IPOIRepository):
        """
        Inicializa el caso de uso.
        
        Args:
            poi_repository: Repositorio de POIs (puerto de salida)
        """
        self.poi_repository = poi_repository
    
    def execute(self, poi_id: str) -> bool:
        """
        Ejecuta el caso de uso.
        
        Args:
            poi_id: ID del POI a eliminar
            
        Returns:
            True si el POI fue eliminado, False si no se encontró
            
        Raises:
            ValueError: Si el ID es inválido
        """
        if not poi_id:
            raise ValueError("El ID del POI es requerido")
        
        return self.poi_repository.remove(poi_id)

