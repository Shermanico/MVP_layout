# Sistema de Coordinación Multi-Dron

Un MVP listo para hackathon que coordina y visualiza múltiples drones en tiempo real. Construido con Python, Flet.dev y MAVSDK-Python.

**Simula DJI Matrice 300 RTK** - Dron empresarial profesional con características de vuelo realistas, posicionamiento RTK y comportamiento de batería TB60.

## Características

- **Visualización Multi-Dron**: Muestra múltiples drones simulados simultáneamente en un mapa interactivo
- **Telemetría en Tiempo Real**: Actualizaciones en vivo de posición, altitud, rumbo, velocidad y batería
- **Mapa Interactivo**: Visualización de drones y POIs en mapa HTML con Folium/Leaflet
- **Actualizaciones Incrementales**: El mapa se actualiza sin recargar la página usando un servidor HTTP interno y polling JavaScript
- **Simulación Matrice 300 RTK**: Características de vuelo realistas incluyendo:
  - Velocidad máxima: 23 m/s (82.8 km/h)
  - Altitud máxima: 5000m AGL
  - Tiempo de vuelo: ~55 minutos (batería TB60)
  - Posicionamiento RTK con precisión a nivel de centímetro
  - Aceleración/desaceleración suave profesional
  - Seguimiento de velocidad vertical
  - Estimaciones de tiempo de vuelo restante
- **Puntos de Interés (POIs)**: Crear, gestionar y sincronizar POIs en todos los clientes
- **Arquitectura Hexagonal**: Diseño modular, escalable y flexible con separación clara de responsabilidades
- **Modo Telemetría Falsa**: Probar sin configuración MAVSDK usando el simulador Matrice 300 RTK integrado
- **Compilación Multiplataforma**: Compilar como ejecutable para Windows, macOS, Linux, Android e iOS

## Arquitectura

El proyecto sigue una **Arquitectura Hexagonal (Ports and Adapters)** que garantiza máxima flexibilidad y escalabilidad:

```
project_root/
├── domain/                    # 🟢 NÚCLEO - Sin dependencias externas
│   ├── entities/            # Entidades de negocio
│   │   ├── drone.py
│   │   ├── telemetry.py
│   │   └── poi.py
│   │
│   ├── ports/                # Puertos (interfaces)
│   │   ├── input/            # Puertos de entrada (casos de uso)
│   │   │   ├── drone_service_port.py
│   │   │   └── poi_service_port.py
│   │   │
│   │   └── output/           # Puertos de salida (repositorios)
│   │       ├── drone_repository_port.py
│   │       ├── poi_repository_port.py
│   │       └── telemetry_repository_port.py
│   │
│   └── value_objects/        # Objetos de valor (futuro)
│
├── application/              # 🟡 CASOS DE USO - Orquestación de lógica
│   ├── use_cases/            # Casos de uso específicos
│   │   ├── drone/
│   │   │   ├── start_drones.py
│   │   │   ├── stop_drones.py
│   │   │   └── get_drone_list.py
│   │   │
│   │   └── poi/
│   │       ├── create_poi.py
│   │       ├── delete_poi.py
│   │       ├── get_all_pois.py
│   │       ├── get_pois_by_type.py
│   │       └── clear_all_pois.py
│   │
│   ├── mappers/              # Convertidores entre entidades y DTOs
│   │   ├── telemetry_mapper.py
│   │   └── poi_mapper.py
│   │
│   └── services/             # Servicios que implementan puertos de entrada
│       ├── drone_service.py
│       └── poi_service.py
│
├── adapters/                 # 🔵 ADAPTADORES - Implementaciones concretas
│   ├── input/                # Adaptadores de entrada (Primary)
│   │   └── flet/             # UI con Flet
│   │       ├── main_app.py
│   │       ├── telemetry_panel.py
│   │       ├── poi_manager.py
│   │       └── map_view.py
│   │
│   └── output/               # Adaptadores de salida (Secondary)
│       ├── persistence/      # Persistencia
│       │   └── json_poi_repository.py
│       │
│       ├── simulation/       # Simulación de drones
│       │   ├── fake_drone_adapter.py
│       │   └── mavsdk_drone_adapter.py
│       │
│       └── http/             # Servidor HTTP
│           └── telemetry_server.py
│
├── infrastructure/            # 🔵 INFRAESTRUCTURA - Herramientas y utilidades
│   ├── config/               # Configuración
│   │   ├── config.py
│   │   ├── constants.py
│   │   ├── colors.py
│   │   └── utils.py
│   │
│   └── shared/               # Utilidades compartidas
│
├── app/                      # DTOs (Data Transfer Objects)
│   └── dtos.py               # TelemetryDTO, POIDTO
│
├── main.py                   # Punto de entrada - Wire up (composición)
├── requirements.txt          # Dependencias
└── flet.json                 # Configuración de compilación Flet
```

