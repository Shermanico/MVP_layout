"""
Generador de telemetría falsa para pruebas y desarrollo.
Simula características del dron DJI Matrice 300 RTK.
Genera telemetría de dron realista sin requerir MAVSDK.
"""
import asyncio
import time
import random
import math
from typing import Dict, Any, Callable, Optional
from common.utils import generate_drone_id, normalize_telemetry
from common.constants import DroneStatus


class FakeTelemetryGenerator:
    """
    Genera datos de telemetría falsa simulando DJI Matrice 300 RTK.
    Especificaciones Matrice 300 RTK:
    - Velocidad máxima: 23 m/s (82.8 km/h)
    - Altitud máxima: 5000m AGL
    - Tiempo de vuelo: ~55 minutos (batería TB60)
    - Posicionamiento RTK: precisión a nivel de centímetro
    - Estabilidad profesional y características de vuelo
    """
    
    # Especificaciones Matrice 300 RTK
    MAX_SPEED = 23.0  # m/s (82.8 km/h)
    MAX_ALTITUDE = 5000.0  # metros AGL
    MAX_FLIGHT_TIME = 55.0 * 60.0  # 55 minutos en segundos
    BATTERY_DRAIN_RATE_FLYING = 100.0 / (55.0 * 60.0)  # % por segundo cuando vuela
    BATTERY_DRAIN_RATE_HOVER = 100.0 / (60.0 * 60.0)  # % por segundo cuando está en vuelo estacionario (ligeramente mejor)
    RTK_ACCURACY = 0.01  # ~1cm de precisión (en grados, aproximadamente)
    
    def __init__(
        self,
        drone_id: str,
        start_lat: float = 37.7749,
        start_lon: float = -122.4194,
        callback: Optional[Callable[[Dict[str, Any]], None]] = None
    ):
        """
        Inicializa el generador de telemetría falsa para Matrice 300 RTK.
        
        Args:
            drone_id: Identificador único para este dron
            start_lat: Latitud inicial
            start_lon: Longitud inicial
            callback: Función a llamar con actualizaciones de telemetría
        """
        self.drone_id = drone_id
        self.latitude = start_lat
        self.longitude = start_lon
        self.altitude = 0.0
        self.heading = random.uniform(0, 360)
        self.velocity = 0.0
        self.battery = 100.0
        self.status = DroneStatus.IDLE.value
        self.callback = callback
        self.running = False
        
        # Parámetros de movimiento
        self.target_lat = start_lat
        self.target_lon = start_lon
        self.speed = 0.0  # m/s
        self.altitude_target = 0.0
        
        # Específico de Matrice 300 RTK
        self.flight_start_time = None
        self.rtk_fix = True  # Posicionamiento RTK activo
        self.vertical_speed = 0.0  # m/s (tasa de ascenso/descenso)
        self.max_vertical_speed = 6.0  # m/s (velocidad máxima de ascenso Matrice 300 RTK)
        
        # Características de vuelo profesional
        self.acceleration_rate = 2.0  # m/s² (aceleración suave)
        self.deceleration_rate = 2.0  # m/s² (desaceleración suave)
        self.altitude_change_rate = 2.0  # m/s (cambios de altitud suaves)
        
    async def start(self, update_interval: float = 0.5):
        """
        Inicia la generación de actualizaciones de telemetría.
        
        Args:
            update_interval: Segundos entre actualizaciones
        """
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Iniciando generador de telemetría para {self.drone_id}")
        
        self.running = True
        
        # Enviar primera telemetría inmediatamente
        try:
            self._update_position()
            telemetry = self._generate_telemetry()
            if self.callback:
                logger.info(f"Enviando primera telemetría para {self.drone_id}")
                self.callback(telemetry)
        except Exception as e:
            logger.error(f"Error en primera telemetría para {self.drone_id}: {e}", exc_info=True)
        
        iteration = 0
        while self.running:
            try:
                iteration += 1
                if iteration % 10 == 0:  # Log cada 10 iteraciones
                    logger.debug(f"{self.drone_id} - Iteración {iteration}, running={self.running}")
                
                self._update_position()
                telemetry = self._generate_telemetry()
                
                if self.callback:
                    try:
                        self.callback(telemetry)
                    except Exception as e:
                        logger.error(f"Error en callback de telemetría para {self.drone_id}: {e}", exc_info=True)
                else:
                    logger.warning(f"Callback no configurado para {self.drone_id}")
                
                await asyncio.sleep(update_interval)
            except asyncio.CancelledError:
                logger.info(f"Tarea cancelada para {self.drone_id}")
                break
            except Exception as e:
                logger.error(f"Error en loop de telemetría para {self.drone_id}: {e}", exc_info=True)
                await asyncio.sleep(update_interval)  # Continuar a pesar del error
    
    async def stop(self):
        """Detiene la generación de telemetría."""
        self.running = False
    
    def _update_position(self):
        """Actualiza la posición del dron basada en simulación de movimiento Matrice 300 RTK."""
        # Simular seguimiento profesional de waypoints (menos aleatorio, más tipo misión)
        if random.random() < 0.005:  # 0.5% de probabilidad de cambiar objetivo (más estable)
            # Generar waypoints realistas dentro del rango operacional
            waypoint_range = 0.05  # rango ~5.5km
            self.target_lat = self.latitude + random.uniform(-waypoint_range, waypoint_range)
            self.target_lon = self.longitude + random.uniform(-waypoint_range, waypoint_range)
            # Rango de altitud profesional: 20-120m típico, hasta 5000m máximo
            self.altitude_target = random.uniform(20, 120)
            self.status = DroneStatus.FLYING.value
            if self.flight_start_time is None:
                self.flight_start_time = time.time()
        
        # Calcular distancia al objetivo
        lat_diff = self.target_lat - self.latitude
        lon_diff = self.target_lon - self.longitude
        distance = math.sqrt(lat_diff**2 + lon_diff**2) * 111000  # Aprox metros
        
        # Comportamiento de vuelo profesional: aceleración/desaceleración suave
        if distance > 5:  # Moverse hacia el objetivo (umbral de 5m para precisión)
            # Actualizar rumbo (cambios de rumbo suaves)
            target_heading = math.degrees(math.atan2(lon_diff, lat_diff))
            if target_heading < 0:
                target_heading += 360
            
            # Transición de rumbo suave (máx 5 grados por actualización)
            heading_diff = target_heading - self.heading
            if abs(heading_diff) > 180:
                heading_diff = heading_diff - 360 if heading_diff > 0 else heading_diff + 360
            
            max_heading_change = 5.0  # grados por actualización
            if abs(heading_diff) > max_heading_change:
                self.heading += max_heading_change if heading_diff > 0 else -max_heading_change
            else:
                self.heading = target_heading
            
            if self.heading < 0:
                self.heading += 360
            elif self.heading >= 360:
                self.heading -= 360
            
            # Cambios de velocidad suaves (aceleración Matrice 300 RTK)
            target_speed = min(self.MAX_SPEED, distance / 5.0)  # Ajustar velocidad basada en distancia
            if self.speed < target_speed:
                self.speed = min(target_speed, self.speed + self.acceleration_rate * 0.5)
            else:
                self.speed = max(target_speed, self.speed - self.deceleration_rate * 0.5)
            
            self.velocity = self.speed
            
            # Actualizar posición con precisión a nivel RTK
            # RTK proporciona precisión a nivel de centímetro, por lo que movimientos muy precisos
            speed_deg_per_sec = self.speed / 111000  # Convertir m/s a grados/s
            update_interval = 0.5  # segundos
            self.latitude += math.cos(math.radians(self.heading)) * speed_deg_per_sec * update_interval
            self.longitude += math.sin(math.radians(self.heading)) * speed_deg_per_sec * update_interval
            
            # Agregar pequeña variación de precisión RTK (nivel de centímetro)
            self.latitude += random.uniform(-self.RTK_ACCURACY / 111000, self.RTK_ACCURACY / 111000)
            self.longitude += random.uniform(-self.RTK_ACCURACY / 111000, self.RTK_ACCURACY / 111000)
            
            # Cambios de altitud suaves (ascenso máximo Matrice 300 RTK: 6 m/s)
            alt_diff = self.altitude_target - self.altitude
            if abs(alt_diff) > 0.5:
                max_alt_change = self.altitude_change_rate * update_interval
                if abs(alt_diff) > max_alt_change:
                    self.altitude += max_alt_change if alt_diff > 0 else -max_alt_change
                else:
                    self.altitude = self.altitude_target
                
                self.vertical_speed = alt_diff / update_interval
            else:
                self.vertical_speed = 0.0
            
            # Asegurar que la altitud se mantenga dentro de los límites
            self.altitude = max(0, min(self.altitude, self.MAX_ALTITUDE))
        else:
            # Objetivo alcanzado - desaceleración profesional y vuelo estacionario
            if self.speed > 0.5:
                self.speed = max(0, self.speed - self.deceleration_rate * 0.5)
                self.velocity = self.speed
            else:
                self.velocity = 0.0
                self.speed = 0.0
                self.status = DroneStatus.IDLE.value
                self.vertical_speed = 0.0
        
        # Simulación de drenaje de batería Matrice 300 RTK (batería TB60)
        # Basado en tiempo de vuelo real: ~55 minutos con batería completa
        if self.status == DroneStatus.FLYING.value:
            # La batería se drena más rápido cuando se mueve vs vuelo estacionario
            if self.velocity > 5.0:  # Moviéndose a velocidad significativa
                drain_rate = self.BATTERY_DRAIN_RATE_FLYING * 0.5  # Por actualización (intervalo de 0.5s)
            else:  # Vuelo estacionario o movimiento lento
                drain_rate = self.BATTERY_DRAIN_RATE_HOVER * 0.5
            self.battery = max(0, self.battery - drain_rate)
        elif self.status == DroneStatus.IDLE.value:
            # La batería no se recarga, pero el drenaje es mínimo cuando está inactivo/aterrizado
            # Pequeña autodescarga
            self.battery = max(0, self.battery - 0.0001)
        
        # Advertencias de batería baja (comportamiento Matrice 300 RTK)
        if self.battery < 10.0 and self.status == DroneStatus.FLYING.value:
            # Forzar aterrizaje cuando la batería está críticamente baja
            if self.altitude > 0:
                self.altitude_target = 0
                self.status = DroneStatus.LANDING.value
        elif self.battery <= 0:
            self.status = DroneStatus.IDLE.value
            self.velocity = 0.0
            self.speed = 0.0
    
    def _generate_telemetry(self) -> Dict[str, Any]:
        """Genera diccionario de telemetría normalizado con datos Matrice 300 RTK."""
        telemetry = normalize_telemetry({
            "drone_id": self.drone_id,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "altitude": self.altitude,
            "heading": self.heading,
            "velocity": self.velocity,
            "battery": self.battery,
            "status": self.status,
            "timestamp": time.time(),
        })
        
        # Agregar campos específicos de Matrice 300 RTK
        telemetry["vertical_speed"] = self.vertical_speed
        telemetry["rtk_fix"] = self.rtk_fix
        telemetry["max_speed"] = self.MAX_SPEED
        telemetry["max_altitude"] = self.MAX_ALTITUDE
        
        # Calcular tiempo de vuelo restante estimado
        if self.battery > 0 and self.status in [DroneStatus.FLYING.value, DroneStatus.TAKEOFF.value]:
            if self.velocity > 5.0:
                flight_time_remaining = (self.battery / 100.0) * self.MAX_FLIGHT_TIME
            else:
                flight_time_remaining = (self.battery / 100.0) * (60.0 * 60.0)  # Tiempo de vuelo estacionario
            telemetry["flight_time_remaining"] = flight_time_remaining
        else:
            telemetry["flight_time_remaining"] = 0.0
        
        return telemetry
    
    def set_target(self, lat: float, lon: float, altitude: float = 20.0):
        """Establece un waypoint objetivo para el dron."""
        self.target_lat = lat
        self.target_lon = lon
        self.altitude_target = altitude
        self.status = DroneStatus.FLYING.value
