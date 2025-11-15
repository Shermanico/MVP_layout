"""
Adaptador de salida: Servidor HTTP para servir datos de telemetría y POIs en tiempo real.
"""
import json
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Dict, Any, Optional


class TelemetryDataStore:
    """Almacén thread-safe para datos de telemetría y POIs."""
    
    def __init__(self):
        """Inicializa el almacén de datos."""
        self.drones: Dict[str, Dict[str, Any]] = {}
        self.pois: Dict[str, Dict[str, Any]] = {}
        self.lock = threading.Lock()
    
    def update_telemetry(self, telemetry: Dict[str, Any]) -> None:
        """Actualiza la telemetría de un dron."""
        with self.lock:
            drone_id = telemetry.get("drone_id", "UNKNOWN")
            self.drones[drone_id] = telemetry
    
    def update_poi(self, poi: Dict[str, Any]) -> None:
        """Actualiza o agrega un POI."""
        with self.lock:
            poi_id = poi.get("id", "")
            if poi_id:
                self.pois[poi_id] = poi
    
    def remove_poi(self, poi_id: str) -> None:
        """Elimina un POI."""
        with self.lock:
            if poi_id in self.pois:
                del self.pois[poi_id]
    
    def get_all_data(self) -> Dict[str, Any]:
        """Obtiene todos los datos (drones y POIs)."""
        with self.lock:
            return {
                "drones": self.drones.copy(),
                "pois": self.pois.copy()
            }


class TelemetryDataHandler(BaseHTTPRequestHandler):
    """Manejador HTTP para servir datos de telemetría."""
    
    def __init__(self, data_store: TelemetryDataStore, *args, **kwargs):
        """Inicializa el manejador con el almacén de datos."""
        self.data_store = data_store
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        """Maneja peticiones GET."""
        if self.path == "/api/data":
            self._send_data()
        elif self.path == "/" or self.path == "/health":
            self._send_health()
        else:
            self._send_not_found()
    
    def _send_data(self):
        """Envía datos de telemetría y POIs."""
        data = self.data_store.get_all_data()
        self._send_json_response(data)
    
    def _send_health(self):
        """Envía respuesta de salud."""
        self._send_json_response({"status": "ok"})
    
    def _send_not_found(self):
        """Envía respuesta 404."""
        self.send_response(404)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps({"error": "Not found"}).encode())
    
    def _send_json_response(self, data: Dict[str, Any]):
        """Envía una respuesta JSON."""
        json_data = json.dumps(data, ensure_ascii=False)
        
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(json_data.encode("utf-8"))
    
    def do_OPTIONS(self):
        """Maneja peticiones OPTIONS (CORS preflight)."""
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
    
    def log_message(self, format, *args):
        """Suprime logs del servidor HTTP."""
        pass  # No loguear cada petición


class TelemetryServer:
    """
    Servidor HTTP para servir datos de telemetría y POIs en tiempo real.
    Se ejecuta en un hilo separado.
    """
    
    def __init__(self, port: int = 8765):
        """
        Inicializa el servidor.
        
        Args:
            port: Puerto en el que escuchar
        """
        self.port = port
        self.data_store = TelemetryDataStore()
        self.server: Optional[HTTPServer] = None
        self.server_thread: Optional[threading.Thread] = None
        self.running = False
    
    def start(self) -> None:
        """Inicia el servidor HTTP en un hilo separado."""
        if self.running:
            return
        
        def handler_factory(data_store):
            def create_handler(*args, **kwargs):
                return TelemetryDataHandler(data_store, *args, **kwargs)
            return create_handler
        
        try:
            self.server = HTTPServer(
                ("localhost", self.port),
                handler_factory(self.data_store)
            )
            self.running = True
            
            def run_server():
                while self.running:
                    self.server.handle_request()
            
            self.server_thread = threading.Thread(target=run_server, daemon=True)
            self.server_thread.start()
        except OSError as e:
            # Puerto ya en uso, continuar sin servidor
            pass
    
    def stop(self) -> None:
        """Detiene el servidor HTTP."""
        self.running = False
        if self.server:
            # Cerrar servidor
            pass
    
    def update_telemetry(self, telemetry: Dict[str, Any]) -> None:
        """Actualiza la telemetría de un dron."""
        self.data_store.update_telemetry(telemetry)
    
    def update_poi(self, poi: Dict[str, Any]) -> None:
        """Actualiza o agrega un POI."""
        self.data_store.update_poi(poi)
    
    def remove_poi(self, poi_id: str) -> None:
        """Elimina un POI."""
        self.data_store.remove_poi(poi_id)