### Explicación de la Arquitectura Hexagonal

**Domain (Dominio) - Núcleo del Sistema:**
- **Entidades**: Representan los conceptos del negocio (Drone, Telemetry, POI)
- **Puertos de Entrada**: Interfaces que definen qué operaciones puede realizar la aplicación (IDroneService, IPOIService)
- **Puertos de Salida**: Interfaces que definen cómo se accede a datos externos (IDroneRepository, IPOIRepository, ITelemetryRepository)
- **Sin dependencias externas**: El dominio no conoce detalles de implementación

**Application (Aplicación) - Casos de Uso:**
- **Casos de Uso**: Cada caso de uso tiene una responsabilidad única (crear POI, iniciar drones, etc.)
- **Mappers**: Convierten entre entidades del dominio y DTOs
- **Servicios**: Orquestan casos de uso e implementan puertos de entrada
- **Depende solo de Domain**: Solo conoce interfaces, no implementaciones

**Adapters (Adaptadores) - Implementaciones:**
- **Adaptadores de Entrada (Primary)**: Implementan cómo la aplicación recibe comandos (UI Flet, CLI, REST API)
- **Adaptadores de Salida (Secondary)**: Implementan cómo la aplicación accede a datos (JSON, Base de Datos, MAVSDK)
- **Dependen de Domain y Application**: Implementan los puertos definidos en el dominio

**Infrastructure (Infraestructura) - Utilidades:**
- **Configuración**: Config, constantes, colores, utilidades
- **Herramientas compartidas**: Logging, validaciones, etc.

**Ventajas de esta Arquitectura:**
- ✅ **Escalabilidad**: Fácil agregar nuevas funcionalidades sin afectar existentes
- ✅ **Flexibilidad**: Cambiar implementaciones (JSON → DB, Flet → Web) sin afectar lógica
- ✅ **Modularidad**: Cada componente tiene responsabilidad única
- ✅ **Testabilidad**: Fácil testear con mocks de interfaces
- ✅ **Mantenibilidad**: Código organizado y predecible
- ✅ **Preparado para el futuro**: Fácil agregar REST API, WebSocket, etc.

## Instalación

### Requisitos Previos

- **Python 3.10+** (verificado con Python 3.13.1, compatible con Python 3.14)
- **Sistema operativo**: Windows, macOS o Linux

### Configuración del Entorno Virtual

**Windows PowerShell:**
```powershell
# Crear entorno virtual
python -m venv venv

# Activar entorno virtual (IMPORTANTE: usa el punto al inicio)
. .\activate_env.ps1

# O activar directamente
.\venv\Scripts\Activate.ps1
```

**Nota importante**: En PowerShell, el script helper requiere el operador de punto (`.`) al inicio para ejecutarse en el contexto actual del shell. Esto permite que la activación modifique el entorno del shell actual.

**Windows Command Prompt:**
```cmd
python -m venv venv
activate_env.bat
# O activar directamente
venv\Scripts\activate.bat
```

**Linux/macOS:**
```bash
python3 -m venv venv
source venv/bin/activate
```

**Verificar activación**: Deberías ver `(venv)` al inicio de tu prompt después de activar.

**Solución de problemas de activación:**
- **Error: "cannot be loaded because running scripts is disabled"**: Ejecuta en PowerShell (como Administrador):
  ```powershell
  Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
  ```
- **Error: "The term 'activate_env.ps1' is not recognized"**: Asegúrate de usar la sintaxis correcta:
  - PowerShell: `.\activate_env.ps1` o `. .\activate_env.ps1`
  - CMD: `activate_env.bat`
- **El entorno virtual no se activa**: Verifica que el directorio `venv` existe:
  ```powershell
  Test-Path .\venv\Scripts\Activate.ps1
  ```
  Si devuelve `False`, crea el entorno virtual: `python -m venv venv`

### Instalación de Dependencias

