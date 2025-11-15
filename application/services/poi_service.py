"""
Servicio de aplicación para POIs.
Implementa el puerto de entrada IPOIService orquestando casos de uso.
"""
from typing import List, Optional
from domain.ports.input.poi_service_port import IPOIService
from application.use_cases.poi.create_poi import CreatePOIUseCase
from application.use_cases.poi.delete_poi import DeletePOIUseCase
from application.use_cases.poi.get_all_pois import GetAllPOIsUseCase
from application.use_cases.poi.get_pois_by_type import GetPOIsByTypeUseCase
from application.use_cases.poi.clear_all_pois import ClearAllPOIsUseCase
from app.dtos import POIDTO


class POIService(IPOIService):
    """
    Servicio de aplicación para gestión de POIs.
    Implementa el puerto de entrada IPOIService.
    """
    
    def __init__(
        self,
        create_poi_use_case: CreatePOIUseCase,
        delete_poi_use_case: DeletePOIUseCase,
        get_all_pois_use_case: GetAllPOIsUseCase,
        get_pois_by_type_use_case: GetPOIsByTypeUseCase,
        clear_all_pois_use_case: ClearAllPOIsUseCase
    ):
        """
        Inicializa el servicio.
        
        Args:
            create_poi_use_case: Caso de uso para crear POI
            delete_poi_use_case: Caso de uso para eliminar POI
            get_all_pois_use_case: Caso de uso para obtener todos los POIs
            get_pois_by_type_use_case: Caso de uso para obtener POIs por tipo
            clear_all_pois_use_case: Caso de uso para limpiar todos los POIs
        """
        self.create_poi_use_case = create_poi_use_case
        self.delete_poi_use_case = delete_poi_use_case
        self.get_all_pois_use_case = get_all_pois_use_case
        self.get_pois_by_type_use_case = get_pois_by_type_use_case
        self.clear_all_pois_use_case = clear_all_pois_use_case
    
    def create_poi(
        self,
        latitude: float,
        longitude: float,
        poi_type: str,
        description: str = "",
        created_by: str = "user"
    ) -> POIDTO:
        """Crea un nuevo POI."""
        return self.create_poi_use_case.execute(latitude, longitude, poi_type, description, created_by)
    
    def delete_poi(self, poi_id: str) -> bool:
        """Elimina un POI por ID."""
        return self.delete_poi_use_case.execute(poi_id)
    
    def get_all_pois(self) -> List[POIDTO]:
        """Obtiene todos los POIs."""
        return self.get_all_pois_use_case.execute()
    
    def get_poi_by_id(self, poi_id: str) -> Optional[POIDTO]:
        """
        Obtiene un POI por ID.
        
        Nota: Esto requiere acceso directo al repositorio.
        En el futuro, debería ser un caso de uso: GetPOIByIdUseCase
        """
        # Por ahora, obtenemos todos y filtramos
        # En el futuro, esto será un caso de uso dedicado
        all_pois = self.get_all_pois()
        for poi in all_pois:
            if poi.id == poi_id:
                return poi
        return None
    
    def get_pois_by_type(self, poi_type: str) -> List[POIDTO]:
        """Obtiene todos los POIs de un tipo específico."""
        return self.get_pois_by_type_use_case.execute(poi_type)
    
    def clear_all_pois(self) -> None:
        """Limpia todos los POIs."""
        self.clear_all_pois_use_case.execute()

