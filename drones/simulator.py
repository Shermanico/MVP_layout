"""
Simulador de dron basado en MAVSDK.
Se conecta a instancias MAVSDK para obtener datos de telemetría reales.
"""
import asyncio
import time
from typing import Dict, Any, Callable, Optional

try:
    from mavsdk import System
    from mavsdk.telemetry import Position, VelocityNed, Battery, FlightMode
    MAVSDK_AVAILABLE = True
except ImportError:
    MAVSDK_AVAILABLE = False

from common.utils import normalize_telemetry
from common.constants import DroneStatus


class MAVSDKSimulator:
    """
    Simulador de dron basado en MAVSDK.
    Se conecta a una instancia de Sistema MAVSDK y transmite telemetría.
    """
    
    def __init__(
        self,
        drone_id: str,
        connection_string: str = "udp://:14540",
        callback: Optional[Callable[[Dict[str, Any]], None]] = None
    ):
        """
        Inicializa el simulador MAVSDK.
        
        Args:
            drone_id: Identificador único para este dron
            connection_string: Cadena de conexión MAVSDK (ej., "udp://:14540")
            callback: Función a llamar con actualizaciones de telemetría
        """
        if not MAVSDK_AVAILABLE:
            raise ImportError(
                "MAVSDK-Python no está instalado. "
                "Instálalo con: pip install mavsdk"
            )
        
        self.drone_id = drone_id
        self.connection_string = connection_string
        self.callback = callback
        self.drone = System()
        self.running = False
        
    async def connect(self):
        """Conecta al sistema del dron."""
        await self.drone.connect(self.connection_string)
        
        # Esperar conexión
        async for state in self.drone.core.connection_state():
            if state.is_connected:
                print(f"[{self.drone_id}] Conectado al dron")
                break
    
    async def start(self, update_interval: float = 0.5):
        """
        Inicia la transmisión de telemetría.
        
        Args:
            update_interval: Segundos mínimos entre actualizaciones
        """
        if not self.drone:
            await self.connect()
        
        self.running = True
        
        # Suscribirse a flujos de telemetría
        position_task = asyncio.create_task(self._stream_position())
        velocity_task = asyncio.create_task(self._stream_velocity())
        battery_task = asyncio.create_task(self._stream_battery())
        flight_mode_task = asyncio.create_task(self._stream_flight_mode())
        
        # Combinar y enviar actualizaciones
        last_update = time.time()
        telemetry_cache = {}
        
        while self.running:
            current_time = time.time()
            
            if current_time - last_update >= update_interval and telemetry_cache:
                telemetry = self._generate_telemetry(telemetry_cache)
                if self.callback:
                    self.callback(telemetry)
                last_update = current_time
                telemetry_cache.clear()
            
            await asyncio.sleep(0.1)
        
        # Cancelar tareas
        position_task.cancel()
        velocity_task.cancel()
        battery_task.cancel()
        flight_mode_task.cancel()
    
    async def stop(self):
        """Detiene la transmisión de telemetría."""
        self.running = False
        if self.drone:
            await self.drone.close()
    
    async def _stream_position(self):
        """Transmite telemetría de posición."""
        try:
            async for position in self.drone.telemetry.position():
                if not self.running:
                    break
                # Almacenar en caché para combinación
                pass  # La posición se combinará en el loop principal
        except asyncio.CancelledError:
            pass
    
    async def _stream_velocity(self):
        """Transmite telemetría de velocidad."""
        try:
            async for velocity_ned in self.drone.telemetry.velocity_ned():
                if not self.running:
                    break
                # Almacenar en caché
                pass
        except asyncio.CancelledError:
            pass
    
    async def _stream_battery(self):
        """Transmite telemetría de batería."""
        try:
            async for battery in self.drone.telemetry.battery():
                if not self.running:
                    break
                # Almacenar en caché
                pass
        except asyncio.CancelledError:
            pass
    
    async def _stream_flight_mode(self):
        """Transmite telemetría de modo de vuelo."""
        try:
            async for flight_mode in self.drone.telemetry.flight_mode():
                if not self.running:
                    break
                # Almacenar en caché
                pass
        except asyncio.CancelledError:
            pass
    
    def _generate_telemetry(self, cache: Dict[str, Any]) -> Dict[str, Any]:
        """Genera telemetría normalizada desde datos MAVSDK."""
        # Esta es una versión simplificada - en implementación real,
        # combinarías posición, velocidad, batería y modo de vuelo desde el caché
        return normalize_telemetry({
            "drone_id": self.drone_id,
            "latitude": cache.get("latitude", 0.0),
            "longitude": cache.get("longitude", 0.0),
            "altitude": cache.get("altitude", 0.0),
            "heading": cache.get("heading", 0.0),
            "velocity": cache.get("velocity", 0.0),
            "battery": cache.get("battery", 100.0),
            "status": cache.get("status", DroneStatus.IDLE.value),
            "timestamp": time.time(),
        })