```bash
# Instalar todas las dependencias (incluye flet[all])
pip install -r requirements.txt
```

**Dependencias principales:**
- `flet[all]>=0.21.0` - Framework UI multiplataforma (incluye desktop, web, CLI)
- `folium>=0.15.0` - Visualización de mapas interactivos

**Dependencias opcionales:**
- `mavsdk>=1.4.0` - Para simulación MAVSDK real (instalar con: `pip install mavsdk`)

### Verificación de Instalación

```bash
# Verificar que las dependencias están instaladas
python -c "import flet; import folium; print('✓ Todas las dependencias instaladas')"
```

## Uso

### Guía Paso a Paso para Ejecutar y Depurar

#### Paso 1: Activar el Entorno Virtual

**Windows PowerShell:**
```powershell
# Navegar al directorio del proyecto
cd "C:\Users\User\Desktop\cursor\New folder\MVP_layout"

# Activar entorno virtual (usa el punto al inicio)
. .\venv\Scripts\Activate.ps1

# Verificar que está activado (deberías ver (venv) en el prompt)
```

**Windows Command Prompt:**
```cmd
cd "C:\Users\User\Desktop\cursor\New folder\MVP_layout"
venv\Scripts\activate.bat
```

**Linux/macOS:**
```bash
cd /ruta/al/proyecto
source venv/bin/activate
```

#### Paso 2: Verificar Dependencias

```bash
# Verificar que Flet está instalado
python -c "import flet; print('✓ Flet instalado')"

# Verificar que Folium está instalado (opcional pero recomendado)
python -c "import folium; print('✓ Folium instalado')"

# Si falta alguna dependencia, instalar:
pip install -r requirements.txt
```

#### Paso 3: Verificar Estructura de Archivos

Verifica que existan los siguientes archivos clave:

```bash
# Verificar estructura principal
python -c "
import os
dirs = ['domain', 'application', 'adapters', 'infrastructure', 'app']
for d in dirs:
    print(f'✓ {d}/' if os.path.exists(d) else f'✗ {d}/ FALTA')
"
```

#### Paso 4: Ejecutar la Aplicación

```bash
# Ejecutar la aplicación
python main.py
```

**Lo que debería suceder:**
1. Verás logs en la consola indicando el proceso de inicialización
2. Se abrirá una ventana de Flet con la UI
3. En la consola verás mensajes como:
   ```
   INFO - Iniciando aplicación con arquitectura hexagonal...
   INFO - Configuración cargada: use_fake_telemetry=True, fake_drone_count=6
   INFO - Creando adaptadores de salida...
   INFO - Creando casos de uso...
   INFO - Creando servicios...
   INFO - Creando adaptador de entrada (UI)...
   INFO - Iniciando simulación de drones...
   INFO - Drones iniciados: 6
   ```

#### Paso 5: Verificar que Todo Funciona

1. **Verifica la UI:**
   - Deberías ver el mapa a la izquierda
   - Panel de telemetría a la derecha (arriba)
   - Panel de POIs a la derecha (abajo)

2. **Verifica los drones:**
   - En el panel de telemetría deberían aparecer 6 drones
   - Los datos deberían actualizarse cada 0.5 segundos

3. **Verifica el mapa:**
   - Si tienes Folium: deberías ver el mapa con iconos de drones
   - Si no tienes Folium: haz clic en "Abrir Mapa en Navegador"

4. **Verifica el servidor HTTP:**
   - Abre tu navegador y ve a: `http://localhost:8765/api/data`
   - Deberías ver un JSON con datos de drones y POIs

### Depuración de Errores Comunes

#### Error 1: "ModuleNotFoundError: No module named 'domain'"

**Causa:** Estás ejecutando desde un directorio incorrecto o el PYTHONPATH no está configurado.

**Solución:**
```bash
# Asegúrate de estar en el directorio raíz del proyecto
cd "C:\Users\User\Desktop\cursor\New folder\MVP_layout"

# Verifica que estás en el lugar correcto
ls main.py  # Debería existir

# Ejecuta desde aquí
python main.py
```

#### Error 2: "ModuleNotFoundError: No module named 'flet'"

**Causa:** Flet no está instalado o el venv no está activado.

**Solución:**
```bash
# Activa el venv primero
. .\venv\Scripts\Activate.ps1  # PowerShell
# O
venv\Scripts\activate.bat  # CMD

# Instala dependencias
pip install -r requirements.txt

# Verifica instalación
python -c "import flet; print('OK')"
```

