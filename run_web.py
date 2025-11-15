"""
Ejecuta la aplicación en modo web (dashboard).
Accesible desde cualquier navegador en la red local.
"""
import flet as ft
import socket
from main import main

def get_local_ip():
    """Obtiene la IP local de la máquina."""
    try:
        # Conectar a un servidor externo para obtener la IP local
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

if __name__ == "__main__":
    local_ip = get_local_ip()
    
    print("=" * 60)
    print("Servidor web iniciando...")
    print(f"Acceso local: http://localhost:8550")
    print(f"Acceso desde red local: http://{local_ip}:8550")
    print("=" * 60)
    
    # Ejecutar en modo web
    # host="0.0.0.0" permite acceso desde otros dispositivos en la red local
    # El navegador debe usar localhost o la IP local, no 0.0.0.0
    ft.app(
        target=main,
        view=ft.AppView.WEB_BROWSER,  # Abre automáticamente en el navegador
        port=8550,  # Puerto por defecto de Flet web
        host="0.0.0.0"  # Escucha en todas las interfaces (permite acceso remoto)
    )

