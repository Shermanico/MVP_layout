"""
Adaptador de salida: Repositorio de POIs usando almacenamiento JSON.
Implementa IPOIRepository del dominio.
"""
import json
import os
from typing import List, Optional
from domain.ports.output.poi_repository_port import IPOIRepository
from domain.entities.poi import POI


class JsonPOIRepository(IPOIRepository):
    """
    Implementación de IPOIRepository usando almacenamiento JSON.
    """
    
    def __init__(self, storage_file: str = "pois.json"):
        """
        Inicializa el repositorio.
        
        Args:
            storage_file: Ruta al archivo JSON para almacenar POIs
        """
        self.storage_file = storage_file
        self._pois: dict[str, POI] = {}
        self._load()
    
    def _load(self) -> None:
        """Carga POIs desde el archivo JSON."""
        if os.path.exists(self.storage_file):
            try:
                with open(self.storage_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        # Formato antiguo: lista de POIs
                        for poi_data in data:
                            poi = POI.from_dict(poi_data)
                            self._pois[poi.id] = poi
                    elif isinstance(data, dict):
                        # Formato nuevo: diccionario por ID
                        for poi_id, poi_data in data.items():
                            poi = POI.from_dict(poi_data)
                            self._pois[poi.id] = poi
            except (json.JSONDecodeError, KeyError, ValueError) as e:
                # Si hay error, empezar con lista vacía
                self._pois = {}
    
    def _save(self) -> None:
        """Guarda POIs al archivo JSON."""
        try:
            data = {poi_id: poi.to_dict() for poi_id, poi in self._pois.items()}
            with open(self.storage_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            # Log error pero no fallar
            pass
    
    def add(self, poi: POI) -> POI:
        """Agrega un POI."""
        self._pois[poi.id] = poi
        self._save()
        return poi
    
    def remove(self, poi_id: str) -> bool:
        """Elimina un POI por ID."""
        if poi_id in self._pois:
            del self._pois[poi_id]
            self._save()
            return True
        return False
    
    def get_all(self) -> List[POI]:
        """Obtiene todos los POIs."""
        return list(self._pois.values())
    
    def get_by_id(self, poi_id: str) -> Optional[POI]:
        """Obtiene un POI por ID."""
        return self._pois.get(poi_id)
    
    def get_by_type(self, poi_type: str) -> List[POI]:
        """Obtiene POIs por tipo."""
        return [poi for poi in self._pois.values() if poi.type == poi_type]
    
    def clear_all(self) -> None:
        """Limpia todos los POIs."""
        self._pois.clear()
        self._save()