#### Error 3: "ImportError: cannot import name 'IDroneService' from 'domain.ports.input'"

**Causa:** Falta el archivo `__init__.py` o hay un error en la estructura.

**Solución:**
```bash
# Verifica que existan los archivos
ls domain/ports/input/__init__.py
ls domain/ports/output/__init__.py

# Si no existen, créalos o verifica la estructura
```

#### Error 4: "AttributeError: 'FakeDroneAdapter' object has no attribute 'telemetry_callback'"

**Causa:** El callback no se está configurando correctamente.

**Solución:** Verifica en `main.py` que el callback se configure ANTES de llamar a `start_drones()`:
```python
# En main.py, línea ~135
drone_repository.telemetry_callback = on_telemetry_update
```

#### Error 5: "TypeError: 'NoneType' object is not callable"

**Causa:** Un callback o servicio no está inicializado correctamente.

**Solución:** Verifica el orden de inicialización en `main.py`:
1. Config
2. Adaptadores de salida
3. Casos de uso
4. Servicios
5. Adaptador de entrada (UI)
6. Callback
7. Iniciar drones

#### Error 6: "OSError: [WinError 10048] Only one usage of each socket address"

**Causa:** El puerto 8765 ya está en uso (otra instancia de la app corriendo).

**Solución:**
```bash
# En Windows PowerShell:
netstat -ano | findstr :8765
# Mata el proceso que está usando el puerto, o cambia el puerto en el código
```

#### Error 7: Los drones no aparecen en el mapa

**Causa:** El servidor HTTP no está funcionando o el JavaScript no está haciendo polling.

**Solución:**
1. Verifica que el servidor HTTP esté corriendo: `http://localhost:8765/api/data`
2. Abre la consola del navegador (F12) y busca errores de JavaScript
3. Verifica que el polling esté funcionando (deberías ver requests cada 1 segundo)

#### Error 8: "ValueError: El número de drones debe ser mayor a 0"

**Causa:** La configuración tiene `fake_drone_count` en 0 o negativo.

**Solución:**
```bash
# Edita config.json o verifica los valores por defecto en infrastructure/config/config.py
# fake_drone_count debe ser >= 1
```

### Proceso de Depuración Sistemática

#### 1. Verificar Imports Básicos

```python
# Crea un script de prueba: test_imports.py
python -c "
try:
    from domain.entities import Drone, Telemetry, POI
    print('✓ Domain entities')
except Exception as e:
    print(f'✗ Domain entities: {e}')

try:
    from domain.ports.input import IDroneService, IPOIService
    print('✓ Domain ports input')
except Exception as e:
    print(f'✗ Domain ports input: {e}')

try:
    from domain.ports.output import IDroneRepository, IPOIRepository
    print('✓ Domain ports output')
except Exception as e:
    print(f'✗ Domain ports output: {e}')

try:
    from application.use_cases.drone.start_drones import StartDronesUseCase
    print('✓ Use cases')
except Exception as e:
    print(f'✗ Use cases: {e}')

try:
    from adapters.output.persistence import JsonPOIRepository
    print('✓ Adapters output')
except Exception as e:
    print(f'✗ Adapters output: {e}')

try:
    from adapters.input.flet.main_app import MainApp
    print('✓ Adapters input')
except Exception as e:
    print(f'✗ Adapters input: {e}')
"
```

#### 2. Verificar Wire Up Paso a Paso

Agrega logs detallados en `main.py` para ver dónde falla:

```python
# En main.py, después de cada paso importante:
logger.info("✓ Paso 1: Config cargada")
logger.info("✓ Paso 2: Adaptadores de salida creados")
logger.info("✓ Paso 3: Casos de uso creados")
# etc.
```

#### 3. Verificar que los Adaptadores Implementan Correctamente

```python
# Crea test_adapters.py
from adapters.output.persistence import JsonPOIRepository
from adapters.output.simulation import FakeDroneAdapter
from domain.ports.output import IPOIRepository, IDroneRepository

# Verificar que JsonPOIRepository implementa IPOIRepository
poi_repo = JsonPOIRepository("test_pois.json")
assert isinstance(poi_repo, IPOIRepository), "JsonPOIRepository debe implementar IPOIRepository"
print("✓ JsonPOIRepository implementa IPOIRepository")

# Verificar que FakeDroneAdapter implementa IDroneRepository
drone_repo = FakeDroneAdapter()
assert isinstance(drone_repo, IDroneRepository), "FakeDroneAdapter debe implementar IDroneRepository"
print("✓ FakeDroneAdapter implementa IDroneRepository")
```

