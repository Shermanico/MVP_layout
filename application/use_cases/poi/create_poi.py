"""
Caso de uso: Crear POI.
"""
import time
from domain.ports.output.poi_repository_port import IPOIRepository
from domain.entities.poi import POI
from application.mappers.poi_mapper import POIMapper
from app.dtos import POIDTO


class CreatePOIUseCase:
    """Caso de uso para crear un nuevo POI."""
    
    def __init__(self, poi_repository: IPOIRepository):
        """
        Inicializa el caso de uso.
        
        Args:
            poi_repository: Repositorio de POIs (puerto de salida)
        """
        self.poi_repository = poi_repository
    
    def execute(
        self,
        latitude: float,
        longitude: float,
        poi_type: str,
        description: str = "",
        created_by: str = "user"
    ) -> POIDTO:
        """
        Ejecuta el caso de uso.
        
        Args:
            latitude: Latitud del POI
            longitude: Longitud del POI
            poi_type: Tipo de POI
            description: Descripción opcional
            created_by: ID de usuario/dispositivo
            
        Returns:
            DTO del POI creado
            
        Raises:
            ValueError: Si los datos son inválidos
        """
        # Validación de negocio
        if not (-90 <= latitude <= 90):
            raise ValueError("La latitud debe estar entre -90 y 90")
        
        if not (-180 <= longitude <= 180):
            raise ValueError("La longitud debe estar entre -180 y 180")
        
        if not poi_type:
            raise ValueError("El tipo de POI es requerido")
        
        # Crear entidad del dominio
        poi = POI(
            id=f"poi_{int(time.time() * 1000)}",
            latitude=latitude,
            longitude=longitude,
            type=poi_type,
            description=description,
            timestamp=time.time(),
            created_by=created_by
        )
        
        # Persistir usando el repositorio (puerto de salida)
        created_poi = self.poi_repository.add(poi)
        
        # Convertir a DTO para retornar
        return POIMapper.to_dto(created_poi)

