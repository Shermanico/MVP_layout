"""
Componente de vista de mapa con marcadores de drones y visualización de POIs.
Usa Folium para generar mapas interactivos con OpenStreetMap.
"""
import flet as ft
import os
import tempfile
import urllib.parse
import json
from typing import Dict, List, Any, Optional, Callable
from common.constants import POIType
from common.colors import GREY_200, GREY_600, RED, GREEN, BLUE, AMBER, GREY
from backend.data_server import TelemetryServer


class MapView:
    """
    Componente de vista de mapa que muestra drones y POIs usando Folium.
    Genera un mapa HTML interactivo y lo muestra en Flet WebView.
    """
    
    def __init__(
        self,
        initial_lat: float = 37.7749,
        initial_lon: float = -122.4194,
        zoom: int = 13,
        on_poi_click: Optional[Callable[[str], None]] = None,
        on_map_click: Optional[Callable[[float, float], None]] = None
    ):
        """
        Inicializa la vista de mapa.
        
        Args:
            initial_lat: Latitud del centro inicial del mapa
            initial_lon: Longitud del centro inicial del mapa
            zoom: Nivel de zoom inicial
            on_poi_click: Callback cuando se hace clic en un POI
            on_map_click: Callback cuando se hace clic en el mapa (para crear POIs)
        """
        self.initial_lat = initial_lat
        self.initial_lon = initial_lon
        self.zoom = zoom
        self.on_poi_click = on_poi_click
        self.on_map_click = on_map_click
        
        self.drones: Dict[str, Dict[str, Any]] = {}
        self.pois: Dict[str, Dict[str, Any]] = {}
        
        # Archivo temporal para el mapa HTML
        self.temp_file = None
        self.map_html_path = None
        
        # Servidor HTTP para servir datos de telemetría
        self.telemetry_server = TelemetryServer(port=8765)
        self.telemetry_server.start()
        
        # Crear mapa inicial
        self._create_map()
        
        # Crear WebView (o fallback si no está soportado)
        # En Windows, WebView puede no estar soportado, así que usamos fallback directamente
        import platform
        if platform.system() == "Windows":
            # En Windows, WebView puede no funcionar, usar fallback directamente
            self.map_view = None
            self.fallback_view = self._create_fallback_view()
        else:
            self.map_view = self._create_webview()
            self.fallback_view = None
    
    def _create_map(self):
        """Crea el mapa HTML usando Folium o HTML/JavaScript puro."""
        try:
            # Intentar usar Folium si está disponible
            import folium
            
            # Crear mapa con Folium
            m = folium.Map(
                location=[self.initial_lat, self.initial_lon],
                zoom_start=self.zoom,
                tiles='OpenStreetMap'
            )
            
            # Agregar marcadores de drones y POIs
            self._add_drones_to_folium_map(m)
            self._add_pois_to_folium_map(m)
            
            # Guardar en archivo temporal
            self.temp_file = tempfile.NamedTemporaryFile(
                mode='w', 
                suffix='.html', 
                delete=False,
                encoding='utf-8'
            )
            m.save(self.temp_file.name)
            self.temp_file.close()
            self.map_html_path = self.temp_file.name
            
        except ImportError:
            # Si Folium no está disponible, usar HTML/JavaScript puro
            self._create_html_map()
    
    def _create_html_map(self):
        """Crea mapa HTML usando JavaScript puro con Leaflet."""
        html_content = self._generate_map_html()
        
        # Guardar en archivo temporal
        self.temp_file = tempfile.NamedTemporaryFile(
            mode='w', 
            suffix='.html', 
            delete=False,
            encoding='utf-8'
        )
        self.temp_file.write(html_content)
        self.temp_file.close()
        self.map_html_path = self.temp_file.name
    
    def _generate_map_html(self) -> str:
        """Genera HTML para OpenStreetMap con Leaflet."""
        # Serializar drones y POIs para JavaScript
        drones_js = []
        for drone_id, telemetry in self.drones.items():
            drones_js.append({
                'id': drone_id,
                'lat': telemetry.get('latitude', 0),
                'lon': telemetry.get('longitude', 0),
                'heading': telemetry.get('heading', 0),
                'battery': telemetry.get('battery', 100),
                'altitude': telemetry.get('altitude', 0),
                'velocity': telemetry.get('velocity', 0)
            })
        
        pois_js = []
        for poi_id, poi in self.pois.items():
            pois_js.append({
                'id': poi_id,
                'lat': poi.get('latitude', 0),
                'lon': poi.get('longitude', 0),
                'type': poi.get('type', 'other'),
                'description': poi.get('description', '')
            })
        
        drones_json = json.dumps(drones_js)
        pois_json = json.dumps(pois_js)
        
        return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <style>
        body {{ margin: 0; padding: 0; }}
        #map {{ height: 100vh; width: 100%; }}
        .drone-icon {{
            background: transparent;
            border: none;
            box-shadow: none;
        }}
        .drone-icon svg {{
            filter: drop-shadow(0 2px 4px rgba(0,0,0,0.4));
        }}
        .poi-icon {{
            width: 16px;
            height: 16px;
            border-radius: 50%;
            border: 2px solid white;
            box-shadow: 0 2px 4px rgba(0,0,0,0.3);
        }}
    </style>
