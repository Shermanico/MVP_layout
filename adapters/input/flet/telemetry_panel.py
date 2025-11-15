"""
Adaptador de entrada: Panel de telemetría de drones.
Muestra telemetría en tiempo real para cada dron.
"""
import flet as ft
from typing import Dict, Any, Optional
from infrastructure.config.colors import (
    GREEN, RED, AMBER, GREY_200, GREY_600, BLUE_700, SURFACE, SURFACE_VARIANT
)
from infrastructure.config.utils import format_timestamp


class TelemetryPanel:
    """
    Panel de telemetría que muestra información de todos los drones activos.
    Panel scrolleable para múltiples drones.
    """
    
    def __init__(self, page: ft.Page):
        """
        Inicializa el panel de telemetría.
        
        Args:
            page: Página Flet
        """
        self.page = page
        self.drone_data: Dict[str, Dict[str, Any]] = {}
        self.drone_cards: Dict[str, ft.Card] = {}
        
        # Componentes UI
        self.active_drones_text = ft.Text(
            "Drones Activos: 0",
            size=18,
            weight=ft.FontWeight.BOLD,
            color=BLUE_700
        )
        self.drone_list_view = ft.Column(
            spacing=10,
            scroll=ft.ScrollMode.AUTO,
            expand=True
        )
        
        self.panel = self._create_panel()
    
    def _create_panel(self) -> ft.Container:
        """Crea el panel de telemetría."""
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Container(
                        content=self.active_drones_text,
                        padding=ft.padding.only(bottom=10)
                    ),
                    ft.Container(
                        content=self.drone_list_view,
                        expand=True
                    )
                ],
                spacing=0,
                expand=True
            ),
            padding=ft.padding.all(15),
            bgcolor=SURFACE,
            expand=True
        )
    
    def update_telemetry(self, telemetry: Dict[str, Any]) -> None:
        """
        Actualiza la telemetría de un dron.
        
        Args:
            telemetry: Diccionario de telemetría del dron
        """
        drone_id = telemetry.get("drone_id", "UNKNOWN")
        self.drone_data[drone_id] = telemetry
        
        # Actualizar o crear tarjeta
        if drone_id in self.drone_cards:
            self._update_card(drone_id, telemetry)
        else:
            self._create_card(drone_id, telemetry)
        
        # Actualizar contador
        self.active_drones_text.value = f"Drones Activos: {len(self.drone_data)}"
        self.page.update()
    
    def _create_card(self, drone_id: str, telemetry: Dict[str, Any]) -> None:
        """Crea una tarjeta de telemetría para un dron."""
        card = self._build_card(drone_id, telemetry)
        self.drone_cards[drone_id] = card
        self.drone_list_view.controls.append(card)
    
    def _update_card(self, drone_id: str, telemetry: Dict[str, Any]) -> None:
        """Actualiza una tarjeta existente."""
        if drone_id in self.drone_cards:
            # Reemplazar la tarjeta
            old_card = self.drone_cards[drone_id]
            new_card = self._build_card(drone_id, telemetry)
            index = self.drone_list_view.controls.index(old_card)
            self.drone_list_view.controls[index] = new_card
            self.drone_cards[drone_id] = new_card
    
    def _build_card(self, drone_id: str, telemetry: Dict[str, Any]) -> ft.Card:
        """Construye una tarjeta de telemetría."""
        battery = telemetry.get("battery", 100.0)
        battery_color = GREEN if battery > 50 else (AMBER if battery > 20 else RED)
        
        altitude = telemetry.get("altitude", 0.0)
        velocity = telemetry.get("velocity", 0.0)
        heading = telemetry.get("heading", 0.0)
        status = telemetry.get("status", "unknown")
        rtk_fix = telemetry.get("rtk_fix", False)
        timestamp = telemetry.get("timestamp", 0.0)
        
        return ft.Card(
            content=ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Row(
                            controls=[
                                ft.Text(
                                    drone_id,
                                    size=16,
                                    weight=ft.FontWeight.BOLD,
                                    color=BLUE_700
                                ),
                                ft.Container(
                                    content=ft.Text(
                                        f"{battery:.1f}%",
                                        size=14,
                                        weight=ft.FontWeight.BOLD,
                                        color="white"
                                    ),
                                    bgcolor=battery_color,
                                    padding=ft.padding.symmetric(horizontal=10, vertical=5),
                                    border_radius=5
                                )
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                        ),
                        ft.Divider(height=1),
                        ft.Row(
                            controls=[
                                ft.Column(
                                    controls=[
                                        ft.Text("Altitud", size=12, color=GREY_600),
                                        ft.Text(f"{altitude:.1f} m", size=14, weight=ft.FontWeight.BOLD)
                                    ],
                                    spacing=2
                                ),
                                ft.Column(
                                    controls=[
                                        ft.Text("Velocidad", size=12, color=GREY_600),
                                        ft.Text(f"{velocity:.1f} m/s", size=14, weight=ft.FontWeight.BOLD)
                                    ],
                                    spacing=2
                                ),
                                ft.Column(
                                    controls=[
                                        ft.Text("Rumbo", size=12, color=GREY_600),
                                        ft.Text(f"{heading:.0f}°", size=14, weight=ft.FontWeight.BOLD)
                                    ],
                                    spacing=2
                                )
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_AROUND
                        ),
                        ft.Row(
                            controls=[
                                ft.Text(f"Estado: {status}", size=12, color=GREY_600),
                                ft.Text(
                                    "RTK ✓" if rtk_fix else "RTK ✗",
                                    size=12,
                                    color=GREEN if rtk_fix else RED
                                )
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN
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
    
    def get_panel(self) -> ft.Container:
        """Obtiene el panel de telemetría."""
        return self.panel

