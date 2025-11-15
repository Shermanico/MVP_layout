"""
Servidor HTTP simple para servir datos de telemetría y POIs como JSON.
Permite actualizaciones incrementales del mapa sin recargar la página.
"""
import json
import threading
from typing import Dict, Any, Optional, List
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import logging

logger = logging.getLogger(__name__)


class TelemetryDataHandler(BaseHTTPRequestHandler):
    """Manejador HTTP para servir datos de telemetría."""
    
    def __init__(self, *args, data_store=None, **kwargs):
        self.data_store = data_store
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        """Maneja peticiones GET."""
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        
        if path == '/api/telemetry':
            # Servir todos los datos de telemetría
            self._send_json_response(self.data_store.get_all_telemetry() if self.data_store else {})
        elif path == '/api/pois':
            # Servir todos los POIs
            self._send_json_response(self.data_store.get_all_pois() if self.data_store else {})
        elif path == '/api/data':
            # Servir telemetría y POIs juntos
            data = {
                'drones': self.data_store.get_all_telemetry() if self.data_store else {},
                'pois': self.data_store.get_all_pois() if self.data_store else {},
                'zones': self.data_store.get_all_zones() if self.data_store else {}
            }
            self._send_json_response(data)
        elif path == '/api/events':
            # Leer eventos del mapa (desde localStorage del navegador)
            # El JavaScript guarda eventos aquí y Python los lee
            events = self.data_store.get_map_events() if self.data_store else []
            self._send_json_response({'events': events})
        elif path == '/api/mode':
            # Obtener o establecer modo del mapa
            query_params = parse_qs(parsed_path.query)
            if 'mode' in query_params:
                # Establecer modo
                mode = query_params['mode'][0]
                if self.data_store:
                    self.data_store.set_map_mode(mode)
                self._send_json_response({'mode': mode, 'status': 'ok'})
            else:
                # Obtener modo
                mode = self.data_store.get_map_mode() if self.data_store else 'click'
                self._send_json_response({'mode': mode})
        else:
            self._send_error(404, "Not Found")
    
    def do_POST(self):
        """Maneja peticiones POST."""
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        
        if path == '/api/events':
            # Recibir evento del mapa desde JavaScript
            try:
                content_length = int(self.headers.get('Content-Length', 0))
                post_data = self.rfile.read(content_length)
                event = json.loads(post_data.decode('utf-8'))
                
                if self.data_store:
                    self.data_store.add_map_event(event)
                
                self._send_json_response({'status': 'ok'})
            except Exception as e:
                logger.error(f"Error procesando evento: {e}")
                self._send_error(400, str(e))
        elif path == '/api/mode':
            # Recibir cambio de modo del mapa desde JavaScript
            try:
                content_length = int(self.headers.get('Content-Length', 0))
                post_data = self.rfile.read(content_length)
                data = json.loads(post_data.decode('utf-8'))
                
                if self.data_store and 'mode' in data:
                    self.data_store.set_map_mode(data['mode'])
                
                self._send_json_response({'status': 'ok', 'mode': data.get('mode', 'click')})
            except Exception as e:
                logger.error(f"Error procesando modo: {e}")
                self._send_error(400, str(e))
        else:
            self._send_error(404, "Not Found")
    
    def _send_json_response(self, data: Dict[str, Any]):
        """Envía una respuesta JSON."""
        try:
            json_data = json.dumps(data, default=str)
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')  # CORS
            self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type')
            self.end_headers()
            self.wfile.write(json_data.encode('utf-8'))
        except Exception as e:
            logger.error(f"Error enviando respuesta JSON: {e}")
            self._send_error(500, str(e))
    
    def _send_error(self, code: int, message: str):
        """Envía una respuesta de error."""
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        error_data = json.dumps({'error': message})
        self.wfile.write(error_data.encode('utf-8'))
    
    def do_OPTIONS(self):
        """Maneja peticiones OPTIONS para CORS."""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def log_message(self, format, *args):
        """Suprime los logs del servidor HTTP."""
        pass  # No mostrar logs del servidor HTTP


