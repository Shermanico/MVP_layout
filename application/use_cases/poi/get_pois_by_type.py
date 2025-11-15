"""
Caso de uso: Obtener POIs por tipo.
"""
from typing import List
from domain.ports.output.poi_repository_port import IPOIRepository
from application.mappers.poi_mapper import POIMapper
from app.dtos import POIDTO


class GetPOIsByTypeUseCase:
    """Caso de uso para obtener POIs filtrados por tipo."""
    
    def __init__(self, poi_repository: IPOIRepository):
        """
        Inicializa el caso de uso.
        
        Args:
            poi_repository: Repositorio de POIs (puerto de salida)
        """
        self.poi_repository = poi_repository
    
    def execute(self, poi_type: str) -> List[POIDTO]:
        """
        Ejecuta el caso de uso.
        
        Args:
            poi_type: Tipo de POI por el cual filtrar
            
        Returns:
            Lista de DTOs de POI del tipo especificado
            
        Raises:
            ValueError: Si el tipo es inválido
        """
        if not poi_type:
            raise ValueError("El tipo de POI es requerido")
        
        pois = self.poi_repository.get_by_type(poi_type)
        return [POIMapper.to_dto(poi) for poi in pois]

