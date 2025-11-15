# Explicación Completa del Flujo de Trabajo - Sistema de Coordinación Multi-Dron

Este documento explica el flujo de trabajo completo entre todos los archivos de script del sistema, incluyendo la integración del mapa interactivo con actualizaciones incrementales.

## 📋 Tabla de Contenidos
1. [Flujo de Inicio de la Aplicación](#1-flujo-de-inicio-de-la-aplicación)
2. [Flujo de Datos en Tiempo de Ejecución](#2-flujo-de-datos-en-tiempo-de-ejecución)
3. [Flujo del Mapa Interactivo con Actualizaciones Incrementales](#3-flujo-del-mapa-interactivo-con-actualizaciones-incrementales)
4. [Interacciones de Componentes](#4-interacciones-de-componentes)
5. [Diagramas de Flujo de Datos](#5-diagramas-de-flujo-de-datos)
6. [Arquitectura del Servidor HTTP](#6-arquitectura-del-servidor-http)
7. [Arquitectura Limpia](#7-arquitectura-limpia)

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
│ 5. Crear Adaptadores de Salida (Secondary Adapters)        │
│    - JsonPOIRepository(poi_storage_file)                    │
│      Implementa IPOIRepository                              │
│    - FakeDroneAdapter(initial_lat, initial_lon)             │
│      Implementa IDroneRepository                            │
└──────────────────────┬──────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│ 6. Crear Casos de Uso (inyectar adaptadores de salida)     │
│    - StartDronesUseCase(drone_repository)                   │
│    - StopDronesUseCase(drone_repository)                    │
│    - GetDroneListUseCase(drone_repository)                  │
│    - CreatePOIUseCase(poi_repository)                       │
│    - DeletePOIUseCase(poi_repository)                       │
│    - GetAllPOIsUseCase(poi_repository)                      │
│    - etc.                                                    │
└──────────────────────┬──────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│ 7. Crear Servicios (inyectar casos de uso)                  │
│    - DroneService(use_cases...)                             │
│      Implementa IDroneService                               │
│    - POIService(use_cases...)                               │
│      Implementa IPOIService                                 │
└──────────────────────┬──────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│ 8. Crear Adaptador de Entrada (inyectar servicios)         │
│    app = MainApp(config, drone_service, poi_service, page) │
│    - Crea instancia de TelemetryPanel                       │
│    - Crea instancia de POIManager                           │
│    - Crea instancia de MapView                              │
│    - MapView inicia TelemetryServer en puerto 8765         │
│    - Carga POIs existentes usando poi_service               │
└──────────────────────┬──────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│ 9. Configurar Página Flet (app.setup_page(page))           │
│    - Establece título y tamaño de ventana                   │
│    - Crea layout principal (mapa + panel lateral)          │
│    - Configura suscripciones pub/sub                       │
└──────────────────────┬──────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│ 10. Iniciar Simulación de Drones (Tarea en Segundo Plano) │
│     drone_task = asyncio.create_task(run_drones())          │
│     - Se ejecuta en tarea async en segundo plano            │
│     - Llama: drone_service.start_drones(count, callback)   │
└──────────────────────┬──────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│ 11. FakeDroneAdapter::start_drones()                       │
│     - Crea múltiples instancias FakeTelemetryGenerator      │
│     - Distribuye drones en cuadrícula                      │
│     - Inicia cada generador con callback                    │
│     - Cada generador actualiza telemetría cada 0.5s         │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. Flujo de Datos en Tiempo de Ejecución

### Flujo de Actualización de Telemetría (Cada 0.5 segundos por dron)

```
┌─────────────────────────────────────────────────────────────┐
│ adapters/output/simulation/fake_drone_adapter.py            │
│ FakeTelemetryGenerator                                      │
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
│    - Normaliza datos usando infrastructure/config/utils.py  │
│    - Llama: self.callback(telemetry)                        │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       │ callback(telemetry)
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
│ adapters/input/flet/main_app.py::MainApp                    │
│                                                              │
│ update_telemetry(telemetry)                                  │
│    ├─> telemetry_panel.update_telemetry(telemetry)          │
│    │   - Actualiza tarjeta de dron en panel lateral         │
│    │   - Muestra: batería, altitud, velocidad, estado RTK   │
│    │                                                          │
│    └─> map_view.update_drone(telemetry)                     │
│        - Actualiza TelemetryServer con nueva telemetría     │
│        - NO regenera HTML (actualizaciones incrementales)    │
│        - JavaScript en el mapa hace polling al servidor     │
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
│ adapters/input/flet/main_app.py::MainApp                    │
│                                                              │
│ _on_add_poi_button_click()                                  │
│    - Muestra diálogo con: lat, lon, tipo, descripción       │
│    - Usuario completa detalles                             │
└──────────────────────┬──────────────────────────────────────┘
                        │
                        │ Usuario hace clic en "Crear"
                        ▼
┌─────────────────────────────────────────────────────────────┐
│ adapters/input/flet/main_app.py::MainApp                   │
│                                                              │
│ create_poi() (dentro del diálogo)                           │
│    ├─> poi_service.create_poi(lat, lon, type, desc)        │
│    │   - Usa CreatePOIUseCase                               │
│    │   - CreatePOIUseCase usa poi_repository.add()          │
│    │   - poi_repository guarda en pois.json                 │
│    │                                                          │
│    ├─> poi_manager.add_poi(poi_dto)                         │
│    │   - Agrega POI a lista UI                              │
│    │   - Crea tarjeta de POI en panel lateral                │
│    │                                                          │
│    ├─> map_view.add_poi(poi_dto)                            │
│    │   - Actualiza TelemetryServer con nuevo POI             │
│    │                                                          │
│    └─> page.pubsub.send_all()                               │
│        - Transmite evento de creación de POI                 │
│        - Tema: CHANNEL_POI                                   │
│        - JavaScript en el mapa detecta el cambio vía polling│
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
│ adapters/input/flet/poi_manager.py::POIManager             │
│                                                              │
│ _on_delete(poi_id)                                           │
│    - Llama: self.on_delete_poi(poi_id)                      │
└──────────────────────┬──────────────────────────────────────┘
                        │
                        │ callback
                        ▼
┌─────────────────────────────────────────────────────────────┐
│ adapters/input/flet/main_app.py::MainApp                    │
│                                                              │
│ _on_delete_poi(poi_id)                                       │
│    ├─> poi_service.delete_poi(poi_id)                       │
│    │   - Usa DeletePOIUseCase                               │
│    │   - DeletePOIUseCase usa poi_repository.remove()       │
│    │   - poi_repository elimina de pois.json                │
│    │                                                          │
│    ├─> poi_manager.remove_poi(poi_id)                       │
│    │   - Elimina de lista UI                                │
│    │                                                          │
│    ├─> map_view.remove_poi(poi_id)                          │
│    │   - Elimina POI del TelemetryServer                     │
│    │                                                          │
│    └─> page.pubsub.send_all()                               │
│        - Transmite evento de eliminación de POI             │
│        - JavaScript en el mapa detecta el cambio vía polling│
└─────────────────────────────────────────────────────────────┘
```

---

## 3. Flujo del Mapa Interactivo con Actualizaciones Incrementales

### Inicialización del Mapa

```
┌─────────────────────────────────────────────────────────────┐
│ adapters/input/flet/main_app.py::MainApp                    │
│                                                              │
│ 1. Crear instancia MapView                                  │
│    map_view = MapView(                                      │
│        initial_lat, initial_lon, zoom                       │
│    )                                                        │
└──────────────────────┬──────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│ adapters/input/flet/map_view.py::MapView.__init__()        │
│                                                              │
│ 1. Iniciar TelemetryServer                                  │
│    self.telemetry_server = TelemetryServer(port=8765)       │
│    self.telemetry_server.start()                            │
│    - Servidor HTTP se ejecuta en hilo separado             │
│    - Endpoint: http://localhost:8765/api/data               │
│                                                              │
│ 2. _create_map()                                            │
│    ├─> Intenta usar Folium (si está disponible)            │
│    │   - Crea mapa Folium con OpenStreetMap                 │
│    │   - Agrega JavaScript para polling                    │
│    │   - Guarda en archivo HTML temporal                   │
│    │                                                          │
│    └─> Si no hay Folium: _create_leaflet_map()              │
│        - Genera HTML con Leaflet.js desde CDN               │
│        - Incluye JavaScript para polling                    │
│        - Guarda en archivo HTML temporal                     │
│                                                              │
│ 3. _create_view()                                           │
│    ├─> En Windows: Usa fallback directamente                │
│    │   - Vista alternativa con lista de drones/POIs         │
│    │   - Botón para abrir mapa en navegador                 │
│    │                                                          │
│    └─> En otras plataformas: Intenta WebView               │
│        - Carga archivo HTML en WebView de Flet              │
│        - JavaScript comienza polling automáticamente         │
└─────────────────────────────────────────────────────────────┘
```

### Actualización del Mapa con Telemetría (Actualizaciones Incrementales)

```
┌─────────────────────────────────────────────────────────────┐
│ adapters/input/flet/map_view.py::MapView                   │
│                                                              │
│ update_drone(telemetry)                                      │
│    1. Almacenar telemetría en self.drones[drone_id]         │
│                                                              │
│    2. Actualizar TelemetryServer                            │
│       self.telemetry_server.update_telemetry(telemetry)      │
│       - Actualiza almacén de datos en memoria                │
│       - NO regenera HTML (evita recargas)                    │
│                                                              │
│    3. JavaScript en el mapa (polling cada 1s)                │
│       - Hace fetch a http://localhost:8765/api/data         │
│       - Recibe JSON con drones y POIs actualizados           │
│       - Actualiza marcadores existentes usando Leaflet.js    │
│         * setLatLng() para posición                         │
│         * setPopupContent() para información                │
│         * setIcon() para color según batería                │
│       - Crea nuevos marcadores si el dron es nuevo          │
│       - Preserva zoom y centro usando localStorage           │
└─────────────────────────────────────────────────────────────┘
```

### Flujo de Polling JavaScript en el Mapa

```
┌─────────────────────────────────────────────────────────────┐
│ JavaScript en mapa HTML (cada 1 segundo)                   │
│                                                              │
│ 1. setInterval(updateFromServer, 1000)                     │
│                                                              │
│ 2. updateFromServer()                                       │
│    ├─> fetch('http://localhost:8765/api/data')             │
│    │   - Solicita datos actualizados                        │
│    │                                                          │
│    ├─> Recibe JSON: {drones: {...}, pois: {...}}          │
│    │                                                          │
│    ├─> Para cada dron en data.drones:                      │
│    │   - Si marcador existe: actualizar posición/icono      │
│    │   - Si no existe: crear nuevo marcador                 │
│    │   - Actualizar popup con nueva información             │
│    │                                                          │
│    └─> Para cada POI en data.pois:                         │
│        - Si marcador existe: actualizar posición            │
│        - Si no existe: crear nuevo marcador                  │
│        - Actualizar popup con información                   │
│                                                              │
│ 3. Preservar estado del mapa                                │
│    - Guardar zoom y centro en localStorage                 │
│    - Restaurar al cargar la página                          │
└─────────────────────────────────────────────────────────────┘
```

---

## 4. Interacciones de Componentes

### Mapa de Dependencias de Archivos (Nueva Estructura)

```
main.py (Wire Up)
├── infrastructure/config/config.py (Config)
├── adapters/output/persistence/json_poi_repository.py (IPOIRepository)
├── adapters/output/simulation/fake_drone_adapter.py (IDroneRepository)
├── application/use_cases/ (Casos de uso)
├── application/services/ (Servicios que implementan puertos de entrada)
└── adapters/input/flet/main_app.py (MainApp)
    ├── adapters/input/flet/telemetry_panel.py
    ├── adapters/input/flet/poi_manager.py
    └── adapters/input/flet/map_view.py

adapters/input/flet/map_view.py
├── adapters/output/http/telemetry_server.py (TelemetryServer)
├── infrastructure/config/constants.py (POIType)
└── folium (opcional, para mapas)

adapters/output/http/telemetry_server.py
├── http.server (HTTPServer, BaseHTTPRequestHandler)
└── threading (Thread)

adapters/output/simulation/fake_drone_adapter.py
├── infrastructure/config/utils.py (generate_drone_id, normalize_telemetry)
├── infrastructure/config/constants.py (DroneStatus)
└── FakeTelemetryGenerator (clase interna)

adapters/output/persistence/json_poi_repository.py
├── domain/ports/output/poi_repository_port.py (IPOIRepository)
└── infrastructure/config/config.py (Config - para ruta de archivo)

adapters/input/flet/main_app.py
├── domain/ports/input/drone_service_port.py (IDroneService)
├── domain/ports/input/poi_service_port.py (IPOIService)
├── infrastructure/config/config.py (Config)
├── infrastructure/config/constants.py (POIType, CHANNEL_*)
├── adapters/input/flet/telemetry_panel.py
├── adapters/input/flet/poi_manager.py
└── adapters/input/flet/map_view.py
```

### Clases Clave y Sus Responsabilidades

#### 1. **Config** (`infrastructure/config/config.py`)
- **Propósito**: Gestión de configuración de la aplicación
- **Responsabilidades**:
  - Cargar/guardar configuración desde JSON
  - Almacenar valores por defecto (incluyendo coordenadas de Mérida, Yucatán)
  - Proporcionar configuraciones a todos los componentes

#### 2. **JsonPOIRepository** (`adapters/output/persistence/json_poi_repository.py`)
- **Propósito**: Implementación del repositorio de POIs usando almacenamiento JSON
- **Responsabilidades**:
  - Implementa la interfaz `IPOIRepository` del dominio
  - Cargar POIs desde archivo JSON al iniciar
  - Guardar POIs en archivo JSON al cambiar
  - Operaciones CRUD para POIs

#### 3. **TelemetryServer** (`adapters/output/http/telemetry_server.py`)
- **Propósito**: Servidor HTTP para servir datos de telemetría y POIs en tiempo real
- **Responsabilidades**:
  - Ejecutar servidor HTTP en hilo separado (puerto 8765)
  - Mantener almacén de datos en memoria (drones y POIs)
  - Servir datos JSON vía endpoint `/api/data`
  - Permitir actualizaciones incrementales sin regenerar HTML

#### 4. **FakeDroneAdapter** (`adapters/output/simulation/fake_drone_adapter.py`)
- **Propósito**: Implementa `IDroneRepository` usando simulación falsa
- **Responsabilidades**:
  - Crear y gestionar múltiples instancias de drones simulados
  - Implementar `start_drones()`, `stop_drones()`, `get_drone_list()`
  - Enrutar actualizaciones de telemetría a callback

#### 5. **FakeTelemetryGenerator** (`adapters/output/simulation/fake_drone_adapter.py`)
- **Propósito**: Simula comportamiento del dron Matrice 300 RTK
- **Responsabilidades**:
  - Generar datos de telemetría realistas
  - Simular física de vuelo
  - Actualizar posición, batería, estado
  - Llamar callback con actualizaciones de telemetría

#### 6. **Casos de Uso** (`application/use_cases/`)
- **Propósito**: Orquestar lógica de negocio específica
- **Responsabilidades**:
  - `StartDronesUseCase`: Validar y iniciar drones
  - `CreatePOIUseCase`: Validar y crear POIs
  - `DeletePOIUseCase`: Eliminar POIs
  - Otros casos de uso específicos

#### 7. **DroneService** (`application/services/drone_service.py`)
- **Propósito**: Implementa `IDroneService` (puerto de entrada)
- **Responsabilidades**:
  - Orquestar casos de uso de drones
  - Proporcionar interfaz unificada para operaciones con drones

#### 8. **POIService** (`application/services/poi_service.py`)
- **Propósito**: Implementa `IPOIService` (puerto de entrada)
- **Responsabilidades**:
  - Orquestar casos de uso de POIs
  - Proporcionar interfaz unificada para operaciones con POIs

#### 9. **MainApp** (`adapters/input/flet/main_app.py`)
- **Propósito**: Adaptador de entrada - Coordina todos los componentes UI
- **Responsabilidades**:
  - Usa `IDroneService` e `IPOIService` (puertos de entrada)
  - Configurar layout de página Flet
  - Manejar interacciones del usuario (creación/eliminación de POI)
  - Actualizar UI con datos de telemetría
  - Coordinar entre componentes UI (incluyendo MapView)

#### 10. **TelemetryPanel** (`adapters/input/flet/telemetry_panel.py`)
- **Propósito**: Panel de telemetría de drones
- **Responsabilidades**:
  - Mostrar telemetría en tiempo real para cada dron
  - Actualizar tarjetas de drones con nuevos datos
  - Mostrar batería, altitud, velocidad, estado RTK
  - Panel scrolleable para múltiples drones

#### 11. **POIManager** (`adapters/input/flet/poi_manager.py`)
- **Propósito**: Gestor de POIs en UI
- **Responsabilidades**:
  - Mostrar lista de POIs
  - Manejar creación de tarjetas de POI
  - Activar callbacks de eliminación de POI
  - Panel scrolleable para múltiples POIs

#### 12. **MapView** (`adapters/input/flet/map_view.py`)
- **Propósito**: Vista del mapa interactivo con actualizaciones incrementales
- **Responsabilidades**:
  - Crear mapa HTML con Folium o JavaScript puro
  - Iniciar y gestionar TelemetryServer
  - Actualizar TelemetryServer con nuevas telemetrías y POIs
  - Generar HTML con JavaScript para polling
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
│  ┌──────────┐         ┌──────────────────┐                  │
│  │  Config  │         │ JsonPOIRepository│                  │
│  │(infra)   │         │ (adapters/output)│                  │
│  └──────────┘         └────┬─────────────┘                  │
│                             │                                 │
└─────────────────────────────┼─────────────────────────────────┘
                               │
                               │
┌─────────────────────────────┼─────────────────────────────────┐
│                    CAPA UI (Flet)                            │
│                                                               │
│  ┌────────────────────────────────────────────────────┐      │
│  │  adapters/input/flet/main_app.py::MainApp          │      │
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
│  │  │  - JavaScript polling (cada 1s)         │     │      │
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
│  │  adapters/output/simulation/fake_drone_adapter.py   │      │
│  │  FakeDroneAdapter (implementa IDroneRepository)     │      │
│  │  - Gestiona múltiples drones simulados              │      │
│  │  - Enruta telemetría a callback                     │      │
│  └───────────────┬──────────────────────────────────────┘      │
│                  │                                           │
│                  ▼                                           │
│  ┌────────────────────────────────────────────────────┐      │
│  │  FakeTelemetryGenerator (por dron)                  │      │
│  │  - Simulación Matrice 300 RTK                       │      │
│  │  - Genera telemetría realista                       │      │
│  │  - Llama callback con actualizaciones               │      │
│  └────────────────────────────────────────────────────┘      │
│                                                               │
└───────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│              CAPA DE SERVIDOR HTTP                           │
│                                                               │
│  ┌────────────────────────────────────────────────────┐     │
│  │  adapters/output/http/telemetry_server.py          │     │
│  │  TelemetryServer                                    │     │
│  │  - Servidor HTTP en hilo separado                  │     │
│  │  - Puerto: 8765                                     │     │
│  │  - Endpoint: /api/data                              │     │
│  │  - Almacén en memoria (drones y POIs)              │     │
│  │  - Sincronización thread-safe                       │     │
│  └────────────────────────────────────────────────────┘     │
│                                                               │
│  ┌────────────────────────────────────────────────────┐     │
│  │  JavaScript en mapa HTML                           │     │
│  │  - Polling cada 1s a /api/data                    │     │
│  │  - Actualiza marcadores Leaflet incrementalmente   │     │
│  │  - Preserva estado del mapa (localStorage)         │     │
│  └────────────────────────────────────────────────────┘     │
└───────────────────────────────────────────────────────────────┘
```

### Ciclo de Actualización de Telemetría (Bucle Continuo con Servidor HTTP)

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
┌─────────────────────────────────────────────────────────────┐│
│  main.py                                                     ││
│                                                              ││
│  on_telemetry_update(telemetry)                              ││
│    ├─> app.update_telemetry(telemetry) ────────────────────┐││
│    └─> page.pubsub.send_all() (transmisión)                 │││
└─────────────────────────────────────────────────────────────┘││
                                                                ││
┌─────────────────────────────────────────────────────────────┐││
│  adapters/input/flet/main_app.py::MainApp                  │││
│                                                              │││
│  update_telemetry(telemetry)                                 │││
│    ├─> telemetry_panel.update_telemetry()                   │││
│    │   - Actualizar tarjeta de dron                         │││
│    │   - Refrescar UI                                        │││
│    │                                                         │││
│    └─> map_view.update_drone()                              │││
│        - Actualizar TelemetryServer                         │││
│        - NO regenerar HTML (actualizaciones incrementales)   │││
└──────────────────────────────────────────────────────────────┘││
                                                                 ││
┌─────────────────────────────────────────────────────────────┐││
│  adapters/output/http/telemetry_server.py                   │││
│  TelemetryServer (Hilo Separado)                            │││
│                                                              │││
│  update_telemetry(telemetry)                                 │││
│    - Almacenar en data_store.drones[drone_id]              │││
│    - Thread-safe con lock                                   │││
└──────────────────────────────────────────────────────────────┘││
                                                                 ││
┌─────────────────────────────────────────────────────────────┐││
│  JavaScript en Mapa HTML (Polling cada 1s)                 │││
│                                                              │││
│  updateFromServer()                                          │││
│    ├─> fetch('http://localhost:8765/api/data')              │││
│    │   - Obtener datos actualizados                         │││
│    │                                                         │││
│    ├─> Recibir JSON: {drones: {...}, pois: {...}}         │││
│    │                                                         │││
│    └─> Actualizar marcadores Leaflet                       │││
│        - setLatLng() para posición                          │││
│        - setPopupContent() para información                 │││
│        - setIcon() para color según batería                 │││
│        - Crear nuevos marcadores si es necesario            │││
└──────────────────────────────────────────────────────────────┘││
                                                                 └┘
                                                              (Bucle)
```

---

## 6. Arquitectura del Servidor HTTP

### Componentes del Servidor HTTP

```
┌─────────────────────────────────────────────────────────────┐
│  TelemetryServer (adapters/output/http/telemetry_server.py) │
│                                                              │
│  ┌────────────────────────────────────────────────────┐   │
│  │  TelemetryDataStore                                │   │
│  │  - self.drones: Dict[str, Dict]                    │   │
│  │  - self.pois: Dict[str, Dict]                      │   │
│  │  - self.lock: threading.Lock (thread-safe)        │   │
│  └────────────────────────────────────────────────────┘   │
│                                                              │
│  ┌────────────────────────────────────────────────────┐   │
│  │  TelemetryDataHandler                               │   │
│  │  - do_GET(): Maneja peticiones HTTP                 │   │
│  │  - /api/data: Retorna {drones: {...}, pois: {...}} │   │
│  │  - CORS habilitado para JavaScript                  │   │
│  └────────────────────────────────────────────────────┘   │
│                                                              │
│  ┌────────────────────────────────────────────────────┐   │
│  │  HTTPServer                                         │   │
│  │  - Puerto: 8765                                     │   │
│  │  - Hilo separado (daemon=True)                      │   │
│  │  - Se detiene automáticamente al cerrar app        │   │
│  └────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### Flujo de Datos del Servidor HTTP

```
┌─────────────────────────────────────────────────────────────┐
│  Actualización de Telemetría                                 │
│                                                              │
│  adapters/input/flet/map_view.py::MapView                   │
│  map_view.update_drone(telemetry)                           │
│    └─> telemetry_server.update_telemetry(telemetry)         │
│        └─> data_store.update_telemetry(telemetry)          │
│            - Con lock: data_store.drones[drone_id] = telemetry│
└─────────────────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│  Petición HTTP desde JavaScript                              │
│                                                              │
│  fetch('http://localhost:8765/api/data')                    │
│    └─> TelemetryDataHandler.do_GET()                        │
│        └─> data_store.get_all_data()                        │
│            - Con lock: return {drones: {...}, pois: {...}}  │
│        └─> _send_json_response(data)                        │
│            - CORS headers                                    │
│            - JSON response                                    │
└─────────────────────────────────────────────────────────────┘
```

---

## 7. Arquitectura Hexagonal (Ports and Adapters)

### Estructura de Capas

El proyecto sigue una **Arquitectura Hexagonal (Ports and Adapters)** que garantiza máxima flexibilidad y escalabilidad:

```
┌─────────────────────────────────────────────────────────────┐
│                    DOMAIN (Núcleo)                          │
│                    Sin dependencias externas                 │
│                                                              │
│  domain/entities/                                            │
│  - drone.py: Entidad de dron                                 │
│  - telemetry.py: Entidad de telemetría                       │
│  - poi.py: Entidad de punto de interés                       │
│                                                              │
│  domain/ports/input/                                         │
│  - IDroneService: Puerto de entrada (casos de uso)          │
│  - IPOIService: Puerto de entrada (casos de uso)           │
│                                                              │
│  domain/ports/output/                                        │
│  - IDroneRepository: Puerto de salida (repositorios)        │
│  - IPOIRepository: Puerto de salida (repositorios)          │
│  - ITelemetryRepository: Puerto de salida (repositorios)    │
└─────────────────────────────────────────────────────────────┘
                        ▲
                        │
┌───────────────────────┴───────────────────────────────────────┐
│                    APPLICATION (Casos de Uso)                 │
│                    Depende solo de Domain                      │
│                                                               │
│  application/use_cases/                                       │
│  - drone/: start_drones, stop_drones, get_drone_list         │
│  - poi/: create_poi, delete_poi, get_all_pois, etc.          │
│                                                               │
│  application/mappers/                                         │
│  - TelemetryMapper, POIMapper                                 │
│                                                               │
│  application/services/                                       │
│  - DroneService: Implementa IDroneService                     │
│  - POIService: Implementa IPOIService                        │
│                                                               │
│  app/dtos.py                                                  │
│  - TelemetryDTO, POIDTO                                       │
└───────────────────────────────────────────────────────────────┘
                        ▲
                        │
┌───────────────────────┴───────────────────────────────────────┐
│                    ADAPTERS (Implementaciones)              │
│                    Dependen de Domain y Application          │
│                                                               │
│  adapters/output/ (Secondary Adapters)                       │
│  - persistence/json_poi_repository.py: Implementa IPOIRepository│
│  - simulation/fake_drone_adapter.py: Implementa IDroneRepository│
│  - http/telemetry_server.py: Servidor HTTP                  │
│                                                               │
│  adapters/input/flet/ (Primary Adapters)                     │
│  - main_app.py: Orquestador UI (usa IDroneService, IPOIService)│
│  - telemetry_panel.py: Panel de telemetría                   │
│  - poi_manager.py: Gestor de POIs                            │
│  - map_view.py: Vista del mapa                               │
│                                                               │
│  infrastructure/config/                                      │
│  - config.py, constants.py, colors.py, utils.py              │
└───────────────────────────────────────────────────────────────┘
```

### Flujo de Dependencias (Inversión de Dependencias)

```
Domain (sin dependencias)
    ↑
    │
Application (depende de Domain)
    ↑
    │
Adapters (dependen de Domain y Application)
    ↑
    │
main.py (Wire Up - composición de dependencias)
```

**Principio**: El dominio define los puertos (interfaces). Los adaptadores implementan estos puertos. Los casos de uso orquestan la lógica usando los puertos. El wire up en `main.py` compone todas las dependencias.

### Ventajas de la Arquitectura Hexagonal

1. **Máxima Modularidad**: El dominio es completamente independiente de implementaciones
2. **Flexibilidad**: Fácil cambiar adaptadores (JSON → DB, Flet → Web) sin afectar lógica
3. **Escalabilidad**: Fácil agregar nuevos casos de uso o adaptadores
4. **Testabilidad**: Fácil testear con mocks de los puertos
5. **Mantenibilidad**: Cambios en infraestructura no afectan la lógica de negocio
6. **Compatibilidad Python 3.14**: Preparado para el futuro sin GIL

---

## 8. Patrones de Diseño Clave

### 1. **Patrón Callback**
- Los drones usan callbacks para enviar actualizaciones de telemetría
- `FakeTelemetryGenerator` → `DroneManager` → `MainApp` → `Componentes UI`

### 2. **Patrón Observador (Pub/Sub)**
- Pub/sub de Flet para sincronización multi-cliente
- Eventos de telemetría y POI se transmiten a todos los suscriptores

### 3. **Patrón Singleton-like**
- `Config` y `POIStorage` se crean una vez y se comparten
- `TelemetryServer` se crea una vez por instancia de `MapView`
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

### 7. **Patrón Polling**
- JavaScript en el mapa hace polling al servidor HTTP cada 1s
- Permite actualizaciones incrementales sin recargar la página
- Evita problemas de recarga constante del mapa

### 8. **Patrón Thread-Safe Data Store**
- `TelemetryDataStore` usa locks para acceso thread-safe
- Permite que múltiples hilos (Python y JavaScript) accedan a los datos de forma segura

### 9. **Patrón Repository**
- `POIRepositoryImpl` implementa `IPOIRepository` del dominio
- Separa la lógica de negocio de los detalles de almacenamiento
- Facilita cambiar de JSON a base de datos en el futuro

---

## 9. Estructuras de Datos

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

### Respuesta del Servidor HTTP (/api/data)
```json
{
    "drones": {
        "DRONE_000": {
            "drone_id": "DRONE_000",
            "latitude": 20.9674,
            "longitude": -89.5926,
            "altitude": 50.5,
            "heading": 180.0,
            "velocity": 15.2,
            "battery": 85.3,
            "status": "flying",
            "timestamp": 1234567890.123
        },
        "DRONE_001": { ... }
    },
    "pois": {
        "poi_1234567890": {
            "id": "poi_1234567890",
            "latitude": 20.9750,
            "longitude": -89.6000,
            "type": "hazard",
            "description": "Zona de construcción",
            "timestamp": 1234567890.123
        }
    }
}
```

---

## 10. Manejo de Errores

- **Carga de configuración**: Recurre a valores por defecto si el archivo no existe
- **Almacenamiento de POI**: Maneja errores de decodificación JSON con gracia
- **Simulación de drones**: Continúa incluso si un dron falla
- **Actualizaciones de UI**: Verifica None antes de actualizar componentes
- **Mapa HTML**: Valida coordenadas antes de agregar marcadores
- **WebView**: Detecta si no está soportado y usa vista alternativa automáticamente
- **Servidor HTTP**: Maneja errores de conexión y continúa funcionando
- **Polling JavaScript**: Maneja errores de red y continúa intentando

---

## Resumen

El sistema sigue una **Arquitectura Hexagonal (Ports and Adapters)** con actualizaciones incrementales:

1. **Punto de Entrada** (`main.py`) - Wire up de todas las dependencias
2. **Capa Domain** (`domain/`) - Define entidades y puertos (interfaces) sin dependencias
3. **Capa Application** (`application/`) - Contiene casos de uso, mappers y servicios
4. **Capa Adapters** (`adapters/`) - Implementaciones concretas (UI, repositorios, simulación, servidores)
5. **Capa Infrastructure** (`infrastructure/`) - Configuración y utilidades compartidas

Los datos fluyen **hacia arriba** desde los drones (adaptadores de salida) a la UI (adaptadores de entrada), y **hacia abajo** desde la UI al almacenamiento. Todos los componentes se comunican a través de **callbacks** y **pub/sub** para actualizaciones en tiempo real. El mapa interactivo se actualiza automáticamente con cada telemetría recibida usando un **servidor HTTP interno** y **polling JavaScript**, evitando recargas constantes de la página y proporcionando una experiencia de usuario fluida.

El **TelemetryServer** actúa como intermediario entre el backend Python y el frontend JavaScript, permitiendo actualizaciones incrementales sin regenerar el HTML completo, lo que resuelve el problema de recargas constantes del mapa.

La **Arquitectura Hexagonal** garantiza que:
- El dominio no depende de nada externo (núcleo independiente)
- La aplicación solo depende del dominio (casos de uso usan puertos)
- Los adaptadores implementan los puertos del dominio (inversión de dependencias)
- Es fácil cambiar adaptadores (JSON → DB, Flet → Web) sin afectar la lógica de negocio
- El código es altamente testeable y mantenible
- Máxima flexibilidad y escalabilidad