</head>
<body>
    <div id="map"></div>
    <script>
        // Inicializar mapa
        var map = L.map('map').setView([{self.initial_lat}, {self.initial_lon}], {self.zoom});
        L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
            attribution: '© OpenStreetMap contributors',
            maxZoom: 19
        }}).addTo(map);
        
        var droneMarkers = {{}};
        var poiMarkers = {{}};
        
        // Colores para POIs
        var poiColors = {{
            'hazard': '#F44336',
            'target': '#2196F3',
            'checkpoint': '#FFC107',
            'landing_zone': '#4CAF50',
            'other': '#9E9E9E'
        }};
        
        // Escuchar clics en el mapa
        map.on('click', function(e) {{
            // Mostrar coordenadas en consola (para debugging)
            console.log('Map click:', e.latlng.lat, e.latlng.lng);
            // Nota: La comunicación con Python se puede hacer vía WebView messages
            // Por ahora, el usuario puede usar el botón "Agregar POI"
        }});
        
        // Función para crear icono de dron con rotación
        function createDroneIcon(batteryColor, heading) {{
            heading = heading || 0;
            var rotation = heading; // Rotar según el heading
            // Crear icono SVG de avión más visible
            var svgIcon = '<div style="width: 32px; height: 32px; position: relative; transform: rotate(' + rotation + 'deg); transform-origin: 16px 16px;">' +
                '<svg width="32" height="32" viewBox="0 0 32 32" xmlns="http://www.w3.org/2000/svg">' +
                '<path d="M16 4 L20 12 L28 14 L20 16 L16 24 L12 16 L4 14 L12 12 Z" fill="' + batteryColor + '" stroke="white" stroke-width="2" stroke-linejoin="round"/>' +
                '<circle cx="16" cy="16" r="4" fill="white" opacity="0.9"/>' +
                '</svg>' +
                '</div>';
            return L.divIcon({{
                className: 'drone-icon',
                html: svgIcon,
                iconSize: [32, 32],
                iconAnchor: [16, 16]
            }});
        }}
        
        // Función para actualizar/agregar dron
        window.updateDrone = function(droneId, lat, lon, heading, battery, altitude, velocity) {{
            velocity = velocity || 0;
            heading = heading || 0;
            var batteryColor = battery > 50 ? '#4CAF50' : (battery > 20 ? '#FFC107' : '#F44336');
            
            // Validar coordenadas
            if (!lat || !lon || isNaN(lat) || isNaN(lon) || lat === 0 || lon === 0) {{
                console.warn('Coordenadas inválidas para', droneId, ':', lat, lon);
                return;
            }}
            
            if (droneMarkers[droneId]) {{
                // Actualizar posición
                droneMarkers[droneId].setLatLng([lat, lon]);
                // Actualizar popup
                droneMarkers[droneId].setPopupContent(
                    '<b>Dron: ' + droneId + '</b><br>' +
                    'Batería: ' + battery.toFixed(1) + '%<br>' +
                    'Altitud: ' + altitude.toFixed(1) + 'm<br>' +
                    'Velocidad: ' + velocity.toFixed(1) + ' m/s<br>' +
                    'Rumbo: ' + heading.toFixed(1) + '°'
                );
                // Actualizar icono (color y rotación)
                var icon = createDroneIcon(batteryColor, heading);
                droneMarkers[droneId].setIcon(icon);
            }} else {{
                // Crear nuevo marcador
                console.log('Creando nuevo marcador para', droneId, 'en', lat, lon);
                var icon = createDroneIcon(batteryColor, heading);
                var marker = L.marker([lat, lon], {{icon: icon}}).addTo(map);
                marker.bindPopup(
                    '<b>Dron: ' + droneId + '</b><br>' +
                    'Batería: ' + battery.toFixed(1) + '%<br>' +
                    'Altitud: ' + altitude.toFixed(1) + 'm<br>' +
                    'Velocidad: ' + velocity.toFixed(1) + ' m/s<br>' +
                    'Rumbo: ' + heading.toFixed(1) + '°'
                );
                droneMarkers[droneId] = marker;
                console.log('Marcador creado para', droneId, 'Total marcadores:', Object.keys(droneMarkers).length);
            }}
        }};
        
        // Función para actualizar/agregar POI
        window.updatePOI = function(poiId, lat, lon, type, description) {{
            var color = poiColors[type] || poiColors['other'];
            var typeNames = {{
                'hazard': 'PELIGRO',
                'target': 'OBJETIVO',
                'checkpoint': 'PUNTO DE CONTROL',
                'landing_zone': 'ZONA DE ATERRIZAJE',
                'other': 'OTRO'
            }};
            var typeName = typeNames[type] || 'OTRO';
            
            if (poiMarkers[poiId]) {{
                poiMarkers[poiId].setLatLng([lat, lon]);
                poiMarkers[poiId].setPopupContent('<b>' + typeName + '</b><br>' + description);
            }} else {{
                var icon = L.divIcon({{
                    className: 'poi-icon',
                    html: '<div style="background: ' + color + '; width: 16px; height: 16px; border-radius: 50%; border: 2px solid white; box-shadow: 0 2px 4px rgba(0,0,0,0.3);"></div>',
                    iconSize: [16, 16],
                    iconAnchor: [8, 8]
                }});
                var marker = L.marker([lat, lon], {{icon: icon}}).addTo(map);
                marker.bindPopup('<b>' + typeName + '</b><br>' + description);
                poiMarkers[poiId] = marker;
            }}
        }};
        
        // Función para eliminar POI
        window.removePOI = function(poiId) {{
            if (poiMarkers[poiId]) {{
                map.removeLayer(poiMarkers[poiId]);
                delete poiMarkers[poiId];
            }}
        }};
        
        // Función para eliminar dron
        window.removeDrone = function(droneId) {{
            if (droneMarkers[droneId]) {{
                map.removeLayer(droneMarkers[droneId]);
                delete droneMarkers[droneId];
            }}
        }};
        
        // Inicializar drones y POIs existentes
        var initialDrones = {drones_json};
        var initialPOIs = {pois_json};
        
        console.log('Inicializando mapa con', initialDrones.length, 'drones y', initialPOIs.length, 'POIs');
        
        // Esperar a que el mapa esté completamente cargado antes de agregar marcadores
        map.whenReady(function() {{
            console.log('Mapa listo, agregando drones iniciales...');
            for (var i = 0; i < initialDrones.length; i++) {{
                var d = initialDrones[i];
                console.log('Agregando dron inicial:', d.id, 'en', d.lat, d.lon);
                window.updateDrone(d.id, d.lat, d.lon, d.heading, d.battery, d.altitude, d.velocity || 0);
            }}
            
            for (var i = 0; i < initialPOIs.length; i++) {{
                var p = initialPOIs[i];
                window.updatePOI(p.id, p.lat, p.lon, p.type, p.description);
            }}
            console.log('Drones y POIs iniciales agregados. Total marcadores:', Object.keys(droneMarkers).length);
        }});
        
        // Guardar estado del mapa periódicamente (sin recargar)
        function saveMapState() {{
            if (typeof map !== 'undefined' && map) {{
                try {{
                    var center = map.getCenter();
                    var zoom = map.getZoom();
                    if (center && typeof center.lat === 'number' && typeof center.lng === 'number') {{
                        localStorage.setItem('mapCenter', JSON.stringify({{lat: center.lat, lng: center.lng}}));
                        localStorage.setItem('mapZoom', zoom.toString());
                    }}
                }} catch(e) {{
                    // Silenciar errores de guardado
                }}
            }}
        }}
        
        function restoreMapState() {{
            if (typeof map !== 'undefined' && map) {{
                var savedCenter = localStorage.getItem('mapCenter');
                var savedZoom = localStorage.getItem('mapZoom');
                if (savedCenter && savedZoom) {{
                    try {{
                        var center = JSON.parse(savedCenter);
                        var zoom = parseInt(savedZoom);
                        if (center && typeof center.lat === 'number' && typeof center.lng === 'number' && !isNaN(zoom)) {{
                            map.setView([center.lat, center.lng], zoom, {{reset: false}});
                            return true;
                        }}
                    }} catch(e) {{
                        // Silenciar errores de restauración
                    }}
                }}
            }}
            return false;
        }}
        
        // Restaurar estado del mapa al cargar (después de que el mapa esté listo)
        // Intentar restaurar inmediatamente y luego con delay para asegurar que funcione
        function tryRestoreState() {{
            if (restoreMapState()) {{
                return true;
            }}
            // Si no se pudo restaurar, intentar de nuevo después de un delay
            setTimeout(function() {{
                restoreMapState();
            }}, 300);
            return false;
        }}
        
        // Intentar restaurar estado cuando el mapa esté listo
        map.whenReady(function() {{
            setTimeout(function() {{
                tryRestoreState();
            }}, 100);
        }});
        
        // También intentar después de un delay adicional
        setTimeout(function() {{
            tryRestoreState();
        }}, 500);
        
        // Guardar estado periódicamente (cada 2 segundos) sin recargar
        setInterval(saveMapState, 2000);
        
        // Guardar estado cuando el usuario mueve o hace zoom en el mapa
        map.on('moveend', saveMapState);
        map.on('zoomend', saveMapState);
        
        // Guardar estado antes de cerrar
        window.addEventListener('beforeunload', saveMapState);
        
        // Polling para actualizar datos desde el servidor HTTP
        var apiUrl = 'http://localhost:8765/api/data';
        var updateCount = 0;
        var lastUpdateTime = 0;
        
        function updateFromServer() {{
            var now = Date.now();
            // Evitar actualizaciones muy frecuentes (mínimo 1 segundo entre actualizaciones)
            if (now - lastUpdateTime < 1000) {{
                return;
            }}
            lastUpdateTime = now;
            updateCount++;
            
            fetch(apiUrl)
                .then(function(response) {{
                    if (!response.ok) {{
                        throw new Error('Network response was not ok: ' + response.status);
                    }}
                    return response.json();
                }})
                .then(function(data) {{
                    // Actualizar drones
                    if (data.drones && typeof data.drones === 'object') {{
                        var droneCount = 0;
                        var droneIds = Object.keys(data.drones);
                        if (updateCount === 1 || updateCount % 20 === 0) {{
                            console.log('Recibidos', droneIds.length, 'drones del servidor:', droneIds);
                        }}
                        for (var droneId in data.drones) {{
                            if (data.drones.hasOwnProperty(droneId)) {{
                                var drone = data.drones[droneId];
                                if (drone && typeof drone === 'object') {{
                                    var lat = drone.latitude || drone.lat || 0;
                                    var lon = drone.longitude || drone.lon || 0;
                                    if (lat && lon && lat !== 0 && lon !== 0) {{
                                        window.updateDrone(
                                            droneId,
                                            lat,
                                            lon,
                                            drone.heading || 0,
                                            drone.battery || 100,
                                            drone.altitude || 0,
                                            drone.velocity || 0
                                        );
                                        droneCount++;
                                    }} else {{
                                        if (updateCount % 20 === 0) {{
                                            console.warn('Dron', droneId, 'tiene coordenadas inválidas:', lat, lon);
                                        }}
                                    }}
                                }}
                            }}
                        }}
                        if (updateCount % 20 === 0) {{
                            console.log('Drones actualizados en mapa:', droneCount, 'de', droneIds.length);
                        }}
                    }}
                    
                    // Actualizar POIs
                    if (data.pois && typeof data.pois === 'object') {{
                        for (var poiId in data.pois) {{
                            if (data.pois.hasOwnProperty(poiId)) {{
                                var poi = data.pois[poiId];
                                if (poi && typeof poi === 'object') {{
                                    window.updatePOI(
                                        poiId,
                                        poi.latitude || 0,
                                        poi.longitude || 0,
                                        poi.type || 'other',
                                        poi.description || ''
                                    );
                                }}
                            }}
                        }}
                    }}
                }})
                .catch(function(error) {{
                    // Solo mostrar errores ocasionalmente para no saturar la consola
                    if (updateCount % 30 === 0) {{
                        console.log('Error actualizando desde servidor (intento ' + updateCount + '):', error.message);
                    }}
                }});
        }}
        
        // Actualizar cada 1 segundo (optimizado para no saturar)
        setInterval(updateFromServer, 1000);
        
        // Actualizar inmediatamente después de un pequeño delay
        setTimeout(function() {{
            console.log('Iniciando polling del servidor en', apiUrl);
            updateFromServer();
        }}, 1500);
    </script>
