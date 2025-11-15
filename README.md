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

### Requisitos Previos

- **Python 3.10+** (verificado con Python 3.13.1)
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
# Verificar que las dependencias están instaladas
python -c "import flet; import folium; print('✓ Todas las dependencias instaladas')"
```

## Uso

### Inicio Rápido (Modo Telemetría Falsa)

Por defecto, la aplicación usa generadores de telemetría falsa, por lo que no se requiere configuración MAVSDK:

```bash
# Asegúrate de que el venv esté activado
python main.py
```

Esto hará:
- Lanzar la ventana UI de Flet
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

El sistema incluye un mapa interactivo que muestra:

- **Marcadores de Drones**:
  - Color dinámico según nivel de batería (verde >50%, naranja 20-50%, rojo <20%)
  - Popup con información detallada (ID, batería, altitud, velocidad, rumbo)
  - Actualización en tiempo real sin recargar la página (polling cada 0.5s)

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
- JavaScript hace polling al servidor HTTP cada 0.5 segundos
- Soporte multi-cliente vía sistema pub/sub de Flet

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

- **drones/**: Simulación de drones y manejo de telemetría
- **backend/**: Almacenamiento de POIs, gestión de datos y servidor HTTP
- **ui/**: Interfaz de usuario basada en Flet
- **common/**: Configuración y utilidades compartidas

### Agregar Nuevas Características

1. **Nuevos Comandos de Dron**: Extender `DroneManager.send_command_to_drone()`
2. **Nuevos Tipos de POI**: Agregar al enum `POIType` en `common/constants.py`
3. **Componentes UI**: Agregar nuevos componentes en el directorio `ui/`
4. **Campos de Telemetría**: Extender `normalize_telemetry()` en `common/utils.py`

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
