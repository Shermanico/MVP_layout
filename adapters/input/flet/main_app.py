"""
Adaptador de entrada: Aplicación principal Flet.
Orquesta todos los componentes UI y usa los servicios del dominio.
"""
import flet as ft
from typing import Dict, Any, Optional
from domain.ports.input.drone_service_port import IDroneService
from domain.ports.input.poi_service_port import IPOIService
from infrastructure.config.config import Config
from infrastructure.config.constants import POIType, CHANNEL_TELEMETRY, CHANNEL_POI
from infrastructure.config.colors import RED, BLUE_700
from adapters.input.flet.telemetry_panel import TelemetryPanel
from adapters.input.flet.poi_manager import POIManager
from adapters.input.flet.map_view import MapView


class MainApp:
    """
    Aplicación principal que coordina todos los componentes UI.
    Usa los puertos de entrada IDroneService e IPOIService.
    """
    
    def __init__(
        self,
        config: Config,
        drone_service: IDroneService,
        poi_service: IPOIService,
        page: ft.Page
    ):
        """
        Inicializa la aplicación principal.
        
        Args:
            config: Configuración de la aplicación
            drone_service: Servicio de drones (puerto de entrada)
            poi_service: Servicio de POIs (puerto de entrada)
            page: Página Flet
        """
        self.config = config
        self.drone_service = drone_service
        self.poi_service = poi_service
        self.page = page
        
        # Componentes UI
        self.telemetry_panel = TelemetryPanel(page)
        self.poi_manager = POIManager(page, on_delete_poi=self._on_delete_poi)
        self.map_view = MapView(
            initial_lat=config.default_latitude,
            initial_lon=config.default_longitude,
            zoom=config.default_zoom
        )
        
        # Cargar POIs existentes
        self._load_existing_pois()
    
    def setup_page(self, page: ft.Page) -> None:
        """
        Configura la página Flet.
        
        Args:
            page: Página Flet
        """
        page.title = self.config.window_title
        page.window.width = self.config.window_width
        page.window.height = self.config.window_height
        
        # Layout principal: Mapa a la izquierda, paneles a la derecha
        page.add(
            ft.Row(
                controls=[
                    # Mapa (izquierda)
                    ft.Container(
                        content=self.map_view.get_view(),
                        expand=2,
                        border=ft.border.all(1, ft.colors.GREY_300)
                    ),
                    # Paneles (derecha)
                    ft.Container(
                        content=ft.Column(
                            controls=[
                                # Panel de telemetría
                                ft.Container(
                                    content=self.telemetry_panel.get_panel(),
                                    expand=1,
                                    border=ft.border.all(1, ft.colors.GREY_300)
                                ),
                                # Panel de POIs
                                ft.Container(
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
                                                    ft.ElevatedButton(
                                                        "Agregar POI",
                                                        icon=ft.Icons.ADD,
                                                        on_click=self._on_add_poi_button_click
                                                    )
                                                ],
                                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                                            ),
                                            self.poi_manager.get_panel()
                                        ],
                                        spacing=10,
                                        expand=True
                                    ),
                                    expand=1,
                                    border=ft.border.all(1, ft.colors.GREY_300),
                                    padding=ft.padding.all(15)
                                )
                            ],
                            spacing=0,
                            expand=True
                        ),
                        width=400,
                        border=ft.border.all(1, ft.colors.GREY_300)
                    )
                ],
                spacing=0,
                expand=True
            )
        )
    
    def update_telemetry(self, telemetry: Dict[str, Any]) -> None:
        """
        Actualiza la telemetría de un dron.
        
        Args:
            telemetry: Diccionario de telemetría
        """
        # Actualizar panel de telemetría
        self.telemetry_panel.update_telemetry(telemetry)
        
        # Actualizar mapa
        self.map_view.update_drone(telemetry)
        
        # Transmitir vía pub/sub (opcional, para multi-cliente)
        try:
            self.page.pubsub.send_all(
                message={
                    "action": "telemetry_update",
                    "telemetry": telemetry,
                },
                topic=CHANNEL_TELEMETRY,
            )
        except:
            pass
    
    def _on_add_poi_button_click(self, e: ft.ControlEvent) -> None:
        """Maneja el clic en el botón de agregar POI."""
        # Campos del diálogo
        lat_field = ft.TextField(label="Latitud", value=str(self.config.default_latitude))
        lon_field = ft.TextField(label="Longitud", value=str(self.config.default_longitude))
        type_field = ft.Dropdown(
            label="Tipo",
            options=[
                ft.dropdown.Option(key=POIType.HAZARD.value, text="Peligro"),
                ft.dropdown.Option(key=POIType.TARGET.value, text="Objetivo"),
                ft.dropdown.Option(key=POIType.CHECKPOINT.value, text="Punto de Control"),
                ft.dropdown.Option(key=POIType.LANDING_ZONE.value, text="Zona de Aterrizaje"),
                ft.dropdown.Option(key=POIType.OTHER.value, text="Otro"),
            ],
            value=POIType.OTHER.value
        )
        desc_field = ft.TextField(label="Descripción", multiline=True, max_lines=3)
        
        def create_poi(e: ft.ControlEvent) -> None:
            try:
                lat = float(lat_field.value)
                lon = float(lon_field.value)
                poi_type = type_field.value or POIType.OTHER.value
                description = desc_field.value or ""
                
                # Usar el servicio (puerto de entrada)
                poi_dto = self.poi_service.create_poi(
                    latitude=lat,
                    longitude=lon,
                    poi_type=poi_type,
                    description=description
                )
                
                # Actualizar UI
                self.poi_manager.add_poi(poi_dto.to_dict())
                self.map_view.add_poi(poi_dto.to_dict())
                
                # Transmitir vía pub/sub
                try:
                    self.page.pubsub.send_all(
                        message={
                            "action": "poi_created",
                            "poi": poi_dto.to_dict(),
                        },
                        topic=CHANNEL_POI,
                    )
                except:
                    pass
                
                dialog.open = False
                self.page.update()
            except ValueError:
                # Mostrar error
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text("Error: Latitud y longitud deben ser números válidos"),
                    bgcolor=RED
                )
                self.page.snack_bar.open = True
                self.page.update()
        
        dialog = ft.AlertDialog(
            title=ft.Text("Agregar Punto de Interés"),
            content=ft.Column(
                controls=[lat_field, lon_field, type_field, desc_field],
                height=300,
                tight=True
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: setattr(dialog, "open", False) or self.page.update()),
                ft.TextButton("Crear", on_click=create_poi)
            ],
            actions_alignment=ft.MainAxisAlignment.END
        )
        
        self.page.dialog = dialog
        dialog.open = True
        self.page.update()
    
    def _on_delete_poi(self, poi_id: str) -> None:
        """Maneja la eliminación de un POI."""
        # Usar el servicio (puerto de entrada)
        success = self.poi_service.delete_poi(poi_id)
        
        if success:
            # Actualizar UI
            self.poi_manager.remove_poi(poi_id)
            self.map_view.remove_poi(poi_id)
            
            # Transmitir vía pub/sub
            try:
                self.page.pubsub.send_all(
                    message={
                        "action": "poi_deleted",
                        "poi_id": poi_id,
                    },
                    topic=CHANNEL_POI,
                )
            except:
                pass
    
    def _load_existing_pois(self) -> None:
        """Carga POIs existentes del servicio."""
        try:
            pois = self.poi_service.get_all_pois()
            for poi_dto in pois:
                poi_dict = poi_dto.to_dict()
                self.poi_manager.add_poi(poi_dict)
                self.map_view.add_poi(poi_dict)
        except:
            pass
    
    def cleanup(self) -> None:
        """Limpia recursos."""
        self.map_view.cleanup()