</body>
</html>
        """
    
    def _add_drones_to_folium_map(self, m):
        """Agrega marcadores de drones al mapa Folium."""
        import folium
        import logging
        logger = logging.getLogger(__name__)
        
        for drone_id, telemetry in self.drones.items():
            lat = telemetry.get('latitude', self.initial_lat)
            lon = telemetry.get('longitude', self.initial_lon)
            battery = telemetry.get('battery', 100)
            altitude = telemetry.get('altitude', 0)
            velocity = telemetry.get('velocity', 0)
            heading = telemetry.get('heading', 0)
            
            # Validar coordenadas
            if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
                logger.warning(f"Coordenadas inválidas para {drone_id}: ({lat}, {lon})")
                continue
            
            # Color basado en batería
            if battery > 50:
                color = 'green'
            elif battery > 20:
                color = 'orange'
            else:
                color = 'red'
            
            # Crear popup con información
            popup_html = f"""
            <b>Dron: {drone_id}</b><br>
            Batería: {battery:.1f}%<br>
            Altitud: {altitude:.1f}m<br>
            Velocidad: {velocity:.1f} m/s<br>
            Rumbo: {heading:.1f}°
            """
            
            # Usar Marker con icono personalizado para mejor visibilidad
            folium.Marker(
                location=[lat, lon],
                popup=folium.Popup(popup_html, max_width=200),
                icon=folium.Icon(color=color, icon='info-sign'),
                tooltip=f"{drone_id} - Batería: {battery:.1f}%"
            ).add_to(m)
            
            logger.debug(f"Agregado dron {drone_id} al mapa Folium en ({lat:.6f}, {lon:.6f})")
    
    def _add_pois_to_folium_map(self, m):
        """Agrega marcadores de POIs al mapa Folium."""
        import folium
        
        poi_colors = {
            'hazard': 'red',
            'target': 'blue',
            'checkpoint': 'orange',
            'landing_zone': 'green',
            'other': 'gray'
        }
        
        poi_names = {
            'hazard': 'PELIGRO',
            'target': 'OBJETIVO',
            'checkpoint': 'PUNTO DE CONTROL',
            'landing_zone': 'ZONA DE ATERRIZAJE',
            'other': 'OTRO'
        }
        
        for poi_id, poi in self.pois.items():
            lat = poi.get('latitude', self.initial_lat)
            lon = poi.get('longitude', self.initial_lon)
            poi_type = poi.get('type', 'other')
            description = poi.get('description', '')
            
            color = poi_colors.get(poi_type, 'gray')
            type_name = poi_names.get(poi_type, 'OTRO')
            
            popup_html = f"""
            <b>{type_name}</b><br>
            {description}
            """
            
            folium.Marker(
                location=[lat, lon],
                popup=folium.Popup(popup_html, max_width=200),
                icon=folium.Icon(color=color, icon='info-sign')
            ).add_to(m)
    
    def _add_auto_refresh_to_folium_html(self):
        """Agrega script de auto-refresh al HTML generado por Folium."""
        if not self.map_html_path or not os.path.exists(self.map_html_path):
            return
        
        try:
            with open(self.map_html_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            # Buscar el cierre de </body> o </html>
            auto_refresh_script = """
        <script>
        // Guardar estado del mapa periódicamente (sin recargar)
        function findMapObject() {
            // Buscar el objeto del mapa de Leaflet
            // Folium puede crear el mapa con diferentes nombres
            if (typeof map !== 'undefined' && map && typeof map.getCenter === 'function') {
                return map;
            }
            // Buscar en window
            for (var key in window) {
                try {
                    var obj = window[key];
                    if (obj && typeof obj === 'object' && typeof obj.getCenter === 'function' && typeof obj.getZoom === 'function') {
                        if (obj._container && obj._container.classList && obj._container.classList.contains('leaflet-container')) {
                            return obj;
                        }
                    }
                } catch(e) {
                    continue;
                }
            }
            // Buscar desde el contenedor del mapa
            var mapContainer = document.querySelector('.leaflet-container');
            if (mapContainer && typeof L !== 'undefined' && L.Map) {
                // Leaflet almacena referencias en el contenedor
                for (var key in L.Map._instances || {}) {
                    try {
                        var mapInstance = L.Map._instances[key];
                        if (mapInstance && mapInstance._container === mapContainer) {
                            return mapInstance;
                                }
                            } catch(e) {
                                continue;
                            }
                        }
                    }
            return null;
        }
        
        function saveMapState() {
            var mapObj = findMapObject();
            if (mapObj) {
                try {
                    var center = mapObj.getCenter();
                    var zoom = mapObj.getZoom();
                    if (center && typeof center.lat === 'number' && typeof center.lng === 'number' && !isNaN(zoom) && zoom > 0) {
                        localStorage.setItem('mapCenter', JSON.stringify({lat: center.lat, lng: center.lng}));
                        localStorage.setItem('mapZoom', zoom.toString());
                        return true;
                    }
                } catch(e) {
                    // Silenciar errores
                }
            }
            return false;
        }
        
        function restoreMapState() {
            var mapObj = findMapObject();
            if (mapObj) {
                var savedCenter = localStorage.getItem('mapCenter');
                var savedZoom = localStorage.getItem('mapZoom');
                if (savedCenter && savedZoom) {
                    try {
                        var center = JSON.parse(savedCenter);
                        var zoom = parseInt(savedZoom);
                        if (center && typeof center.lat === 'number' && typeof center.lng === 'number' && !isNaN(zoom) && zoom > 0) {
                            mapObj.setView([center.lat, center.lng], zoom, {reset: false});
                            return true;
                        }
                    } catch(e) {
                        // Silenciar errores
                    }
                }
            }
            return false;
        }
        
        // Esperar a que el mapa esté listo
        function waitForMap(callback) {
            var attempts = 0;
            var maxAttempts = 20;
            function check() {
                attempts++;
                var mapObj = findMapObject();
                if (mapObj) {
                    try {
                        var center = mapObj.getCenter();
                        var zoom = mapObj.getZoom();
                        if (center && !isNaN(zoom) && zoom > 0) {
                            callback(mapObj);
                            return;
                        }
                    } catch(e) {
                        // Mapa aún no está listo
                    }
                }
                if (attempts < maxAttempts) {
                    setTimeout(check, 500);
                } else {
                    callback(null);
                }
            }
            check();
        }
        
                // Restaurar estado cuando el mapa esté listo
        waitForMap(function(mapObj) {
            if (mapObj) {
                    setTimeout(function() {
                        restoreMapState();
                }, 300);
            }
        });
        
        // Guardar estado periódicamente (cada 2 segundos) sin recargar
        setInterval(saveMapState, 2000);
        
        // Guardar estado cuando el usuario mueve o hace zoom en el mapa
        waitForMap(function(mapObj) {
            if (mapObj) {
                mapObj.on('moveend', saveMapState);
                mapObj.on('zoomend', saveMapState);
            }
        });
        
        // Guardar estado antes de cerrar
        window.addEventListener('beforeunload', saveMapState);
        
        // Funciones para actualizar drones y POIs (si no existen ya)
        if (typeof window.updateDrone === 'undefined') {
            window.droneMarkers = window.droneMarkers || {};
            window.poiMarkers = window.poiMarkers || {};
            
            // Función para crear icono de dron con rotación
            function createDroneIconFolium(batteryColor, heading) {
                heading = heading || 0;
                var rotation = heading;
                // Crear icono SVG de avión más visible
                var svgIcon = '<div style="width: 32px; height: 32px; position: relative; transform: rotate(' + rotation + 'deg); transform-origin: 16px 16px;">' +
                    '<svg width="32" height="32" viewBox="0 0 32 32" xmlns="http://www.w3.org/2000/svg">' +
                    '<path d="M16 4 L20 12 L28 14 L20 16 L16 24 L12 16 L4 14 L12 12 Z" fill="' + batteryColor + '" stroke="white" stroke-width="2" stroke-linejoin="round"/>' +
                    '<circle cx="16" cy="16" r="4" fill="white" opacity="0.9"/>' +
                    '</svg>' +
                    '</div>';
                return L.divIcon({
                    className: 'drone-icon',
                    html: svgIcon,
                    iconSize: [32, 32],
                    iconAnchor: [16, 16]
                });
            }
            
            window.updateDrone = function(droneId, lat, lon, heading, battery, altitude, velocity) {
                velocity = velocity || 0;
                heading = heading || 0;
                var batteryColor = battery > 50 ? '#4CAF50' : (battery > 20 ? '#FFC107' : '#F44336');
                var mapObj = findMapObject();
                if (!mapObj) {
                    console.warn('No se encontró objeto del mapa para', droneId);
                    return;
                }
                
                // Validar coordenadas
                if (!lat || !lon || isNaN(lat) || isNaN(lon) || lat === 0 || lon === 0) {
                    console.warn('Coordenadas inválidas para', droneId, ':', lat, lon);
                    return;
                }
                
                if (window.droneMarkers[droneId]) {
                    window.droneMarkers[droneId].setLatLng([lat, lon]);
                    window.droneMarkers[droneId].setPopupContent(
                        '<b>Dron: ' + droneId + '</b><br>' +
                        'Batería: ' + battery.toFixed(1) + '%<br>' +
                        'Altitud: ' + altitude.toFixed(1) + 'm<br>' +
                        'Velocidad: ' + velocity.toFixed(1) + ' m/s<br>' +
                        'Rumbo: ' + heading.toFixed(1) + '°'
                    );
                    // Actualizar icono (color y rotación)
                    var icon = createDroneIconFolium(batteryColor, heading);
                    window.droneMarkers[droneId].setIcon(icon);
                } else {
                    console.log('Creando nuevo marcador para', droneId, 'en', lat, lon);
                    var icon = createDroneIconFolium(batteryColor, heading);
                    var marker = L.marker([lat, lon], {icon: icon}).addTo(mapObj);
                    marker.bindPopup(
                        '<b>Dron: ' + droneId + '</b><br>' +
                        'Batería: ' + battery.toFixed(1) + '%<br>' +
                        'Altitud: ' + altitude.toFixed(1) + 'm<br>' +
                        'Velocidad: ' + velocity.toFixed(1) + ' m/s<br>' +
                        'Rumbo: ' + heading.toFixed(1) + '°'
                    );
                    window.droneMarkers[droneId] = marker;
                    console.log('Marcador creado para', droneId, 'Total marcadores:', Object.keys(window.droneMarkers).length);
                }
            };
            
            window.updatePOI = function(poiId, lat, lon, type, description) {
                var poiColors = {
                    'hazard': '#F44336',
                    'target': '#2196F3',
                    'checkpoint': '#FFC107',
                    'landing_zone': '#4CAF50',
                    'other': '#9E9E9E'
                };
                var color = poiColors[type] || poiColors['other'];
                var mapObj = findMapObject();
                if (!mapObj) return;
                
                if (window.poiMarkers[poiId]) {
                    window.poiMarkers[poiId].setLatLng([lat, lon]);
                    window.poiMarkers[poiId].setPopupContent('<b>' + type.toUpperCase() + '</b><br>' + description);
                } else {
                    var icon = L.divIcon({
                        className: 'poi-icon',
                        html: '<div style="background: ' + color + '; width: 16px; height: 16px; border-radius: 50%; border: 2px solid white; box-shadow: 0 2px 4px rgba(0,0,0,0.3);"></div>',
                        iconSize: [16, 16],
                        iconAnchor: [8, 8]
                    });
                    var marker = L.marker([lat, lon], {icon: icon}).addTo(mapObj);
                    marker.bindPopup('<b>' + type.toUpperCase() + '</b><br>' + description);
                    window.poiMarkers[poiId] = marker;
                }
            };
        }
        
        // Polling para actualizar datos desde el servidor HTTP
        var apiUrl = 'http://localhost:8765/api/data';
        var updateCount = 0;
        var lastUpdateTime = 0;
        
        function updateFromServer() {
            var now = Date.now();
            // Evitar actualizaciones muy frecuentes (mínimo 1 segundo entre actualizaciones)
            if (now - lastUpdateTime < 1000) {
                return;
            }
            lastUpdateTime = now;
            updateCount++;
            
            fetch(apiUrl)
                .then(function(response) {
                    if (!response.ok) {
                        throw new Error('Network response was not ok: ' + response.status);
                    }
                    return response.json();
                })
                .then(function(data) {
                    // Actualizar drones
                    if (data.drones && typeof data.drones === 'object') {
                        var droneCount = 0;
                        var droneIds = Object.keys(data.drones);
                        if (updateCount === 1 || updateCount % 20 === 0) {
                            console.log('Recibidos', droneIds.length, 'drones del servidor:', droneIds);
                        }
                        for (var droneId in data.drones) {
                            if (data.drones.hasOwnProperty(droneId)) {
                                var drone = data.drones[droneId];
                                if (drone && typeof drone === 'object') {
                                    var lat = drone.latitude || drone.lat || 0;
                                    var lon = drone.longitude || drone.lon || 0;
                                    if (lat && lon && lat !== 0 && lon !== 0) {
                                        window.updateDrone(
                                            droneId,
                                            lat,
                                            lon,
                                            drone.heading || 0,
                                            drone.battery || 100,
                                            drone.altitude || 0,
                                            drone.velocity || 0
                                        );
                                        droneCount++;
                                    } else {
                                        if (updateCount % 20 === 0) {
                                            console.warn('Dron', droneId, 'tiene coordenadas inválidas:', lat, lon);
                                        }
                                    }
                                }
                            }
                        }
                        if (updateCount % 20 === 0) {
                            console.log('Drones actualizados en mapa:', droneCount, 'de', droneIds.length);
                        }
                    }
                    
                    // Actualizar POIs
                    if (data.pois && typeof data.pois === 'object') {
                        for (var poiId in data.pois) {
                            if (data.pois.hasOwnProperty(poiId)) {
                                var poi = data.pois[poiId];
                                if (poi && typeof poi === 'object') {
                                    window.updatePOI(
                                        poiId,
                                        poi.latitude || 0,
                                        poi.longitude || 0,
                                        poi.type || 'other',
                                        poi.description || ''
                                    );
                                }
                            }
                        }
                    }
                })
                .catch(function(error) {
                    // Solo mostrar errores ocasionalmente para no saturar la consola
                    if (updateCount % 30 === 0) {
                        console.log('Error actualizando desde servidor (intento ' + updateCount + '):', error.message);
                    }
                });
        }
        
        // Actualizar cada 1 segundo (optimizado para no saturar)
        setInterval(updateFromServer, 1000);
        
        // Actualizar inmediatamente después de un pequeño delay
        setTimeout(function() {
            console.log('Iniciando polling del servidor en', apiUrl);
            updateFromServer();
        }, 1500);
        </script>