#### 4. Verificar Flujo de Datos

Agrega breakpoints o logs en puntos clave:

```python
# En adapters/output/simulation/fake_drone_adapter.py
# En el método _generate_telemetry(), agrega:
logger.debug(f"Generando telemetría para {self.drone_id}: {normalized}")

# En main.py, en on_telemetry_update:
logger.debug(f"Telemetría recibida: {telemetry}")

# En adapters/input/flet/main_app.py, en update_telemetry:
logger.debug(f"Actualizando UI con telemetría: {telemetry.get('drone_id')}")
```

### Inicio Rápido (Modo Telemetría Falsa)

Por defecto, la aplicación usa generadores de telemetría falsa, por lo que no se requiere configuración MAVSDK:

```bash
# Asegúrate de que el venv esté activado
python main.py
```

Esto hará:
- Lanzar la ventana UI de Flet
- Iniciar servidor HTTP interno en `http://localhost:8765`
- Iniciar 6 drones simulados (configurable)
- Mostrar telemetría en tiempo real
- Permitir creación y gestión de POIs
- Generar mapa HTML interactivo con drones y POIs que se actualiza automáticamente

### Usando MAVSDK (Opcional)

Para usar simulación MAVSDK real:

1. Instalar MAVSDK:
   ```bash
   pip install mavsdk
   ```

2. Editar `config.json` (o crearlo):
   ```json
   {
     "use_fake_telemetry": false,
     "fake_drone_count": 3
   }
   ```

3. Asegurar que MAVSDK está instalado y los drones están conectados

4. Ejecutar la aplicación:
   ```bash
   python main.py
   ```

## Configuración

Crear un archivo `config.json` para personalizar la configuración:

```json
{
  "default_latitude": 20.9674,
  "default_longitude": -89.5926,
  "default_zoom": 13,
  "max_drones": 10,
  "telemetry_update_interval": 0.5,
  "use_fake_telemetry": true,
  "fake_drone_count": 6,
  "poi_storage_file": "pois.json",
  "window_width": 1400,
  "window_height": 900,
  "window_title": "Sistema de Coordinación Multi-Dron"
}
```

**Nota**: Las coordenadas por defecto están configuradas para Mérida, Yucatán, México.

## Características en Detalle

### Telemetría de Dron (Matrice 300 RTK)

Cada dron muestra:
- **Posición**: Latitud y longitud (precisión RTK)
- **Altitud**: Altura sobre el nivel del suelo (metros, hasta 5000m)
- **Rumbo**: Dirección de la brújula (grados)
- **Velocidad**: Velocidad en m/s y km/h (máx 23 m/s)
- **Velocidad Vertical**: Tasa de ascenso/descenso (m/s)
- **Batería**: Nivel de batería TB60 (0-100%)
- **Tiempo de Vuelo Restante**: Tiempo estimado basado en batería actual y modo de vuelo
- **Estado RTK**: Indicador de fijación RTK para posicionamiento a nivel de centímetro
- **Estado**: Estado de vuelo actual (inactivo, volando, aterrizando, etc.)

### Mapa Interactivo

El sistema incluye un mapa interactivo que muestra:

- **Marcadores de Drones**:
  - Iconos SVG que rotan según el rumbo del dron
  - Color dinámico según nivel de batería (verde >50%, naranja 20-50%, rojo <20%)
  - Popup con información detallada (ID, batería, altitud, velocidad, rumbo)
  - Actualización en tiempo real sin recargar la página (polling cada 1s)

- **Marcadores de POIs**:
  - Colores por tipo (Peligro: rojo, Objetivo: azul, Punto de Control: amarillo, Zona de Aterrizaje: verde)
  - Popup con tipo y descripción
  - Persistencia en archivo JSON

- **Funcionalidades**:
  - Zoom y pan interactivos
  - Actualizaciones incrementales vía servidor HTTP interno
  - Preservación de estado del mapa (zoom, centro) usando localStorage
  - Botón para abrir mapa en navegador externo (útil en Windows donde WebView puede no estar soportado)
  - Vista alternativa con lista de drones y POIs cuando WebView no está disponible

