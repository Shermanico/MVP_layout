# Explicación Completa del Flujo de Trabajo - Sistema de Coordinación Multi-Dron

Este documento explica el flujo de trabajo completo entre todos los archivos de script del sistema, incluyendo la integración del mapa interactivo.

## 📋 Tabla de Contenidos
1. [Flujo de Inicio de la Aplicación](#1-flujo-de-inicio-de-la-aplicación)
2. [Flujo de Datos en Tiempo de Ejecución](#2-flujo-de-datos-en-tiempo-de-ejecución)
3. [Flujo del Mapa Interactivo](#3-flujo-del-mapa-interactivo)
4. [Interacciones de Componentes](#4-interacciones-de-componentes)
5. [Diagramas de Flujo de Datos](#5-diagramas-de-flujo-de-datos)

---

## 1. Flujo de Inicio de la Aplicación

### Secuencia de Inicio Paso a Paso

```
┌─────────────────────────────────────────────────────────────┐
│ 1. Usuario ejecuta: python main.py                         │
└──────────────────────┬──────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. main.py::run_app()                                       │
│    - Llama ft.app(target=main)                              │
│    - El framework Flet se inicializa                        │
└──────────────────────┬──────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. main.py::main(page: ft.Page) [FUNCIÓN ASYNC]            │
│    - Recibe instancia de página Flet                         │
│    - Este es el punto de entrada de la aplicación           │
└──────────────────────┬──────────────────────────────────────┘
                        │
        ┌───────────────┴───────────────┐
        │                               │
        ▼                               ▼
┌───────────────────┐         ┌───────────────────┐
│ 4a. Cargar Config│         │ 4b. Inicializar   │
│ Config.load_from_│         │ Almacenamiento    │
│ file()            │         │ POIStorage()      │
│ - Lee config.    │         │ - Carga pois.json│
│   json o usa      │         │ - Crea instancia │
│   valores por     │         │   de almacenamiento│
│   defecto         │         │                   │
└─────────┬─────────┘         └─────────┬─────────┘
          │                             │
          └───────────────┬───────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│ 5. Inicializar UI (ui/main.py::MainApp)                     │
│    app = MainApp(config, storage)                           │
│    - Crea instancia de TelemetryPanel                       │
│    - Crea instancia de POIManager                           │
│    - Configura manejadores de callbacks                     │
└──────────────────────┬──────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│ 6. Configurar Página Flet (app.setup_page(page))           │
│    - Establece título y tamaño de ventana                   │
│    - Crea layout principal (mapa + panel lateral)          │
│    - Inicializa MapView (con Folium o fallback)            │
│    - Carga POIs existentes del almacenamiento               │
│    - Configura suscripciones pub/sub                       │
└──────────────────────┬──────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│ 7. Inicializar Gestor de Drones                             │
│    drone_manager = DroneManager(config, callback)           │
│    - Almacena función callback para actualizaciones de      │
│      telemetría                                             │
│    - Callback: app.update_telemetry()                       │
└──────────────────────┬──────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│ 8. Iniciar Simulación de Drones (Tarea en Segundo Plano)   │
│    drone_task = asyncio.create_task(run_drones())           │
│    - Se ejecuta en tarea async en segundo plano            │
│    - Llama: drone_manager.start()                          │
└──────────────────────┬──────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│ 9. DroneManager::start()                                    │
│    - Verifica config.use_fake_telemetry                     │
│    - Llama _start_fake_drones() o _start_mavsdk_drones()    │
└──────────────────────┬──────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│ 10. Crear Múltiples Drones                                  │
│     Para cada dron (por defecto: 3):                       │
│     - Generar ID único (DRONE_000, DRONE_001, etc.)         │
│     - Crear instancia FakeTelemetryGenerator                │
│     - Establecer posición inicial (distribuidos en cuadrícula)│
│     - Establecer callback: DroneManager._on_telemetry_update()│
│     - Iniciar tarea async: drone.start(update_interval)     │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. Flujo de Datos en Tiempo de Ejecución

### Flujo de Actualización de Telemetría (Cada 0.5 segundos por dron)

```
┌─────────────────────────────────────────────────────────────┐
│ drones/fake_generator.py::FakeTelemetryGenerator           │
│                                                              │
│ 1. _update_position()                                       │
│    - Calcula nueva posición basada en waypoint              │
│    - Actualiza: lat, lon, alt, heading, velocity, battery  │
│    - Simula características de vuelo Matrice 300 RTK        │
│                                                              │
│ 2. _generate_telemetry()                                    │
│    - Crea diccionario de telemetría con todos los datos     │
│      del dron                                               │
│    - Agrega campos específicos RTK (vertical_speed, rtk_fix)│
│    - Normaliza datos usando common/utils.py                 │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       │ callback(telemetry)
                       ▼
┌─────────────────────────────────────────────────────────────┐
│ drones/drone_manager.py::DroneManager                       │
│                                                              │
│ _on_telemetry_update(telemetry)                             │
│    - Recibe telemetría del dron individual                  │
│    - Llama: self.telemetry_callback(telemetry)             │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       │ telemetry_callback
                       ▼
┌─────────────────────────────────────────────────────────────┐
│ main.py::on_telemetry_update() [DEFINIDO EN MAIN]          │
│                                                              │
│ 1. app.update_telemetry(telemetry)                          │
│    - Actualiza UI con nuevos datos de telemetría            │
│                                                              │
│ 2. page.pubsub.send_all()                                   │
│    - Transmite telemetría vía pub/sub de Flet               │
│    - Tema: CHANNEL_TELEMETRY                                │
│    - Para sincronización multi-cliente (uso futuro)         │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       │ app.update_telemetry()
                       ▼
┌─────────────────────────────────────────────────────────────┐
│ ui/main.py::MainApp                                          │
│                                                              │
│ update_telemetry(telemetry)                                  │
│    ├─> telemetry_panel.update_telemetry(telemetry)          │
│    │   - Actualiza tarjeta de dron en panel lateral         │
│    │   - Muestra: batería, altitud, velocidad, estado RTK   │
│    │                                                          │
│    ├─> _update_map_drones()                                 │
│    │   - Actualiza posiciones de drones en vista de mapa     │
│    │   - Muestra: posición, batería, altitud                │
│    │                                                          │
│    └─> map_view.update_drone(telemetry)                    │
│        - Actualiza marcador de dron en mapa HTML            │
│        - Regenera archivo HTML con Folium                   │
│        - Actualiza vista alternativa si WebView no disponible│
└─────────────────────────────────────────────────────────────┘
```

### Flujo de Creación de POI (Interacción del Usuario)

```
┌─────────────────────────────────────────────────────────────┐
│ Usuario hace clic en botón "Agregar POI"                   │
└──────────────────────┬──────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│ ui/main.py::MainApp                                          │
│                                                              │
│ _on_add_poi_button_click()                                  │
│    - Muestra diálogo con: lat, lon, tipo, descripción       │
│    - Usuario completa detalles                             │
└──────────────────────┬──────────────────────────────────────┘
                        │
                        │ Usuario hace clic en "Crear"
                        ▼
┌─────────────────────────────────────────────────────────────┐
│ ui/main.py::MainApp                                          │
│                                                              │
│ _on_create_poi(lat, lon, type, description)                 │
│    ├─> storage.add_poi()                                    │
│    │   - Crea diccionario de POI                            │
│    │   - Guarda en archivo pois.json                        │
│    │                                                          │
│    ├─> poi_manager.add_poi(poi)                              │
│    │   - Agrega POI a lista UI                              │
│    │   - Crea tarjeta de POI en panel lateral                │
│    │                                                          │
│    ├─> page.pubsub.send_all()                               │
│    │   - Transmite evento de creación de POI                 │
│    │   - Tema: CHANNEL_POI                                   │
│    │                                                          │
│    ├─> _update_map_pois()                                   │
│    │   - Actualiza marcadores POI en vista de mapa           │
│    │                                                          │
│    └─> map_view.add_poi(poi)                                │
│        - Agrega marcador POI al mapa HTML                   │
│        - Regenera archivo HTML con Folium                   │
└─────────────────────────────────────────────────────────────┘
```

### Flujo de Eliminación de POI

```
┌─────────────────────────────────────────────────────────────┐
│ Usuario hace clic en botón eliminar en tarjeta POI         │
└──────────────────────┬──────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│ ui/poi_manager.py::POIManager                               │
│                                                              │
│ _on_delete(poi_id)                                           │
│    - Llama: self.on_delete_poi(poi_id)                      │
└──────────────────────┬──────────────────────────────────────┘
                        │
                        │ callback
                        ▼
┌─────────────────────────────────────────────────────────────┐
│ ui/main.py::MainApp                                          │
│                                                              │
│ _on_delete_poi(poi_id)                                       │
│    ├─> storage.remove_poi(poi_id)                           │
│    │   - Elimina de archivo pois.json                       │
│    │                                                          │
│    ├─> poi_manager.remove_poi(poi_id)                       │
│    │   - Elimina de lista UI                                │
│    │                                                          │
│    ├─> page.pubsub.send_all()                               │
│    │   - Transmite evento de eliminación de POI             │
│    │                                                          │
│    ├─> _update_map_pois()                                   │
│    │   - Actualiza vista de mapa                             │
│    │                                                          │
│    └─> map_view.remove_poi(poi_id)                          │
│        - Elimina marcador POI del mapa HTML                 │
│        - Regenera archivo HTML                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. Flujo del Mapa Interactivo

### Inicialización del Mapa

```
┌─────────────────────────────────────────────────────────────┐
│ ui/main.py::_create_map_view()                              │
│                                                              │
│ 1. Crear instancia MapView                                  │
│    map_view = MapView(                                      │
│        initial_lat, initial_lon, zoom,                      │
│        on_poi_click, on_map_click                           │
│    )                                                        │
└──────────────────────┬──────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│ ui/map_view.py::MapView.__init__()                          │
│                                                              │
│ 1. _create_map()                                            │
│    ├─> Intenta usar Folium (si está disponible)            │
│    │   - Crea mapa Folium con OpenStreetMap                │
│    │   - Guarda en archivo HTML temporal                   │
│    │                                                          │
│    └─> Si no hay Folium: _create_html_map()                │
│        - Genera HTML con Leaflet.js desde CDN               │
│        - Guarda en archivo HTML temporal                     │
│                                                              │
│ 2. _create_webview() o _create_fallback_view()             │
│    ├─> En Windows: Usa fallback directamente               │
│    │   - Vista alternativa con lista de drones/POIs        │
│    │   - Botón para abrir mapa en navegador                 │
│    │                                                          │
│    └─> En otras plataformas: Intenta WebView               │
│        - Carga archivo HTML en WebView de Flet              │
└─────────────────────────────────────────────────────────────┘
```

### Actualización del Mapa con Telemetría

```
┌─────────────────────────────────────────────────────────────┐
│ ui/map_view.py::MapView.update_drone()                     │
│                                                              │
│ 1. Almacenar telemetría en self.drones[drone_id]           │
│                                                              │
│ 2. _update_map_html()                                       │
│    ├─> Si Folium disponible:                                │
│    │   - Crear nuevo mapa Folium                            │
│    │   - _add_drones_to_folium_map()                        │
│    │     * Para cada dron: crear Marker con color según     │
│    │       batería, popup con información                    │
│    │   - _add_pois_to_folium_map()                          │
│    │     * Para cada POI: crear Marker con color según tipo │
│    │   - Guardar en archivo HTML                            │
│    │                                                          │
│    └─> Si no hay Folium:                                    │
│        - _generate_map_html()                                │
│        - Generar HTML con JavaScript puro                    │
│        - Guardar en archivo HTML                             │
│                                                              │
│ 3. _reload_map() (si WebView disponible)                    │
│    - Actualizar URL del WebView con timestamp               │
│    - Forzar recarga del mapa                                │
│                                                              │
│ 4. _update_fallback_view() (si fallback activo)             │
│    - Actualizar lista de drones en vista alternativa        │
│    - Actualizar lista de POIs en vista alternativa          │
└─────────────────────────────────────────────────────────────┘
```

### Apertura del Mapa en Navegador

```
┌─────────────────────────────────────────────────────────────┐
│ Usuario hace clic en "Abrir Mapa en Navegador"             │
└──────────────────────┬──────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│ ui/map_view.py::_open_map_in_browser()                     │
│                                                              │
│ 1. Verificar que archivo HTML existe                        │
│                                                              │
│ 2. webbrowser.open(file_url)                                │
│    - Abre archivo HTML en navegador predeterminado          │
│    - Muestra mapa interactivo con todos los marcadores      │
│    - Usuario puede hacer zoom, pan, ver popups              │
└─────────────────────────────────────────────────────────────┘
```

---

## 4. Interacciones de Componentes

### Mapa de Dependencias de Archivos

```
main.py
├── common/config.py (Clase Config)
├── backend/storage.py (Clase POIStorage)
├── drones/drone_manager.py (Clase DroneManager)
└── ui/main.py (Clase MainApp)
    ├── ui/telemetry_panel.py (TelemetryPanel)
    ├── ui/poi_manager.py (POIManager)
    ├── ui/map_view.py (MapView)
    └── backend/storage.py (POIStorage - pasado como parámetro)

drones/drone_manager.py
├── common/config.py (Config)
├── common/utils.py (generate_drone_id)
├── drones/fake_generator.py (FakeTelemetryGenerator)
└── drones/simulator.py (MAVSDKSimulator - opcional)

drones/fake_generator.py
├── common/utils.py (normalize_telemetry)
└── common/constants.py (DroneStatus)

backend/storage.py
├── common/utils.py (create_poi)
└── common/config.py (Config - para ruta de archivo)

ui/main.py
├── common/config.py (Config)
├── common/constants.py (POIType, CHANNEL_*)
├── backend/storage.py (POIStorage)
├── ui/telemetry_panel.py (TelemetryPanel)
├── ui/poi_manager.py (POIManager)
└── ui/map_view.py (MapView)

ui/map_view.py
├── common/constants.py (POIType)
├── common/colors.py (Colores)
└── folium (opcional, para mapas)
```

### Clases Clave y Sus Responsabilidades

#### 1. **Config** (`common/config.py`)
- **Propósito**: Gestión de configuración de la aplicación
- **Responsabilidades**:
  - Cargar/guardar configuración desde JSON
  - Almacenar valores por defecto (incluyendo coordenadas de Mérida, Yucatán)
  - Proporcionar configuraciones a todos los componentes

#### 2. **POIStorage** (`backend/storage.py`)
- **Propósito**: Almacenamiento persistente para Puntos de Interés
- **Responsabilidades**:
  - Cargar POIs desde archivo JSON al iniciar
  - Guardar POIs en archivo JSON al cambiar
  - Operaciones CRUD para POIs

#### 3. **DroneManager** (`drones/drone_manager.py`)
- **Propósito**: Orquesta múltiples simulaciones de drones
- **Responsabilidades**:
  - Crear y gestionar múltiples instancias de drones
  - Enrutar actualizaciones de telemetría a UI
  - Manejar ciclo de vida de drones (iniciar/detener)

#### 4. **FakeTelemetryGenerator** (`drones/fake_generator.py`)
- **Propósito**: Simula comportamiento del dron Matrice 300 RTK
- **Responsabilidades**:
  - Generar datos de telemetría realistas
  - Simular física de vuelo
  - Actualizar posición, batería, estado
  - Llamar callback con actualizaciones de telemetría

#### 5. **MainApp** (`ui/main.py`)
- **Propósito**: Coordina todos los componentes UI
- **Responsabilidades**:
  - Configurar layout de página Flet
  - Manejar interacciones del usuario (creación/eliminación de POI)
  - Actualizar UI con datos de telemetría
  - Coordinar entre componentes UI (incluyendo MapView)

#### 6. **TelemetryPanel** (`ui/telemetry_panel.py`)
- **Propósito**: Mostrar telemetría de drones en UI
- **Responsabilidades**:
  - Mostrar telemetría en tiempo real para cada dron
  - Actualizar tarjetas de drones con nuevos datos
  - Mostrar batería, altitud, velocidad, estado RTK

#### 7. **POIManager** (`ui/poi_manager.py`)
- **Propósito**: Gestionar visualización e interacciones de POIs
- **Responsabilidades**:
  - Mostrar lista de POIs
  - Manejar creación de tarjetas de POI
  - Activar callbacks de eliminación de POI

#### 8. **MapView** (`ui/map_view.py`)
- **Propósito**: Gestionar visualización de mapa interactivo
- **Responsabilidades**:
  - Crear mapa HTML con Folium o JavaScript puro
  - Actualizar marcadores de drones y POIs
  - Gestionar vista alternativa cuando WebView no está disponible
  - Proporcionar botón para abrir mapa en navegador

---

## 5. Diagramas de Flujo de Datos

### Arquitectura Completa del Sistema

```
┌─────────────────────────────────────────────────────────────┐
│                    CAPA DE APLICACIÓN                       │
│                                                              │
│  ┌────────────────────────────────────────────────────┐   │
│  │  main.py                                             │   │
│  │  - Punto de entrada                                  │   │
│  │  - Inicializa todos los componentes                 │   │
│  │  - Configura tareas async                            │   │
│  └───────────────┬──────────────────────────────────────┘   │
│                  │                                           │
│      ┌───────────┴───────────┐                               │
│      │                       │                               │
│      ▼                       ▼                               │
│  ┌──────────┐         ┌──────────┐                          │
│  │  Config  │         │ Storage  │                          │
│  │ (common) │         │(backend)│                          │
│  └──────────┘         └────┬─────┘                          │
│                             │                                 │
└─────────────────────────────┼─────────────────────────────────┘
                               │
                               │
┌─────────────────────────────┼─────────────────────────────────┐
│                    CAPA UI (Flet)                            │
│                                                               │
│  ┌────────────────────────────────────────────────────┐      │
│  │  ui/main.py::MainApp                                │      │
│  │  ┌────────────────┐  ┌──────────────────┐         │      │
│  │  │ TelemetryPanel │  │   POIManager     │         │      │
│  │  │ - Tarjetas     │  │   - Tarjetas POI │         │      │
│  │  │   de drones    │  │   - Lista POI    │         │      │
│  │  │ - Actualiz.    │  │   - Eliminar POIs│         │      │
│  │  │   en tiempo    │  │                  │         │      │
│  │  │   real         │  │                  │         │      │
│  │  └────────────────┘  └──────────────────┘         │      │
│  │                                                    │      │
│  │  ┌──────────────────────────────────────────┐     │      │
│  │  │  MapView                                 │     │      │
│  │  │  - Mapa HTML (Folium/Leaflet)          │     │      │
│  │  │  - Marcadores de drones                 │     │      │
│  │  │  - Marcadores POI                       │     │      │
│  │  │  - Vista alternativa (si WebView no     │     │      │
│  │  │    disponible)                          │     │      │
│  │  └──────────────────────────────────────────┘     │      │
│  └────────────────────────────────────────────────────┘      │
│                                                               │
└─────────────────────────────┬─────────────────────────────────┘
                               │
                               │ Actualizaciones de Telemetría
                               │ (cada 0.5s)
                               │
┌─────────────────────────────┼─────────────────────────────────┐
│                    CAPA DE SIMULACIÓN DE DRONES               │
│                                                               │
│  ┌────────────────────────────────────────────────────┐      │
│  │  drones/drone_manager.py::DroneManager             │      │
│  │  - Gestiona múltiples drones                       │      │
│  │  - Enruta telemetría a UI                          │      │
│  └───────────────┬──────────────────────────────────────┘      │
│                  │                                           │
│      ┌───────────┴───────────┐                               │
│      │                       │                               │
│      ▼                       ▼                               │
│  ┌──────────────┐    ┌──────────────┐                       │
│  │ FakeTelemetry│    │ MAVSDKSim    │                       │
│  │ Generator    │    │ (opcional)  │                       │
│  │ - Simulación │    │ - Conexión   │                       │
│  │   Matrice    │    │   MAVSDK     │                       │
│  │   300 RTK    │    │   real       │                       │
│  └──────────────┘    └──────────────┘                       │
│                                                               │
└───────────────────────────────────────────────────────────────┘
```

### Ciclo de Actualización de Telemetría (Bucle Continuo)

```
┌─────────────────────────────────────────────────────────────┐
│  FakeTelemetryGenerator (por dron)                          │
│                                                              │
│  Bucle cada 0.5 segundos:                                   │
│    1. _update_position()                                    │
│       - Calcular nueva lat/lon/alt                           │
│       - Actualizar heading, velocity                         │
│       - Simular drenaje de batería                           │
│                                                              │
│    2. _generate_telemetry()                                 │
│       - Crear diccionario de telemetría                      │
│       - Normalizar datos                                     │
│                                                              │
│    3. callback(telemetry) ────────────────────────────────┐│
└────────────────────────────────────────────────────────────┘│
                                                               │
                                                               │
┌─────────────────────────────────────────────────────────────┐│
│  DroneManager                                                ││
│                                                              ││
│  _on_telemetry_update(telemetry)                            ││
│    └─> telemetry_callback(telemetry) ──────────────────────┐││
└─────────────────────────────────────────────────────────────┘││
                                                                ││
┌─────────────────────────────────────────────────────────────┐││
│  main.py                                                     │││
│                                                              │││
│  on_telemetry_update(telemetry)                              │││
│    ├─> app.update_telemetry(telemetry) ────────────────────┐│││
│    └─> page.pubsub.send_all() (transmisión)                 ││││
└─────────────────────────────────────────────────────────────┘│││
                                                                 │││
┌─────────────────────────────────────────────────────────────┐│││
│  MainApp                                                     ││││
│                                                              ││││
│  update_telemetry(telemetry)                                 ││││
│    ├─> telemetry_panel.update_telemetry()                   ││││
│    │   - Actualizar tarjeta de dron                         ││││
│    │   - Refrescar UI                                        ││││
│    │                                                         ││││
│    ├─> _update_map_drones()                                 ││││
│    │   - Actualizar posiciones de drones en mapa             ││││
│    │   - Refrescar vista de mapa                             ││││
│    │                                                         ││││
│    └─> map_view.update_drone()                             ││││
│        - Regenerar mapa HTML con Folium                     ││││
│        - Actualizar marcadores de drones                    ││││
│        - Actualizar vista alternativa si aplica              ││││
└──────────────────────────────────────────────────────────────┘│││
                                                                  │││
                                                                  └┴┴┘
                                                              (Bucle)
```

---

## 6. Patrones de Diseño Clave

### 1. **Patrón Callback**
- Los drones usan callbacks para enviar actualizaciones de telemetría
- `FakeTelemetryGenerator` → `DroneManager` → `MainApp` → `Componentes UI`

### 2. **Patrón Observador (Pub/Sub)**
- Pub/sub de Flet para sincronización multi-cliente
- Eventos de telemetría y POI se transmiten a todos los suscriptores

### 3. **Patrón Singleton-like**
- `Config` y `POIStorage` se crean una vez y se comparten
- Asegura estado consistente entre componentes

### 4. **Patrón Factory**
- `DroneManager` crea múltiples instancias de `FakeTelemetryGenerator`
- Cada dron se crea con ID único y posición
- `MapView` crea marcadores dinámicamente

### 5. **Patrón Async/Await**
- Todas las operaciones de drones son async
- Permite que múltiples drones se ejecuten concurrentemente
- Actualizaciones de UI no bloqueantes

### 6. **Patrón Strategy**
- `MapView` usa estrategia diferente según plataforma (WebView vs Fallback)
- `MapView` usa estrategia diferente según disponibilidad (Folium vs HTML puro)

---

## 7. Estructuras de Datos

### Diccionario de Telemetría
```python
{
    "drone_id": "DRONE_000",
    "latitude": 20.9674,
    "longitude": -89.5926,
    "altitude": 50.5,
    "heading": 180.0,
    "velocity": 15.2,
    "battery": 85.3,
    "status": "flying",
    "timestamp": 1234567890.123,
    "vertical_speed": 2.0,      # Específico Matrice 300 RTK
    "rtk_fix": True,            # Específico Matrice 300 RTK
    "flight_time_remaining": 2800.0  # segundos
}
```

### Diccionario de POI
```python
{
    "id": "poi_1234567890",
    "latitude": 20.9750,
    "longitude": -89.6000,
    "type": "hazard",
    "description": "Zona de construcción",
    "timestamp": 1234567890.123,
    "created_by": "user"
}
```

---

## 8. Manejo de Errores

- **Carga de configuración**: Recurre a valores por defecto si el archivo no existe
- **Almacenamiento de POI**: Maneja errores de decodificación JSON con gracia
- **Simulación de drones**: Continúa incluso si un dron falla
- **Actualizaciones de UI**: Verifica None antes de actualizar componentes
- **Mapa HTML**: Valida coordenadas antes de agregar marcadores
- **WebView**: Detecta si no está soportado y usa vista alternativa automáticamente

---

## Resumen

El sistema sigue una **arquitectura en capas**:

1. **Punto de Entrada** (`main.py`) - Inicializa todo
2. **Capa UI** (`ui/`) - Maneja interfaz de usuario e interacciones, incluyendo mapa interactivo
3. **Capa de Simulación** (`drones/`) - Genera datos de telemetría
4. **Capa de Almacenamiento** (`backend/`) - Persiste datos de POI
5. **Capa Común** (`common/`) - Utilidades y configuración compartidas

Los datos fluyen **hacia arriba** desde los drones a la UI, y **hacia abajo** desde la UI al almacenamiento. Todos los componentes se comunican a través de **callbacks** y **pub/sub** para actualizaciones en tiempo real. El mapa interactivo se actualiza automáticamente con cada telemetría recibida, regenerando el HTML con Folium o JavaScript puro según disponibilidad.
