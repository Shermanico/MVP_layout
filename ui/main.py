"""
Aplicación UI principal de Flet.
Coordina todos los componentes UI y maneja actualizaciones en tiempo real.
"""
import flet as ft
import asyncio
from typing import Dict, Any, Optional
from common.config import Config
from common.constants import POIType, CHANNEL_TELEMETRY, CHANNEL_POI
from common.colors import (
    RED, GREEN, BLUE, AMBER, GREY, GREY_600, 
    SURFACE, BLUE_GREY_50
)
from backend.storage import POIStorage
from ui.telemetry_panel import TelemetryPanel
from ui.poi_manager import POIManager
from ui.map_view import MapView


class MainApp:
    """
    Clase principal de la aplicación que coordina todos los componentes UI.
    """
    
    def __init__(self, config: Config, storage: POIStorage):
        """
        Inicializa la aplicación principal.
        
        Args:
            config: Configuración de la aplicación
            storage: Instancia de almacenamiento de POIs
        """
        self.config = config
        self.storage = storage
        self.page: Optional[ft.Page] = None
        
        # Componentes UI
        self.telemetry_panel = TelemetryPanel()
        self.poi_manager = POIManager(
            on_create_poi=self._on_create_poi,
            on_delete_poi=self._on_delete_poi
        )
        
        # Marcadores de mapa (simplificado - usando marcadores Flet)
        self.drone_markers: Dict[str, ft.Marker] = {}
        self.poi_markers: Dict[str, ft.Marker] = {}
        
        # Referencias de controles UI para actualizaciones
        self.drone_positions_container: Optional[ft.Container] = None
        self.poi_markers_container: Optional[ft.Container] = None
        
        # Vista de mapa
        self.map_view: Optional[MapView] = None
        
        # Suscribirse a canales pub/sub
        self.telemetry_subscription = None
        self.poi_subscription = None
    
    def setup_page(self, page: ft.Page):
        """
        Configura la página Flet con todos los componentes UI.
        
        Args:
            page: Instancia de página Flet
        """
        self.page = page
        page.title = self.config.window_title
        page.window.width = self.config.window_width
        page.window.height = self.config.window_height
        
        # Crear layout principal
        page.add(self._create_main_layout())
        
        # Cargar POIs existentes (después de agregar a la página)
        # Usar page.update() para asegurar que los controles estén en la página
        page.update()
        self._load_pois()
        
        # Suscribirse a pub/sub
        self._setup_pubsub()
    
    def _create_main_layout(self) -> ft.Row:
        """Crea el layout principal de la aplicación."""
        # Crear vista de mapa (simplificado para MVP)
        map_view = self._create_map_view()
        
        # Crear panel lateral
        side_panel = self._create_side_panel()
        
        return ft.Row(
            controls=[
                map_view,  # El mapa ocupa la mayor parte del espacio
                side_panel,  # Panel lateral con telemetría y POIs
            ],
            expand=True,
            spacing=0,
        )
    
    def _create_map_view(self) -> ft.Container:
        """Crea el componente de vista de mapa."""
        # Crear instancia de MapView
        self.map_view = MapView(
            initial_lat=self.config.default_latitude,
            initial_lon=self.config.default_longitude,
            zoom=self.config.default_zoom,
            on_poi_click=self._on_poi_click,
            on_map_click=self._on_map_click
        )
        
        # Crear contenedores para información adicional (opcional)
        self.drone_positions_container = ft.Container(
            content=ft.Column(
                controls=[],
                spacing=5,
            ),
        )
        
        self.poi_markers_container = ft.Container(
            content=ft.Column(
                controls=[],
                spacing=5,
            ),
        )
        
        # Layout con mapa y controles
        map_container = ft.Container(
            content=ft.Column(
                controls=[
                    # Barra superior con controles
                    ft.Row(
                        controls=[
                            ft.Text("Vista de Mapa", size=20, weight=ft.FontWeight.BOLD),
                            ft.ElevatedButton(
                                "Agregar POI",
                                icon=ft.Icons.ADD_LOCATION,
                                on_click=self._on_add_poi_button_click,
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    ft.Text(
                        "Haz clic en el mapa para crear un POI o usa el botón 'Agregar POI'",
                        size=12,
                        color=GREY_600
                    ),
                    ft.Divider(),
                    # Mapa interactivo
                    self.map_view.get_view(),
                ],
                spacing=10,
                expand=True,
            ),
            expand=True,
            bgcolor=BLUE_GREY_50,
            padding=10,
        )
        
        return map_container
    
    def _on_map_click(self, lat: float, lon: float):
        """Maneja clic en el mapa para crear POI."""
        self._create_poi_dialog(lat, lon)
    
    def _on_poi_click(self, poi_id: str):
        """Maneja clic en un POI del mapa."""
        # Opcional: mostrar información del POI o permitir edición
        pass
    
    def _create_side_panel(self) -> ft.Container:
        """Crea el panel lateral con telemetría y gestión de POIs."""
        return ft.Container(
            content=ft.Column(
                controls=[
                    self.telemetry_panel.get_panel(),
                    ft.Divider(),
                    self.poi_manager.get_panel(),
                ],
                spacing=10,
                expand=True,
            ),
            width=320,
            bgcolor=SURFACE,
            padding=0,
        )
    
    def _create_poi_dialog(self, lat: float, lon: float):
        """Crea un diálogo para la creación de POI."""
        poi_type_dropdown = ft.Dropdown(
            label="Tipo de POI",
            options=[
                ft.dropdown.Option(key=POIType.HAZARD.value, text="Peligro"),
                ft.dropdown.Option(key=POIType.TARGET.value, text="Objetivo"),
                ft.dropdown.Option(key=POIType.CHECKPOINT.value, text="Punto de Control"),
                ft.dropdown.Option(key=POIType.LANDING_ZONE.value, text="Zona de Aterrizaje"),
                ft.dropdown.Option(key=POIType.OTHER.value, text="Otro"),
            ],
            value=POIType.OTHER.value,
        )
        
        description_field = ft.TextField(
            label="Descripción",
            multiline=True,
            max_lines=3,
        )
        
        def on_save(e):
            poi_type = poi_type_dropdown.value
            description = description_field.value or ""
            self._on_create_poi(lat, lon, poi_type, description)
            self.page.close_dialog()
        
        dialog = ft.AlertDialog(
            title=ft.Text("Crear Punto de Interés"),
            content=ft.Column(
                controls=[
                    ft.Text(f"Ubicación: {lat:.6f}, {lon:.6f}"),
                    poi_type_dropdown,
                    description_field,
                ],
                tight=True,
                height=200,
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: self.page.close_dialog()),
                ft.ElevatedButton("Crear", on_click=on_save),
            ],
        )
        
        self.page.dialog = dialog
        dialog.open = True
        self.page.update()
    
    def _on_create_poi(self, lat: float, lon: float, poi_type: str, description: str):
        """
        Maneja la creación de POI.
        
        Args:
            lat: Latitud
            lon: Longitud
            poi_type: Tipo de POI
            description: Descripción del POI
        """
        poi = self.storage.add_poi(lat, lon, poi_type, description, "user")
        self.poi_manager.add_poi(poi)
        
        # Transmitir vía pub/sub
        if self.page:
            self.page.pubsub.send_all(
                message={
                    "action": "poi_created",
                    "poi": poi,
                },
                topic=CHANNEL_POI,
            )
        
        self._update_map_pois()
        
        # Actualizar mapa
        if self.map_view:
            self.map_view.add_poi(poi)
    
    def _on_delete_poi(self, poi_id: str):
        """
        Maneja la eliminación de POI.
        
        Args:
            poi_id: ID del POI a eliminar
        """
        if self.storage.remove_poi(poi_id):
            self.poi_manager.remove_poi(poi_id)
            
            # Transmitir vía pub/sub
            if self.page:
                self.page.pubsub.send_all(
                    message={
                        "action": "poi_deleted",
                        "poi_id": poi_id,
                    },
                    topic=CHANNEL_POI,
                )
            
            self._update_map_pois()
            
            # Actualizar mapa
            if self.map_view:
                self.map_view.remove_poi(poi_id)
    
    def _load_pois(self):
        """Carga POIs existentes del almacenamiento."""
        pois = self.storage.get_all_pois()
        for poi in pois:
            self.poi_manager.add_poi(poi)
            # Agregar al mapa
            if self.map_view:
                self.map_view.add_poi(poi)
        self._update_map_pois()
    
    def _on_add_poi_button_click(self, e):
        """Maneja el clic del botón agregar POI."""
        # Para MVP, usaremos un diálogo simple con coordenadas
        lat_field = ft.TextField(label="Latitud", value=str(self.config.default_latitude))
        lon_field = ft.TextField(label="Longitud", value=str(self.config.default_longitude))
        poi_type_dropdown = ft.Dropdown(
            label="Tipo de POI",
            options=[
                ft.dropdown.Option(key=POIType.HAZARD.value, text="Peligro"),
                ft.dropdown.Option(key=POIType.TARGET.value, text="Objetivo"),
                ft.dropdown.Option(key=POIType.CHECKPOINT.value, text="Punto de Control"),
                ft.dropdown.Option(key=POIType.LANDING_ZONE.value, text="Zona de Aterrizaje"),
                ft.dropdown.Option(key=POIType.OTHER.value, text="Otro"),
            ],
            value=POIType.OTHER.value,
        )
        description_field = ft.TextField(label="Descripción", multiline=True, max_lines=3)
        
        def on_save(dialog_e):
            try:
                lat = float(lat_field.value)
                lon = float(lon_field.value)
                poi_type = poi_type_dropdown.value
                description = description_field.value or ""
                self._on_create_poi(lat, lon, poi_type, description)
                self.page.close_dialog()
                self.page.update()
            except ValueError:
                pass
        
        dialog = ft.AlertDialog(
            title=ft.Text("Crear Punto de Interés"),
            content=ft.Column(
                controls=[lat_field, lon_field, poi_type_dropdown, description_field],
                tight=True,
                height=250,
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: self.page.close_dialog()),
                ft.ElevatedButton("Crear", on_click=on_save),
            ],
        )
        
        self.page.dialog = dialog
        dialog.open = True
        self.page.update()
    
    def _update_map_pois(self):
        """Actualiza los marcadores POI en el mapa."""
        if not self.page or not self.poi_markers_container:
            return
        
        # Verificar que el contenedor esté en la página antes de actualizar
        try:
            # Intentar acceder a la página del contenedor
            if not hasattr(self.poi_markers_container, '_Control__page') or self.poi_markers_container._Control__page is None:
                return
        except:
            return
        
        pois = self.storage.get_all_pois()
        self.poi_markers_container.content.controls.clear()
        
        # Traducciones de tipos de POI
        poi_type_names = {
            "hazard": "PELIGRO",
            "target": "OBJETIVO",
            "checkpoint": "PUNTO DE CONTROL",
            "landing_zone": "ZONA DE ATERRIZAJE",
            "other": "OTRO"
        }
        
        for poi in pois:
            poi_type = poi.get("type", "other")
            colors = {
                "hazard": RED,
                "target": BLUE,
                "checkpoint": AMBER,
                "landing_zone": GREEN,
                "other": GREY,
            }
            color = colors.get(poi_type, GREY)
            type_display = poi_type_names.get(poi_type, poi_type.upper())
            
            self.poi_markers_container.content.controls.append(
                ft.Container(
                    content=ft.Row(
                        controls=[
                            ft.Container(
                                width=12,
                                height=12,
                                bgcolor=color,
                                border_radius=6,
                            ),
                            ft.Text(
                                f"{type_display}: {poi.get('description', 'Sin descripción')}",
                                size=11,
                            ),
                        ],
                        spacing=5,
                    ),
                    padding=5,
                )
            )
        
        self.poi_markers_container.update()
    
    def update_telemetry(self, telemetry: Dict[str, Any]):
        """
        Actualiza la visualización de telemetría.
        
        Args:
            telemetry: Diccionario de telemetría
        """
        try:
            self.telemetry_panel.update_telemetry(telemetry)
            self._update_map_drones()
            
            # Actualizar mapa si está disponible
            if self.map_view:
                self.map_view.update_drone(telemetry)
            
            # Asegurar que la página se actualice
            if self.page:
                self.page.update()
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error en update_telemetry: {e}", exc_info=True)
    
    def _update_map_drones(self):
        """Actualiza los marcadores de drones en el mapa."""
        if not self.page or not self.drone_positions_container:
            return
        
        # Verificar que el contenedor esté en la página antes de actualizar
        try:
            # Intentar acceder a la página del contenedor
            if not hasattr(self.drone_positions_container, '_Control__page') or self.drone_positions_container._Control__page is None:
                return
        except:
            return
        
        drones = self.telemetry_panel.drones
        self.drone_positions_container.content.controls.clear()
        
        for drone_id, telemetry in drones.items():
            battery = telemetry.get("battery", 0.0)
            battery_color = (
                GREEN if battery > 50
                else AMBER if battery > 20
                else RED
            )
            
            self.drone_positions_container.content.controls.append(
                ft.Container(
                    content=ft.Row(
                        controls=[
                            ft.Icon(ft.Icons.FLIGHT_TAKEOFF, size=16, color=GREEN),
                            ft.Text(drone_id, size=11, weight=ft.FontWeight.BOLD),
                            ft.Text(
                                f"Batería: {battery:.1f}%",
                                size=10,
                                color=battery_color,
                            ),
                            ft.Text(
                                f"Alt: {telemetry.get('altitude', 0):.1f}m",
                                size=10,
                            ),
                            ft.Text(
                                f"Pos: {telemetry.get('latitude', 0):.4f}, {telemetry.get('longitude', 0):.4f}",
                                size=9,
                                color=GREY_600,
                            ),
                        ],
                        spacing=5,
                    ),
                    padding=5,
                )
            )
        
        self.drone_positions_container.update()
    
    def _setup_pubsub(self):
        """Configura suscripciones pub/sub para actualizaciones en tiempo real."""
        if not self.page:
            return
        
        # Suscribirse a actualizaciones de telemetría
        def on_telemetry(message):
            if message.get("action") == "telemetry_update":
                self.update_telemetry(message.get("telemetry", {}))
        
        # Suscribirse a actualizaciones de POI
        def on_poi(message):
            action = message.get("action")
            if action == "poi_created":
                self.poi_manager.add_poi(message.get("poi", {}))
                self._update_map_pois()
            elif action == "poi_deleted":
                self.poi_manager.remove_poi(message.get("poi_id", ""))
                self._update_map_pois()
        
        # Nota: El pub/sub de Flet funciona de manera diferente - lo manejaremos en el loop principal
        # Por ahora, las actualizaciones vienen directamente del gestor de drones
