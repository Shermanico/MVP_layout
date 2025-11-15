"""
Adaptador de entrada: Vista del mapa interactivo.
Gestiona visualización de mapa con actualizaciones incrementales.
"""
import flet as ft
import tempfile
import os
import platform
from typing import Dict, Any, Optional, Callable
from adapters.output.http.telemetry_server import TelemetryServer
from infrastructure.config.constants import POIType


class MapView:
    """
    Vista del mapa interactivo que muestra drones y POIs.
    Usa Folium si está disponible, o HTML/JavaScript puro como fallback.
    """
    
    def __init__(
        self,
        initial_lat: float = 20.9674,
        initial_lon: float = -89.5926,
        zoom: int = 13,
        on_poi_click: Optional[Callable[[str], None]] = None,
        on_map_click: Optional[Callable[[float, float], None]] = None
    ):
        """
        Inicializa la vista del mapa.
        
        Args:
            initial_lat: Latitud inicial
            initial_lon: Longitud inicial
            zoom: Nivel de zoom inicial
            on_poi_click: Callback cuando se hace clic en un POI
            on_map_click: Callback cuando se hace clic en el mapa
        """
        self.initial_lat = initial_lat
        self.initial_lon = initial_lon
        self.zoom = zoom
        self.on_poi_click = on_poi_click
        self.on_map_click = on_map_click
        
        self.drones: Dict[str, Dict[str, Any]] = {}
        self.pois: Dict[str, Dict[str, Any]] = {}
        self.html_file: Optional[str] = None
        
        # Iniciar servidor HTTP
        self.telemetry_server = TelemetryServer(port=8765)
        self.telemetry_server.start()
        
        # Crear mapa
        self.map_html = self._create_map()
        
        # Crear vista
        self.view = self._create_view()
    
    def _create_map(self) -> str:
        """Crea el mapa HTML."""
        # Intentar usar Folium
        try:
            import folium
            return self._create_folium_map()
        except ImportError:
            return self._create_leaflet_map()
    
    def _create_folium_map(self) -> str:
        """Crea mapa usando Folium."""
        import folium
        
        m = folium.Map(
            location=[self.initial_lat, self.initial_lon],
            zoom_start=self.zoom,
            tiles='OpenStreetMap'
        )
        
        # Agregar JavaScript para polling
        polling_js = """
        <script>
        let droneMarkers = {};
        let poiMarkers = {};
        let map = null;
        
        function initMap() {
            // El mapa ya está inicializado por Folium
            map = window.map || window.m;
            if (!map) {
                setTimeout(initMap, 100);
                return;
            }
            
            // Restaurar estado del mapa
            const savedZoom = localStorage.getItem('mapZoom');
            const savedCenter = localStorage.getItem('mapCenter');
            if (savedZoom && savedCenter) {
                const center = JSON.parse(savedCenter);
                map.setView(center, parseInt(savedZoom));
            }
            
            // Guardar estado cuando cambia
            map.on('moveend', function() {
                localStorage.setItem('mapZoom', map.getZoom());
                localStorage.setItem('mapCenter', JSON.stringify(map.getCenter()));
            });
            
            // Iniciar polling
            setInterval(updateFromServer, 1000);
            updateFromServer();
        }
        
        function updateFromServer() {
            fetch('http://localhost:8765/api/data')
                .then(response => response.json())
                .then(data => {
                    updateDrones(data.drones || {});
                    updatePOIs(data.pois || {});
                })
                .catch(error => console.error('Error:', error));
        }
        
        function updateDrones(drones) {
            for (const [droneId, drone] of Object.entries(drones)) {
                if (!droneMarkers[droneId]) {
                    createDroneMarker(droneId, drone);
                } else {
                    updateDroneMarker(droneId, drone);
                }
            }
        }
        
        function createDroneMarker(droneId, drone) {
            const icon = createDroneIcon(drone.battery || 100);
            const marker = L.marker([drone.latitude, drone.longitude], {
                icon: icon,
                rotationAngle: drone.heading || 0
            }).addTo(map);
            
            marker.bindPopup(createDronePopup(drone));
            droneMarkers[droneId] = marker;
        }
        
        function updateDroneMarker(droneId, drone) {
            const marker = droneMarkers[droneId];
            if (marker) {
                marker.setLatLng([drone.latitude, drone.longitude]);
                marker.setIcon(createDroneIcon(drone.battery || 100));
                marker.setPopupContent(createDronePopup(drone));
            }
        }
        
        function createDroneIcon(battery) {
            const color = battery > 50 ? 'green' : (battery > 20 ? 'orange' : 'red');
            return L.divIcon({
                className: 'drone-icon',
                html: `<div style="color: ${color}; font-size: 24px;">✈</div>`,
                iconSize: [30, 30],
                iconAnchor: [15, 15]
            });
        }
        
        function createDronePopup(drone) {
            return `
                <b>${drone.drone_id}</b><br>
                Batería: ${drone.battery?.toFixed(1) || 0}%<br>
                Altitud: ${drone.altitude?.toFixed(1) || 0} m<br>
                Velocidad: ${drone.velocity?.toFixed(1) || 0} m/s<br>
                Rumbo: ${drone.heading?.toFixed(0) || 0}°
            `;
        }
        
        function updatePOIs(pois) {
            for (const [poiId, poi] of Object.entries(pois)) {
                if (!poiMarkers[poiId]) {
                    createPOIMarker(poiId, poi);
                }
            }
        }
        
        function createPOIMarker(poiId, poi) {
            const colors = {
                'hazard': 'red',
                'target': 'blue',
                'checkpoint': 'orange',
                'landing_zone': 'green',
                'other': 'gray'
            };
            const color = colors[poi.type] || 'gray';
            
            const marker = L.circleMarker([poi.latitude, poi.longitude], {
                color: color,
                fillColor: color,
                fillOpacity: 0.7,
                radius: 8
            }).addTo(map);
            
            marker.bindPopup(`
                <b>${poi.type}</b><br>
                ${poi.description || 'Sin descripción'}
            `);
            poiMarkers[poiId] = marker;
        }
        
        window.addEventListener('load', initMap);
        </script>
        """
        
        # Guardar en archivo temporal
        html_content = m._repr_html_()
        html_content = html_content.replace('</body>', polling_js + '</body>')
        
        # Guardar en archivo temporal
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as f:
            f.write(html_content)
            self.html_file = f.name
        
        return html_content
    
    def _create_leaflet_map(self) -> str:
        """Crea mapa usando Leaflet.js puro."""
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Mapa de Drones</title>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <style>
        body {{ margin: 0; padding: 0; }}
        #map {{ height: 100vh; width: 100%; }}
    </style>
