"""
Servidor HTTP simple para servir datos de telemetría y POIs como JSON.
Permite actualizaciones incrementales del mapa sin recargar la página.
"""
import json
import threading
from typing import Dict, Any, Optional
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
                'pois': self.data_store.get_all_pois() if self.data_store else {}
            }
            self._send_json_response(data)
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
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
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
    
    def get_url(self) -> str:
        """Obtiene la URL del servidor."""
        return f"http://localhost:{self.port}"

