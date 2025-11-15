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
from common.colors import (
    GREY_200, GREY_600, RED, GREEN, BLUE, AMBER, GREY,
    get_background_color, get_text_color, get_text_secondary_color
)
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
        on_map_click: Optional[Callable[[float, float], None]] = None,
        on_zone_created: Optional[Callable[[Dict[str, Any]], None]] = None,
        page: Optional[ft.Page] = None
    ):
        """
        Inicializa la vista de mapa.
        
        Args:
            initial_lat: Latitud del centro inicial del mapa
            initial_lon: Longitud del centro inicial del mapa
            zoom: Nivel de zoom inicial
            on_poi_click: Callback cuando se hace clic en un POI
            on_map_click: Callback cuando se hace clic en el mapa (para crear POIs)
            on_zone_created: Callback cuando se crea una zona de interés
            page: Instancia de página Flet para acceso al tema
        """
        self.initial_lat = initial_lat
        self.initial_lon = initial_lon
        self.zoom = zoom
        self.on_poi_click = on_poi_click
        self.on_map_click = on_map_click
        self.on_zone_created = on_zone_created
        self.page = page
        
        self.drones: Dict[str, Dict[str, Any]] = {}
        self.pois: Dict[str, Dict[str, Any]] = {}
        self.zones: Dict[str, Dict[str, Any]] = {}
        
        # Polling para leer eventos del mapa desde localStorage
        self.last_event_timestamp = 0
        
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
            
            # Agregar script de auto-refresh inmediatamente después de guardar
            self._add_auto_refresh_to_folium_html()
            
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
            background: transparent;
            border: none;
            box-shadow: none;
        }}
        .poi-icon svg {{
            filter: drop-shadow(0 2px 4px rgba(0,0,0,0.4));
        }}
        .map-controls {{
            background: white;
            padding: 10px;
            border-radius: 5px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.3);
            margin: 10px;
        }}
        .map-controls button {{
            display: block;
            width: 100%;
            margin: 5px 0;
            padding: 8px 12px;
            background: #2196F3;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 14px;
            font-weight: bold;
        }}
        .map-controls button:hover {{
            background: #1976D2;
        }}
        .map-controls button.active {{
            background: #4CAF50;
        }}
        .map-controls button.zone-mode {{
            background: #FF9800;
        }}
        .map-controls button.zone-mode:hover {{
            background: #F57C00;
        }}
        .map-controls .mode-indicator {{
            font-size: 11px;
            color: #666;
            margin-top: 5px;
            text-align: center;
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
        
        // ============================================
        // FUNCIONALIDAD DE INTERACCIÓN CON EL MAPA
        // ============================================
        
        // Variables para modos de interacción
        window.mapInteractionMode = 'click'; // 'click' para POI, 'rectangle' para zona
        window.isDrawingRectangle = false;
        window.rectangleStart = null;
        window.rectangleLayer = null;
        window.zones = window.zones || {{}};
        
        // Función para cambiar modo de interacción
        window.setMapMode = function(mode) {{
            window.mapInteractionMode = mode;
            console.log('Modo de mapa cambiado a:', mode);
            if (mode === 'rectangle') {{
                map.dragging.disable();
                map.doubleClickZoom.disable();
            }} else {{
                map.dragging.enable();
                map.doubleClickZoom.enable();
            }}
        }};
        
        // Escuchar clics en el mapa para crear POIs
        map.on('click', function(e) {{
            if (window.mapInteractionMode === 'click') {{
                var lat = e.latlng.lat;
                var lon = e.latlng.lng;
                console.log('Map click para POI:', lat, lon);
                
                // Enviar evento al servidor HTTP
                fetch('http://localhost:8765/api/events', {{
                    method: 'POST',
                    headers: {{'Content-Type': 'application/json'}},
                    body: JSON.stringify({{
                        type: 'map_click',
                        lat: lat,
                        lon: lon,
                        timestamp: Date.now()
                    }})
                }})
                .then(function(response) {{
                    if (response.ok) {{
                        console.log('Evento de clic enviado exitosamente al servidor');
                    }} else {{
                        console.warn('Error en respuesta del servidor:', response.status);
                    }}
                }})
                .catch(function(err) {{
                    console.error('Error enviando evento de clic:', err);
                }});
            }}
        }});
        
        // Funcionalidad de dibujo de rectángulo para zonas
        map.on('mousedown', function(e) {{
            if (window.mapInteractionMode === 'rectangle') {{
                window.isDrawingRectangle = true;
                window.rectangleStart = e.latlng;
                
                // Eliminar rectángulo anterior si existe
                if (window.rectangleLayer) {{
                    map.removeLayer(window.rectangleLayer);
                }}
                
                // Crear rectángulo temporal
                window.rectangleLayer = L.rectangle([window.rectangleStart, window.rectangleStart], {{
                    color: '#3388ff',
                    weight: 2,
                    fillColor: '#3388ff',
                    fillOpacity: 0.2
                }}).addTo(map);
            }}
        }});
        
        map.on('mousemove', function(e) {{
            if (window.isDrawingRectangle && window.rectangleStart) {{
                // Actualizar rectángulo mientras se arrastra
                var bounds = [window.rectangleStart, e.latlng];
                window.rectangleLayer.setBounds(bounds);
            }}
        }});
        
        map.on('mouseup', function(e) {{
            if (window.isDrawingRectangle && window.rectangleStart) {{
                window.isDrawingRectangle = false;
                
                var end = e.latlng;
                var bounds = {{
                    north: Math.max(window.rectangleStart.lat, end.lat),
                    south: Math.min(window.rectangleStart.lat, end.lat),
                    east: Math.max(window.rectangleStart.lng, end.lng),
                    west: Math.min(window.rectangleStart.lng, end.lng)
                }};
                
                // Eliminar rectángulo temporal
                if (window.rectangleLayer) {{
                    map.removeLayer(window.rectangleLayer);
                    window.rectangleLayer = null;
                }}
                
                // Crear zona
                var zoneId = 'zone_' + Date.now();
                var zone = {{
                    id: zoneId,
                    bounds: bounds,
                    timestamp: Date.now()
                }};
                
                // NO agregar a window.zones aquí - el servidor lo hará y el polling lo mostrará
                // window.zones[zoneId] = zone;  // Comentado: el polling lo manejará
                
                // Enviar evento al servidor HTTP
                fetch('http://localhost:8765/api/events', {{
                    method: 'POST',
                    headers: {{'Content-Type': 'application/json'}},
                    body: JSON.stringify({{
                        type: 'zone_created',
                        zone: zone,
                        timestamp: Date.now()
                    }})
                }}).then(function(response) {{
                    if (response.ok) {{
                        console.log('Zona enviada al servidor:', zoneId);
                    }}
                }}).catch(function(err) {{
                    console.warn('Error enviando evento de zona:', err);
                }});
                
                // Volver al modo click después de crear la zona
                window.mapInteractionMode = 'click';
                if (typeof updateControlButtons === 'function') {{
                    updateControlButtons();
                }}
                
                // Cambiar de vuelta a modo clic en el servidor
                window.setMapMode('click');
                
                console.log('Zona creada y enviada al servidor:', zoneId);
            }}
        }});
        
        // ============================================
        // INICIO DEL SCRIPT DE ACTUALIZACIÓN DEL MAPA (HTML PURO)
        // ============================================
        (function() {{
            console.log('=== SCRIPT DE MAPA CARGADO (HTML PURO) ===');
            console.log('Tiempo de carga:', new Date().toISOString());
            console.log('Leaflet disponible:', typeof L !== 'undefined');
            console.log('Document ready:', document.readyState);
        
        // Flag global para indicar que el mapa está listo
        window.mapReady = false;
        window.mapObject = map;  // Guardar referencia directa
        console.log('Variables globales inicializadas: mapReady =', window.mapReady, 'mapObject =', typeof map);
        
        // Función para crear icono de dron con rotación (versión simplificada)
        function createDroneIcon(batteryColor, heading) {{
            heading = heading || 0;
            var rotation = heading;
            batteryColor = batteryColor || '#4CAF50';
            
            // Usar icono más simple y confiable con emoji/unicode
            var iconHtml = '<div style="' +
                'width: 32px; height: 32px; ' +
                'background: ' + batteryColor + '; ' +
                'border-radius: 50%; ' +
                'border: 3px solid white; ' +
                'box-shadow: 0 2px 8px rgba(0,0,0,0.5); ' +
                'display: flex; ' +
                'align-items: center; ' +
                'justify-content: center; ' +
                'transform: rotate(' + rotation + 'deg); ' +
                'transform-origin: center;' +
                '">' +
                '<span style="color: white; font-size: 18px; font-weight: bold; line-height: 1;">✈</span>' +
                '</div>';
            
            return L.divIcon({{
                className: 'drone-icon',
                html: iconHtml,
                iconSize: [32, 32],
                iconAnchor: [16, 16],
                popupAnchor: [0, -16]
            }});
        }}
        
        // Función para actualizar/agregar dron (versión mejorada)
        window.updateDrone = function(droneId, lat, lon, heading, battery, altitude, velocity) {{
            // Validaciones iniciales
            if (!droneId || !lat || !lon || isNaN(lat) || isNaN(lon) || lat === 0 || lon === 0) {{
                console.warn('updateDrone: Parámetros inválidos', {{droneId: droneId, lat: lat, lon: lon}});
                return false;
            }}
            
            // Verificar que el mapa esté listo
            if (!window.mapReady && typeof map !== 'undefined' && map) {{
                // Si tenemos el mapa, marcarlo como listo
                try {{
                    var center = map.getCenter();
                    if (center) {{
                        window.mapReady = true;
                        window.mapObject = map;
                    }}
                }} catch(e) {{
                    // Mapa aún no está listo
                    console.warn('updateDrone: Mapa no está listo aún para', droneId);
                    setTimeout(function() {{
                        window.updateDrone(droneId, lat, lon, heading, battery, altitude, velocity);
                    }}, 500);
                    return false;
                }}
            }}
            
            if (typeof map === 'undefined' || !map) {{
                console.error('updateDrone: Mapa no está definido');
                return false;
            }}
            
            velocity = velocity || 0;
            heading = heading || 0;
            battery = battery || 100;
            var batteryColor = battery > 50 ? '#4CAF50' : (battery > 20 ? '#FFC107' : '#F44336');
            
            try {{
                if (droneMarkers[droneId]) {{
                    // Actualizar marcador existente
                    droneMarkers[droneId].setLatLng([lat, lon]);
                    var icon = createDroneIcon(batteryColor, heading);
                    droneMarkers[droneId].setIcon(icon);
                    droneMarkers[droneId].setPopupContent(
                        '<b>Dron: ' + droneId + '</b><br>' +
                        'Batería: ' + battery.toFixed(1) + '%<br>' +
                        'Altitud: ' + altitude.toFixed(1) + 'm<br>' +
                        'Velocidad: ' + velocity.toFixed(1) + ' m/s<br>' +
                        'Rumbo: ' + heading.toFixed(1) + '°'
                    );
                    return true;
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
                    console.log('Marcador creado exitosamente para', droneId, 'Total marcadores:', Object.keys(droneMarkers).length);
                    return true;
                }}
            }} catch(error) {{
                console.error('Error actualizando dron', droneId, ':', error);
                return false;
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
            window.mapReady = true;
            window.mapObject = map;
            console.log('Mapa listo, agregando drones iniciales...');
            
            // Pequeño delay para asegurar que todo esté inicializado
            setTimeout(function() {{
                for (var i = 0; i < initialDrones.length; i++) {{
                    var d = initialDrones[i];
                    if (d && d.id && d.lat && d.lon) {{
                        console.log('Agregando dron inicial:', d.id, 'en', d.lat, d.lon);
                        window.updateDrone(d.id, d.lat, d.lon, d.heading || 0, d.battery || 100, d.altitude || 0, d.velocity || 0);
                    }}
                }}
                
                for (var i = 0; i < initialPOIs.length; i++) {{
                    var p = initialPOIs[i];
                    if (p && p.id && p.lat && p.lon) {{
                        window.updatePOI(p.id, p.lat, p.lon, p.type || 'other', p.description || '');
                    }}
                }}
                console.log('Drones y POIs iniciales agregados. Total marcadores:', Object.keys(droneMarkers).length);
            }}, 300);
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
        
        // Solo comenzar polling después de que el mapa esté listo
        map.whenReady(function() {{
            window.mapReady = true;
            window.mapObject = map;
            console.log('Mapa listo, iniciando polling del servidor');
            
            // Iniciar polling después de un pequeño delay
            setTimeout(function() {{
                console.log('Iniciando polling del servidor en', apiUrl);
                updateFromServer();
                // Actualizar cada 1 segundo
                setInterval(updateFromServer, 1000);
            }}, 1000);
        }});
        
        console.log('=== FIN DE LA INICIALIZACIÓN DEL SCRIPT (HTML PURO) ===');
        }})(); // Ejecutar inmediatamente
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
            auto_refresh_script = f"""
        <script>
        // ============================================
        // INICIO DEL SCRIPT DE ACTUALIZACIÓN DEL MAPA
        // ============================================
        (function() {{
            console.log('=== SCRIPT DE MAPA CARGADO ===');
            console.log('Tiempo de carga:', new Date().toISOString());
            console.log('Leaflet disponible:', typeof L !== 'undefined');
            console.log('Document ready:', document.readyState);
        
        // ============================================
        // FUNCIONALIDAD DE INTERACCIÓN CON EL MAPA (FOLIUM)
        // ============================================
        
        // Variables para modos de interacción
        if (typeof window.mapInteractionMode === 'undefined') {{
            window.mapInteractionMode = 'click'; // 'click' para POI, 'rectangle' para zona
            window.isDrawingRectangle = false;
            window.rectangleStart = null;
            window.rectangleLayer = null;
            window.zones = window.zones || {{}};
        }}
        
        // Función para actualizar el estado visual de los botones
        function updateControlButtons() {{
            var poiBtn = document.getElementById('btn-create-poi');
            var zoneBtn = document.getElementById('btn-draw-zone');
            var modeText = document.getElementById('mode-indicator');
            
            if (poiBtn && zoneBtn && modeText) {{
                if (window.mapInteractionMode === 'click') {{
                    poiBtn.classList.add('active');
                    zoneBtn.classList.remove('active');
                    modeText.textContent = 'Modo: Clic en mapa para POI';
                }} else if (window.mapInteractionMode === 'rectangle') {{
                    poiBtn.classList.remove('active');
                    zoneBtn.classList.add('active');
                    modeText.textContent = 'Modo: Arrastra para dibujar zona';
                }}
            }}
        }}
        
        // Crear controles personalizados para el mapa
        function createMapControls(mapObj) {{
            if (!mapObj) return;
            
            // Crear contenedor de controles
            var controlDiv = document.createElement('div');
            controlDiv.className = 'map-controls';
            controlDiv.innerHTML = `
                <button id="btn-create-poi" onclick="window.setMapMode('click')">
                    📍 Crear POI
                </button>
                <button id="btn-draw-zone" class="zone-mode" onclick="window.setMapMode('rectangle')">
                    ⬜ Dibujar Zona
                </button>
                <div id="mode-indicator" class="mode-indicator">Modo: Clic en mapa para POI</div>
            `;
            
            // Agregar control al mapa (esquina superior derecha)
            var control = L.control({{position: 'topright'}});
            control.onAdd = function(map) {{
                return controlDiv;
            }};
            control.addTo(mapObj);
            
            // Inicializar estado de botones después de crear los controles
            setTimeout(function() {{
                updateControlButtons();
            }}, 100);
        }}
        
        // Función para cambiar modo de interacción
        if (typeof window.setMapMode === 'undefined') {{
            window.setMapMode = function(mode) {{
                window.mapInteractionMode = mode;
                console.log('Modo de mapa cambiado a:', mode);
                var mapObj = findMapObject();
                if (mapObj) {{
                    if (mode === 'rectangle') {{
                        mapObj.dragging.disable();
                        mapObj.doubleClickZoom.disable();
                    }} else {{
                        mapObj.dragging.enable();
                        mapObj.doubleClickZoom.enable();
                    }}
                }}
                // Actualizar botones
                updateControlButtons();
                // Notificar al servidor del cambio de modo
                fetch('http://localhost:8765/api/mode', {{
                    method: 'POST',
                    headers: {{'Content-Type': 'application/json'}},
                    body: JSON.stringify({{mode: mode}})
                }}).catch(function(err) {{
                    console.warn('Error enviando modo al servidor:', err);
                }});
            }};
        }}
        
        // Guardar estado del mapa periódicamente (sin recargar)
        function findMapObject() {{
            // Si ya tenemos el objeto del mapa guardado, usarlo
            if (window.mapObject && typeof window.mapObject.getCenter === 'function') {{
                try {{
                    var center = window.mapObject.getCenter();
                    if (center) return window.mapObject;
                }} catch(e) {{
                    // El objeto puede haber cambiado, buscar de nuevo
                    window.mapObject = null;
                }}
            }}
            
            // Método 1: Buscar variable global 'map' (Folium estándar)
            if (typeof map !== 'undefined' && map && typeof map.getCenter === 'function') {{
                window.mapObject = map;
                return map;
            }}
            
            // Método 2: Buscar en window con nombres comunes
            var commonNames = ['map', 'm', '_map', 'leafletMap', 'foliumMap'];
            for (var i = 0; i < commonNames.length; i++) {{
                try {{
                    if (window[commonNames[i]] && typeof window[commonNames[i]].getCenter === 'function') {{
                        window.mapObject = window[commonNames[i]];
                        return window.mapObject;
                    }}
                }} catch(e) {{
                    continue;
                }}
            }}
            
            // Método 3: Buscar desde el contenedor del mapa
            var mapContainer = document.querySelector('.leaflet-container');
            if (mapContainer && typeof L !== 'undefined' && L.Map) {{
                // Leaflet almacena la referencia en el contenedor
                if (mapContainer._leaflet_id && L.Map._instances) {{
                    var mapId = mapContainer._leaflet_id;
                    if (L.Map._instances[mapId]) {{
                        window.mapObject = L.Map._instances[mapId];
                        return window.mapObject;
                    }}
                }}
                // Buscar en todos los objetos del contenedor
                for (var key in mapContainer) {{
                    try {{
                        var obj = mapContainer[key];
                        if (obj && typeof obj === 'object' && typeof obj.getCenter === 'function') {{
                            window.mapObject = obj;
                            return obj;
                        }}
                    }} catch(e) {{
                        continue;
                    }}
                }}
            }}
            
            // Método 4: Buscar en todos los objetos de window
            for (var key in window) {{
                try {{
                    var obj = window[key];
                    if (obj && typeof obj === 'object' && 
                        typeof obj.getCenter === 'function' && 
                        typeof obj.getZoom === 'function' &&
                        obj._container && 
                        obj._container.classList && 
                        obj._container.classList.contains('leaflet-container')) {{
                        window.mapObject = obj;
                        return obj;
                    }}
                }} catch(e) {{
                    continue;
                }}
            }}
            
            return null;
        }}
        
        function saveMapState() {{
            var mapObj = findMapObject();
            if (mapObj) {{
                try {{
                    var center = mapObj.getCenter();
                    var zoom = mapObj.getZoom();
                    if (center && typeof center.lat === 'number' && typeof center.lng === 'number' && !isNaN(zoom) && zoom > 0) {{
                        localStorage.setItem('mapCenter', JSON.stringify({{lat: center.lat, lng: center.lng}}));
                        localStorage.setItem('mapZoom', zoom.toString());
                        return true;
                    }}
                }} catch(e) {{
                    // Silenciar errores
                }}
            }}
            return false;
        }}
        
        function restoreMapState() {{
            var mapObj = findMapObject();
            if (mapObj) {{
                var savedCenter = localStorage.getItem('mapCenter');
                var savedZoom = localStorage.getItem('mapZoom');
                if (savedCenter && savedZoom) {{
                    try {{
                        var center = JSON.parse(savedCenter);
                        var zoom = parseInt(savedZoom);
                        if (center && typeof center.lat === 'number' && typeof center.lng === 'number' && !isNaN(zoom) && zoom > 0) {{
                            mapObj.setView([center.lat, center.lng], zoom, {{reset: false}});
                            return true;
                        }}
                    }} catch(e) {{
                        // Silenciar errores
                    }}
                }}
            }}
            return false;
        }}
        
        // Flag global para indicar que el mapa está listo
        window.mapReady = false;
        window.mapObject = null;
        console.log('Variables globales inicializadas: mapReady =', window.mapReady);
        
        // Esperar a que el mapa esté completamente listo
        function waitForMapReady(callback) {{
            console.log('waitForMapReady: Iniciando búsqueda del mapa...');
            var attempts = 0;
            var maxAttempts = 50;  // Aumentar intentos
            function check() {{
                attempts++;
                var mapObj = findMapObject();
                if (mapObj) {{
                    try {{
                        var center = mapObj.getCenter();
                        var zoom = mapObj.getZoom();
                        if (center && typeof center.lat === 'number' && typeof center.lng === 'number' && !isNaN(zoom) && zoom > 0) {{
                            window.mapReady = true;
                            window.mapObject = mapObj;
                            console.log('Mapa listo después de', attempts, 'intentos');
                            callback(mapObj);
                            return;
                        }}
                    }} catch(e) {{
                        // Mapa aún no está listo
                        if (attempts % 10 === 0) {{
                            console.log('Esperando mapa... intento', attempts);
                        }}
                    }}
                }}
                if (attempts < maxAttempts) {{
                    setTimeout(check, 200);  // Verificar más frecuentemente
                }} else {{
                    console.error('Mapa no se pudo inicializar después de', maxAttempts, 'intentos');
                    window.mapReady = false;
                    callback(null);
                }}
            }}
            check();
        }}
        
        // Función legacy para compatibilidad
        function waitForMap(callback) {{
            waitForMapReady(callback);
        }}
        
                // Restaurar estado cuando el mapa esté listo
        waitForMap(function(mapObj) {{
            if (mapObj) {{
                    setTimeout(function() {{
                        restoreMapState();
                }}, 300);
            }}
        }});
        
        // Guardar estado periódicamente (cada 2 segundos) sin recargar
        setInterval(saveMapState, 2000);
        
        // Guardar estado cuando el usuario mueve o hace zoom en el mapa
        waitForMap(function(mapObj) {{
            if (mapObj) {{
                mapObj.on('moveend', saveMapState);
                mapObj.on('zoomend', saveMapState);
            }}
        }});
        
        // Guardar estado antes de cerrar
        window.addEventListener('beforeunload', saveMapState);
        
        // Agregar listeners de eventos del mapa (para Folium)
        function setupMapInteractions(mapObj) {{
            if (!mapObj) return;
            
            // Escuchar clics en el mapa para crear POIs
            mapObj.on('click', function(e) {{
                if (window.mapInteractionMode === 'click') {{
                    var lat = e.latlng.lat;
                    var lon = e.latlng.lng;
                    console.log('Map click para POI:', lat, lon);
                    
                    // Enviar evento al servidor HTTP
                    fetch('http://localhost:8765/api/events', {{
                        method: 'POST',
                        headers: {{'Content-Type': 'application/json'}},
                        body: JSON.stringify({{
                            type: 'map_click',
                            lat: lat,
                            lon: lon,
                            timestamp: Date.now()
                        }})
                    }})
                    .then(function(response) {{
                        if (response.ok) {{
                            console.log('Evento de clic enviado exitosamente al servidor');
                        }} else {{
                            console.warn('Error en respuesta del servidor:', response.status);
                        }}
                    }})
                    .catch(function(err) {{
                        console.error('Error enviando evento de clic:', err);
                    }});
                }}
            }});
            
            // Funcionalidad de dibujo de rectángulo para zonas
            mapObj.on('mousedown', function(e) {{
                if (window.mapInteractionMode === 'rectangle') {{
                    window.isDrawingRectangle = true;
                    window.rectangleStart = e.latlng;
                    
                    // Eliminar rectángulo anterior si existe
                    if (window.rectangleLayer) {{
                        mapObj.removeLayer(window.rectangleLayer);
                    }}
                    
                    // Crear rectángulo temporal
                    window.rectangleLayer = L.rectangle([window.rectangleStart, window.rectangleStart], {{
                        color: '#3388ff',
                        weight: 2,
                        fillColor: '#3388ff',
                        fillOpacity: 0.2
                    }}).addTo(mapObj);
                }}
            }});
            
            mapObj.on('mousemove', function(e) {{
                if (window.isDrawingRectangle && window.rectangleStart) {{
                    // Actualizar rectángulo mientras se arrastra
                    var bounds = [window.rectangleStart, e.latlng];
                    window.rectangleLayer.setBounds(bounds);
                }}
            }});
            
            mapObj.on('mouseup', function(e) {{
                if (window.isDrawingRectangle && window.rectangleStart) {{
                    window.isDrawingRectangle = false;
                    
                    var end = e.latlng;
                    var bounds = {{
                        north: Math.max(window.rectangleStart.lat, end.lat),
                        south: Math.min(window.rectangleStart.lat, end.lat),
                        east: Math.max(window.rectangleStart.lng, end.lng),
                        west: Math.min(window.rectangleStart.lng, end.lng)
                    }};
                    
                    // Crear zona
                    var zoneId = 'zone_' + Date.now();
                    var zone = {{
                        id: zoneId,
                        bounds: bounds,
                        timestamp: Date.now()
                    }};
                    
                    window.zones[zoneId] = zone;
                    
                    // Enviar evento al servidor HTTP
                    fetch('http://localhost:8765/api/events', {{
                        method: 'POST',
                        headers: {{'Content-Type': 'application/json'}},
                        body: JSON.stringify({{
                            type: 'zone_created',
                            zone: zone,
                            timestamp: Date.now()
                        }})
                    }}).catch(function(err) {{
                        console.warn('Error enviando evento de zona:', err);
                    }});
                    
                    console.log('Zona creada:', zone);
                    
                    // Cambiar de vuelta a modo clic
                    window.setMapMode('click');
                }}
            }});
        }}
        
        // Configurar interacciones cuando el mapa esté listo
        waitForMap(function(mapObj) {{
            if (mapObj) {{
                setupMapInteractions(mapObj);
                // Crear controles de botones en el mapa
                createMapControls(mapObj);
            }}
        }});
        
        // Funciones para actualizar drones y POIs (si no existen ya)
        console.log('Verificando si window.updateDrone existe:', typeof window.updateDrone);
        if (typeof window.updateDrone === 'undefined') {{
            console.log('Definiendo funciones updateDrone y updatePOI...');
            window.droneMarkers = window.droneMarkers || {{}};
            window.poiMarkers = window.poiMarkers || {{}};
            console.log('Marcadores inicializados. Drones:', Object.keys(window.droneMarkers).length, 'POIs:', Object.keys(window.poiMarkers).length);
            
            // Función para crear icono de dron con rotación (versión simplificada y más confiable)
            function createDroneIconFolium(batteryColor, heading) {{
                heading = heading || 0;
                var rotation = heading;
                batteryColor = batteryColor || '#4CAF50';
                
                // Usar icono más simple y confiable con emoji/unicode
                var iconHtml = '<div style="' +
                    'width: 32px; height: 32px; ' +
                    'background: ' + batteryColor + '; ' +
                    'border-radius: 50%; ' +
                    'border: 3px solid white; ' +
                    'box-shadow: 0 2px 8px rgba(0,0,0,0.5); ' +
                    'display: flex; ' +
                    'align-items: center; ' +
                    'justify-content: center; ' +
                    'transform: rotate(' + rotation + 'deg); ' +
                    'transform-origin: center;' +
                    '">' +
                    '<span style="color: white; font-size: 18px; font-weight: bold; line-height: 1;">✈</span>' +
                    '</div>';
                
                return L.divIcon({{
                    className: 'drone-icon',
                    html: iconHtml,
                    iconSize: [32, 32],
                    iconAnchor: [16, 16],
                    popupAnchor: [0, -16]
                }});
            }}
            
            window.updateDrone = function(droneId, lat, lon, heading, battery, altitude, velocity) {{
                // Validaciones iniciales
                if (!droneId || !lat || !lon || isNaN(lat) || isNaN(lon) || lat === 0 || lon === 0) {{
                    console.warn('updateDrone: Parámetros inválidos', {{droneId: droneId, lat: lat, lon: lon}});
                    return false;
                }}
                
                // Verificar que el mapa esté listo
                if (!window.mapReady) {{
                    console.warn('updateDrone: Mapa no está listo aún para', droneId);
                    // Reintentar después de un delay
                    setTimeout(function() {{
                        window.updateDrone(droneId, lat, lon, heading, battery, altitude, velocity);
                    }}, 500);
                    return false;
                }}
                
                var mapObj = findMapObject();
                if (!mapObj) {{
                    console.error('updateDrone: No se encontró el objeto del mapa para', droneId);
                    // Intentar resetear y buscar de nuevo
                    window.mapObject = null;
                    window.mapReady = false;
                    waitForMapReady(function(m) {{
                        if (m) {{
                            window.updateDrone(droneId, lat, lon, heading, battery, altitude, velocity);
                        }}
                    }});
                    return false;
                }}
                
                velocity = velocity || 0;
                heading = heading || 0;
                battery = battery || 100;
                var batteryColor = battery > 50 ? '#4CAF50' : (battery > 20 ? '#FFC107' : '#F44336');
                
                try {{
                    if (window.droneMarkers[droneId]) {{
                        // Actualizar marcador existente
                        window.droneMarkers[droneId].setLatLng([lat, lon]);
                        var icon = createDroneIconFolium(batteryColor, heading);
                        window.droneMarkers[droneId].setIcon(icon);
                        window.droneMarkers[droneId].setPopupContent(
                            '<b>Dron: ' + droneId + '</b><br>' +
                            'Batería: ' + battery.toFixed(1) + '%<br>' +
                            'Altitud: ' + altitude.toFixed(1) + 'm<br>' +
                            'Velocidad: ' + velocity.toFixed(1) + ' m/s<br>' +
                            'Rumbo: ' + heading.toFixed(1) + '°'
                        );
                        return true;
                    }} else {{
                        // Crear nuevo marcador
                        console.log('Creando nuevo marcador para', droneId, 'en', lat, lon);
                        var icon = createDroneIconFolium(batteryColor, heading);
                        var marker = L.marker([lat, lon], {{icon: icon}}).addTo(mapObj);
                        marker.bindPopup(
                            '<b>Dron: ' + droneId + '</b><br>' +
                            'Batería: ' + battery.toFixed(1) + '%<br>' +
                            'Altitud: ' + altitude.toFixed(1) + 'm<br>' +
                            'Velocidad: ' + velocity.toFixed(1) + ' m/s<br>' +
                            'Rumbo: ' + heading.toFixed(1) + '°'
                        );
                        window.droneMarkers[droneId] = marker;
                        console.log('Marcador creado exitosamente para', droneId, 'Total marcadores:', Object.keys(window.droneMarkers).length);
                        return true;
                    }}
                }} catch(error) {{
                    console.error('Error actualizando dron', droneId, ':', error);
                    return false;
                }}
            }};
            
            window.updatePOI = function(poiId, lat, lon, type, description) {{
                if (!poiId || !lat || !lon || lat === 0 || lon === 0) {{
                    console.warn('updatePOI: coordenadas inválidas', poiId, lat, lon);
                    return;
                }}
                
                // Todos los POIs se muestran en rojo
                var color = '#F44336';  // Rojo para todos los POIs
                var mapObj = findMapObject();
                if (!mapObj) {{
                    console.warn('updatePOI: mapa no disponible');
                    return;
                }}
                
                if (window.poiMarkers[poiId]) {{
                    // Actualizar marcador existente
                    window.poiMarkers[poiId].setLatLng([lat, lon]);
                    window.poiMarkers[poiId].setPopupContent('<b>' + (type || 'other').toUpperCase() + '</b><br>' + (description || ''));
                    // Actualizar icono a rojo si cambió
                    var pinSvg = '<svg width="24" height="32" viewBox="0 0 24 32" xmlns="http://www.w3.org/2000/svg">' +
                        '<path d="M12 0C7.58 0 4 3.58 4 8c0 6 8 16 8 16s8-10 8-16c0-4.42-3.58-8-8-8z" fill="' + color + '" stroke="white" stroke-width="1.5"/>' +
                        '<circle cx="12" cy="8" r="3" fill="white"/>' +
                        '</svg>';
                    var icon = L.divIcon({{
                        className: 'poi-icon',
                        html: pinSvg,
                        iconSize: [24, 32],
                        iconAnchor: [12, 32],
                        popupAnchor: [0, -32]
                    }});
                    window.poiMarkers[poiId].setIcon(icon);
                }} else {{
                    // Crear nuevo marcador con icono de pin más visible
                    // Usar un icono de pin SVG personalizado
                    var pinSvg = '<svg width="24" height="32" viewBox="0 0 24 32" xmlns="http://www.w3.org/2000/svg">' +
                        '<path d="M12 0C7.58 0 4 3.58 4 8c0 6 8 16 8 16s8-10 8-16c0-4.42-3.58-8-8-8z" fill="' + color + '" stroke="white" stroke-width="1.5"/>' +
                        '<circle cx="12" cy="8" r="3" fill="white"/>' +
                        '</svg>';
                    var icon = L.divIcon({{
                        className: 'poi-icon',
                        html: pinSvg,
                        iconSize: [24, 32],
                        iconAnchor: [12, 32],
                        popupAnchor: [0, -32]
                    }});
                    var marker = L.marker([lat, lon], {{icon: icon}}).addTo(mapObj);
                    marker.bindPopup('<b>' + (type || 'other').toUpperCase() + '</b><br>' + (description || ''));
                    window.poiMarkers[poiId] = marker;
                    console.log('POI creado en mapa:', poiId, lat, lon, type);
                }}
            }};
        }}
        
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
                        var poiCount = 0;
                        var poiKeys = Object.keys(data.pois);
                        if (updateCount === 1 || (updateCount % 20 === 0 && poiKeys.length > 0)) {{
                            console.log('Recibidos', poiKeys.length, 'POIs del servidor:', poiKeys);
                        }}
                        for (var poiId in data.pois) {{
                            if (data.pois.hasOwnProperty(poiId)) {{
                                var poi = data.pois[poiId];
                                if (poi && typeof poi === 'object') {{
                                    var lat = poi.latitude || poi.lat || 0;
                                    var lon = poi.longitude || poi.lon || 0;
                                    if (lat && lon && lat !== 0 && lon !== 0) {{
                                        window.updatePOI(
                                            poiId,
                                            lat,
                                            lon,
                                            poi.type || 'other',
                                            poi.description || ''
                                        );
                                        poiCount++;
                                    }} else {{
                                        if (updateCount % 20 === 0) {{
                                            console.warn('POI', poiId, 'tiene coordenadas inválidas:', lat, lon, poi);
                                        }}
                                    }}
                                }}
                            }}
                        }}
                        if (updateCount % 20 === 0 && poiCount > 0) {{
                            console.log('POIs actualizados en mapa:', poiCount, 'de', poiKeys.length);
                        }}
                        
                        // Limpiar POIs que ya no están en el servidor
                        var mapObj = findMapObject();
                        if (mapObj && window.poiMarkers) {{
                            for (var existingPoiId in window.poiMarkers) {{
                                if (!data.pois[existingPoiId]) {{
                                    // POI eliminado del servidor, remover del mapa
                                    if (window.poiMarkers[existingPoiId]) {{
                                        mapObj.removeLayer(window.poiMarkers[existingPoiId]);
                                        delete window.poiMarkers[existingPoiId];
                                        if (updateCount % 20 === 0) {{
                                            console.log('POI eliminado del mapa:', existingPoiId);
                                        }}
                                    }}
                                }}
                            }}
                        }}
                    }}
                    
                    // Actualizar zonas
                    if (data.zones && typeof data.zones === 'object') {{
                        var mapObj = findMapObject();
                        if (mapObj) {{
                            // Limpiar zonas existentes que no están en el servidor
                            for (var zoneId in window.zones) {{
                                if (!data.zones[zoneId]) {{
                                    if (window.zones[zoneId].layer) {{
                                        mapObj.removeLayer(window.zones[zoneId].layer);
                                    }}
                                    delete window.zones[zoneId];
                                }}
                            }}
                            
                            // Agregar/actualizar zonas del servidor
                            for (var zoneId in data.zones) {{
                                if (data.zones.hasOwnProperty(zoneId)) {{
                                    var zone = data.zones[zoneId];
                                    if (zone && zone.bounds) {{
                                        if (!window.zones[zoneId]) {{
                                            // Crear nueva zona
                                            var bounds = zone.bounds;
                                            var rectangle = L.rectangle([
                                                [bounds.south, bounds.west],
                                                [bounds.north, bounds.east]
                                            ], {{
                                                color: '#3388ff',
                                                fillColor: '#3388ff',
                                                fillOpacity: 0.2,
                                                weight: 2
                                            }}).addTo(mapObj);
                                            
                                            window.zones[zoneId] = {{
                                                id: zoneId,
                                                bounds: bounds,
                                                layer: rectangle,
                                                timestamp: zone.timestamp || Date.now()
                                            }};
                                            
                                            if (updateCount % 20 === 0) {{
                                                console.log('Zona creada en mapa:', zoneId);
                                            }}
                                        }} else {{
                                            // Actualizar zona existente si cambió
                                            var existingZone = window.zones[zoneId];
                                            if (existingZone && existingZone.layer) {{
                                                var bounds = zone.bounds;
                                                existingZone.layer.setBounds([
                                                    [bounds.south, bounds.west],
                                                    [bounds.north, bounds.east]
                                                ]);
                                                existingZone.bounds = bounds;
                                            }}
                                        }}
                                    }}
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
        
        // Solo comenzar polling después de que el mapa esté listo
        console.log('Iniciando waitForMapReady para comenzar polling...');
        waitForMapReady(function(mapObj) {{
            if (mapObj) {{
                console.log('✓ Mapa listo, iniciando actualizaciones de drones y POIs');
                console.log('Centro del mapa:', mapObj.getCenter());
                console.log('Zoom:', mapObj.getZoom());
                
                // Restaurar estado del mapa
                setTimeout(function() {{
                    restoreMapState();
                }}, 300);
                
                // Iniciar polling después de un pequeño delay
                setTimeout(function() {{
                    console.log('=== INICIANDO POLLING DEL SERVIDOR ===');
                    console.log('URL del servidor:', apiUrl);
                    updateFromServer();
                    // Actualizar cada 1 segundo
                    var pollInterval = setInterval(updateFromServer, 1000);
                    console.log('Polling configurado cada 1 segundo. Interval ID:', pollInterval);
                    
                    // Polling para leer modo del mapa y cambiar si es necesario
                    setInterval(function() {{
                        fetch('http://localhost:8765/api/mode')
                            .then(function(response) {{ return response.json(); }})
                            .then(function(data) {{
                                if (data.mode && window.mapInteractionMode !== data.mode) {{
                                    if (typeof window.setMapMode === 'function') {{
                                        window.setMapMode(data.mode);
                                    }}
                                }}
                            }})
                            .catch(function(err) {{
                                // Ignorar errores silenciosamente
                            }});
                    }}, 500);
                }}, 1000);
            }} else {{
                console.error('✗ ERROR: No se pudo inicializar el mapa, el polling no comenzará');
                console.error('El mapa puede no estar disponible o no se encontró el objeto del mapa');
            }}
        }});
        
        console.log('=== FIN DE LA INICIALIZACIÓN DEL SCRIPT ===');
        }})(); // Ejecutar inmediatamente
        </script>
"""
            
            # Insertar antes de </body> o al final si no hay </body>
            # Usar replace solo una vez para evitar reemplazos múltiples
            script_inserted = False
            if '</body>' in html_content:
                # Buscar la última ocurrencia de </body>
                last_body_index = html_content.rfind('</body>')
                html_content = html_content[:last_body_index] + auto_refresh_script + '\n    </body>' + html_content[last_body_index + 7:]
                script_inserted = True
            elif '</html>' in html_content:
                # Buscar la última ocurrencia de </html>
                last_html_index = html_content.rfind('</html>')
                html_content = html_content[:last_html_index] + auto_refresh_script + '\n</html>' + html_content[last_html_index + 7:]
                script_inserted = True
            else:
                html_content += auto_refresh_script
                script_inserted = True
            
            if script_inserted:
                import logging
                logger = logging.getLogger(__name__)
                logger.info(f"✓ Script de actualización agregado al HTML. Tamaño del script: {len(auto_refresh_script)} caracteres")
                logger.debug(f"HTML actualizado. Tamaño total: {len(html_content)} caracteres")
            
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
        import logging
        logger = logging.getLogger(__name__)
        poi_id = poi.get("id")
        if poi_id:
            logger.info(f"MapView.add_poi: Agregando POI {poi_id} con datos: {poi}")
            self.pois[poi_id] = poi
            # Actualizar servidor HTTP (el JavaScript hará polling)
            if self.telemetry_server:
                self.telemetry_server.update_poi(poi)
                logger.info(f"POI {poi_id} actualizado en servidor HTTP")
            else:
                logger.error("No hay servidor de telemetría disponible para actualizar POI")
            
            # Si estamos usando fallback, actualizar vista alternativa
            if hasattr(self, 'poi_list'):
                self._update_fallback_view()
        else:
            logger.warning(f"MapView.add_poi: POI sin ID, ignorando: {poi}")
    
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
                        weight=ft.FontWeight.BOLD,
                        color=get_text_color(self.page) if self.page else "#000000"
                    ),
                    ft.Text(
                        "Nota: WebView no está soportado en esta plataforma.\n"
                        "El mapa HTML se guardó en: " + (self.map_html_path or "N/A"),
                        size=11,
                        color=get_text_secondary_color(self.page) if self.page else GREY_600,
                    ),
                    ft.ElevatedButton(
                        "Abrir Mapa en Navegador",
                        icon=ft.Icons.OPEN_IN_BROWSER,
                        on_click=self._open_map_in_browser,
                    ),
                    ft.Divider(),
                    ft.Text(
                        "Drones en el Mapa:", 
                        weight=ft.FontWeight.BOLD, 
                        size=14,
                        color=get_text_color(self.page) if self.page else "#000000"
                    ),
                    ft.Container(
                        content=self.drone_list,
                        height=list_height,
                        expand=False,
                    ),
                    ft.Divider(),
                    ft.Text(
                        "POIs en el Mapa:", 
                        weight=ft.FontWeight.BOLD, 
                        size=14,
                        color=get_text_color(self.page) if self.page else "#000000"
                    ),
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
            bgcolor=get_background_color(self.page) if self.page else GREY_200,
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
        
        # Colores adaptativos del tema
        # Asegurar que siempre tengamos un color válido
        if self.page:
            text_color = get_text_color(self.page)
            text_secondary = get_text_secondary_color(self.page)
        else:
            # Fallback para cuando no hay página (modo claro por defecto)
            text_color = "#000000"  # Negro para modo claro
            text_secondary = GREY_600  # Gris oscuro para modo claro
        
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
                                        ft.Text(drone_id, weight=ft.FontWeight.BOLD, color=text_color),
                                    ]
                                ),
                                ft.Text(f"Posición: {lat:.6f}, {lon:.6f}", color=text_secondary),
                                ft.Text(f"Batería: {battery:.1f}%", color=battery_color),
                                ft.Text(f"Altitud: {altitude:.1f}m", color=text_secondary),
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
                                        ft.Text(type_name, weight=ft.FontWeight.BOLD, color=text_color),
                                    ]
                                ),
                                ft.Text(f"Posición: {lat:.6f}, {lon:.6f}", color=text_color),
                                ft.Text(description, color=text_color),
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
