"""
Componente UI de gestión de POIs.
Maneja la creación, edición y visualización de Puntos de Interés.
"""
import flet as ft
from typing import Dict, List, Any, Optional, Callable
from common.constants import POIType
from common.colors import (
    RED, GREEN, BLUE, AMBER, GREY, GREY_600, SURFACE_VARIANT
)
from common.utils import format_timestamp


class POIManager:
    """
    Componente UI para gestionar Puntos de Interés.
    """
    
    def __init__(
        self,
        on_create_poi: Optional[Callable[[float, float, str, str], None]] = None,
        on_delete_poi: Optional[Callable[[str], None]] = None
    ):
        """
        Inicializa el gestor de POIs.
        
        Args:
            on_create_poi: Callback cuando se crea un POI (lat, lon, type, description)
            on_delete_poi: Callback cuando se elimina un POI (poi_id)
        """
        self.on_create_poi = on_create_poi
        self.on_delete_poi = on_delete_poi
        self.pois: Dict[str, Dict[str, Any]] = {}
        self.poi_list_view = ft.ListView(expand=True, spacing=5)
        self.poi_panel = self._create_panel()
    
    def _create_panel(self) -> ft.Container:
        """Crea el panel de gestión de POIs."""
        # Traducciones de tipos de POI
        poi_type_names = {
            "hazard": "PELIGRO",
            "target": "OBJETIVO",
            "checkpoint": "PUNTO DE CONTROL",
            "landing_zone": "ZONA DE ATERRIZAJE",
            "other": "OTRO"
        }
        
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text("Puntos de Interés", size=18, weight=ft.FontWeight.BOLD),
                    ft.Divider(),
                    self.poi_list_view,
                    ft.Divider(),
                    ft.ElevatedButton(
                        "Limpiar Todos los POIs",
                        on_click=self._on_clear_all,
                        color=RED
                    ),
                ],
                spacing=10,
                expand=True,
            ),
            padding=10,
            width=300,
            bgcolor=SURFACE_VARIANT,
        )
    
    def _create_poi_card(self, poi: Dict[str, Any]) -> ft.Card:
        """Crea un widget de tarjeta para un POI."""
        poi_type = poi.get("type", "other")
        description = poi.get("description", "")
        timestamp = format_timestamp(poi.get("timestamp", 0))
        
        # Color basado en tipo
        colors = {
            "hazard": RED,
            "target": BLUE,
            "checkpoint": AMBER,
            "landing_zone": GREEN,
            "other": GREY,
        }
        color = colors.get(poi_type, GREY)
        
        # Nombres traducidos de tipos
        poi_type_names = {
            "hazard": "PELIGRO",
            "target": "OBJETIVO",
            "checkpoint": "PUNTO DE CONTROL",
            "landing_zone": "ZONA DE ATERRIZAJE",
            "other": "OTRO"
        }
        type_display = poi_type_names.get(poi_type, poi_type.upper())
        
        return ft.Card(
            content=ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Row(
                            controls=[
                                ft.Container(
                                    width=10,
                                    height=10,
                                    bgcolor=color,
                                    border_radius=5,
                                ),
                                ft.Text(
                                    type_display,
                                    weight=ft.FontWeight.BOLD,
                                    size=12,
                                ),
                                ft.IconButton(
                                    icon=ft.Icons.DELETE,
                                    icon_size=16,
                                    tooltip="Eliminar POI",
                                    on_click=lambda e, pid=poi["id"]: self._on_delete(pid),
                                ),
                            ],
                            spacing=5,
                        ),
                        ft.Text(description or "Sin descripción", size=11),
                        ft.Text(f"Creado: {timestamp}", size=9, color=GREY_600),
                        ft.Text(
                            f"Lat: {poi['latitude']:.6f}, Lon: {poi['longitude']:.6f}",
                            size=9,
                            color=GREY_600,
                        ),
                    ],
                    spacing=5,
                    tight=True,
                ),
                padding=10,
            ),
        )
    
    def add_poi(self, poi: Dict[str, Any]):
        """
        Agrega un POI a la lista.
        
        Args:
            poi: Diccionario de POI
        """
        self.pois[poi["id"]] = poi
        self._refresh_list()
    
    def remove_poi(self, poi_id: str):
        """
        Elimina un POI de la lista.
        
        Args:
            poi_id: ID del POI a eliminar
        """
        if poi_id in self.pois:
            del self.pois[poi_id]
            self._refresh_list()
    
    def update_pois(self, pois: List[Dict[str, Any]]):
        """
        Actualiza todos los POIs.
        
        Args:
            pois: Lista de diccionarios de POI
        """
        self.pois = {poi["id"]: poi for poi in pois}
        self._refresh_list()
    
    def _refresh_list(self):
        """Actualiza la vista de lista de POIs."""
        self.poi_list_view.controls.clear()
        for poi in self.pois.values():
            self.poi_list_view.controls.append(self._create_poi_card(poi))
        self.poi_list_view.update()
    
    def _on_delete(self, poi_id: str):
        """Maneja la eliminación de POI."""
        if self.on_delete_poi:
            self.on_delete_poi(poi_id)
    
    def _on_clear_all(self, e):
        """Maneja la limpieza de todos los POIs."""
        if self.on_delete_poi:
            for poi_id in list(self.pois.keys()):
                self.on_delete_poi(poi_id)
    
    def get_panel(self) -> ft.Container:
        """Obtiene el panel de gestión de POIs."""
        return self.poi_panel
