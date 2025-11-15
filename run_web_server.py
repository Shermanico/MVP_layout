"""
Ejecuta la aplicación en modo servidor web (sin abrir navegador automáticamente).
Útil para ejecutar en servidor remoto o cuando no quieres que se abra el navegador.
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
    print("Presiona CTRL+C para detener el servidor")
    print("=" * 60)
    
    # Ejecutar en modo web sin abrir navegador
    ft.app(
        target=main,
        view=ft.AppView.FLET_APP,  # No abre navegador automáticamente
        port=8550,
        host="0.0.0.0"  # Escucha en todas las interfaces (permite acceso remoto)
    )

