"""
Adaptador de entrada: Gestor de POIs en UI.
Gestiona visualización e interacciones de POIs.
"""
import flet as ft
from typing import Dict, Any, Callable, Optional
from infrastructure.config.colors import (
    RED, BLUE, AMBER, GREEN, GREY_200, GREY_600, BLUE_700, SURFACE
)
from infrastructure.config.constants import POIType
from infrastructure.config.utils import format_timestamp


class POIManager:
    """
    Gestor de POIs que muestra lista de POIs y maneja interacciones.
    Panel scrolleable para múltiples POIs.
    """
    
    def __init__(self, page: ft.Page, on_delete_poi: Optional[Callable[[str], None]] = None):
        """
        Inicializa el gestor de POIs.
        
        Args:
            page: Página Flet
            on_delete_poi: Callback para eliminar POI
        """
        self.page = page
        self.on_delete_poi = on_delete_poi
        self.poi_data: Dict[str, Dict[str, Any]] = {}
        self.poi_cards: Dict[str, ft.Card] = {}
        
        # Componentes UI
        self.poi_list_view = ft.Column(
            spacing=10,
            scroll=ft.ScrollMode.AUTO,
            expand=True
        )
        
        self.panel = self._create_panel()
    
    def _create_panel(self) -> ft.Container:
        """Crea el panel de POIs."""
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Text(
                                "Puntos de Interés",
                                size=18,
                                weight=ft.FontWeight.BOLD,
                                color=BLUE_700
                            ),
                            ft.Text(
                                f"({len(self.poi_data)})",
                                size=14,
                                color=GREY_600
                            )
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                    ),
                    ft.Container(
                        content=self.poi_list_view,
                        expand=True
                    )
                ],
                spacing=10,
                expand=True
            ),
            padding=ft.padding.all(15),
            bgcolor=SURFACE,
            expand=True
        )
    
    def add_poi(self, poi: Dict[str, Any]) -> None:
        """
        Agrega un POI a la lista.
        
        Args:
            poi: Diccionario de POI
        """
        poi_id = poi.get("id", "")
        if not poi_id:
            return
        
        self.poi_data[poi_id] = poi
        
        if poi_id not in self.poi_cards:
            card = self._build_card(poi)
            self.poi_cards[poi_id] = card
            self.poi_list_view.controls.append(card)
            self._update_count()
            self.page.update()
    
    def remove_poi(self, poi_id: str) -> None:
        """
        Elimina un POI de la lista.
        
        Args:
            poi_id: ID del POI a eliminar
        """
        if poi_id in self.poi_cards:
            card = self.poi_cards[poi_id]
            self.poi_list_view.controls.remove(card)
            del self.poi_cards[poi_id]
        
        if poi_id in self.poi_data:
            del self.poi_data[poi_id]
        
        self._update_count()
        self.page.update()
    
    def _update_count(self) -> None:
        """Actualiza el contador de POIs."""
        # El contador se actualiza en el panel
        pass
    
    def _build_card(self, poi: Dict[str, Any]) -> ft.Card:
        """Construye una tarjeta de POI."""
        poi_id = poi.get("id", "")
        poi_type = poi.get("type", "other")
        description = poi.get("description", "")
        latitude = poi.get("latitude", 0.0)
        longitude = poi.get("longitude", 0.0)
        timestamp = poi.get("timestamp", 0.0)
        
        # Color según tipo
        type_colors = {
            POIType.HAZARD.value: RED,
            POIType.TARGET.value: BLUE,
            POIType.CHECKPOINT.value: AMBER,
            POIType.LANDING_ZONE.value: GREEN,
            POIType.OTHER.value: GREY_600
        }
        type_color = type_colors.get(poi_type, GREY_600)
        
        # Nombre del tipo
        type_names = {
            POIType.HAZARD.value: "Peligro",
            POIType.TARGET.value: "Objetivo",
            POIType.CHECKPOINT.value: "Punto de Control",
            POIType.LANDING_ZONE.value: "Zona de Aterrizaje",
            POIType.OTHER.value: "Otro"
        }
        type_name = type_names.get(poi_type, "Otro")
        
        return ft.Card(
            content=ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Row(
                            controls=[
                                ft.Container(
                                    content=ft.Text(
                                        type_name,
                                        size=12,
                                        weight=ft.FontWeight.BOLD,
                                        color="white"
                                    ),
                                    bgcolor=type_color,
                                    padding=ft.padding.symmetric(horizontal=10, vertical=5),
                                    border_radius=5
                                ),
                                ft.IconButton(
                                    icon=ft.Icons.DELETE,
                                    icon_color=RED,
                                    icon_size=20,
                                    tooltip="Eliminar POI",
                                    on_click=lambda e, pid=poi_id: self._on_delete(pid)
                                ) if self.on_delete_poi else ft.Container()
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                        ),
                        ft.Text(
                            description if description else "Sin descripción",
                            size=14,
                            color=GREY_600
                        ),
                        ft.Row(
                            controls=[
                                ft.Text(f"Lat: {latitude:.6f}", size=12, color=GREY_600),
                                ft.Text(f"Lon: {longitude:.6f}", size=12, color=GREY_600)
                            ],
                            spacing=10
                        ),
                        ft.Text(
                            format_timestamp(timestamp),
                            size=10,
                            color=GREY_600
                        )
                    ],
                    spacing=8,
                    tight=True
                ),
                padding=ft.padding.all(15),
                width=float("inf")
            ),
            elevation=2
        )
    
    def _on_delete(self, poi_id: str) -> None:
        """Maneja la eliminación de un POI."""
        if self.on_delete_poi:
            self.on_delete_poi(poi_id)
    
    def get_panel(self) -> ft.Container:
        """Obtiene el panel de POIs."""
        return self.panel