"""
            
            # Insertar antes de </body> o al final si no hay </body>
            if '</body>' in html_content:
                html_content = html_content.replace('</body>', auto_refresh_script + '\n    </body>')
            elif '</html>' in html_content:
                html_content = html_content.replace('</html>', auto_refresh_script + '\n</html>')
            else:
                html_content += auto_refresh_script
            
            with open(self.map_html_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Error agregando auto-refresh al HTML de Folium: {e}")
    
    def _create_webview(self) -> ft.Control:
        """Crea el componente WebView de Flet o fallback si no está soportado."""
        try:
            # Intentar crear WebView
            if self.map_html_path and os.path.exists(self.map_html_path):
                file_path = os.path.abspath(self.map_html_path)
                file_url = f"file:///{file_path.replace(os.sep, '/')}"
                webview = ft.WebView(
                    url=file_url,
                    expand=True,
                    on_page_started=self._on_map_ready
                )
                # Verificar si WebView está soportado probando crear uno
                return webview
            else:
                html_content = self._generate_map_html()
                encoded = urllib.parse.quote(html_content)
                return ft.WebView(
                    url=f"data:text/html;charset=utf-8,{encoded}",
                    expand=True,
                    on_page_started=self._on_map_ready
                )
        except Exception as e:
            # Si WebView no está soportado, crear fallback visual
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"WebView no soportado, usando fallback visual: {e}")
            return self._create_fallback_view()
    
    def _on_map_ready(self, e):
        """Llamado cuando el mapa está listo."""
        pass
    
    def update_drone(self, telemetry: Dict[str, Any]):
        """
        Actualiza la posición del dron en el mapa.
        Ahora solo actualiza el servidor HTTP, el JavaScript hace el polling.
        
        Args:
            telemetry: Diccionario de telemetría con datos del dron
        """
        import logging
        logger = logging.getLogger(__name__)
        
        drone_id = telemetry.get("drone_id")
        if not drone_id:
            return
        
        self.drones[drone_id] = telemetry
        logger.debug(f"Actualizando dron {drone_id} en mapa: {len(self.drones)} drones totales")
        
        # Actualizar servidor HTTP (el JavaScript hará polling y actualizará los marcadores)
        self.telemetry_server.update_telemetry(telemetry)
        
        # Si estamos usando fallback, actualizar vista alternativa siempre
        if hasattr(self, 'drone_list'):
            self._update_fallback_view()
    
    def add_poi(self, poi: Dict[str, Any]):
        """
        Agrega o actualiza un POI en el mapa.
        
        Args:
            poi: Diccionario de POI
        """
        poi_id = poi.get("id")
        if poi_id:
            self.pois[poi_id] = poi
            # Actualizar servidor HTTP (el JavaScript hará polling)
            self.telemetry_server.update_poi(poi)
            
            # Si estamos usando fallback, actualizar vista alternativa
            if hasattr(self, 'poi_list'):
                self._update_fallback_view()
    
    def remove_poi(self, poi_id: str):
        """
        Elimina un POI del mapa.
        
        Args:
            poi_id: ID del POI a eliminar
        """
        if poi_id in self.pois:
            del self.pois[poi_id]
            # Actualizar servidor HTTP
            self.telemetry_server.remove_poi(poi_id)
            
            # Si estamos usando fallback, actualizar vista alternativa
            if hasattr(self, 'poi_list'):
                self._update_fallback_view()
    
    def _update_map_html(self):
        """Actualiza el archivo HTML del mapa."""
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            import folium
            # Si Folium está disponible, regenerar mapa
            m = folium.Map(
                location=[self.initial_lat, self.initial_lon],
                zoom_start=self.zoom,
                tiles='OpenStreetMap'
            )
            self._add_drones_to_folium_map(m)
            self._add_pois_to_folium_map(m)
            
            if self.map_html_path:
                m.save(self.map_html_path)
                # Agregar auto-refresh al HTML generado por Folium
                self._add_auto_refresh_to_folium_html()
                logger.debug(f"Mapa HTML actualizado: {len(self.drones)} drones, {len(self.pois)} POIs")
        except ImportError:
            # Si no hay Folium, regenerar HTML
            html_content = self._generate_map_html()
            if self.map_html_path:
                with open(self.map_html_path, 'w', encoding='utf-8') as f:
                    f.write(html_content)
                logger.debug(f"Mapa HTML (sin Folium) actualizado: {len(self.drones)} drones, {len(self.pois)} POIs")
    
    def _reload_map(self):
        """Recarga el mapa en el WebView."""
        if self.map_view and self.map_html_path:
            file_path = os.path.abspath(self.map_html_path)
            file_url = f"file:///{file_path.replace(os.sep, '/')}"
            # Forzar recarga cambiando la URL ligeramente
            self.map_view.url = file_url + "?t=" + str(os.path.getmtime(self.map_html_path))
            if self.map_view.page:
                self.map_view.update()
    
    def _create_fallback_view(self) -> ft.Container:
        """Crea una vista alternativa cuando WebView no está disponible."""
        # Crear una representación visual del mapa usando componentes Flet
        if not hasattr(self, 'drone_list'):
            self.drone_list = ft.Column(controls=[], spacing=5, scroll=ft.ScrollMode.AUTO, expand=True)
        if not hasattr(self, 'poi_list'):
            self.poi_list = ft.Column(controls=[], spacing=5, scroll=ft.ScrollMode.AUTO, expand=True)
        
        # Calcular altura para las listas scrolleables (aproximadamente mitad de la ventana cada una)
        # Usar altura fija razonable para habilitar scroll
        list_height = 250  # Altura fija para cada lista
        
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text(
                        "Vista de Mapa",
                        size=18,
                        weight=ft.FontWeight.BOLD
                    ),
                    ft.Text(
                        "Nota: WebView no está soportado en esta plataforma.\n"
                        "El mapa HTML se guardó en: " + (self.map_html_path or "N/A"),
                        size=11,
                        color=GREY_600,
                    ),
                    ft.ElevatedButton(
                        "Abrir Mapa en Navegador",
                        icon=ft.Icons.OPEN_IN_BROWSER,
                        on_click=self._open_map_in_browser,
                    ),
                    ft.Divider(),
                    ft.Text("Drones en el Mapa:", weight=ft.FontWeight.BOLD, size=14),
                    ft.Container(
                        content=self.drone_list,
                        height=list_height,
                        expand=False,
                    ),
                    ft.Divider(),
                    ft.Text("POIs en el Mapa:", weight=ft.FontWeight.BOLD, size=14),
                    ft.Container(
                        content=self.poi_list,
                        height=list_height,
                        expand=False,
                    ),
                ],
                spacing=10,
                expand=True,
            ),
            expand=True,
            bgcolor=GREY_200,
            padding=15,
        )
    
    def _open_map_in_browser(self, e):
        """Abre el mapa HTML en el navegador predeterminado."""
        import webbrowser
        if self.map_html_path and os.path.exists(self.map_html_path):
            file_path = os.path.abspath(self.map_html_path)
            file_url = f"file:///{file_path.replace(os.sep, '/')}"
            webbrowser.open(file_url)
    
    def _update_fallback_view(self):
        """Actualiza la vista alternativa con información de drones y POIs."""
        if not hasattr(self, 'drone_list') or not hasattr(self, 'poi_list'):
            return
        
        # Actualizar lista de drones
        self.drone_list.controls.clear()
        for drone_id, telemetry in self.drones.items():
            lat = telemetry.get('latitude', 0)
            lon = telemetry.get('longitude', 0)
            battery = telemetry.get('battery', 100)
            altitude = telemetry.get('altitude', 0)
            
            battery_color = GREEN if battery > 50 else (AMBER if battery > 20 else RED)
            
            self.drone_list.controls.append(
                ft.Card(
                    content=ft.Container(
                        content=ft.Column(
                            controls=[
                                ft.Row(
                                    controls=[
                                        ft.Icon(ft.Icons.FLIGHT_TAKEOFF, color=GREEN),
                                        ft.Text(drone_id, weight=ft.FontWeight.BOLD),
                                    ]
                                ),
                                ft.Text(f"Posición: {lat:.6f}, {lon:.6f}"),
                                ft.Text(f"Batería: {battery:.1f}%", color=battery_color),
                                ft.Text(f"Altitud: {altitude:.1f}m"),
                            ],
                            spacing=5,
                        ),
                        padding=10,
                    )
                )
            )
        
        # Actualizar lista de POIs
        self.poi_list.controls.clear()
        poi_colors = {
            'hazard': RED,
            'target': BLUE,
            'checkpoint': AMBER,
            'landing_zone': GREEN,
            'other': GREY
        }
        poi_names = {
            'hazard': 'PELIGRO',
            'target': 'OBJETIVO',
            'checkpoint': 'PUNTO DE CONTROL',
            'landing_zone': 'ZONA DE ATERRIZAJE',
            'other': 'OTRO'
        }
        
        for poi_id, poi in self.pois.items():
            lat = poi.get('latitude', 0)
            lon = poi.get('longitude', 0)
            poi_type = poi.get('type', 'other')
            description = poi.get('description', '')
            
            color = poi_colors.get(poi_type, GREY)
            type_name = poi_names.get(poi_type, 'OTRO')
            
            self.poi_list.controls.append(
                ft.Card(
                    content=ft.Container(
                        content=ft.Column(
                            controls=[
                                ft.Row(
                                    controls=[
                                        ft.Container(
                                            width=16,
                                            height=16,
                                            bgcolor=color,
                                            border_radius=8,
                                        ),
                                        ft.Text(type_name, weight=ft.FontWeight.BOLD),
                                    ]
                                ),
                                ft.Text(f"Posición: {lat:.6f}, {lon:.6f}"),
                                ft.Text(description),
                            ],
                            spacing=5,
                        ),
                        padding=10,
                    )
                )
            )
        
        # Actualizar UI
        if hasattr(self, 'drone_list'):
            self.drone_list.update()
        if hasattr(self, 'poi_list'):
            self.poi_list.update()
    
    def get_view(self) -> ft.Control:
        """Obtiene el control Flet para la vista de mapa."""
        if hasattr(self, 'fallback_view') and self.fallback_view:
            return self.fallback_view
        elif self.map_view:
            return self.map_view
        else:
            # Fallback si no se pudo crear el mapa
            if not hasattr(self, 'fallback_view'):
                self.fallback_view = self._create_fallback_view()
            return self.fallback_view
    
    def __del__(self):
        """Limpia archivos temporales y detiene el servidor al destruir el objeto."""
        # Detener servidor HTTP
        if hasattr(self, 'telemetry_server'):
            try:
                self.telemetry_server.stop()
            except:
                pass
        
        # Limpiar archivos temporales
        if self.temp_file and self.map_html_path and os.path.exists(self.map_html_path):
            try:
                os.unlink(self.map_html_path)
            except:
                pass
