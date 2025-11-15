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
- **Arquitectura Ligera**: Diseño simple y modular perfecto para desarrollo en hackathon
- **Modo Telemetría Falsa**: Probar sin configuración MAVSDK usando el simulador Matrice 300 RTK integrado
- **Compilación Multiplataforma**: Compilar como ejecutable para Windows, macOS, Linux, Android e iOS

## Arquitectura

```
project_root/
├── drones/              # Capa de simulación de drones
│   ├── simulator.py     # Simulación basada en MAVSDK
│   ├── fake_generator.py # Generador de telemetría falsa
│   └── drone_manager.py # Gestiona múltiples drones
│
├── backend/             # Servicios backend
│   ├── storage.py       # Persistencia de POIs
│   ├── schemas.py       # Esquemas de datos
│   └── data_server.py   # Servidor HTTP para datos en tiempo real
│
├── ui/                  # Capa de interfaz (Flet)
│   ├── main.py          # Aplicación UI principal
│   ├── map_view.py      # Componente de mapa interactivo
│   ├── telemetry_panel.py # Visualización de telemetría
│   └── poi_manager.py   # UI de gestión de POIs
│
├── common/              # Utilidades compartidas
│   ├── config.py        # Configuración
│   ├── constants.py     # Constantes
│   ├── colors.py        # Colores para UI
│   └── utils.py         # Funciones utilitarias
│
├── main.py              # Punto de entrada de la aplicación
├── requirements.txt     # Dependencias
└── flet.json            # Configuración de compilación Flet
```

## Instalación

### Setup Rápido (Recomendado)

```bash
# Setup automático (crea venv e instala dependencias)
python setup.py

# Activar entorno virtual
# Windows PowerShell:
. .\venv\Scripts\Activate.ps1
# Windows CMD:
venv\Scripts\activate.bat
# Linux/macOS:
source venv/bin/activate

# Verificar setup
python setup_check.py

# Ejecutar aplicación
python main.py
```

### Requisitos Previos

- **Python 3.10+** (verificado con Python 3.13.1)
- **Sistema operativo**: Windows, macOS o Linux

### Configuración Manual del Entorno Virtual

**Windows PowerShell:**
```powershell
# Crear entorno virtual
python -m venv venv

# Activar entorno virtual (IMPORTANTE: usa el punto al inicio)
. .\activate_env.ps1

# O activar directamente
.\venv\Scripts\Activate.ps1
```

**Nota**: En PowerShell, el script helper requiere el operador de punto (`.`) al inicio para ejecutarse en el contexto actual del shell. Ver `ACTIVATE_ENV.md` para más detalles.

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
# Verificar setup completo (recomendado)
python setup_check.py

# O verificar manualmente
python -c "import flet; import folium; print('✓ Todas las dependencias instaladas')"
```

**Scripts de desarrollo:**
- `setup.py` - Setup automático (crea venv e instala dependencias)
- `setup_check.py` - Verificación completa del setup
- `diagnostico.py` - Diagnóstico del sistema

## Uso

### Modos de Ejecución

La aplicación puede ejecutarse en diferentes modos:

#### 1. Modo Desktop (Por Defecto)

```bash
# Asegúrate de que el venv esté activado
python main.py
```

- Abre una ventana de escritorio nativa
- Funciona en Windows, macOS y Linux

#### 2. Modo Web (Dashboard)

```bash
# Abre automáticamente en el navegador
python run_web.py

# O solo servidor (sin abrir navegador)
python run_web_server.py
```

- Accesible desde `http://localhost:8550`
- Accesible desde otros dispositivos en la red local: `http://TU_IP:8550`
- Funciona en cualquier navegador moderno
- Ideal para demos, acceso remoto o uso desde móviles/tablets

**Ver `PLATFORMS.md` para más detalles sobre ejecución en diferentes plataformas (Web, Android, Linux).**

### Inicio Rápido (Modo Telemetría Falsa)

Por defecto, la aplicación usa generadores de telemetría falsa, por lo que no se requiere configuración MAVSDK.

