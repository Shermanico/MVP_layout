"""
Aplicación UI principal de Flet.
Coordina todos los componentes UI y maneja actualizaciones en tiempo real.
"""
import flet as ft
import asyncio
from typing import Dict, Any, Optional, List
from common.config import Config
from common.constants import POIType, CHANNEL_TELEMETRY, CHANNEL_POI
from common.colors import (
    RED, GREEN, BLUE, AMBER, GREY, GREY_600, 
    SURFACE, BLUE_GREY_50,
    get_surface_color, get_surface_variant_color, 
    get_text_color, get_text_secondary_color, get_background_color
)
from backend.storage import POIStorage
from ui.telemetry_panel import TelemetryPanel
from ui.poi_manager import POIManager
from ui.map_view import MapView
from ui.zone_manager import ZoneManager
from common.constants import FlightFormation


class MainApp:
    """
    Clase principal de la aplicación que coordina todos los componentes UI.
    """
    
    def __init__(self, config: Config, storage: POIStorage, drone_manager=None):
        """
        Inicializa la aplicación principal.
        
        Args:
            config: Configuración de la aplicación
            storage: Instancia de almacenamiento de POIs
            drone_manager: Instancia de DroneManager para enviar comandos a los drones
        """
        self.config = config
        self.storage = storage
        self.drone_manager = drone_manager
        self.page: Optional[ft.Page] = None
        
        # Componentes UI (se inicializarán con la página para acceso al tema)
        self.telemetry_panel = None
        self.poi_manager = None
        self.zone_manager = None
        
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
        
        # Inicializar componentes UI con acceso a la página para colores adaptativos
        self.telemetry_panel = TelemetryPanel(page=page, page_height=self.config.window_height)
        self.poi_manager = POIManager(
            page=page,
            on_create_poi=self._on_create_poi,
            on_delete_poi=self._on_delete_poi,
            page_height=self.config.window_height
        )
        self.zone_manager = ZoneManager(
            page=page,
            on_zone_created=self._on_zone_created,
            on_zone_deleted=self._on_delete_zone,
            on_formation_selected=self._on_formation_selected,
            page_height=self.config.window_height
        )
        
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
                ft.Container(
                    content=map_view,
                    expand=True,
                ),
                ft.Container(
                    content=side_panel,
                    width=320,
                ),
            ],
            expand=True,
            spacing=0,
            vertical_alignment=ft.CrossAxisAlignment.START,
        )
    
    def _create_map_view(self) -> ft.Container:
        """Crea el componente de vista de mapa."""
        # Crear instancia de MapView
        self.map_view = MapView(
            initial_lat=self.config.default_latitude,
            initial_lon=self.config.default_longitude,
            zoom=self.config.default_zoom,
            on_poi_click=self._on_poi_click,
            on_map_click=self._on_map_click,
            on_zone_created=self._on_zone_created,
            page=self.page
        )
        
        # Iniciar polling para leer eventos del mapa
        self._start_map_events_polling()
        
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
        
        # Layout con mapa (los controles ahora están en el mapa)
        map_container = ft.Container(
            content=ft.Column(
                controls=[
                    # Título del mapa
                    ft.Text("Vista de Mapa", size=20, weight=ft.FontWeight.BOLD, color=get_text_color(self.page) if self.page else "#000000"),
                    ft.Divider(),
                    # Mapa interactivo (los botones están integrados en el mapa)
                    self.map_view.get_view(),
                ],
                spacing=10,
                expand=True,
            ),
            expand=True,
            bgcolor=get_background_color(self.page) if self.page else BLUE_GREY_50,
            padding=10,
        )
        
        return map_container
    
    def _on_map_click(self, lat: float, lon: float):
        """Maneja clic en el mapa para crear POI."""
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"_on_map_click llamado con lat={lat}, lon={lon}")
        
        # Verificar modo del mapa
        if self.map_view and self.map_view.telemetry_server:
            mode = self.map_view.telemetry_server.data_store.get_map_mode()
            if mode != "click":
                logger.info(f"Modo del mapa no es 'click' ({mode}), ignorando clic")
                return
        
        # TEMPORAL: Crear POI automáticamente sin diálogo para pruebas
        # Esto nos permite verificar si el problema es el diálogo o la visualización
        logger.info("Creando POI automáticamente (modo de prueba, sin diálogo)")
        try:
            self._on_create_poi(lat, lon, "other", "POI creado desde mapa")
            if self.page:
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text(f"POI creado en {lat:.6f}, {lon:.6f}"),
                    bgcolor=GREEN
                )
                self.page.snack_bar.open = True
                self.page.update()
        except Exception as err:
            logger.error(f"Error al crear POI automáticamente: {err}", exc_info=True)
            if self.page:
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text(f"Error al crear POI: {err}"),
                    bgcolor=RED
                )
                self.page.snack_bar.open = True
                self.page.update()
        
        # Mostrar diálogo para crear POI (comentado temporalmente para pruebas)
        # self._create_poi_dialog(lat, lon)
    
    def _on_poi_click(self, poi_id: str):
        """Maneja clic en un POI del mapa."""
        # Opcional: mostrar información del POI o permitir edición
        pass
    
    def _on_draw_zone_button_click(self, e):
        """Maneja el clic del botón para dibujar zona."""
        # Cambiar modo del mapa a 'rectangle'
        if self.map_view and self.map_view.telemetry_server:
            self.map_view.telemetry_server.set_map_mode('rectangle')
        
        # Mostrar mensaje al usuario
        if self.page:
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text("Modo dibujo activado: Arrastra el cursor en el mapa para dibujar una zona"),
                bgcolor=BLUE
            )
            self.page.snack_bar.open = True
            self.page.update()
    
    def _on_zone_created(self, zone: Dict[str, Any]):
        """Maneja la creación de una zona de interés."""
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"_on_zone_created llamado: {zone.get('id', 'unknown')}")
        
        # Agregar zona al ZoneManager (skip_callback=True para evitar bucle infinito)
        self.zone_manager.add_zone(zone, skip_callback=True)
        
        # Actualizar servidor HTTP
        if self.map_view and self.map_view.telemetry_server:
            self.map_view.telemetry_server.update_zone(zone)
        
        # Mostrar mensaje
        if self.page:
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(f"Zona creada: {zone.get('id', 'unknown')}"),
                bgcolor=GREEN
            )
            self.page.snack_bar.open = True
            self.page.update()
    
    def _on_delete_zone(self, zone_id: str):
        """Maneja la eliminación de una zona de interés."""
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"_on_delete_zone llamado: {zone_id}")
        
        # Eliminar del servidor HTTP
        if self.map_view and self.map_view.telemetry_server:
            self.map_view.telemetry_server.remove_zone(zone_id)
            logger.info(f"Zona {zone_id} eliminada del servidor HTTP")
        
        # El JavaScript detectará que la zona ya no está en el servidor y la eliminará del mapa automáticamente
    
    def _on_formation_selected(self, zone_id: str, formation: FlightFormation):
        """Maneja la selección de una formación de vuelo."""
        import logging
        logger = logging.getLogger(__name__)
        
        # Obtener zona
        zone = self.zone_manager.zones.get(zone_id)
        if not zone:
            logger.warning(f"Zona {zone_id} no encontrada")
            return
        
        # Obtener drones disponibles (filtrados por batería y estado)
        available_drones = self._get_available_drones()
        
        if not available_drones:
            if self.page:
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text("No hay drones disponibles para la formación"),
                    bgcolor=RED
                )
                self.page.snack_bar.open = True
                self.page.update()
            return
        
        # Calcular waypoints según la formación
        waypoints = self._calculate_formation_waypoints(zone, formation, available_drones)
        
        # Mostrar mensaje
        if self.page:
            self.page.snack_bar = ft.SnackBar(
                content=ft.Text(f"Formación {formation.value} aplicada a {len(waypoints)} drones"),
                bgcolor=GREEN
            )
            self.page.snack_bar.open = True
            self.page.update()
        
        logger.info(f"Formación {formation.value} aplicada a zona {zone_id} con {len(waypoints)} waypoints")
    
    def _calculate_formation_waypoints(self, zone: Dict[str, Any], formation: FlightFormation, drone_ids: List[str]) -> List[Dict[str, Any]]:
        """
        Calcula waypoints para una formación de vuelo.
        
        Args:
            zone: Zona de interés con bounds
            formation: Tipo de formación
            drone_ids: Lista de IDs de drones disponibles
            
        Returns:
            Lista de waypoints para cada dron
        """
        bounds = zone.get('bounds', {})
        north = bounds.get('north', 0)
        south = bounds.get('south', 0)
        east = bounds.get('east', 0)
        west = bounds.get('west', 0)
        
        center_lat = (north + south) / 2
        center_lon = (east + west) / 2
        
        waypoints = []
        num_drones = len(drone_ids)
        
        if formation == FlightFormation.GRID:
            # Formación en cuadrícula
            rows = int(num_drones ** 0.5) + 1
            cols = (num_drones + rows - 1) // rows
            
            lat_step = (north - south) / (rows + 1)
            lon_step = (east - west) / (cols + 1)
            
            for i, drone_id in enumerate(drone_ids):
                row = i // cols
                col = i % cols
                waypoints.append({
                    'drone_id': drone_id,
                    'latitude': south + lat_step * (row + 1),
                    'longitude': west + lon_step * (col + 1),
                    'altitude': 50.0
                })
        
        elif formation == FlightFormation.LINE:
            # Formación en línea
            lat_step = (north - south) / (num_drones + 1)
            for i, drone_id in enumerate(drone_ids):
                waypoints.append({
                    'drone_id': drone_id,
                    'latitude': south + lat_step * (i + 1),
                    'longitude': center_lon,
                    'altitude': 50.0
                })
        
        elif formation == FlightFormation.CIRCLE:
            # Formación circular
            import math
            radius = min((north - south) / 2, (east - west) / 2) * 0.4
            angle_step = 2 * math.pi / num_drones
            
            for i, drone_id in enumerate(drone_ids):
                angle = i * angle_step
                waypoints.append({
                    'drone_id': drone_id,
                    'latitude': center_lat + radius * math.cos(angle),
                    'longitude': center_lon + radius * math.sin(angle),
                    'altitude': 50.0
                })
        
        elif formation == FlightFormation.SPIRAL:
            # Formación en espiral
            import math
            max_radius = min((north - south) / 2, (east - west) / 2) * 0.4
            radius_step = max_radius / num_drones
            angle_step = 2 * math.pi / 3  # 3 vueltas
            
            for i, drone_id in enumerate(drone_ids):
                radius = radius_step * (i + 1)
                angle = i * angle_step
                waypoints.append({
                    'drone_id': drone_id,
                    'latitude': center_lat + radius * math.cos(angle),
                    'longitude': center_lon + radius * math.sin(angle),
                    'altitude': 50.0
                })
        
        elif formation == FlightFormation.ZIGZAG:
            # Formación en zigzag
            rows = int(num_drones ** 0.5) + 1
            cols = (num_drones + rows - 1) // rows
            
            lat_step = (north - south) / (rows + 1)
            lon_step = (east - west) / (cols + 1)
            
            for i, drone_id in enumerate(drone_ids):
                row = i // cols
                col = i % cols
                # Zigzag: alternar dirección en cada fila
                if row % 2 == 1:
                    col = cols - 1 - col
                waypoints.append({
                    'drone_id': drone_id,
                    'latitude': south + lat_step * (row + 1),
                    'longitude': west + lon_step * (col + 1),
                    'altitude': 50.0
                })
        
        return waypoints
    
    def _get_available_drones(self) -> List[str]:
        """
        Obtiene lista de drones disponibles para vuelo coordinado.
        Un dron está disponible si:
        - Tiene batería > 20%
        - Está en estado 'flying', 'armed', o 'idle' (no 'error' o 'landing')
        - Está calibrado (rtk_fix=True si está disponible en telemetría)
        
        Returns:
            Lista de IDs de drones disponibles
        """
        if not self.telemetry_panel:
            return []
        
        available = []
        for drone_id, telemetry in self.telemetry_panel.drones.items():
            battery = telemetry.get('battery', 0)
            status = telemetry.get('status', 'idle').lower()
            
            # Verificar batería (mínimo 20%)
            if battery < 20:
                continue
            
            # Verificar estado (debe estar listo para volar)
            if status in ['error', 'landing']:
                continue
            
            # Verificar calibración RTK si está disponible
            rtk_fix = telemetry.get('rtk_fix', True)  # Por defecto True si no está disponible
            if not rtk_fix:
                continue
            
            available.append(drone_id)
        
        return available
    
    def _calculate_sequential_vertical_formation(self, zone: Dict[str, Any], drone_ids: List[str]) -> List[Dict[str, Any]]:
        """
        Calcula waypoints para formación de cuadrícula que cubre la zona de interés.
        Los drones se distribuyen uniformemente dentro del rectángulo azul para cubrirlo completamente.
        
        Args:
            zone: Zona de interés con bounds
            drone_ids: Lista de IDs de drones disponibles
            
        Returns:
            Lista de waypoints para cada dron
        """
        bounds = zone.get('bounds', {})
        north = bounds.get('north', 0)
        south = bounds.get('south', 0)
        east = bounds.get('east', 0)
        west = bounds.get('west', 0)
        
        waypoints = []
        num_drones = len(drone_ids)
        
        if num_drones == 0:
            return waypoints
        
        # Formación de cuadrícula: distribuir drones uniformemente dentro de la zona
        # Calcular número de filas y columnas para una distribución óptima
        import math
        rows = int(math.sqrt(num_drones))
        cols = int(math.ceil(num_drones / rows))
        
        # Espaciado dentro de la zona (con márgenes para evitar bordes)
        margin = 0.05  # 5% de margen desde los bordes
        lat_range = north - south
        lon_range = east - west
        lat_margin = lat_range * margin
        lon_margin = lon_range * margin
        
        # Área útil dentro de la zona
        usable_south = south + lat_margin
        usable_north = north - lat_margin
        usable_west = west + lon_margin
        usable_east = east - lon_margin
        
        # Pasos para distribuir los drones
        if rows > 1:
            lat_step = (usable_north - usable_south) / (rows - 1)
        else:
            lat_step = 0
            usable_south = (usable_north + usable_south) / 2  # Centrar si solo hay una fila
        
        if cols > 1:
            lon_step = (usable_east - usable_west) / (cols - 1)
        else:
            lon_step = 0
            usable_west = (usable_east + usable_west) / 2  # Centrar si solo hay una columna
        
        # Distribuir drones en la cuadrícula
        for i, drone_id in enumerate(drone_ids):
            row = i // cols
            col = i % cols
            
            # Calcular posición dentro de la zona
            lat = usable_south + lat_step * row
            lon = usable_west + lon_step * col
            
            waypoints.append({
                'drone_id': drone_id,
                'latitude': lat,
                'longitude': lon,
                'altitude': 50.0  # Altura fija de 50m
            })
        
        return waypoints
    
    def _execute_coordinated_flight(self, e):
        """
        Ejecuta vuelo coordinado para todos los drones disponibles.
        Los drones se organizan en formación de cuadrícula dentro de la zona activa
        para cubrirla completamente de forma coordinada y alineada.
        """
        import logging
        import asyncio
        logger = logging.getLogger(__name__)
        logger.info("Iniciando vuelo coordinado...")
        
        # Verificar que haya zona activa
        if not self.zone_manager or not self.zone_manager.active_zone_id:
            if self.page:
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text("No hay zona activa. Selecciona una zona primero."),
                    bgcolor=RED
                )
                self.page.snack_bar.open = True
                self.page.update()
            return
        
        zone_id = self.zone_manager.active_zone_id
        zone = self.zone_manager.zones.get(zone_id)
        
        if not zone:
            if self.page:
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text("Zona activa no encontrada."),
                    bgcolor=RED
                )
                self.page.snack_bar.open = True
                self.page.update()
            return
        
        # Obtener drones disponibles
        available_drones = self._get_available_drones()
        
        if not available_drones:
            if self.page:
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text("No hay drones disponibles. Verifica batería y estado."),
                    bgcolor=RED
                )
                self.page.snack_bar.open = True
                self.page.update()
            return
        
        # Calcular waypoints en formación de cuadrícula
        waypoints = self._calculate_sequential_vertical_formation(zone, available_drones)
        
        if not waypoints:
            if self.page:
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text("No se pudieron calcular waypoints."),
                    bgcolor=RED
                )
                self.page.snack_bar.open = True
                self.page.update()
            return
        
        # Enviar comandos a los drones
        if not self.drone_manager:
            logger.error("DroneManager no disponible")
            if self.page:
                self.page.snack_bar = ft.SnackBar(
                    content=ft.Text("Error: Gestor de drones no disponible."),
                    bgcolor=RED
                )
                self.page.snack_bar.open = True
                self.page.update()
            return
        
        # Enviar comandos de forma asíncrona
        async def send_commands():
            try:
                for waypoint in waypoints:
                    await self.drone_manager.send_command_to_drone(
                        waypoint['drone_id'],
                        "set_target",
                        latitude=waypoint['latitude'],
                        longitude=waypoint['longitude'],
                        altitude=waypoint['altitude']
                    )
                    logger.info(f"Comando enviado a {waypoint['drone_id']}: lat={waypoint['latitude']:.6f}, lon={waypoint['longitude']:.6f}")
                
                # Mostrar mensaje de éxito
                if self.page:
                    self.page.snack_bar = ft.SnackBar(
                        content=ft.Text(f"Vuelo coordinado iniciado: {len(waypoints)} drones en formación de cuadrícula"),
                        bgcolor=GREEN
                    )
                    self.page.snack_bar.open = True
                    self.page.update()
                
                logger.info(f"Vuelo coordinado iniciado: {len(waypoints)} drones")
            except Exception as err:
                logger.error(f"Error enviando comandos de vuelo: {err}", exc_info=True)
                if self.page:
                    self.page.snack_bar = ft.SnackBar(
                        content=ft.Text(f"Error al iniciar vuelo coordinado: {err}"),
                        bgcolor=RED
                    )
                    self.page.snack_bar.open = True
                    self.page.update()
        
        # Ejecutar comandos en un hilo separado con su propio event loop
        import threading
        def run_async():
            try:
                # Crear un nuevo event loop para este hilo
                new_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(new_loop)
                new_loop.run_until_complete(send_commands())
                new_loop.close()
            except Exception as err:
                logger.error(f"Error ejecutando comandos en hilo: {err}", exc_info=True)
        
        # Ejecutar en un hilo separado para no bloquear la UI
        thread = threading.Thread(target=run_async, daemon=True)
        thread.start()
    
    def _start_map_events_polling(self):
        """Inicia polling para leer eventos del mapa."""
        import threading
        import time
        import logging
        logger = logging.getLogger(__name__)
        
        def poll_events():
            logger.info("Iniciando polling de eventos del mapa...")
            poll_count = 0
            while True:
                try:
                    poll_count += 1
                    if poll_count % 20 == 0:  # Log cada 10 segundos (20 * 0.5s)
                        logger.debug(f"Polling activo (ciclo {poll_count})")
                    
                    if self.map_view and self.map_view.telemetry_server:
                        events = self.map_view.telemetry_server.get_map_events()
                        if events:
                            logger.info(f"Polling: {len(events)} eventos recibidos del servidor")
                        for event in events:
                            event_type = event.get('type')
                            logger.info(f"Procesando evento: {event_type}")
                            
                            if event_type == 'map_click':
                                # Clic en mapa para crear POI
                                lat = event.get('lat')
                                lon = event.get('lon')
                                logger.info(f"Evento map_click recibido: lat={lat}, lon={lon}")
                                if lat and lon:
                                    # Llamar directamente al método
                                    logger.info("Llamando a _on_map_click")
                                    try:
                                        self._on_map_click(lat, lon)
                                    except Exception as e:
                                        logger.error(f"Error en _on_map_click: {e}", exc_info=True)
                            
                            elif event_type == 'zone_created':
                                # Zona creada
                                zone = event.get('zone')
                                logger.info(f"Evento zone_created recibido: {zone.get('id', 'unknown') if zone else 'None'}")
                                if zone:
                                    # Llamar directamente al método
                                    try:
                                        self._on_zone_created(zone)
                                    except Exception as e:
                                        logger.error(f"Error en _on_zone_created: {e}", exc_info=True)
                    else:
                        if poll_count == 1:
                            logger.warning("map_view o telemetry_server no disponible para polling")
                    
                    time.sleep(0.5)  # Polling cada 0.5 segundos
                except Exception as e:
                    logger.error(f"Error en polling de eventos del mapa: {e}", exc_info=True)
                    time.sleep(1)
        
        polling_thread = threading.Thread(target=poll_events, daemon=True)
        polling_thread.start()
    
    def _create_side_panel(self) -> ft.Container:
        """Crea el panel lateral con telemetría, gestión de POIs y zonas."""
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Container(
                        content=self.telemetry_panel.get_panel(),
                        expand=True,
                    ),
                    ft.Divider(),
                    ft.Container(
                        content=self.poi_manager.get_panel(),
                        expand=True,
                    ),
                    ft.Divider(),
                    ft.Container(
                        content=self.zone_manager.get_panel(),
                        expand=True,
                    ),
                    ft.Divider(),
                    # Botón para vuelo coordinado
                    ft.Container(
                        content=ft.ElevatedButton(
                            "Iniciar Vuelo Coordinado",
                            icon=ft.Icons.FLIGHT_TAKEOFF,
                            on_click=self._execute_coordinated_flight,
                            color=GREEN,
                            tooltip="Activa patrón de vuelo coordinado para todos los drones disponibles en la zona activa"
                        ),
                        padding=10,
                    ),
                ],
                spacing=10,
                expand=True,
            ),
            width=320,
            bgcolor=get_surface_color(self.page) if self.page else SURFACE,
            padding=0,
            expand=True,
        )
    
    def _create_poi_dialog(self, lat: float, lon: float):
        """Crea un diálogo para la creación de POI."""
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"_create_poi_dialog llamado: lat={lat}, lon={lon}")
        
        if not self.page:
            logger.error("No hay página disponible para mostrar el diálogo")
            return
        
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
            value="POI creado desde mapa",
        )
        
        def on_save(e):
            import logging
            logger = logging.getLogger(__name__)
            logger.info("Botón 'Crear' presionado en diálogo de POI")
            poi_type = poi_type_dropdown.value
            description = description_field.value or ""
            logger.info(f"Guardando POI: type={poi_type}, desc={description}, lat={lat}, lon={lon}")
            try:
                logger.info("Llamando a _on_create_poi...")
                self._on_create_poi(lat, lon, poi_type, description)
                logger.info("_on_create_poi completado, cerrando diálogo...")
                self.page.close_dialog()
                self.page.update()
                logger.info("Diálogo cerrado y página actualizada")
            except Exception as err:
                logger.error(f"Error al crear POI: {err}", exc_info=True)
                # Mostrar error al usuario
                if self.page:
                    self.page.snack_bar = ft.SnackBar(
                        content=ft.Text(f"Error al crear POI: {err}"),
                        bgcolor=RED
                    )
                    self.page.snack_bar.open = True
                    self.page.update()
        
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
        
        try:
            self.page.dialog = dialog
            dialog.open = True
            self.page.update()
            logger.info("Diálogo de POI mostrado correctamente")
        except Exception as e:
            logger.error(f"Error al mostrar diálogo de POI: {e}", exc_info=True)
    
    def _on_create_poi(self, lat: float, lon: float, poi_type: str, description: str):
        """
        Maneja la creación de POI.
        
        Args:
            lat: Latitud
            lon: Longitud
            poi_type: Tipo de POI
            description: Descripción del POI
        """
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"_on_create_poi llamado: lat={lat}, lon={lon}, type={poi_type}, desc={description}")
        
        poi = self.storage.add_poi(lat, lon, poi_type, description, "user")
        logger.info(f"POI creado en storage: {poi.get('id', 'unknown')}")
        
        self.poi_manager.add_poi(poi)
        logger.info("POI agregado al POIManager")
        
        # Transmitir vía pub/sub (opcional, no crítico)
        if self.page:
            try:
                # Intentar usar la API correcta de Flet pub/sub
                # Nota: La API puede variar según la versión de Flet
                if hasattr(self.page.pubsub, 'send_all_on_topic'):
                    self.page.pubsub.send_all_on_topic(
                        topic=CHANNEL_POI,
                        message={
                            "action": "poi_created",
                            "poi": poi,
                        }
                    )
                else:
                    # Fallback: intentar sin topic o ignorar si falla
                    self.page.pubsub.send_all(
                        message={
                            "action": "poi_created",
                            "poi": poi,
                        }
                    )
            except Exception as e:
                # No crítico, solo log de depuración
                logger.debug(f"Error en pub/sub (puede ignorarse): {e}")
        
        self._update_map_pois()
        logger.info("Mapa actualizado con POIs")
        
        # Actualizar mapa (CRÍTICO: esto es lo que hace que aparezcan en el mapa)
        if self.map_view:
            self.map_view.add_poi(poi)
            logger.info("POI agregado al MapView")
        else:
            logger.error("No hay MapView disponible para agregar POI")
    
    def _on_delete_poi(self, poi_id: str):
        """
        Maneja la eliminación de POI.
        
        Args:
            poi_id: ID del POI a eliminar
        """
        if self.storage.remove_poi(poi_id):
            self.poi_manager.remove_poi(poi_id)
            
            # Transmitir vía pub/sub (opcional, no crítico)
            if self.page:
                try:
                    if hasattr(self.page.pubsub, 'send_all_on_topic'):
                        self.page.pubsub.send_all_on_topic(
                            topic=CHANNEL_POI,
                            message={
                                "action": "poi_deleted",
                                "poi_id": poi_id,
                            }
                        )
                    else:
                        self.page.pubsub.send_all(
                            message={
                                "action": "poi_deleted",
                                "poi_id": poi_id,
                            }
                        )
                except Exception as e:
                    logger.debug(f"Error en pub/sub (puede ignorarse): {e}")
            
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
        
        text_color = get_text_color(self.page) if self.page else None
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
                                color=text_color,
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
        
        # Asegurar que siempre tengamos colores válidos
        if self.page:
            text_color = get_text_color(self.page)
            text_secondary = get_text_secondary_color(self.page)
        else:
            # Fallback para cuando no hay página (modo claro por defecto)
            text_color = "#000000"  # Negro para modo claro
            text_secondary = GREY_600  # Gris oscuro para modo claro
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
                            ft.Text(drone_id, size=11, weight=ft.FontWeight.BOLD, color=text_color),
                            ft.Text(
                                f"Batería: {battery:.1f}%",
                                size=10,
                                color=battery_color,
                            ),
                            ft.Text(
                                f"Alt: {telemetry.get('altitude', 0):.1f}m",
                                size=10,
                                color=text_color,
                            ),
                            ft.Text(
                                f"Pos: {telemetry.get('latitude', 0):.4f}, {telemetry.get('longitude', 0):.4f}",
                                size=9,
                                color=text_secondary,
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
