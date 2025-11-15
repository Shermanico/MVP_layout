"""
Puerto de entrada para servicio de POIs.
Define los casos de uso relacionados con POIs.
"""
from abc import ABC, abstractmethod
from typing import List, Optional
from app.dtos import POIDTO


class IPOIService(ABC):
    """Puerto de entrada para operaciones con POIs."""
    
    @abstractmethod
    def create_poi(
        self,
        latitude: float,
        longitude: float,
        poi_type: str,
        description: str = "",
        created_by: str = "user"
    ) -> POIDTO:
        """Crea un nuevo POI."""
        pass
    
    @abstractmethod
    def delete_poi(self, poi_id: str) -> bool:
        """Elimina un POI por ID."""
        pass
    
    @abstractmethod
    def get_all_pois(self) -> List[POIDTO]:
        """Obtiene todos los POIs."""
        pass
    
    @abstractmethod
    def get_poi_by_id(self, poi_id: str) -> Optional[POIDTO]:
        """Obtiene un POI por ID."""
        pass
    
    @abstractmethod
    def get_pois_by_type(self, poi_type: str) -> List[POIDTO]:
        """Obtiene todos los POIs de un tipo específico."""
        pass
    
    @abstractmethod
    def clear_all_pois(self) -> None:
        """Limpia todos los POIs."""
        pass

