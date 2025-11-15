# Explicación Completa del Flujo de Trabajo - Sistema de Coordinación Multi-Dron

Este documento explica el flujo de trabajo completo entre todos los archivos de script del sistema, incluyendo la integración del mapa interactivo con actualizaciones incrementales.

## 📋 Tabla de Contenidos
1. [Flujo de Inicio de la Aplicación](#1-flujo-de-inicio-de-la-aplicación)
2. [Flujo de Datos en Tiempo de Ejecución](#2-flujo-de-datos-en-tiempo-de-ejecución)
3. [Flujo del Mapa Interactivo con Actualizaciones Incrementales](#3-flujo-del-mapa-interactivo-con-actualizaciones-incrementales)
4. [Interacciones de Componentes](#4-interacciones-de-componentes)
5. [Diagramas de Flujo de Datos](#5-diagramas-de-flujo-de-datos)
6. [Arquitectura del Servidor HTTP](#6-arquitectura-del-servidor-http)

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
│    - MapView inicia TelemetryServer en puerto 8765         │
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
│        - Actualiza TelemetryServer con nuevo POI             │
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
│        - Elimina POI del TelemetryServer                     │
│        - JavaScript en el mapa detecta el cambio vía polling│
└─────────────────────────────────────────────────────────────┘
```

---

## 3. Flujo del Mapa Interactivo con Actualizaciones Incrementales

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
│ 1. Iniciar TelemetryServer                                  │
│    self.telemetry_server = TelemetryServer(port=8765)     │
│    self.telemetry_server.start()                            │
│    - Servidor HTTP se ejecuta en hilo separado             │
│    - Endpoint: http://localhost:8765/api/data             │
│                                                              │
│ 2. _create_map()                                            │
│    ├─> Intenta usar Folium (si está disponible)            │
│    │   - Crea mapa Folium con OpenStreetMap                │
│    │   - Agrega JavaScript para polling                    │
│    │   - Guarda en archivo HTML temporal                   │
│    │                                                          │
│    └─> Si no hay Folium: _generate_map_html()               │
│        - Genera HTML con Leaflet.js desde CDN               │
│        - Incluye JavaScript para polling                    │
│        - Guarda en archivo HTML temporal                     │
│                                                              │
│ 3. _create_webview() o _create_fallback_view()             │
│    ├─> En Windows: Usa fallback directamente               │
│    │   - Vista alternativa con lista de drones/POIs        │
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
│ ui/map_view.py::MapView.update_drone()                     │
│                                                              │
│ 1. Almacenar telemetría en self.drones[drone_id]           │
│    - Cache local para referencia rápida                    │
│                                                              │
│ 2. Actualizar TelemetryServer                               │
│    self.telemetry_server.update_telemetry(telemetry)       │
│    - Actualiza almacén de datos en memoria (thread-safe)   │
│    - NO regenera HTML (evita recargas constantes)          │
│    - Los datos quedan disponibles para JavaScript           │
│                                                              │
│ 3. JavaScript en el mapa (polling cada 1 segundo)        │
│    - Hace fetch a http://localhost:8765/api/data           │
│    - Recibe JSON: {drones: {...}, pois: {...}}            │
│    - Para cada dron:                                        │
│      * Si marcador existe:                                  │
│        - marker.setLatLng([lat, lon]) para posición       │
│        - marker.setIcon(nuevo_icono) para color/rotación   │
│        - marker.setPopupContent(html) para información     │
│      * Si no existe:                                        │
│        - Crea nuevo marcador con L.marker()                │
│        - Agrega icono personalizado (circular con ✈)      │
│        - Guarda en window.droneMarkers[drone_id]          │
│    - Preserva zoom y centro usando localStorage             │
│    - Logs de depuración en consola del navegador           │
└─────────────────────────────────────────────────────────────┘
```

### Flujo de Polling JavaScript en el Mapa

```
┌─────────────────────────────────────────────────────────────┐
│ JavaScript en mapa HTML (cada 1 segundo)                 │
│                                                              │
│ 1. Inicialización (al cargar página)                        │
│    ├─> waitForMapReady()                                    │
│    │   - Busca objeto del mapa con findMapObject()          │
│    │   - Usa múltiples métodos de búsqueda                 │
│    │   - Cachea referencia en window.mapObject             │
│    │   - Establece window.mapReady = true cuando está listo│
│    │                                                          │
│    └─> Cuando mapa está listo:                              │
│        - Restaura estado (zoom/centro) desde localStorage  │
│        - Inicia polling: setInterval(updateFromServer, 1000)│
│                                                              │
│ 2. updateFromServer() (cada 1 segundo)                    │
│    ├─> fetch('http://localhost:8765/api/data')             │
│    │   - Solicita datos actualizados                        │
│    │   - Maneja errores de red con try-catch               │
│    │                                                          │
│    ├─> Recibe JSON: {drones: {...}, pois: {...}}          │
│    │                                                          │
│    ├─> Para cada dron en data.drones:                      │
│    │   - Valida coordenadas (lat, lon)                      │
│    │   - Si marcador existe en window.droneMarkers:        │
│    │     * marker.setLatLng([lat, lon])                     │
│    │     * marker.setIcon(createDroneIcon(color, heading))  │
│    │     * marker.setPopupContent(html_info)                │
│    │   - Si no existe:                                      │
│    │     * Crea icono circular con emoji ✈                  │
│    │     * Color según batería (verde/amarillo/rojo)       │
│    │     * Rotación según heading                           │
│    │     * Crea marcador: L.marker([lat, lon], {icon})      │
│    │     * Agrega al mapa: marker.addTo(map)                │
│    │     * Guarda: window.droneMarkers[drone_id] = marker   │
│    │                                                          │
│    └─> Para cada POI en data.pois:                         │
│        - Similar proceso para marcadores de POI            │
│                                                              │
│ 3. Preservar estado del mapa                                  │
│    - Guardar zoom y centro en localStorage periódicamente  │
│    - Restaurar al cargar la página                          │
│    - saveMapState() se llama en eventos de zoom/pan        │
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
│    - Abre archivo HTML en navegador predeterminado        │
│    - Muestra mapa interactivo con todos los marcadores      │
│    - JavaScript comienza polling automáticamente             │
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

ui/map_view.py
├── backend/data_server.py (TelemetryServer)
├── common/constants.py (POIType)
├── common/colors.py (Colores)
└── folium (opcional, para mapas)

backend/data_server.py
├── http.server (HTTPServer, BaseHTTPRequestHandler)
└── threading (Thread)

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

#### 3. **TelemetryServer** (`backend/data_server.py`)
- **Propósito**: Servidor HTTP para servir datos de telemetría y POIs en tiempo real
- **Responsabilidades**:
  - Ejecutar servidor HTTP en hilo separado (puerto 8765)
  - Mantener almacén de datos en memoria (drones y POIs)
  - Servir datos JSON vía endpoint `/api/data`
  - Permitir actualizaciones incrementales sin regenerar HTML

#### 4. **DroneManager** (`drones/drone_manager.py`)
- **Propósito**: Orquesta múltiples simulaciones de drones
- **Responsabilidades**:
  - Crear y gestionar múltiples instancias de drones
  - Enrutar actualizaciones de telemetría a UI
  - Manejar ciclo de vida de drones (iniciar/detener)

#### 5. **FakeTelemetryGenerator** (`drones/fake_generator.py`)
- **Propósito**: Simula comportamiento del dron Matrice 300 RTK
- **Responsabilidades**:
  - Generar datos de telemetría realistas
  - Simular física de vuelo
  - Actualizar posición, batería, estado
  - Llamar callback con actualizaciones de telemetría

#### 6. **MainApp** (`ui/main.py`)
- **Propósito**: Coordina todos los componentes UI
- **Responsabilidades**:
  - Configurar layout de página Flet
  - Manejar interacciones del usuario (creación/eliminación de POI)
  - Actualizar UI con datos de telemetría
  - Coordinar entre componentes UI (incluyendo MapView)

#### 7. **TelemetryPanel** (`ui/telemetry_panel.py`)
- **Propósito**: Mostrar telemetría de drones en UI
- **Responsabilidades**:
  - Mostrar telemetría en tiempo real para cada dron
  - Actualizar tarjetas de drones con nuevos datos
  - Mostrar batería, altitud, velocidad, estado RTK

#### 8. **POIManager** (`ui/poi_manager.py`)
- **Propósito**: Gestionar visualización e interacciones de POIs
- **Responsabilidades**:
  - Mostrar lista de POIs
  - Manejar creación de tarjetas de POI
  - Activar callbacks de eliminación de POI

#### 9. **MapView** (`ui/map_view.py`)
- **Propósito**: Gestionar visualización de mapa interactivo con actualizaciones incrementales
- **Responsabilidades**:
  - Crear mapa HTML con Folium o JavaScript puro
  - Iniciar y gestionar TelemetryServer (puerto 8765)
  - Actualizar TelemetryServer con nuevas telemetrías y POIs
  - Inyectar JavaScript para polling y actualización de marcadores
  - Gestionar vista alternativa cuando WebView no está disponible
  - Proporcionar botón para abrir mapa en navegador
  - Mantener cache local de drones y POIs para referencia rápida

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
│  │  │  - JavaScript polling (cada 0.5s)       │     │      │
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

┌─────────────────────────────────────────────────────────────┐
│              CAPA DE SERVIDOR HTTP (NUEVO)                   │
│                                                               │
│  ┌────────────────────────────────────────────────────┐     │
│  │  backend/data_server.py::TelemetryServer            │     │
│  │  - Servidor HTTP en hilo separado                  │     │
│  │  - Puerto: 8765                                     │     │
│  │  - Endpoint: /api/data                              │     │
│  │  - Almacén en memoria (drones y POIs)              │     │
│  │  - Sincronización thread-safe                       │     │
│  └────────────────────────────────────────────────────┘     │
│                                                               │
│  ┌────────────────────────────────────────────────────┐     │
│  │  JavaScript en mapa HTML                           │     │
│  │  - Polling cada 0.5s a /api/data                  │     │
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
│    │                                                         ││││
│    └─> map_view.update_drone()                             ││││
│        - Actualizar TelemetryServer                         ││││
│        - NO regenerar HTML (actualizaciones incrementales)   ││││
└──────────────────────────────────────────────────────────────┘│││
                                                                  │││
┌─────────────────────────────────────────────────────────────┐│││
│  TelemetryServer (Hilo Separado)                            ││││
│                                                              ││││
│  update_telemetry(telemetry)                                 ││││
│    - Almacenar en data_store.drones[drone_id]              ││││
│    - Thread-safe con lock                                   ││││
└──────────────────────────────────────────────────────────────┘│││
                                                                  │││
┌─────────────────────────────────────────────────────────────┐│││
│  JavaScript en Mapa HTML (Polling cada 0.5s)                ││││
│                                                              ││││
│  updateFromServer()                                          ││││
│    ├─> fetch('http://localhost:8765/api/data')              ││││
│    │   - Obtener datos actualizados                         ││││
│    │                                                         ││││
│    ├─> Recibir JSON: {drones: {...}, pois: {...}}         ││││
│    │                                                         ││││
│    └─> Actualizar marcadores Leaflet                       ││││
│        - setLatLng() para posición                          ││││
│        - setPopupContent() para información                 ││││
│        - setIcon() para color según batería                 ││││
│        - Crear nuevos marcadores si es necesario            ││││
└──────────────────────────────────────────────────────────────┘│││
                                                                  └┴┴┘
                                                              (Bucle)
```

---

## 6. Arquitectura del Servidor HTTP

### Componentes del Servidor HTTP

```
┌─────────────────────────────────────────────────────────────┐
│  TelemetryServer (backend/data_server.py)                   │
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

## 7. Patrones de Diseño Clave

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
- JavaScript en el mapa hace polling al servidor HTTP cada 1 segundo
- Permite actualizaciones incrementales sin recargar la página
- Evita problemas de recarga constante del mapa
- El servidor HTTP actúa como intermediario entre Python y JavaScript
- Los datos se almacenan en memoria (thread-safe) y se sirven como JSON

### 8. **Patrón Thread-Safe Data Store**
- `TelemetryDataStore` usa locks para acceso thread-safe
- Permite que múltiples hilos (Python y JavaScript) accedan a los datos de forma segura

---

## 8. Estructuras de Datos

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

## 9. Manejo de Errores

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

El sistema sigue una **arquitectura en capas** con actualizaciones incrementales:

1. **Punto de Entrada** (`main.py`) - Inicializa todo
2. **Capa UI** (`ui/`) - Maneja interfaz de usuario e interacciones, incluyendo mapa interactivo
3. **Capa de Simulación** (`drones/`) - Genera datos de telemetría
4. **Capa de Almacenamiento** (`backend/`) - Persiste datos de POI y sirve datos en tiempo real
5. **Capa Común** (`common/`) - Utilidades y configuración compartidas

Los datos fluyen **hacia arriba** desde los drones a la UI, y **hacia abajo** desde la UI al almacenamiento. Todos los componentes se comunican a través de **callbacks** y **pub/sub** para actualizaciones en tiempo real. El mapa interactivo se actualiza automáticamente con cada telemetría recibida usando un **servidor HTTP interno** y **polling JavaScript**, evitando recargas constantes de la página y proporcionando una experiencia de usuario fluida.

El **TelemetryServer** actúa como intermediario entre el backend Python y el frontend JavaScript, permitiendo actualizaciones incrementales sin regenerar el HTML completo, lo que resuelve el problema de recargas constantes del mapa.

## Scripts de Desarrollo

Para verificar el setup y diagnosticar problemas:

- **`setup.py`** - Setup automático del proyecto (crea venv, instala dependencias)
- **`setup_check.py`** - Verificación completa: Python, entorno virtual, dependencias, estructura, imports
- **`diagnostico.py`** - Diagnóstico del sistema en tiempo de ejecución

Ejecutar antes de desarrollar o hacer commit para asegurar que todo esté configurado correctamente.