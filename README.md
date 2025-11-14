# Sistema de Coordinación Multi-Dron

Un MVP listo para hackathon que coordina y visualiza múltiples drones en tiempo real. Construido con Python, Flet.dev y MAVSDK-Python.

**Simula DJI Matrice 300 RTK** - Dron empresarial profesional con características de vuelo realistas, posicionamiento RTK y comportamiento de batería TB60.

## Características

- **Visualización Multi-Dron**: Muestra múltiples drones simulados simultáneamente en un mapa interactivo
- **Telemetría en Tiempo Real**: Actualizaciones en vivo de posición, altitud, rumbo, velocidad y batería
- **Mapa Interactivo**: Visualización de drones y POIs en mapa HTML con Folium/Leaflet
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
│   └── schemas.py       # Esquemas de datos
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
└── requirements.txt     # Dependencias
```

## Instalación

1. **Clonar o descargar este repositorio**

2. **Instalar Python 3.10+** (si no está ya instalado)

3. **Instalar dependencias**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Opcional: Instalar MAVSDK** (solo si se usa simulación MAVSDK real):
   ```bash
   pip install mavsdk
   ```

## Uso

### Inicio Rápido (Modo Telemetría Falsa)

Por defecto, la aplicación usa generadores de telemetría falsa, por lo que no se requiere configuración MAVSDK:

```bash
python main.py
```

Esto hará:
- Lanzar la ventana UI de Flet
- Iniciar 3 drones simulados (configurable)
- Mostrar telemetría en tiempo real
- Permitir creación y gestión de POIs
- Generar mapa HTML interactivo con drones y POIs

### Usando MAVSDK (Opcional)

Para usar simulación MAVSDK real:

1. Editar `config.json` (o crearlo):
   ```json
   {
     "use_fake_telemetry": false,
     "fake_drone_count": 3
   }
   ```

2. Asegurar que MAVSDK está instalado y los drones están conectados

3. Ejecutar la aplicación:
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
  - Actualización en tiempo real con cada telemetría

- **Marcadores de POIs**:
  - Colores por tipo (Peligro: rojo, Objetivo: azul, Punto de Control: amarillo, Zona de Aterrizaje: verde)
  - Popup con tipo y descripción
  - Persistencia en archivo JSON

- **Funcionalidades**:
  - Zoom y pan interactivos
  - Botón para abrir mapa en navegador externo (útil en Windows donde WebView puede no estar soportado)
  - Vista alternativa con lista de drones y POIs cuando WebView no está disponible

**Tecnologías del Mapa**:
- **Folium** (recomendado): Biblioteca Python para mapas interactivos
- **HTML/JavaScript puro** (fallback): Si Folium no está disponible
- **OpenStreetMap**: Tiles de mapa sin necesidad de API keys

### Puntos de Interés (POIs)

Crear POIs con:
- **Tipo**: Peligro, Objetivo, Punto de Control, Zona de Aterrizaje u Otro
- **Descripción**: Descripción de texto personalizada
- **Ubicación**: Especificar coordenadas manualmente
- **Auto-sincronización**: Los POIs se sincronizan instantáneamente a todos los clientes conectados

### Actualizaciones en Tiempo Real

- Telemetría se actualiza cada 0.5 segundos (configurable)
- Cambios de POI se transmiten inmediatamente
- Mapa HTML se regenera con cada actualización de telemetría
- Soporte multi-cliente vía sistema pub/sub de Flet

## Desarrollo

### Estructura del Proyecto

- **drones/**: Simulación de drones y manejo de telemetría
- **backend/**: Almacenamiento de POIs y gestión de datos
- **ui/**: Interfaz de usuario basada en Flet
- **common/**: Configuración y utilidades compartidas

### Agregar Nuevas Características

1. **Nuevos Comandos de Dron**: Extender `DroneManager.send_command_to_drone()`
2. **Nuevos Tipos de POI**: Agregar al enum `POIType` en `common/constants.py`
3. **Componentes UI**: Agregar nuevos componentes en el directorio `ui/`
4. **Campos de Telemetría**: Extender `normalize_telemetry()` en `common/utils.py`

## Solución de Problemas

### Ventana de Flet No Se Abre

- Asegurar que Flet está instalado: `pip install flet`
- Verificar versión de Python: `python --version` (debe ser 3.10+)

### No Aparecen Drones

- Verificar configuración en `config.json`
- Verificar que `use_fake_telemetry` es `true` para modo falso
- Revisar consola para mensajes de error
- Verificar que los drones se están creando en los logs

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
- Recargar el navegador (F5) después de que los drones estén activos
- Verificar que el archivo HTML se está actualizando (revisar timestamp del archivo)
- Revisar logs para confirmar que `update_drone()` se está llamando

### El Mapa Se Actualiza Muy Lento

- Esto es normal con el enfoque actual (regeneración completa del HTML)
- El mapa se regenera cada vez que llega telemetría
- Para mejor rendimiento, considerar implementar actualizaciones incrementales con JavaScript (mejora futura)

## Licencia

Este proyecto está diseñado para uso en hackathon. Siéntete libre de modificar y extender según sea necesario.

## Notas

- Este MVP prioriza velocidad y simplicidad sobre física de vuelo perfecta
- El modo de telemetría falsa es recomendado para desarrollo en hackathon
- La integración MAVSDK es opcional y puede agregarse después
- El sistema está diseñado para ser fácilmente extensible
- El mapa HTML se guarda en un archivo temporal que se limpia al cerrar la aplicación

## Mejoras Futuras

- Integración completa de mapa con marcadores interactivos (parcialmente implementado)
- Actualizaciones incrementales del mapa sin regenerar HTML completo
- Clic directo en el mapa para crear POIs
- Planificación de misión y seguimiento de waypoints
- Interfaz de comandos de dron
- Registro histórico de telemetría
- Backend WebSocket multi-cliente
- Exportar/importar datos de POI
- Rutas y trayectorias de drones en el mapa
- Capas toggleables (mostrar/ocultar drones/POIs)

## Referencias

- [Flet Documentation](https://flet.dev/)
- [Folium Documentation](https://python-visualization.github.io/folium/)
- [Leaflet.js Documentation](https://leafletjs.com/)
- [MAVSDK-Python Documentation](https://mavsdk.mavlink.io/)
