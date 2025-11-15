"""
Componente para gestionar zonas de interés y formaciones de vuelo.
"""
import flet as ft
from typing import Dict, Any, Optional, Callable, List
from common.constants import FlightFormation
from common.colors import (
    RED, GREEN, BLUE, AMBER, GREY,
    get_text_color, get_text_secondary_color, get_surface_variant_color
)


class ZoneManager:
    """
    Gestiona zonas de interés y formaciones de vuelo para cobertura de áreas.
    """
    
    def __init__(
        self,
        page: Optional[ft.Page] = None,
        on_zone_created: Optional[Callable[[Dict[str, Any]], None]] = None,
        on_zone_deleted: Optional[Callable[[str], None]] = None,
        on_formation_selected: Optional[Callable[[str, FlightFormation], None]] = None,
        page_height: int = 900
    ):
        """
        Inicializa el gestor de zonas.
        
        Args:
            page: Instancia de página Flet para acceso al tema
            on_zone_created: Callback cuando se crea una zona
            on_formation_selected: Callback cuando se selecciona una formación
            page_height: Altura de la página para calcular scroll
        """
        self.page = page
        self.on_zone_created = on_zone_created
        self.on_zone_deleted = on_zone_deleted
        self.on_formation_selected = on_formation_selected
        self.page_height = page_height
        
        self.zones: Dict[str, Dict[str, Any]] = {}
        self.active_zone_id: Optional[str] = None
        
        self.zone_list_view = ft.ListView(expand=True, spacing=5)
        self.formation_buttons_container = ft.Container(visible=False)
        
        self._create_panel()
    
    def _create_panel(self) -> ft.Container:
        """Crea el panel de gestión de zonas."""
        text_color = get_text_color(self.page) if self.page else "#000000"
        text_secondary = get_text_secondary_color(self.page) if self.page else GREY
        
        scroll_height = max(200, (self.page_height - 400) // 2)
        
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text("Zonas de Interés", size=18, weight=ft.FontWeight.BOLD, color=text_color),
                    ft.Divider(),
                    ft.Text(
                        "Dibuja un rectángulo en el mapa para crear una zona",
                        size=12,
                        color=text_secondary
                    ),
                    ft.Container(
                        content=self.zone_list_view,
                        height=scroll_height,
                        expand=False,
                    ),
                    ft.Divider(),
                    # Botones de formaciones (solo visibles cuando hay zona activa)
                    self.formation_buttons_container,
                    ft.ElevatedButton(
                        "Limpiar Todas las Zonas",
                        on_click=self._on_clear_all,
                        color=RED
                    ),
                ],
                spacing=5,
                expand=True,
            ),
            padding=10,
            width=300,
            bgcolor=get_surface_variant_color(self.page) if self.page else "#F5F5F5",
            expand=True,
        )
    
    def get_panel(self) -> ft.Container:
        """Retorna el panel de gestión de zonas."""
        return self._create_panel()
    
    def add_zone(self, zone: Dict[str, Any], skip_callback: bool = False):
        """
        Agrega una zona de interés.
        
        Args:
            zone: Diccionario con datos de la zona (id, bounds, etc.)
            skip_callback: Si es True, no llama al callback (evita bucles infinitos)
        """
        zone_id = zone.get("id")
        if zone_id:
            # Evitar agregar la misma zona dos veces
            if zone_id in self.zones:
                return
            
            self.zones[zone_id] = zone
            self._update_zone_list()
            
            # Activar la zona recién creada
            self.set_active_zone(zone_id)
            
            # Solo llamar al callback si no se está saltando (para evitar bucles)
            if self.on_zone_created and not skip_callback:
                self.on_zone_created(zone)
    
    def set_active_zone(self, zone_id: str):
        """Establece una zona como activa y muestra botones de formaciones."""
        if zone_id in self.zones:
            self.active_zone_id = zone_id
            self._update_formation_buttons()
            self._update_zone_list()
    
    def remove_zone(self, zone_id: str):
        """Elimina una zona."""
        if zone_id in self.zones:
            del self.zones[zone_id]
            if self.active_zone_id == zone_id:
                self.active_zone_id = None
                self._update_formation_buttons()
            self._update_zone_list()
    
    def _update_zone_list(self):
        """Actualiza la lista de zonas."""
        self.zone_list_view.controls.clear()
        
        for zone_id, zone in self.zones.items():
            card = self._create_zone_card(zone_id, zone)
            self.zone_list_view.controls.append(card)
        
        if self.page:
            self.page.update()
    
    def _create_zone_card(self, zone_id: str, zone: Dict[str, Any]) -> ft.Card:
        """Crea una tarjeta para una zona."""
        bounds = zone.get("bounds", {})
        is_active = zone_id == self.active_zone_id
        
        text_color = get_text_color(self.page) if self.page else "#000000"
        bg_color = BLUE if is_active else None
        
        card_content = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Text(
                                f"Zona {zone_id[-4:]}",
                                size=14,
                                weight=ft.FontWeight.BOLD,
                                color=text_color if not is_active else ft.Colors.WHITE
                            ),
                            ft.IconButton(
                                icon=ft.Icons.DELETE,
                                icon_color=RED,
                                icon_size=20,
                                tooltip="Eliminar zona",
                                on_click=lambda e, zid=zone_id: self._on_delete_zone(zid),
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    ft.Text(
                        f"Área: {self._calculate_area(bounds):.2f} km²",
                        size=12,
                        color=text_color if not is_active else ft.Colors.WHITE
                    ),
                    ft.Text(
                        f"Bounds: [{bounds.get('south', 0):.4f}, {bounds.get('west', 0):.4f}] - [{bounds.get('north', 0):.4f}, {bounds.get('east', 0):.4f}]",
                        size=10,
                        color=get_text_secondary_color(self.page) if self.page else GREY
                    ),
                ],
                spacing=5,
                tight=True,
            ),
            padding=10,
            bgcolor=bg_color,
        )
        
        # Hacer el Card clickeable usando Container con Ink
        return ft.Container(
            content=ft.Card(content=card_content),
            on_click=lambda e, zid=zone_id: self.set_active_zone(zid),
            ink=True,
        )
    
    def _calculate_area(self, bounds: Dict[str, float]) -> float:
        """Calcula el área aproximada de la zona en km²."""
        from math import radians, cos
        
        lat1 = bounds.get("south", 0)
        lat2 = bounds.get("north", 0)
        lon1 = bounds.get("west", 0)
        lon2 = bounds.get("east", 0)
        
        # Cálculo aproximado del área usando fórmula de Haversine
        R = 6371  # Radio de la Tierra en km
        dlat = radians(lat2 - lat1)
        dlon = radians(lon2 - lon1)
        
        a = (dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * (dlon / 2) ** 2
        c = 2 * (a ** 0.5)
        
        # Aproximación rectangular
        width = R * dlon * cos(radians((lat1 + lat2) / 2))
        height = R * dlat
        
        return abs(width * height)
    
    def _update_formation_buttons(self):
        """Actualiza los botones de formaciones según la zona activa."""
        if not self.active_zone_id:
            self.formation_buttons_container.visible = False
            self.formation_buttons_container.content = None
            return
        
        text_color = get_text_color(self.page) if self.page else "#000000"
        
        formation_buttons = ft.Column(
            controls=[
                ft.Text("Formaciones de Vuelo", size=14, weight=ft.FontWeight.BOLD, color=text_color),
                ft.Divider(),
                ft.ElevatedButton(
                    "Cuadrícula",
                    icon=ft.Icons.GRID_ON,
                    on_click=lambda e: self._on_formation_selected(FlightFormation.GRID),
                    tooltip="Cobertura sistemática en cuadrícula",
                ),
                ft.ElevatedButton(
                    "Línea",
                    icon=ft.Icons.SHOW_CHART,
                    on_click=lambda e: self._on_formation_selected(FlightFormation.LINE),
                    tooltip="Búsqueda en línea",
                ),
                ft.ElevatedButton(
                    "Círculo",
                    icon=ft.Icons.RADIO_BUTTON_CHECKED,
                    on_click=lambda e: self._on_formation_selected(FlightFormation.CIRCLE),
                    tooltip="Cobertura perimetral",
                ),
                ft.ElevatedButton(
                    "Espiral",
                    icon=ft.Icons.ROTATE_RIGHT,
                    on_click=lambda e: self._on_formation_selected(FlightFormation.SPIRAL),
                    tooltip="Búsqueda centrada en espiral",
                ),
                ft.ElevatedButton(
                    "Zigzag",
                    icon=ft.Icons.TIMELINE,
                    on_click=lambda e: self._on_formation_selected(FlightFormation.ZIGZAG),
                    tooltip="Cobertura eficiente en zigzag",
                ),
            ],
            spacing=5,
        )
        
        self.formation_buttons_container.content = formation_buttons
        self.formation_buttons_container.visible = True
        
        if self.page:
            self.page.update()
    
    def _on_formation_selected(self, formation: FlightFormation):
        """Maneja la selección de una formación."""
        if self.active_zone_id and self.on_formation_selected:
            self.on_formation_selected(self.active_zone_id, formation)
    
    def _on_delete_zone(self, zone_id: str):
        """Maneja la eliminación de una zona."""
        self.remove_zone(zone_id)
        # Llamar al callback para eliminar del servidor y mapa
        if self.on_zone_deleted:
            self.on_zone_deleted(zone_id)
    
    def _on_clear_all(self, e):
        """Limpia todas las zonas."""
        self.zones.clear()
        self.active_zone_id = None
        self._update_formation_buttons()
        self._update_zone_list()

