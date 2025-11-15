# Análisis de Compatibilidad: Matrice 300 RTK vs AUTEL EVO II

## Resumen Ejecutivo

**Respuesta corta:** Sí, este MVP **puede ser usado con AUTEL EVO II**, pero requiere modificaciones menores en el código de simulación. La arquitectura base es compatible.

## Comparación de Especificaciones

### DJI Matrice 300 RTK (Actual)
- **Velocidad máxima**: 23 m/s (82.8 km/h)
- **Altitud máxima**: 5000m AGL
- **Tiempo de vuelo**: ~55 minutos (batería TB60)
- **Posicionamiento**: RTK (precisión a nivel de centímetro)
- **Velocidad vertical máxima**: 6 m/s
- **Protocolo**: MAVLink (compatible con MAVSDK)

### AUTEL EVO II (Variantes)
Las especificaciones varían según el modelo:

#### AUTEL EVO II Pro/Enterprise
- **Velocidad máxima**: ~20 m/s (72 km/h)
- **Altitud máxima**: 8000m AGL
- **Tiempo de vuelo**: ~40 minutos
- **Posicionamiento**: GPS/GLONASS (algunos modelos tienen RTK opcional)
- **Velocidad vertical máxima**: ~5 m/s
- **Protocolo**: MAVLink (compatible con MAVSDK)

#### AUTEL EVO II Dual 640T
- **Velocidad máxima**: ~20 m/s
- **Altitud máxima**: 8000m AGL
- **Tiempo de vuelo**: ~38 minutos
- **Posicionamiento**: GPS/GLONASS

## Compatibilidad del MVP

### ✅ Compatible Sin Cambios

1. **Arquitectura General**
   - El sistema está diseñado de forma modular
   - La estructura de telemetría es genérica
   - MAVSDK funciona con ambos drones (si usan MAVLink)

2. **Componentes UI**
   - El panel de telemetría muestra datos genéricos
   - El mapa funciona con cualquier dron
   - Los POIs son independientes del tipo de dron

3. **Backend y Almacenamiento**
   - El servidor HTTP es agnóstico al tipo de dron
   - El almacenamiento de POIs es universal

### ⚠️ Requiere Modificaciones

1. **Simulación Falsa (`drones/fake_generator.py`)**
   - Actualmente hardcodeado para Matrice 300 RTK
   - Especificaciones específicas (velocidad, altitud, tiempo de vuelo)
   - Campo `rtk_fix` siempre en `True`

2. **Normalización de Telemetría (`common/utils.py`)**
   - Preserva campos específicos de Matrice 300 RTK
   - Puede necesitar ajustes para campos específicos de AUTEL

3. **Documentación**
   - Referencias específicas a Matrice 300 RTK en README y código

## Solución Propuesta: Sistema Multi-Dron

Para hacer el MVP verdaderamente compatible con múltiples tipos de drones, se recomienda implementar un sistema de perfiles de dron.

### Opción 1: Perfiles de Dron (Recomendado)

Crear una clase base `DroneProfile` y perfiles específicos:

```python
# drones/profiles.py
from dataclasses import dataclass
from typing import Optional

@dataclass
class DroneProfile:
    """Perfil de especificaciones de un dron."""
    name: str
    max_speed: float  # m/s
    max_altitude: float  # metros AGL
    max_flight_time: float  # segundos
    battery_drain_rate_flying: float  # % por segundo
    battery_drain_rate_hover: float  # % por segundo
    max_vertical_speed: float  # m/s
    has_rtk: bool
    rtk_accuracy: Optional[float] = None  # metros
    acceleration_rate: float = 2.0  # m/s²
    deceleration_rate: float = 2.0  # m/s²

# Perfiles predefinidos
MATRICE_300_RTK = DroneProfile(
    name="DJI Matrice 300 RTK",
    max_speed=23.0,
    max_altitude=5000.0,
    max_flight_time=55.0 * 60.0,
    battery_drain_rate_flying=100.0 / (55.0 * 60.0),
    battery_drain_rate_hover=100.0 / (60.0 * 60.0),
    max_vertical_speed=6.0,
    has_rtk=True,
    rtk_accuracy=0.01
)

AUTEL_EVO_II_PRO = DroneProfile(
    name="AUTEL EVO II Pro",
    max_speed=20.0,
    max_altitude=8000.0,
    max_flight_time=40.0 * 60.0,
    battery_drain_rate_flying=100.0 / (40.0 * 60.0),
    battery_drain_rate_hover=100.0 / (45.0 * 60.0),
    max_vertical_speed=5.0,
    has_rtk=False,  # O True si tiene RTK opcional
    rtk_accuracy=None
)

AUTEL_EVO_II_DUAL = DroneProfile(
    name="AUTEL EVO II Dual 640T",
    max_speed=20.0,
    max_altitude=8000.0,
    max_flight_time=38.0 * 60.0,
    battery_drain_rate_flying=100.0 / (38.0 * 60.0),
    battery_drain_rate_hover=100.0 / (42.0 * 60.0),
    max_vertical_speed=5.0,
    has_rtk=False,
    rtk_accuracy=None
)
```

