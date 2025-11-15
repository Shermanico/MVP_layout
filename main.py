"""
Punto de entrada principal para el sistema de coordinación multi-dron.
Wire up de la arquitectura hexagonal.
"""
import asyncio
import flet as ft
import logging
from infrastructure.config import Config
from infrastructure.config.constants import CHANNEL_TELEMETRY

# Adaptadores de salida
from adapters.output.persistence import JsonPOIRepository
from adapters.output.simulation import FakeDroneAdapter
from adapters.output.http import TelemetryServer

# Casos de uso
from application.use_cases.drone.start_drones import StartDronesUseCase
from application.use_cases.drone.stop_drones import StopDronesUseCase
from application.use_cases.drone.get_drone_list import GetDroneListUseCase
from application.use_cases.poi.create_poi import CreatePOIUseCase
from application.use_cases.poi.delete_poi import DeletePOIUseCase
from application.use_cases.poi.get_all_pois import GetAllPOIsUseCase
from application.use_cases.poi.get_pois_by_type import GetPOIsByTypeUseCase
from application.use_cases.poi.clear_all_pois import ClearAllPOIsUseCase

# Servicios (implementan puertos de entrada)
from application.services.drone_service import DroneService
from application.services.poi_service import POIService

# Adaptador de entrada (UI)
from adapters.input.flet.main_app import MainApp

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main(page: ft.Page):
    """
    Punto de entrada principal de la aplicación.
    Wire up de todas las dependencias según arquitectura hexagonal.
    
    Args:
        page: Instancia de página Flet
    """
    try:
        logger.info("Iniciando aplicación con arquitectura hexagonal...")
        
        # 1. Cargar configuración
        config = Config.load_from_file()
        logger.info(f"Configuración cargada: use_fake_telemetry={config.use_fake_telemetry}, fake_drone_count={config.fake_drone_count}")
        
        # 2. Crear adaptadores de salida (Secondary Adapters)
        logger.info("Creando adaptadores de salida...")
        poi_repository = JsonPOIRepository(config.poi_storage_file)
        drone_repository = FakeDroneAdapter(
            initial_lat=config.default_latitude,
            initial_lon=config.default_longitude
        )
        
        # 3. Crear casos de uso (inyectar adaptadores de salida)
        logger.info("Creando casos de uso...")
        start_drones_use_case = StartDronesUseCase(drone_repository)
        stop_drones_use_case = StopDronesUseCase(drone_repository)
        get_drone_list_use_case = GetDroneListUseCase(drone_repository)
        
        create_poi_use_case = CreatePOIUseCase(poi_repository)
        delete_poi_use_case = DeletePOIUseCase(poi_repository)
        get_all_pois_use_case = GetAllPOIsUseCase(poi_repository)
        get_pois_by_type_use_case = GetPOIsByTypeUseCase(poi_repository)
        clear_all_pois_use_case = ClearAllPOIsUseCase(poi_repository)
        
        # 4. Crear servicios (inyectar casos de uso)
        logger.info("Creando servicios...")
        drone_service = DroneService(
            start_drones_use_case=start_drones_use_case,
            stop_drones_use_case=stop_drones_use_case,
            get_drone_list_use_case=get_drone_list_use_case
        )
        
        poi_service = POIService(
            create_poi_use_case=create_poi_use_case,
            delete_poi_use_case=delete_poi_use_case,
            get_all_pois_use_case=get_all_pois_use_case,
            get_pois_by_type_use_case=get_pois_by_type_use_case,
            clear_all_pois_use_case=clear_all_pois_use_case
        )
        
        # 5. Crear adaptador de entrada (inyectar servicios)
        logger.info("Creando adaptador de entrada (UI)...")
        app = MainApp(
            config=config,
            drone_service=drone_service,
            poi_service=poi_service,
            page=page
        )
        app.setup_page(page)
        logger.info("UI inicializada")
        
        # 6. Configurar callback para telemetría
        def on_telemetry_update(telemetry):
            """Maneja actualizaciones de telemetría de los drones."""
            try:
                # Log ocasionalmente para no saturar
                if hasattr(on_telemetry_update, '_log_count'):
                    on_telemetry_update._log_count += 1
                else:
                    on_telemetry_update._log_count = 1
                
                if on_telemetry_update._log_count % 20 == 0:
                    logger.info(f"Telemetría recibida: {telemetry.get('drone_id', 'UNKNOWN')} (total: {on_telemetry_update._log_count})")
                
                # Actualizar UI
                app.update_telemetry(telemetry)
                
                # Transmitir vía pub/sub (opcional, para multi-cliente)
                try:
                    page.pubsub.send_all(
                        message={
                            "action": "telemetry_update",
                            "telemetry": telemetry,
                        },
                        topic=CHANNEL_TELEMETRY,
                    )
                except Exception as e:
                    logger.debug(f"Error en pub/sub (puede ignorarse): {e}")
                
            except Exception as e:
                logger.error(f"Error al actualizar telemetría: {e}", exc_info=True)
        
        # Configurar callback en el repositorio de drones
        drone_repository.telemetry_callback = on_telemetry_update
        
        # 7. Iniciar simulación de drones
        async def run_drones():
            try:
                logger.info("Iniciando simulación de drones...")
                await drone_service.start_drones(
                    count=config.fake_drone_count,
                    update_interval=config.telemetry_update_interval,
                    callback=on_telemetry_update
                )
                logger.info(f"Drones iniciados: {drone_service.get_drone_count()}")
                
                # Mantener ejecutándose hasta que se cierre la página
                while True:
                    await asyncio.sleep(1)
            except asyncio.CancelledError:
                logger.info("Tarea de drones cancelada")
            except Exception as e:
                logger.error(f"Error en simulación de drones: {e}", exc_info=True)
            finally:
                logger.info("Deteniendo drones...")
                await drone_service.stop_drones()
        
        # Iniciar tarea del gestor de drones
        loop = asyncio.get_event_loop()
        drone_task = loop.create_task(run_drones())
        logger.info(f"Tarea de drones creada: {drone_task}")
        
        # Limpiar al cerrar
        def on_window_event(e):
            if e.data == "close":
                app.cleanup()
        
        page.window.on_event = on_window_event
        
    except Exception as e:
        logger.error(f"Error al inicializar aplicación: {e}", exc_info=True)
        # Mostrar error en la UI
        page.snack_bar = ft.SnackBar(
            content=ft.Text(f"Error al iniciar: {str(e)}"),
            bgcolor="#F44336"
        )
        page.snack_bar.open = True
        page.update()


def run_app():
    """Ejecuta la aplicación Flet."""
    ft.app(target=main)


if __name__ == "__main__":
    run_app()
