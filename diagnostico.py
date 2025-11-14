"""
Script de diagnóstico para verificar la configuración del sistema.
Ejecuta: python diagnostico.py
"""
import os
import json
import sys

# Configurar encoding para Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

def verificar_configuracion():
    """Verifica la configuración del sistema."""
    print("=" * 60)
    print("DIAGNÓSTICO DEL SISTEMA DE COORDINACIÓN MULTI-DRON")
    print("=" * 60)
    print()
    
    # Verificar Python
    print(f"[OK] Python: {sys.version}")
    print()
    
    # Verificar dependencias
    print("Verificando dependencias...")
    try:
        import flet as ft
        version = getattr(ft, '__version__', 'instalado (version desconocida)')
        print(f"[OK] Flet instalado: {version}")
    except ImportError:
        print("[ERROR] Flet NO esta instalado")
        print("  Ejecuta: pip install flet")
        return False
    
    try:
        import asyncio
        print("[OK] asyncio disponible")
    except ImportError:
        print("[ERROR] asyncio NO disponible")
        return False
    
    print()
    
    # Verificar archivos
    print("Verificando archivos...")
    archivos_requeridos = [
        "main.py",
        "common/config.py",
        "common/utils.py",
        "common/constants.py",
        "common/colors.py",
        "backend/storage.py",
        "drones/drone_manager.py",
        "drones/fake_generator.py",
        "ui/main.py",
        "ui/telemetry_panel.py",
        "ui/poi_manager.py",
    ]
    
    todos_ok = True
    for archivo in archivos_requeridos:
        if os.path.exists(archivo):
            print(f"[OK] {archivo}")
        else:
            print(f"[ERROR] {archivo} NO encontrado")
            todos_ok = False
    
    print()
    
    # Verificar configuración
    print("Verificando configuración...")
    if os.path.exists("config.json"):
        print("[OK] config.json encontrado")
        try:
            with open("config.json", "r") as f:
                config = json.load(f)
            print(f"  - use_fake_telemetry: {config.get('use_fake_telemetry', 'N/A')}")
            print(f"  - fake_drone_count: {config.get('fake_drone_count', 'N/A')}")
        except Exception as e:
            print(f"[ERROR] Error al leer config.json: {e}")
    else:
        print("[ADVERTENCIA] config.json NO encontrado (usara valores por defecto)")
        print("  - use_fake_telemetry: True (por defecto)")
        print("  - fake_drone_count: 3 (por defecto)")
    
    print()
    
    # Verificar imports
    print("Verificando imports...")
    try:
        from common.config import Config
        print("[OK] common.config importado")
        
        from backend.storage import POIStorage
        print("[OK] backend.storage importado")
        
        from drones.drone_manager import DroneManager
        print("[OK] drones.drone_manager importado")
        
        from drones.fake_generator import FakeTelemetryGenerator
        print("[OK] drones.fake_generator importado")
        
        from ui.main import MainApp
        print("[OK] ui.main importado")
        
        from ui.telemetry_panel import TelemetryPanel
        print("[OK] ui.telemetry_panel importado")
        
        from ui.poi_manager import POIManager
        print("[OK] ui.poi_manager importado")
        
    except Exception as e:
        print(f"[ERROR] Error al importar modulos: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print()
    
    # Probar creación de objetos
    print("Probando creacion de objetos...")
    try:
        config = Config.load_from_file()
        print(f"[OK] Config creado: use_fake_telemetry={config.use_fake_telemetry}")
        
        storage = POIStorage(config.poi_storage_file)
        print("[OK] POIStorage creado")
        
        def dummy_callback(telemetry):
            pass
        
        drone_manager = DroneManager(config, dummy_callback)
        print("[OK] DroneManager creado")
        
    except Exception as e:
        print(f"[ERROR] Error al crear objetos: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print()
    print("=" * 60)
    print("[OK] DIAGNOSTICO COMPLETADO - Sistema listo")
    print("=" * 60)
    print()
    print("PRÓXIMOS PASOS:")
    print("1. Ejecuta: python main.py")
    print("2. Revisa la consola para mensajes de logging")
    print("3. Si ves 'Drones Activos: 0', verifica los logs")
    print()
    
    return True

if __name__ == "__main__":
    verificar_configuracion()