### Opción 2: Configuración Simple (Rápida)

Modificar `FakeTelemetryGenerator` para aceptar parámetros configurables:

```python
class FakeTelemetryGenerator:
    def __init__(
        self,
        drone_id: str,
        start_lat: float = 37.7749,
        start_lon: float = -122.4194,
        callback: Optional[Callable[[Dict[str, Any]], None]] = None,
        # Nuevos parámetros configurables
        max_speed: float = 23.0,
        max_altitude: float = 5000.0,
        max_flight_time: float = 55.0 * 60.0,
        has_rtk: bool = True
    ):
        self.MAX_SPEED = max_speed
        self.MAX_ALTITUDE = max_altitude
        self.MAX_FLIGHT_TIME = max_flight_time
        self.rtk_fix = has_rtk
        # ... resto del código
```

## Cambios Necesarios para AUTEL EVO II

### Cambios Mínimos (Opción 2 - Rápida)

1. **Modificar `drones/fake_generator.py`**:
   - Hacer parámetros configurables en lugar de constantes
   - Permitir desactivar RTK

2. **Modificar `common/config.py`**:
   - Agregar opción `drone_type` o parámetros de dron

3. **Actualizar `config.json.example`**:
   ```json
   {
     "drone_type": "autel_evo_ii_pro",
     "max_speed": 20.0,
     "max_altitude": 8000.0,
     "max_flight_time": 2400.0,
     "has_rtk": false
   }
   ```

### Cambios Completos (Opción 1 - Recomendada)

1. Crear `drones/profiles.py` con perfiles de dron
2. Modificar `FakeTelemetryGenerator` para usar perfiles
3. Actualizar `DroneManager` para seleccionar perfil
4. Actualizar configuración y documentación

## Compatibilidad con MAVSDK

### ✅ Compatible

Ambos drones usan MAVLink cuando están conectados a sistemas compatibles:
- **Matrice 300 RTK**: Compatible con MAVSDK vía DJI SDK o MAVLink
- **AUTEL EVO II**: Compatible con MAVSDK si el dron está configurado para MAVLink

**Nota importante**: AUTEL EVO II puede requerir configuración adicional para habilitar MAVLink, ya que por defecto usa el protocolo propietario de Autel.

## Recomendaciones

### Para Uso Inmediato con AUTEL EVO II

1. **Usar modo de telemetría falsa** con parámetros ajustados manualmente
2. **Modificar temporalmente** las constantes en `fake_generator.py`:
   ```python
   MAX_SPEED = 20.0  # En lugar de 23.0
   MAX_ALTITUDE = 8000.0  # En lugar de 5000.0
   MAX_FLIGHT_TIME = 40.0 * 60.0  # En lugar de 55.0 * 60.0
   self.rtk_fix = False  # Si no tiene RTK
   ```

### Para Solución Permanente

1. **Implementar sistema de perfiles** (Opción 1)
2. **Actualizar documentación** para reflejar soporte multi-dron
3. **Agregar validación** de parámetros según tipo de dron

## Conclusión

**Sí, el MVP puede usarse con AUTEL EVO II** con modificaciones menores. La arquitectura es compatible, pero la simulación actual está específicamente calibrada para Matrice 300 RTK.

**Esfuerzo estimado:**
- **Cambios mínimos**: 1-2 horas (ajustar constantes)
- **Solución completa**: 4-6 horas (sistema de perfiles)

**Recomendación**: Implementar la Opción 1 (sistema de perfiles) para hacer el MVP verdaderamente multi-dron y facilitar futuras integraciones.

## Referencias

- [DJI Matrice 300 RTK Specifications](https://www.dji.com/matrice-300)
- [AUTEL EVO II Specifications](https://shop.autelrobotics.com/pages/evo-ii-specification)
- [MAVSDK Documentation](https://mavsdk.mavlink.io/)

