"""
Almacenamiento y gestión de POIs.
Maneja la persistencia y recuperación de Puntos de Interés.
"""
import json
import os
import time
from typing import List, Dict, Any, Optional
from common.utils import create_poi
from common.config import Config


class POIStorage:
    """
    Gestiona el almacenamiento y recuperación de POIs.
    Usa archivo JSON para persistencia (simple y amigable para hackathon).
    """
    
    def __init__(self, storage_file: str = "pois.json"):
        """
        Inicializa el almacenamiento de POIs.
        
        Args:
            storage_file: Ruta al archivo JSON para almacenamiento
        """
        self.storage_file = storage_file
        self.pois: List[Dict[str, Any]] = []
        self.load()
    
    def load(self):
        """Carga POIs desde el archivo de almacenamiento."""
        if os.path.exists(self.storage_file):
            try:
                with open(self.storage_file, "r") as f:
                    self.pois = json.load(f)
            except (json.JSONDecodeError, IOError):
                self.pois = []
        else:
            self.pois = []
    
    def save(self):
        """Guarda POIs en el archivo de almacenamiento."""
        try:
            with open(self.storage_file, "w") as f:
                json.dump(self.pois, f, indent=2)
        except IOError as e:
            print(f"Error al guardar POIs: {e}")
    
    def add_poi(
        self,
        latitude: float,
        longitude: float,
        poi_type: str,
        description: str = "",
        created_by: str = "user"
    ) -> Dict[str, Any]:
        """
        Agrega un nuevo POI.
        
        Args:
            latitude: Latitud del POI
            longitude: Longitud del POI
            poi_type: Tipo de POI
            description: Descripción opcional
            created_by: ID de usuario/dispositivo
            
        Returns:
            Diccionario de POI creado
        """
        poi = create_poi(latitude, longitude, poi_type, description, created_by)
        self.pois.append(poi)
        self.save()
        return poi
    
    def remove_poi(self, poi_id: str) -> bool:
        """
        Elimina un POI por ID.
        
        Args:
            poi_id: ID del POI a eliminar
            
        Returns:
            True si el POI fue eliminado, False si no se encontró
        """
        initial_count = len(self.pois)
        self.pois = [p for p in self.pois if p["id"] != poi_id]
        
        if len(self.pois) < initial_count:
            self.save()
            return True
        return False
    
    def get_all_pois(self) -> List[Dict[str, Any]]:
        """Obtiene todos los POIs."""
        return self.pois.copy()
    
    def get_poi_by_id(self, poi_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene un POI por ID.
        
        Args:
            poi_id: ID del POI a recuperar
            
        Returns:
            Diccionario de POI o None si no se encontró
        """
        for poi in self.pois:
            if poi["id"] == poi_id:
                return poi.copy()
        return None
    
    def get_pois_by_type(self, poi_type: str) -> List[Dict[str, Any]]:
        """
        Obtiene todos los POIs de un tipo específico.
        
        Args:
            poi_type: Tipo de POI por el cual filtrar
            
        Returns:
            Lista de diccionarios de POI
        """
        return [p.copy() for p in self.pois if p["type"] == poi_type]
    
    def clear_all(self):
        """Limpia todos los POIs."""
        self.pois = []
        self.save()
