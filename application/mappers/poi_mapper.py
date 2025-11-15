"""
Mapper para convertir entre entidades de POI y DTOs.
"""
from domain.entities.poi import POI
from app.dtos import POIDTO


class POIMapper:
    """Mapper para POIs."""
    
    @staticmethod
    def to_dto(poi: POI) -> POIDTO:
        """Convierte una entidad POI a POIDTO."""
        return POIDTO(
            id=poi.id,
            latitude=poi.latitude,
            longitude=poi.longitude,
            type=poi.type,
            description=poi.description,
            timestamp=poi.timestamp,
            created_by=poi.created_by,
        )
    
    @staticmethod
    def to_entity(dto: POIDTO) -> POI:
        """Convierte un POIDTO a entidad POI."""
        return POI(
            id=dto.id,
            latitude=dto.latitude,
            longitude=dto.longitude,
            type=dto.type,
            description=dto.description,
            timestamp=dto.timestamp,
            created_by=dto.created_by,
        )
    
    @staticmethod
    def dict_to_entity(data: dict) -> POI:
        """Convierte un diccionario a entidad POI."""
        return POI.from_dict(data)

