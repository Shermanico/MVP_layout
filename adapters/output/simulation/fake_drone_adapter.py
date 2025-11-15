"""
Adaptador de salida: Simulación de drones con telemetría falsa.
Implementa IDroneRepository del dominio.
Simula comportamiento del DJI Matrice 300 RTK.
"""
import asyncio
import math
import random
import time
from typing import List, Callable, Optional, Dict, Any
from domain.ports.output.drone_repository_port import IDroneRepository
from domain.entities.drone import Drone
from domain.entities.telemetry import Telemetry
from infrastructure.config.utils import generate_drone_id, normalize_telemetry
from infrastructure.config.constants import DroneStatus


class FakeTelemetryGenerator:
    """
    Generador de telemetría falsa para un dron individual.
    Simula características del DJI Matrice 300 RTK.
    """
    
    # Especificaciones Matrice 300 RTK
    MAX_SPEED = 23.0  # m/s (82.8 km/h)
    MAX_ALTITUDE = 5000.0  # metros AGL
    MAX_FLIGHT_TIME = 55.0 * 60.0  # segundos (55 minutos con batería TB60)
    BATTERY_DRAIN_RATE = 0.01  # % por segundo en vuelo
    
    def __init__(
        self,
        drone_id: str,
        initial_lat: float,
        initial_lon: float,
        callback: Optional[Callable[[Dict[str, Any]], None]] = None
    ):
        """
        Inicializa el generador de telemetría.
        
        Args:
            drone_id: ID único del dron
            initial_lat: Latitud inicial
            initial_lon: Longitud inicial
            callback: Función a llamar con actualizaciones de telemetría
        """
        self.drone_id = drone_id
        self.latitude = initial_lat
        self.longitude = initial_lon
        self.altitude = 0.0
        self.heading = random.uniform(0, 360)
        self.velocity = 0.0
        self.battery = 100.0
        self.status = DroneStatus.IDLE.value
        self.callback = callback
        self.running = False
        self.task: Optional[asyncio.Task] = None
        
        # Parámetros de simulación
        self.target_lat = initial_lat
        self.target_lon = initial_lon
        self.target_altitude = random.uniform(30, 100)
        self.vertical_speed = 0.0
        self.rtk_fix = True  # Matrice 300 RTK tiene RTK
        self.max_speed = self.MAX_SPEED
        self.max_altitude = self.MAX_ALTITUDE
        self.flight_time_remaining = self.MAX_FLIGHT_TIME
        
        # Generar waypoints aleatorios
        self._generate_waypoints()
    
    def _generate_waypoints(self) -> None:
        """Genera waypoints aleatorios para el dron."""
        # Crear 5-10 waypoints en un área alrededor de la posición inicial
        num_waypoints = random.randint(5, 10)
        self.waypoints = []
        for _ in range(num_waypoints):
            lat_offset = random.uniform(-0.01, 0.01)  # ~1km
            lon_offset = random.uniform(-0.01, 0.01)
            self.waypoints.append((
                self.latitude + lat_offset,
                self.longitude + lon_offset,
                random.uniform(30, 150)  # altitud
            ))
        self.current_waypoint = 0
    
    async def start(self, update_interval: float = 0.5) -> None:
        """Inicia la simulación del dron."""
        if self.running:
            return
        
        self.running = True
        self.status = DroneStatus.ARMED.value
        
        # Tarea async para actualizar posición
        async def update_loop():
            await asyncio.sleep(2)  # Esperar antes de despegar
            self.status = DroneStatus.TAKEOFF.value
            
            # Simular despegue
            while self.altitude < self.target_altitude and self.running:
                self.altitude += 2.0  # Subir 2m por segundo
                self.vertical_speed = 2.0
                await asyncio.sleep(update_interval)
            
            self.status = DroneStatus.FLYING.value
            self.vertical_speed = 0.0
            
            # Bucle principal de vuelo
            while self.running:
                await self._update_position(update_interval)
                await self._generate_telemetry()
                await asyncio.sleep(update_interval)
        
        self.task = asyncio.create_task(update_loop())
    
    async def stop(self) -> None:
        """Detiene la simulación del dron."""
        self.running = False
        self.status = DroneStatus.LANDING.value
        
        # Simular aterrizaje
        while self.altitude > 0.1 and self.task and not self.task.done():
            self.altitude = max(0, self.altitude - 2.0)
            self.vertical_speed = -2.0
            await asyncio.sleep(0.5)
        
        self.altitude = 0.0
        self.vertical_speed = 0.0
        self.status = DroneStatus.IDLE.value
        
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
    
    async def _update_position(self, dt: float) -> None:
        """Actualiza la posición del dron hacia el waypoint actual."""
        if not self.waypoints:
            return
        
        target_lat, target_lon, target_alt = self.waypoints[self.current_waypoint]
        
        # Calcular distancia al waypoint
        lat_diff = target_lat - self.latitude
        lon_diff = target_lon - self.longitude
        distance = math.sqrt(lat_diff**2 + lon_diff**2) * 111000  # metros (aproximado)
        
        # Si está cerca del waypoint, ir al siguiente
        if distance < 50:  # 50 metros
            self.current_waypoint = (self.current_waypoint + 1) % len(self.waypoints)
            target_lat, target_lon, target_alt = self.waypoints[self.current_waypoint]
            lat_diff = target_lat - self.latitude
            lon_diff = target_lon - self.longitude
            distance = math.sqrt(lat_diff**2 + lon_diff**2) * 111000
        
        # Calcular heading hacia el waypoint
        self.heading = math.degrees(math.atan2(lon_diff, lat_diff))
        if self.heading < 0:
            self.heading += 360
        
        # Mover hacia el waypoint
        speed = min(self.MAX_SPEED, distance / 2.0)  # Acelerar/desacelerar suavemente
        self.velocity = speed
        
        # Actualizar posición
        move_distance = speed * dt / 111000  # Convertir m/s a grados
        self.latitude += move_distance * math.cos(math.radians(self.heading))
        self.longitude += move_distance * math.sin(math.radians(self.heading))
        
        # Actualizar altitud hacia el objetivo
        alt_diff = target_alt - self.altitude
        if abs(alt_diff) > 1.0:
            self.vertical_speed = math.copysign(2.0, alt_diff)
            self.altitude += self.vertical_speed * dt
        else:
            self.vertical_speed = 0.0
        
        # Simular drenaje de batería
        if self.status == DroneStatus.FLYING.value:
            self.battery = max(0, self.battery - self.BATTERY_DRAIN_RATE * dt)
            # Calcular tiempo de vuelo restante
            if self.battery > 0:
                self.flight_time_remaining = (self.battery / 100.0) * self.MAX_FLIGHT_TIME
            else:
                self.flight_time_remaining = 0.0
    
    async def _generate_telemetry(self) -> None:
        """Genera y envía telemetría."""
        raw_telemetry = {
            "drone_id": self.drone_id,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "altitude": self.altitude,
            "heading": self.heading,
            "velocity": self.velocity,
            "battery": self.battery,
            "status": self.status,
            "timestamp": time.time(),
            "vertical_speed": self.vertical_speed,
            "rtk_fix": self.rtk_fix,
            "max_speed": self.max_speed,
            "max_altitude": self.max_altitude,
            "flight_time_remaining": self.flight_time_remaining,
        }
        
        normalized = normalize_telemetry(raw_telemetry)
        
        if self.callback:
            self.callback(normalized)


