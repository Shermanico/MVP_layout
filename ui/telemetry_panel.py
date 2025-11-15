"""
Componente de panel de visualización de telemetría.
Muestra telemetría en tiempo real para todos los drones.
"""
import flet as ft
from typing import Dict, List, Any
from common.utils import format_timestamp
from common.colors import (
    RED, GREEN, BLUE, AMBER, GREY, GREY_300, GREY_600, 
    BLUE_700, SURFACE_VARIANT
)


class TelemetryPanel:
    """
    Componente UI para mostrar telemetría de drones.
    """
    
    def __init__(self, page_height: int = 900):
        """
        Inicializa el panel de telemetría.
        
        Args:
            page_height: Altura de la página para calcular altura del scroll
        """
        self.drones: Dict[str, Dict[str, Any]] = {}
        self.page_height = page_height
        # Crear Column con scroll para contenido scrolleable
        self.drone_list_view = ft.Column(
            controls=[],
            spacing=5,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )
        self.panel = self._create_panel()
    
    def _create_panel(self) -> ft.Container:
        """Crea el panel de telemetría."""
        # Crear el texto de drones activos como atributo para poder actualizarlo
        self.active_drones_text = ft.Text(f"Drones Activos: {len(self.drones)}", size=12, color=GREY_600)
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Container(
                        content=ft.Column(
                            controls=[
                                ft.Text("Telemetría de Drones", size=18, weight=ft.FontWeight.BOLD),
                                ft.Divider(),
                                self.active_drones_text,
                            ],
                            spacing=5,
                            tight=True,
                        ),
                        padding=ft.padding.only(bottom=5),
                    ),
                    ft.Container(
                        content=self.drone_list_view,
                        expand=True,  # Usar expand=True para ocupar todo el espacio disponible
                    ),
                ],
                spacing=0,
                expand=True,
            ),
            padding=10,
            width=300,
            bgcolor=SURFACE_VARIANT,
            expand=True,
        )
    
    def _create_drone_card(self, telemetry: Dict[str, Any]) -> ft.Card:
        """Crea un widget de tarjeta para la telemetría de un dron (Matrice 300 RTK)."""
        drone_id = telemetry.get("drone_id", "DESCONOCIDO")
        battery = telemetry.get("battery", 0.0)
        altitude = telemetry.get("altitude", 0.0)
        velocity = telemetry.get("velocity", 0.0)
        heading = telemetry.get("heading", 0.0)
        status = telemetry.get("status", "desconocido")
        lat = telemetry.get("latitude", 0.0)
        lon = telemetry.get("longitude", 0.0)
        vertical_speed = telemetry.get("vertical_speed", 0.0)
        rtk_fix = telemetry.get("rtk_fix", False)
        flight_time_remaining = telemetry.get("flight_time_remaining", 0.0)
        
        # Color de batería
        if battery > 50:
            battery_color = GREEN
        elif battery > 20:
            battery_color = AMBER
        else:
            battery_color = RED
        
        # Formatear tiempo de vuelo restante
        if flight_time_remaining > 0:
            minutes = int(flight_time_remaining / 60)
            seconds = int(flight_time_remaining % 60)
            time_str = f"{minutes}m {seconds}s"
        else:
            time_str = "N/A"
        
        # Traducir estado
        status_translations = {
            "idle": "inactivo",
            "flying": "volando",
            "landing": "aterrizando",
            "takeoff": "despegando",
            "armed": "armado",
            "error": "error"
        }
        status_text = status_translations.get(status.lower(), status.upper())
        
        controls = [
            ft.Row(
                controls=[
                    ft.Icon(ft.Icons.FLIGHT_TAKEOFF, size=20),
                    ft.Text(drone_id, weight=ft.FontWeight.BOLD, size=14),
                    ft.Container(
                        content=ft.Row(
                            controls=[
                                ft.Icon(ft.Icons.SATELLITE_ALT, size=14, color=GREEN if rtk_fix else GREY),
                                ft.Text("RTK" if rtk_fix else "GPS", size=9, color=GREY_600),
                            ],
                            spacing=2,
                        ),
                    ) if rtk_fix is not None else ft.Container(),
                ],
                spacing=5,
            ),
            ft.Divider(height=1),
            ft.Row(
                controls=[
                    ft.Text("Batería:", size=11),
                    ft.Container(
                        content=ft.ProgressBar(
                            value=battery / 100,
                            color=battery_color,
                            bgcolor=GREY_300,
                        ),
                        width=100,
                        height=10,
                    ),
                    ft.Text(f"{battery:.1f}%", size=11, color=battery_color),
                ],
                spacing=5,
            ),
            ft.Text(f"Estado: {status_text.upper()}", size=11),
            ft.Text(f"Altitud: {altitude:.1f} m AGL", size=11),
            ft.Text(f"Velocidad: {velocity:.1f} m/s ({velocity * 3.6:.1f} km/h)", size=11),
            ft.Text(f"Rumbo: {heading:.1f}°", size=11),
        ]
        
        # Agregar velocidad vertical si está disponible
        if vertical_speed is not None and abs(vertical_speed) > 0.1:
            vertical_icon = ft.Icons.ARROW_UPWARD if vertical_speed > 0 else ft.Icons.ARROW_DOWNWARD
            controls.append(
                ft.Row(
                    controls=[
                        ft.Icon(vertical_icon, size=12, color=BLUE),
                        ft.Text(f"Vertical: {vertical_speed:.1f} m/s", size=10),
                    ],
                    spacing=3,
                )
            )
        
        # Agregar tiempo de vuelo restante
        if flight_time_remaining > 0:
            controls.append(
                ft.Text(f"Tiempo de vuelo: {time_str}", size=10, color=BLUE_700)
            )
        
        controls.append(
            ft.Text(f"Posición: {lat:.6f}, {lon:.6f}", size=9, color=GREY_600)
        )
        
        return ft.Card(
            content=ft.Container(
                content=ft.Column(
                    controls=controls,
                    spacing=5,
                    tight=True,
                ),
                padding=10,
            ),
        )
    
    def update_telemetry(self, telemetry: Dict[str, Any]):
        """
        Actualiza la telemetría de un dron.
        
        Args:
            telemetry: Diccionario de telemetría
        """
        import logging
        logger = logging.getLogger(__name__)
        
        drone_id = telemetry.get("drone_id")
        if drone_id:
            is_new = drone_id not in self.drones
            self.drones[drone_id] = telemetry
            
            if is_new:
                logger.info(f"Nuevo dron agregado al panel: {drone_id}, total: {len(self.drones)}")
            
            self._refresh_list()
        else:
            logger.warning(f"Telemetría recibida sin drone_id: {telemetry}")
    
    def remove_drone(self, drone_id: str):
        """
        Elimina un dron del panel.
        
        Args:
            drone_id: ID del dron a eliminar
        """
        if drone_id in self.drones:
            del self.drones[drone_id]
            self._refresh_list()
    
    def _refresh_list(self):
        """Actualiza la vista de lista de drones."""
        import logging
        logger = logging.getLogger(__name__)
        
        logger.debug(f"Refrescando lista de drones: {len(self.drones)} drones")
        
        # Limpiar y actualizar el ListView
        self.drone_list_view.controls.clear()
        for telemetry in self.drones.values():
            drone_id = telemetry.get("drone_id", "UNKNOWN")
            self.drone_list_view.controls.append(self._create_drone_card(telemetry))
            logger.debug(f"Agregada tarjeta para {drone_id}")
        
        # Actualizar contador de drones activos (usar el atributo en lugar de buscar en controls)
        if hasattr(self, 'active_drones_text'):
            self.active_drones_text.value = f"Drones Activos: {len(self.drones)}"
        
        try:
            self.drone_list_view.update()
            if hasattr(self, 'active_drones_text'):
                self.active_drones_text.update()
            self.panel.update()
            logger.debug(f"UI actualizada, drones en lista: {[d.get('drone_id') for d in self.drones.values()]}")
        except Exception as e:
            logger.error(f"Error al actualizar UI: {e}", exc_info=True)
    
    def get_panel(self) -> ft.Container:
        """Obtiene el panel de telemetría."""
        return self.panel
