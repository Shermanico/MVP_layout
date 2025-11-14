"""
Gestor de drones para manejar múltiples drones simultáneamente.
Coordina la recolección y distribución de telemetría.
"""
import asyncio
from typing import Dict, List, Optional, Callable
from common.config import Config
from common.utils import generate_drone_id
from drones.fake_generator import FakeTelemetryGenerator
from drones.simulator import MAVSDKSimulator, MAVSDK_AVAILABLE


class DroneManager:
    """
    Gestiona múltiples instancias de drones y sus flujos de telemetría.
    """
    
    def __init__(self, config: Config, telemetry_callback: Optional[Callable] = None):
        """
        Inicializa el gestor de drones.
        
        Args:
            config: Configuración de la aplicación
            telemetry_callback: Función callback para actualizaciones de telemetría
        """
        self.config = config
        self.telemetry_callback = telemetry_callback
        self.drones: Dict[str, FakeTelemetryGenerator | MAVSDKSimulator] = {}
        self.running = False
        self.tasks: List[asyncio.Task] = []
    
    async def start(self):
        """Inicia todas las simulaciones de drones."""
        if self.running:
            return
        
        self.running = True
        
        if self.config.use_fake_telemetry:
            await self._start_fake_drones()
        else:
            await self._start_mavsdk_drones()
    
    async def stop(self):
        """Detiene todas las simulaciones de drones."""
        self.running = False
        
        # Detener todos los drones
        for drone in self.drones.values():
            if isinstance(drone, FakeTelemetryGenerator):
                await drone.stop()
            elif isinstance(drone, MAVSDKSimulator):
                await drone.stop()
        
        # Cancelar todas las tareas
        for task in self.tasks:
            task.cancel()
        
        await asyncio.gather(*self.tasks, return_exceptions=True)
        self.tasks.clear()
        self.drones.clear()
    
    async def _start_fake_drones(self):
        """Inicia generadores de telemetría falsa."""
        import logging
        logger = logging.getLogger(__name__)
        
        count = self.config.fake_drone_count
        logger.info(f"Creando {count} drones falsos...")
        
        # Distribuir drones alrededor de la ubicación inicial
        base_lat = self.config.default_latitude
        base_lon = self.config.default_longitude
        
        for i in range(count):
            drone_id = generate_drone_id(i)
            offset_lat = (i % 3 - 1) * 0.01  # Distribuir en una cuadrícula
            offset_lon = (i // 3 - 1) * 0.01
            
            logger.info(f"Creando dron {drone_id} en posición ({base_lat + offset_lat:.6f}, {base_lon + offset_lon:.6f})")
            
            drone = FakeTelemetryGenerator(
                drone_id=drone_id,
                start_lat=base_lat + offset_lat,
                start_lon=base_lon + offset_lon,
                callback=self._on_telemetry_update
            )
            
            self.drones[drone_id] = drone
            
            # Crear tarea y agregar callback para verificar que se ejecute
            # IMPORTANTE: Capturar drone_id y drone en el closure para evitar problemas
            def create_drone_task(d_id, d_instance):
                async def drone_task_wrapper():
                    try:
                        logger.info(f"Iniciando tarea para {d_id}")
                        await d_instance.start(self.config.telemetry_update_interval)
                    except Exception as e:
                        logger.error(f"Error en tarea de {d_id}: {e}", exc_info=True)
                return drone_task_wrapper
            
            task_wrapper = create_drone_task(drone_id, drone)
            task = asyncio.create_task(task_wrapper())
            self.tasks.append(task)
            logger.info(f"Tarea creada para {drone_id}, total tareas: {len(self.tasks)}")
    
    async def _start_mavsdk_drones(self):
        """Inicia drones basados en MAVSDK."""
        if not MAVSDK_AVAILABLE:
            raise ImportError(
                "MAVSDK-Python no está disponible. "
                "Instálalo con: pip install mavsdk"
            )
        
        # Para MVP, asumiremos un dron por cadena de conexión
        # En producción, configurarías múltiples cadenas de conexión
        connection_strings = ["udp://:14540", "udp://:14541", "udp://:14542"]
        count = min(self.config.fake_drone_count, len(connection_strings))
        
        for i in range(count):
            drone_id = generate_drone_id(i)
            drone = MAVSDKSimulator(
                drone_id=drone_id,
                connection_string=connection_strings[i],
                callback=self._on_telemetry_update
            )
            
            self.drones[drone_id] = drone
            task = asyncio.create_task(
                drone.start(self.config.telemetry_update_interval)
            )
            self.tasks.append(task)
    
    def _on_telemetry_update(self, telemetry: Dict):
        """Maneja la actualización de telemetría de un dron."""
        import logging
        logger = logging.getLogger(__name__)
        
        if self.telemetry_callback:
            try:
                self.telemetry_callback(telemetry)
            except Exception as e:
                logger.error(f"Error en callback de telemetría: {e}", exc_info=True)
        else:
            logger.warning("No hay callback configurado para telemetría")
    
    def get_drone_list(self) -> List[str]:
        """Obtiene la lista de IDs de drones activos."""
        return list(self.drones.keys())
    
    def get_drone_count(self) -> int:
        """Obtiene el número de drones activos."""
        return len(self.drones)
    
    async def send_command_to_drone(self, drone_id: str, command: str, **kwargs):
        """
        Envía un comando a un dron específico.
        
        Args:
            drone_id: ID del dron objetivo
            command: Nombre del comando (ej., "set_target")
            **kwargs: Parámetros del comando
        """
        if drone_id not in self.drones:
            return
        
        drone = self.drones[drone_id]
        
        if isinstance(drone, FakeTelemetryGenerator):
            if command == "set_target":
                drone.set_target(
                    kwargs.get("latitude"),
                    kwargs.get("longitude"),
                    kwargs.get("altitude", 20.0)
                )
        # Agregar más manejadores de comandos según sea necesario