class FakeDroneAdapter(IDroneRepository):
    """
    Adaptador que implementa IDroneRepository usando simulación falsa.
    Gestiona múltiples drones simulados.
    """
    
    def __init__(
        self,
        initial_lat: float = 20.9674,
        initial_lon: float = -89.5926,
        telemetry_callback: Optional[Callable[[Dict[str, Any]], None]] = None
    ):
        """
        Inicializa el adaptador.
        
        Args:
            initial_lat: Latitud inicial para distribución de drones
            initial_lon: Longitud inicial para distribución de drones
            telemetry_callback: Callback para actualizaciones de telemetría
        """
        self.initial_lat = initial_lat
        self.initial_lon = initial_lon
        self.telemetry_callback = telemetry_callback
        self.drones: List[Drone] = []
        self.generators: List[FakeTelemetryGenerator] = []
        self.tasks: List[asyncio.Task] = []
    
    async def start_drones(
        self,
        count: int,
        update_interval: float = 0.5,
        callback: Optional[Callable[[Dict[str, Any]], None]] = None
    ) -> List[Drone]:
        """Inicia múltiples drones."""
        # Usar callback proporcionado o el del constructor
        effective_callback = callback or self.telemetry_callback
        
        # Distribuir drones en una cuadrícula
        grid_size = int(math.ceil(math.sqrt(count)))
        spacing = 0.001  # ~100 metros
        
        for i in range(count):
            drone_id = generate_drone_id(i)
            
            # Calcular posición en cuadrícula
            row = i // grid_size
            col = i % grid_size
            lat = self.initial_lat + (row - grid_size/2) * spacing
            lon = self.initial_lon + (col - grid_size/2) * spacing
            
            # Crear generador
            generator = FakeTelemetryGenerator(
                drone_id=drone_id,
                initial_lat=lat,
                initial_lon=lon,
                callback=effective_callback
            )
            
            # Crear entidad Drone
            drone = Drone(drone_id=drone_id)
            
            self.generators.append(generator)
            self.drones.append(drone)
            
            # Iniciar generador
            await generator.start(update_interval)
        
        return self.drones
    
    async def stop_drones(self) -> None:
        """Detiene todos los drones."""
        for generator in self.generators:
            await generator.stop()
        
        self.generators.clear()
        self.drones.clear()
        self.tasks.clear()
    
    def get_drone_count(self) -> int:
        """Obtiene el número de drones activos."""
        return len(self.drones)
    
    def get_drone_list(self) -> List[str]:
        """Obtiene la lista de IDs de drones activos."""
        return [drone.drone_id for drone in self.drones]
    
    async def send_command(self, drone_id: str, command: str, **kwargs) -> None:
        """Envía un comando a un dron específico."""
        # Por ahora, no implementado en simulación falsa
        # En el futuro, podría cambiar waypoints, velocidad, etc.
        pass