</head>
<body>
    <div id="map"></div>
    <script>
        const map = L.map('map').setView([{self.initial_lat}, {self.initial_lon}], {self.zoom});
        L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
            attribution: '© OpenStreetMap contributors'
        }}).addTo(map);
        
        let droneMarkers = {{}};
        let poiMarkers = {{}};
        
        // Restaurar estado
        const savedZoom = localStorage.getItem('mapZoom');
        const savedCenter = localStorage.getItem('mapCenter');
        if (savedZoom && savedCenter) {{
            const center = JSON.parse(savedCenter);
            map.setView(center, parseInt(savedZoom));
        }}
        
        // Guardar estado
        map.on('moveend', function() {{
            localStorage.setItem('mapZoom', map.getZoom());
            localStorage.setItem('mapCenter', JSON.stringify(map.getCenter()));
        }});
        
        function updateFromServer() {{
            fetch('http://localhost:8765/api/data')
                .then(response => response.json())
                .then(data => {{
                    updateDrones(data.drones || {{}});
                    updatePOIs(data.pois || {{}});
                }})
                .catch(error => console.error('Error:', error));
        }}
        
        function updateDrones(drones) {{
            for (const [droneId, drone] of Object.entries(drones)) {{
                if (!droneMarkers[droneId]) {{
                    createDroneMarker(droneId, drone);
                }} else {{
                    updateDroneMarker(droneId, drone);
                }}
            }}
        }}
        
        function createDroneMarker(droneId, drone) {{
            const color = drone.battery > 50 ? 'green' : (drone.battery > 20 ? 'orange' : 'red');
            const icon = L.divIcon({{
                className: 'drone-icon',
                html: `<div style="color: ${{color}}; font-size: 24px; transform: rotate(${{drone.heading || 0}}deg);">✈</div>`,
                iconSize: [30, 30],
                iconAnchor: [15, 15]
            }});
            
            const marker = L.marker([drone.latitude, drone.longitude], {{icon: icon}}).addTo(map);
            marker.bindPopup(`
                <b>${{droneId}}</b><br>
                Batería: ${{drone.battery?.toFixed(1) || 0}}%<br>
                Altitud: ${{drone.altitude?.toFixed(1) || 0}} m<br>
                Velocidad: ${{drone.velocity?.toFixed(1) || 0}} m/s<br>
                Rumbo: ${{drone.heading?.toFixed(0) || 0}}°
            `);
            droneMarkers[droneId] = marker;
        }}
        
        function updateDroneMarker(droneId, drone) {{
            const marker = droneMarkers[droneId];
            if (marker) {{
                marker.setLatLng([drone.latitude, drone.longitude]);
                const color = drone.battery > 50 ? 'green' : (drone.battery > 20 ? 'orange' : 'red');
                const icon = L.divIcon({{
                    className: 'drone-icon',
                    html: `<div style="color: ${{color}}; font-size: 24px; transform: rotate(${{drone.heading || 0}}deg);">✈</div>`,
                    iconSize: [30, 30],
                    iconAnchor: [15, 15]
                }});
                marker.setIcon(icon);
                marker.setPopupContent(`
                    <b>${{droneId}}</b><br>
                    Batería: ${{drone.battery?.toFixed(1) || 0}}%<br>
                    Altitud: ${{drone.altitude?.toFixed(1) || 0}} m<br>
                    Velocidad: ${{drone.velocity?.toFixed(1) || 0}} m/s<br>
                    Rumbo: ${{drone.heading?.toFixed(0) || 0}}°
                `);
            }}
        }}
        
        function updatePOIs(pois) {{
            for (const [poiId, poi] of Object.entries(pois)) {{
                if (!poiMarkers[poiId]) {{
                    createPOIMarker(poiId, poi);
                }}
            }}
        }}
        
        function createPOIMarker(poiId, poi) {{
            const colors = {{
                'hazard': 'red',
                'target': 'blue',
                'checkpoint': 'orange',
                'landing_zone': 'green',
                'other': 'gray'
            }};
            const color = colors[poi.type] || 'gray';
            
            const marker = L.circleMarker([poi.latitude, poi.longitude], {{
                color: color,
                fillColor: color,
                fillOpacity: 0.7,
                radius: 8
            }}).addTo(map);
            
            marker.bindPopup(`
                <b>${{poi.type}}</b><br>
                ${{poi.description || 'Sin descripción'}}
            `);
            poiMarkers[poiId] = marker;
        }}
        
        // Iniciar polling
        setInterval(updateFromServer, 1000);
        updateFromServer();
    </script>
