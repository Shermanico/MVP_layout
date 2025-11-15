"""
Puerto de salida para repositorio de POIs.
"""
from abc import ABC, abstractmethod
from typing import List, Optional
from domain.entities.poi import POI


class IPOIRepository(ABC):
    """Puerto para repositorio de POIs."""
    
    @abstractmethod
    def add(self, poi: POI) -> POI:
        """Agrega un POI."""
        pass
    
    @abstractmethod
    def remove(self, poi_id: str) -> bool:
        """Elimina un POI por ID."""
        pass
    
    @abstractmethod
    def get_all(self) -> List[POI]:
        """Obtiene todos los POIs."""
        pass
    
    @abstractmethod
    def get_by_id(self, poi_id: str) -> Optional[POI]:
        """Obtiene un POI por ID."""
        pass
    
    @abstractmethod
    def get_by_type(self, poi_type: str) -> List[POI]:
        """Obtiene POIs por tipo."""
        pass
    
    @abstractmethod
    def clear_all(self) -> None:
        """Limpia todos los POIs."""
        pass