**Tecnologías del Mapa**:
- **Folium** (recomendado): Biblioteca Python para mapas interactivos
- **HTML/JavaScript puro** (fallback): Si Folium no está disponible
- **Leaflet.js**: Para actualizaciones incrementales de marcadores
- **OpenStreetMap**: Tiles de mapa sin necesidad de API keys
- **Servidor HTTP interno**: Sirve datos JSON en `http://localhost:8765/api/data`

### Puntos de Interés (POIs)

Crear POIs con:
- **Tipo**: Peligro, Objetivo, Punto de Control, Zona de Aterrizaje u Otro
- **Descripción**: Descripción de texto personalizada
- **Ubicación**: Especificar coordenadas manualmente
- **Auto-sincronización**: Los POIs se sincronizan instantáneamente a todos los clientes conectados

### Actualizaciones en Tiempo Real

- Telemetría se actualiza cada 0.5 segundos (configurable)
- Cambios de POI se transmiten inmediatamente
- Mapa HTML se actualiza incrementalmente sin recargar la página
- JavaScript hace polling al servidor HTTP cada 1 segundo (throttled)
- Soporte multi-cliente vía sistema pub/sub de Flet

## Compatibilidad con Otros Drones

### AUTEL EVO II

**Respuesta corta**: Sí, este MVP **puede ser usado con AUTEL EVO II**, pero requiere modificaciones menores en el código de simulación.

**Comparación de especificaciones:**

| Característica | Matrice 300 RTK (Actual) | AUTEL EVO II Pro |
|----------------|--------------------------|------------------|
| Velocidad máxima | 23 m/s (82.8 km/h) | ~20 m/s (72 km/h) |
| Altitud máxima | 5000m AGL | 8000m AGL |
| Tiempo de vuelo | ~55 minutos | ~40 minutos |
| Posicionamiento | RTK (centímetro) | GPS/GLONASS (RTK opcional) |
| Protocolo | MAVLink (MAVSDK) | MAVLink (si está configurado) |

**Compatibilidad del MVP:**
- ✅ **Arquitectura General**: Compatible sin cambios
- ✅ **Componentes UI**: Compatible sin cambios
- ✅ **Backend y Almacenamiento**: Compatible sin cambios
- ⚠️ **Simulación Falsa**: Requiere modificar constantes en el adaptador de simulación

**Solución rápida para AUTEL EVO II:**

Modificar las constantes en el adaptador de simulación (`adapters/output/simulation/fake_drone_adapter.py`):
```python
MAX_SPEED = 20.0  # En lugar de 23.0
MAX_ALTITUDE = 8000.0  # En lugar de 5000.0
MAX_FLIGHT_TIME = 40.0 * 60.0  # En lugar de 55.0 * 60.0
self.rtk_fix = False  # Si no tiene RTK
```

**Solución recomendada (futuro):**

Implementar un sistema de perfiles de dron que permita seleccionar el tipo de dron desde la configuración. Esto haría el MVP verdaderamente multi-dron y facilitaría futuras integraciones.

**Esfuerzo estimado:**
- **Cambios mínimos**: 1-2 horas (ajustar constantes)
- **Solución completa**: 4-6 horas (sistema de perfiles)

## Compilación Multiplataforma

Flet permite compilar la aplicación como ejecutable independiente para múltiples plataformas.

### Requisitos Previos para Compilación

1. **Activar el entorno virtual:**
   ```powershell
   .\venv\Scripts\Activate.ps1
   ```

2. **Verificar que Flet CLI está instalado:**
   ```bash
   flet --version
   ```
   Si no está instalado, se instaló automáticamente con `flet[all]`.

### Windows

```bash
flet build windows
```

**Resultado:**
- Ejecutable `.exe` en la carpeta `dist/`
- Ejecutable independiente (no requiere Python instalado)
- Tamaño aproximado: 50-100 MB

### macOS

**Requisitos Previos:**
1. **Rosetta 2** (para sistemas con Apple Silicon):
   ```bash
   sudo softwareupdate --install-rosetta --agree-to-license
   ```
2. **Xcode 15 o superior** (desde App Store)
3. **CocoaPods 1.16 o superior:**
   ```bash
   sudo gem install cocoapods
   ```

**Compilar:**
```bash
flet build macos
```