</body>
</html>
        """
        
        # Guardar en archivo temporal
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as f:
            f.write(html_content)
            self.html_file = f.name
        
        return html_content
    
    def _create_view(self) -> ft.Container:
        """Crea la vista del mapa."""
        # En Windows, usar vista alternativa
        if platform.system() == "Windows":
            return self._create_fallback_view()
        
        # Intentar usar WebView
        try:
            if self.html_file:
                return ft.WebView(
                    url=f"file://{self.html_file}",
                    expand=True
                )
        except:
            pass
        
        # Fallback
        return self._create_fallback_view()
    
    def _create_fallback_view(self) -> ft.Container:
        """Crea vista alternativa cuando WebView no está disponible."""
        import webbrowser
        
        def open_map(e):
            if self.html_file:
                webbrowser.open(f"file://{self.html_file}")
        
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text(
                        "Vista del Mapa",
                        size=18,
                        weight=ft.FontWeight.BOLD
                    ),
                    ft.ElevatedButton(
                        "Abrir Mapa en Navegador",
                        icon=ft.Icons.OPEN_IN_BROWSER,
                        on_click=open_map
                    ),
                    ft.Divider(),
                    ft.Text("Drones en el mapa:", weight=ft.FontWeight.BOLD),
                    ft.Container(
                        content=ft.Column(
                            controls=[],
                            scroll=ft.ScrollMode.AUTO,
                            height=200
                        )
                    ),
                    ft.Text("POIs en el mapa:", weight=ft.FontWeight.BOLD),
                    ft.Container(
                        content=ft.Column(
                            controls=[],
                            scroll=ft.ScrollMode.AUTO,
                            height=200
                        )
                    )
                ],
                spacing=10
            ),
            padding=ft.padding.all(15),
            expand=True
        )
    
    def update_drone(self, telemetry: Dict[str, Any]) -> None:
        """Actualiza la telemetría de un dron en el mapa."""
        drone_id = telemetry.get("drone_id", "UNKNOWN")
        self.drones[drone_id] = telemetry
        self.telemetry_server.update_telemetry(telemetry)
    
    def add_poi(self, poi: Dict[str, Any]) -> None:
        """Agrega un POI al mapa."""
        poi_id = poi.get("id", "")
        if poi_id:
            self.pois[poi_id] = poi
            self.telemetry_server.update_poi(poi)
    
    def remove_poi(self, poi_id: str) -> None:
        """Elimina un POI del mapa."""
        if poi_id in self.pois:
            del self.pois[poi_id]
        self.telemetry_server.remove_poi(poi_id)
    
    def get_view(self) -> ft.Control:
        """Obtiene la vista del mapa."""
        return self.view
    
    def cleanup(self) -> None:
        """Limpia recursos."""
        if self.html_file and os.path.exists(self.html_file):
            try:
                os.remove(self.html_file)
            except:
                pass
        self.telemetry_server.stop()