class TelemetryDataStore:
    """Almacén de datos de telemetría y POIs."""
    
    def __init__(self):
        self.telemetry: Dict[str, Dict[str, Any]] = {}
        self.pois: Dict[str, Dict[str, Any]] = {}
        self.zones: Dict[str, Dict[str, Any]] = {}
        self.map_events: List[Dict[str, Any]] = []  # Eventos del mapa (clic, zonas, etc.)
        self.map_mode: str = "click"  # Modo de interacción del mapa
        self.lock = threading.Lock()
    
    def update_telemetry(self, telemetry: Dict[str, Any]):
        """Actualiza telemetría de un dron."""
        drone_id = telemetry.get('drone_id')
        if drone_id:
            with self.lock:
                self.telemetry[drone_id] = telemetry.copy()
    
    def update_poi(self, poi: Dict[str, Any]):
        """Actualiza o agrega un POI."""
        poi_id = poi.get('id')
        if poi_id:
            with self.lock:
                self.pois[poi_id] = poi.copy()
    
    def remove_poi(self, poi_id: str):
        """Elimina un POI."""
        with self.lock:
            if poi_id in self.pois:
                del self.pois[poi_id]
    
    def get_all_telemetry(self) -> Dict[str, Dict[str, Any]]:
        """Obtiene todos los datos de telemetría."""
        with self.lock:
            return {k: v.copy() for k, v in self.telemetry.items()}
    
    def get_all_pois(self) -> Dict[str, Dict[str, Any]]:
        """Obtiene todos los POIs."""
        with self.lock:
            return {k: v.copy() for k, v in self.pois.items()}
    
    def update_zone(self, zone: Dict[str, Any]):
        """Actualiza o agrega una zona de interés."""
        zone_id = zone.get('id')
        if zone_id:
            with self.lock:
                self.zones[zone_id] = zone.copy()
    
    def remove_zone(self, zone_id: str):
        """Elimina una zona de interés."""
        with self.lock:
            if zone_id in self.zones:
                del self.zones[zone_id]
    
    def get_all_zones(self) -> Dict[str, Dict[str, Any]]:
        """Obtiene todas las zonas de interés."""
        with self.lock:
            return {k: v.copy() for k, v in self.zones.items()}
    
    def add_map_event(self, event: Dict[str, Any]):
        """Agrega un evento del mapa."""
        import logging
        logger = logging.getLogger(__name__)
        with self.lock:
            logger.info(f"Agregando evento al almacén: {event.get('type', 'unknown')}")
            self.map_events.append(event)
            # Mantener solo los últimos 100 eventos
            if len(self.map_events) > 100:
                self.map_events = self.map_events[-100:]
    
    def get_map_events(self) -> List[Dict[str, Any]]:
        """Obtiene y limpia los eventos del mapa."""
        with self.lock:
            events = self.map_events.copy()
            self.map_events.clear()
            return events
    
    def set_map_mode(self, mode: str):
        """Establece el modo de interacción del mapa."""
        with self.lock:
            self.map_mode = mode
    
    def get_map_mode(self) -> str:
        """Obtiene el modo de interacción del mapa."""
        with self.lock:
            return self.map_mode


class TelemetryServer:
    """Servidor HTTP para servir datos de telemetría."""
    
    def __init__(self, port: int = 8765):
        self.port = port
        self.data_store = TelemetryDataStore()
        self.server: Optional[HTTPServer] = None
        self.server_thread: Optional[threading.Thread] = None
        self.running = False
    
    def start(self):
        """Inicia el servidor en un hilo separado."""
        if self.running:
            return
        
        def handler_factory(*args, **kwargs):
            return TelemetryDataHandler(*args, data_store=self.data_store, **kwargs)
        
        try:
            self.server = HTTPServer(('localhost', self.port), handler_factory)
            self.running = True
            
            def run_server():
                logger.info(f"Servidor de telemetría iniciado en http://localhost:{self.port}")
                try:
                    self.server.serve_forever()
                except Exception as e:
                    if self.running:
                        logger.error(f"Error en servidor de telemetría: {e}")
            
            self.server_thread = threading.Thread(target=run_server, daemon=True)
            self.server_thread.start()
            logger.info(f"Servidor de telemetría iniciado en puerto {self.port}")
        except Exception as e:
            logger.error(f"Error iniciando servidor de telemetría: {e}")
            self.running = False
    
    def stop(self):
        """Detiene el servidor."""
        self.running = False
        if self.server:
            try:
                self.server.shutdown()
                self.server.server_close()
            except:
                pass
        logger.info("Servidor de telemetría detenido")
    
    def update_telemetry(self, telemetry: Dict[str, Any]):
        """Actualiza telemetría en el almacén."""
        self.data_store.update_telemetry(telemetry)
    
    def update_poi(self, poi: Dict[str, Any]):
        """Actualiza POI en el almacén."""
        self.data_store.update_poi(poi)
    
    def remove_poi(self, poi_id: str):
        """Elimina POI del almacén."""
        self.data_store.remove_poi(poi_id)
    
    def update_zone(self, zone: Dict[str, Any]):
        """Actualiza o agrega una zona de interés."""
        self.data_store.update_zone(zone)
    
    def remove_zone(self, zone_id: str):
        """Elimina una zona de interés."""
        self.data_store.remove_zone(zone_id)
    
    def add_map_event(self, event: Dict[str, Any]):
        """Agrega un evento del mapa."""
        self.data_store.add_map_event(event)
    
    def get_map_events(self) -> List[Dict[str, Any]]:
        """Obtiene eventos del mapa."""
        return self.data_store.get_map_events()
    
    def set_map_mode(self, mode: str):
        """Establece el modo de interacción del mapa."""
        self.data_store.set_map_mode(mode)
    
    def get_url(self) -> str:
        """Obtiene la URL del servidor."""
        return f"http://localhost:{self.port}"

