"""
Punto de entrada principal para el sistema de coordinación multi-dron.
"""
import asyncio
import flet as ft
import logging
from common.config import Config
from backend.storage import POIStorage
from drones.drone_manager import DroneManager
from ui.main import MainApp
from common.constants import CHANNEL_TELEMETRY
from common.colors import RED

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main(page: ft.Page):
    """
    Punto de entrada principal de la aplicación.
    
    Args:
        page: Instancia de página Flet
    """
    try:
        logger.info("Iniciando aplicación...")
        
        # Cargar configuración
        config = Config.load_from_file()
        logger.info(f"Configuración cargada: use_fake_telemetry={config.use_fake_telemetry}, fake_drone_count={config.fake_drone_count}")
        
        # Inicializar almacenamiento
        storage = POIStorage(config.poi_storage_file)
        logger.info("Almacenamiento de POIs inicializado")
        
        # Inicializar UI
        app = MainApp(config, storage)
        app.setup_page(page)
        logger.info("UI inicializada")
        
        # Inicializar gestor de drones
        def on_telemetry_update(telemetry):
            """Maneja actualizaciones de telemetría de los drones."""
            try:
                # Log solo ocasionalmente para no saturar
                if hasattr(on_telemetry_update, '_log_count'):
                    on_telemetry_update._log_count += 1
                else:
                    on_telemetry_update._log_count = 1
                
                if on_telemetry_update._log_count % 20 == 0:  # Log cada 20 actualizaciones
                    logger.info(f"Telemetría recibida: {telemetry.get('drone_id', 'UNKNOWN')} (total: {on_telemetry_update._log_count})")
                
                # Actualizar UI directamente (Flet maneja el threading)
                app.update_telemetry(telemetry)
                
                # Transmitir vía pub/sub (si es necesario para multi-cliente)
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
        
        drone_manager = DroneManager(config, on_telemetry_update)
        logger.info("Gestor de drones inicializado")
        
        # Iniciar simulación de drones en segundo plano
        async def run_drones():
            try:
                logger.info("Iniciando simulación de drones...")
                await drone_manager.start()
                logger.info(f"Drones iniciados: {drone_manager.get_drone_count()}")
                logger.info(f"Tareas creadas: {len(drone_manager.tasks)}")
                
                # Verificar que las tareas se estén ejecutando
                await asyncio.sleep(0.1)  # Dar tiempo para que las tareas comiencen
                logger.info("Verificando estado de tareas...")
                for i, task in enumerate(drone_manager.tasks):
                    logger.info(f"Tarea {i}: done={task.done()}, cancelled={task.cancelled()}")
                
                # Mantener ejecutándose hasta que se cierre la página
                while True:
                    await asyncio.sleep(1)
            except asyncio.CancelledError:
                logger.info("Tarea de drones cancelada")
            except Exception as e:
                logger.error(f"Error en simulación de drones: {e}", exc_info=True)
            finally:
                logger.info("Deteniendo drones...")
                await drone_manager.stop()
        
        # Iniciar tarea del gestor de drones
        # Usar el loop de eventos actual (que debería ser el de Flet)
        loop = asyncio.get_event_loop()
        logger.info(f"Loop de eventos: {loop}")
        drone_task = loop.create_task(run_drones())
        logger.info(f"Tarea de drones creada: {drone_task}")
        
        # Nota: Flet maneja funciones async automáticamente
        # La tarea de drones se ejecutará en segundo plano
        # Cuando se cierre la página, Flet limpiará
        
    except Exception as e:
        logger.error(f"Error al inicializar aplicación: {e}", exc_info=True)
        # Mostrar error en la UI
        page.snack_bar = ft.SnackBar(
            content=ft.Text(f"Error al iniciar: {str(e)}"),
            bgcolor=RED
        )
        page.snack_bar.open = True
        page.update()


def run_app():
    """Ejecuta la aplicación Flet."""
    ft.app(target=main)


if __name__ == "__main__":
    run_app()

  