**Resultado:**
- Paquete `.app` en la carpeta `dist/`

### Linux

**Requisitos Previos:**

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install libgtk-3-dev libgstreamer1.0-dev libgstreamer-plugins-base1.0-dev
sudo apt install libmpv-dev mpv
```

**Fedora:**
```bash
sudo dnf install gtk3-devel gstreamer1-devel gstreamer1-plugins-base-devel
sudo dnf install mpv-devel mpv
```

**Compilar:**
```bash
flet build linux
```

**Resultado:**
- Ejecutable independiente en la carpeta `dist/`

### Android

```bash
flet build apk
```

**Resultado:**
- Archivo `.apk` en la carpeta `dist/`

**Para crear un APK firmado (release):**
```bash
flet build apk --release
```

### iOS

**Requisitos:**
- macOS (requerido por Apple)
- Xcode instalado
- Cuenta de desarrollador de Apple (para firmar)

**Compilar:**
```bash
flet build ipa
```

**Resultado:**
- Archivo `.ipa` en la carpeta `dist/`

### Personalizar el Build

Edita el archivo `flet.json` para personalizar:

```json
{
  "name": "Multi-Drone Coordination System",
  "version": "1.0.0",
  "description": "Sistema de coordinación multi-dron",
  "author": "Tu Nombre",
  "main": "main.py",
  "assets_dir": "assets",
  "icon": "assets/icon.png"
}
```

### Notas Importantes sobre Compilación

1. **Primera compilación:** Puede tardar varios minutos mientras Flet descarga las herramientas necesarias.
2. **Tamaño del ejecutable:** Los ejecutables incluyen Python y todas las dependencias (~50-100 MB).
3. **Servidor HTTP:** El servidor HTTP interno (puerto 8765) funcionará correctamente en el ejecutable.
4. **Archivos temporales:** Los archivos temporales del mapa se crearán en el directorio temporal del sistema.

## Desarrollo

### Estructura del Proyecto

- **domain/**: Entidades del dominio, puertos (interfaces)
- **application/**: Casos de uso, mappers, servicios
- **adapters/**: Implementaciones concretas (UI, repositorios, simulación)
- **infrastructure/**: Configuración y utilidades
- **app/**: DTOs para transferencia de datos

### Agregar Nuevas Características

1. **Nuevos Casos de Uso**: Crear en `application/use_cases/`
2. **Nuevos Tipos de POI**: Agregar al enum `POIType` en `infrastructure/config/constants.py`
3. **Nuevos Adaptadores**: Crear en `adapters/input/` o `adapters/output/`
4. **Campos de Telemetría**: Extender entidad `Telemetry` en `domain/entities/telemetry.py`

## Ejecución y Depuración

### Guía Rápida de Ejecución

1. **Activar entorno virtual:**
   ```powershell
   . .\venv\Scripts\Activate.ps1
   ```

2. **Verificar dependencias:**
   ```bash
   python -c "import flet; print('✓ Flet OK')"
   ```

3. **Ejecutar aplicación:**
   ```bash
   python main.py
   ```

4. **Verificar funcionamiento:**
   - Ventana Flet debe abrirse
   - Panel de telemetría muestra 6 drones
   - Servidor HTTP en `http://localhost:8765/api/data`

### Depuración de Errores Comunes

**Error: "ModuleNotFoundError: No module named 'domain'"**
- **Solución:** Asegúrate de estar en el directorio raíz del proyecto donde está `main.py`

**Error: "ImportError: cannot import name 'IDroneService'"**
- **Solución:** Verifica que existan los archivos `__init__.py` en `domain/ports/input/` y `domain/ports/output/`

**Error: "AttributeError: 'FakeDroneAdapter' object has no attribute 'telemetry_callback'"**
- **Solución:** En `main.py`, configura el callback ANTES de llamar a `start_drones()`:
  ```python
  drone_repository.telemetry_callback = on_telemetry_update
  ```

**Error: "OSError: [WinError 10048] Only one usage of each socket address"**
- **Solución:** El puerto 8765 está ocupado. Mata el proceso anterior o cambia el puerto.

**Los drones no aparecen:**
- Verifica logs en consola para ver si hay errores
- Verifica que el servidor HTTP esté corriendo: `http://localhost:8765/api/data`
- Abre la consola del navegador (F12) para ver errores de JavaScript

Para más detalles, consulta la sección completa de depuración más abajo.