Esto hará:
- Lanzar la ventana UI de Flet (o abrir en navegador si usas modo web)
- Iniciar servidor HTTP interno en `http://localhost:8765`
- Iniciar 3 drones simulados (configurable)
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
  "fake_drone_count": 3,
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

El sistema incluye un mapa interactivo con actualizaciones incrementales en tiempo real que muestra:

- **Marcadores de Drones**:
  - Iconos circulares con emoji de avión (✈) que rotan según el rumbo
  - Color dinámico según nivel de batería:
    - Verde (#4CAF50): Batería > 50%
    - Amarillo (#FFC107): Batería 20-50%
    - Rojo (#F44336): Batería < 20%
  - Popup con información detallada (ID, batería, altitud, velocidad, rumbo)
  - Actualización en tiempo real sin recargar la página (polling cada 1 segundo)
  - Los iconos se crean/actualizan dinámicamente usando Leaflet.js

- **Marcadores de POIs**:
  - Colores por tipo (Peligro: rojo, Objetivo: azul, Punto de Control: amarillo, Zona de Aterrizaje: verde)
  - Popup con tipo y descripción
  - Persistencia en archivo JSON
  - Sincronización automática con el mapa

- **Funcionalidades**:
  - Zoom y pan interactivos
  - **Actualizaciones incrementales**: El mapa NO se recarga, solo se actualizan los marcadores
  - Preservación de estado del mapa (zoom, centro) usando `localStorage` del navegador
  - Botón para abrir mapa en navegador externo (útil en Windows donde WebView puede no estar soportado)
  - Vista alternativa con lista de drones y POIs cuando WebView no está disponible
  - Logs de depuración en consola del navegador (F12) para troubleshooting

**Arquitectura del Mapa**:
- **Python (Backend)**:
  - `MapView` genera HTML con Folium o JavaScript puro
  - `TelemetryServer` (puerto 8765) sirve datos JSON en tiempo real
  - Almacén thread-safe en memoria para drones y POIs
- **JavaScript (Frontend)**:
  - Polling cada 1 segundo a `http://localhost:8765/api/data`
  - Actualiza marcadores Leaflet dinámicamente (`setLatLng()`, `setIcon()`)
  - Búsqueda robusta del objeto del mapa (compatible con Folium y HTML puro)
  - Manejo de errores y reintentos automáticos

**Tecnologías del Mapa**:
- **Folium** (recomendado): Biblioteca Python para generar mapas HTML con Leaflet.js embebido
- **HTML/JavaScript puro** (fallback): Si Folium no está disponible, genera HTML manualmente
- **Leaflet.js**: Librería de mapas interactivos en el navegador (incluida por Folium o desde CDN)
- **OpenStreetMap**: Tiles de mapa sin necesidad de API keys
- **Servidor HTTP interno** (`backend/data_server.py`): Sirve datos JSON en `http://localhost:8765/api/data`

### Puntos de Interés (POIs)

Crear POIs con:
- **Tipo**: Peligro, Objetivo, Punto de Control, Zona de Aterrizaje u Otro
- **Descripción**: Descripción de texto personalizada
- **Ubicación**: Especificar coordenadas manualmente
- **Auto-sincronización**: Los POIs se sincronizan instantáneamente a todos los clientes conectados

### Actualizaciones en Tiempo Real

- Telemetría se actualiza cada ~2 segundos por dron (configurable)
- Cambios de POI se transmiten inmediatamente
- **Mapa HTML se actualiza incrementalmente sin recargar la página**:
  - Python actualiza `TelemetryServer` (almacén en memoria)
  - JavaScript hace polling al servidor HTTP cada 1 segundo
  - Solo se actualizan los marcadores existentes, no se regenera el HTML
  - El zoom y centro del mapa se preservan durante las actualizaciones
- Soporte multi-cliente vía sistema pub/sub de Flet
- Logs de depuración disponibles en consola del navegador (F12)

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

**Script rápido:**
```powershell
.\build_windows.ps1
```

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

**Script rápido:**
```bash
./build_macos.sh
```

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

**Script rápido:**
```bash
./build_linux.sh
```

### Android

**Opción 1: Compilar APK**
```bash
flet build apk
```

**Resultado:**
- Archivo `.apk` en la carpeta `dist/`
- Instalar en dispositivo: `adb install dist/app.apk`

**Opción 2: Modo Desarrollo**
```bash
flet run -d android
```
Requiere Android SDK y dispositivo conectado vía USB.

**Opción 3: Acceso Web desde Android**
1. Ejecutar `python run_web.py` en tu computadora
2. Abrir navegador en Android: `http://TU_IP:8550`

**Ver `PLATFORMS.md` para más detalles.**

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

### Scripts de Desarrollo

- **`setup.py`** - Setup automático: crea entorno virtual e instala dependencias
- **`setup_check.py`** - Verificación completa: Python, venv, dependencias, estructura, imports
- **`diagnostico.py`** - Diagnóstico del sistema: verifica configuración y funcionamiento

### Estructura del Proyecto

- **drones/**: Simulación de drones y manejo de telemetría
- **backend/**: Almacenamiento de POIs, gestión de datos y servidor HTTP
- **ui/**: Interfaz de usuario basada en Flet
- **common/**: Configuración y utilidades compartidas

### Agregar Nuevas Características

1. **Nuevos Comandos de Dron**: Extender `DroneManager.send_command_to_drone()`
2. **Nuevos Tipos de POI**: Agregar al enum `POIType` en `common/constants.py`
3. **Componentes UI**: Agregar nuevos componentes en el directorio `ui/`
4. **Campos de Telemetría**: Extender `normalize_telemetry()` en `common/utils.py`

### Verificación Pre-Commit

Antes de hacer commit, verifica que todo funcione:

```bash
# Verificar setup
python setup_check.py

# Diagnóstico
python diagnostico.py
```

## Solución de Problemas

### Error al Instalar Dependencias: "pydantic-core requiere Rust"

**Problema:** Si usas Python 3.15+ (alpha/beta), algunas dependencias intentan compilarse desde fuente y requieren Rust.

**Soluciones:**

1. **Usar Python 3.11 o 3.12 (Recomendado):**
   ```powershell
   # Instalar Python 3.12 desde python.org
   # Luego crear venv con esa versión:
   py -3.12 -m venv venv
   . .\venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```

2. **Instalar Rust:**
   - Descarga desde [rustup.rs](https://rustup.rs/)
   - Reinicia PowerShell después de instalar
   - Verifica: `rustc --version` y `cargo --version`
   - Vuelve a intentar: `pip install -r requirements.txt`

3. **Instalar solo dependencias básicas:**
   ```powershell
   pip install flet folium
   ```

### Ventana de Flet No Se Abre

- Asegurar que Flet está instalado: `pip install 'flet[all]'`
- Verificar versión de Python: `python --version` (debe ser 3.10+, recomendado 3.11 o 3.12)
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
- Abrir la consola del navegador (F12) para ver logs de depuración:
  - Deberías ver: `=== SCRIPT DE MAPA CARGADO ===`
  - Deberías ver: `Mapa listo después de X intentos`
  - Deberías ver: `=== INICIANDO POLLING DEL SERVIDOR ===`
  - Deberías ver: `Recibidos X drones del servidor`
  - Deberías ver: `Creando nuevo marcador para DRONE_XXX`
- Si no ves estos logs, el script JavaScript puede no estar ejecutándose correctamente
- Verificar que no hay errores de JavaScript en la consola

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

## Mejoras Futuras

- Clic directo en el mapa para crear POIs
- Planificación de misión y seguimiento de waypoints
- Interfaz de comandos de dron
- Registro histórico de telemetría
- Backend WebSocket multi-cliente (reemplazar polling HTTP)
- Exportar/importar datos de POI
- Rutas y trayectorias de drones en el mapa
- Capas toggleables (mostrar/ocultar drones/POIs)

## Referencias

- [Flet Documentation](https://flet.dev/)
- [Flet Packaging Guide](https://flet.dev/docs/cookbook/packaging-desktop-app/)
- [Folium Documentation](https://python-visualization.github.io/folium/)
- [Leaflet.js Documentation](https://leafletjs.com/)
- [MAVSDK-Python Documentation](https://mavsdk.mavlink.io/)
