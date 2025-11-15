"""
Caso de uso: Obtener todos los POIs.
"""
from typing import List
from domain.ports.output.poi_repository_port import IPOIRepository
from application.mappers.poi_mapper import POIMapper
from app.dtos import POIDTO


class GetAllPOIsUseCase:
    """Caso de uso para obtener todos los POIs."""
    
    def __init__(self, poi_repository: IPOIRepository):
        """
        Inicializa el caso de uso.
        
        Args:
            poi_repository: Repositorio de POIs (puerto de salida)
        """
        self.poi_repository = poi_repository
    
    def execute(self) -> List[POIDTO]:
        """
        Ejecuta el caso de uso.
        
        Returns:
            Lista de DTOs de POI
        """
        pois = self.poi_repository.get_all()
        return [POIMapper.to_dto(poi) for poi in pois]