## Solución de Problemas

### Ventana de Flet No Se Abre

- Asegurar que Flet está instalado: `pip install 'flet[all]'`
- Verificar versión de Python: `python --version` (debe ser 3.10+)
- Verificar que el venv esté activado (deberías ver `(venv)` en el prompt)

### No Aparecen Drones

- Verificar configuración en `config.json`
- Verificar que `use_fake_telemetry` es `true` para modo falso
- Revisar consola para mensajes de error
- Verificar que los drones se están creando en los logs
- Verificar que el servidor HTTP está corriendo en `http://localhost:8765`

### POIs No Se Guardan

- Verificar permisos de archivo para `pois.json`
- Verificar ruta `poi_storage_file` en la configuración

### Error: "Container Control must be added to the page first"

- Este error ocurre cuando se intenta actualizar un componente antes de agregarlo a la página
- Ya está corregido en el código actual, pero si aparece, verificar que `page.update()` se llama después de agregar controles

### WebView No Soportado (Windows)

- En Windows, Flet WebView puede no estar soportado
- El sistema automáticamente usa una vista alternativa con:
  - Lista de drones con información detallada
  - Lista de POIs
  - Botón para abrir el mapa HTML en el navegador externo
- El mapa HTML se genera automáticamente y se puede abrir en cualquier navegador

### Los Drones No Aparecen en el Mapa HTML

- Esperar unos segundos después de iniciar la aplicación para que los drones envíen telemetría
- Verificar que el servidor HTTP está corriendo: `http://localhost:8765/api/data`
- Abrir la consola del navegador (F12) para ver errores de JavaScript
- Verificar que el polling JavaScript está funcionando (deberías ver logs en la consola)

### El Mapa Se Recarga Constantemente

- Este problema ya está resuelto con actualizaciones incrementales
- El mapa ahora usa polling JavaScript y actualiza solo los marcadores
- Si aún ocurre, verificar que el servidor HTTP está funcionando correctamente

### Error al Compilar

**Windows:**
- Asegúrate de tener permisos de administrador si es necesario
- Verifica que no haya antivirus bloqueando la compilación

**macOS:**
- Verifica que Xcode esté completamente instalado
- Ejecuta: `xcode-select --install`

**Linux:**
- Instala todas las dependencias del sistema listadas arriba
- Verifica que las bibliotecas de desarrollo estén instaladas

### Virtual Environment No Se Activa

- Asegúrate de estar en el directorio raíz del proyecto
- Verifica que la carpeta `venv/` existe
- En Windows PowerShell, puede ser necesario cambiar la política de ejecución:
  ```powershell
  Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
  ```

## Licencia

Este proyecto está diseñado para uso en hackathon. Siéntete libre de modificar y extender según sea necesario.

## Notas

- Este MVP prioriza velocidad y simplicidad sobre física de vuelo perfecta
- El modo de telemetría falsa es recomendado para desarrollo en hackathon
- La integración MAVSDK es opcional y puede agregarse después
- El sistema está diseñado para ser fácilmente extensible
- El mapa HTML se guarda en un archivo temporal que se limpia al cerrar la aplicación
- El servidor HTTP interno se ejecuta en un hilo separado y se detiene automáticamente al cerrar la aplicación
- La arquitectura hexagonal está preparada para Python 3.14 (sin GIL)

## Mejoras Futuras

- Clic directo en el mapa para crear POIs
- Planificación de misión y seguimiento de waypoints
- Interfaz de comandos de dron
- Registro histórico de telemetría
- Backend WebSocket multi-cliente (reemplazar polling HTTP)
- Exportar/importar datos de POI
- Rutas y trayectorias de drones en el mapa
- Capas toggleables (mostrar/ocultar drones/POIs)
- Sistema de perfiles de dron para soporte multi-dron
- REST API para integración externa
- CLI para operaciones desde terminal

## Referencias

- [Flet Documentation](https://flet.dev/)
- [Flet Packaging Guide](https://flet.dev/docs/cookbook/packaging-desktop-app/)
- [Folium Documentation](https://python-visualization.github.io/folium/)
- [Leaflet.js Documentation](https://leafletjs.com/)
- [MAVSDK-Python Documentation](https://mavsdk.mavlink.io/)
- [Hexagonal Architecture (Alistair Cockburn)](https://alistair.cockburn.us/hexagonal-architecture/)
