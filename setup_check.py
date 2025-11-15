"""
Script de verificación de setup para desarrollo.
Ejecuta: python setup_check.py
Verifica que todas las dependencias y archivos estén listos para desarrollo.
"""
import os
import sys
import subprocess
import json
from pathlib import Path

# Configurar encoding para Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

def print_header(text):
    """Imprime un encabezado formateado."""
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70)

def print_success(text):
    """Imprime un mensaje de éxito."""
    print(f"✓ {text}")

def print_warning(text):
    """Imprime un mensaje de advertencia."""
    print(f"⚠ {text}")

def print_error(text):
    """Imprime un mensaje de error."""
    print(f"✗ {text}")

def check_python_version():
    """Verifica la versión de Python."""
    print_header("VERIFICANDO PYTHON")
    version = sys.version_info
    if version.major >= 3 and version.minor >= 10:
        print_success(f"Python {version.major}.{version.minor}.{version.micro} (requerido: 3.10+)")
        return True
    else:
        print_error(f"Python {version.major}.{version.minor}.{version.micro} (requerido: 3.10+)")
        return False

def check_virtual_environment():
    """Verifica si estamos en un entorno virtual."""
    print_header("VERIFICANDO ENTORNO VIRTUAL")
    in_venv = hasattr(sys, 'real_prefix') or (
        hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix
    )
    if in_venv:
        print_success(f"Entorno virtual activo: {sys.prefix}")
        return True
    else:
        print_warning("No se detectó entorno virtual activo")
        print("  Recomendado: python -m venv venv")
        print("  Luego activa: .\\venv\\Scripts\\Activate.ps1 (Windows) o source venv/bin/activate (Linux/Mac)")
        return False

def check_dependencies():
    """Verifica que todas las dependencias estén instaladas."""
    print_header("VERIFICANDO DEPENDENCIAS")
    
    required_packages = {
        'flet': 'flet[all]>=0.21.0',
        'folium': 'folium>=0.15.0',
    }
    
    optional_packages = {
        'mavsdk': 'mavsdk>=1.4.0 (opcional - solo para simulación MAVSDK real)',
    }
    
    all_ok = True
    
    # Verificar paquetes requeridos
    for package, requirement in required_packages.items():
        try:
            __import__(package)
            print_success(f"{package} instalado")
        except ImportError:
            print_error(f"{package} NO instalado")
            print(f"  Instalar con: pip install {requirement}")
            all_ok = False
    
    # Verificar paquetes opcionales
    for package, description in optional_packages.items():
        try:
            __import__(package)
            print_success(f"{package} instalado (opcional)")
        except ImportError:
            print_warning(f"{package} NO instalado - {description}")
    
    # Verificar módulos estándar
    std_modules = ['asyncio', 'json', 'dataclasses', 'threading', 'http.server']
    for module in std_modules:
        try:
            __import__(module)
            print_success(f"{module} disponible (built-in)")
        except ImportError:
            print_error(f"{module} NO disponible")
            all_ok = False
    
    return all_ok

def check_project_structure():
    """Verifica que la estructura del proyecto esté completa."""
    print_header("VERIFICANDO ESTRUCTURA DEL PROYECTO")
    
    required_files = [
        'main.py',
        'requirements.txt',
        'config.json.example',
        '.gitignore',
        'README.md',
        'common/__init__.py',
        'common/config.py',
        'common/constants.py',
        'common/utils.py',
        'common/colors.py',
        'backend/__init__.py',
        'backend/storage.py',
        'backend/schemas.py',
        'backend/data_server.py',
        'drones/__init__.py',
        'drones/drone_manager.py',
        'drones/fake_generator.py',
        'drones/simulator.py',
        'ui/main.py',
        'ui/map_view.py',
        'ui/telemetry_panel.py',
        'ui/poi_manager.py',
    ]
    
    all_ok = True
    for file_path in required_files:
        if os.path.exists(file_path):
            print_success(f"{file_path}")
        else:
            print_error(f"{file_path} NO encontrado")
            all_ok = False
    
    return all_ok

def check_config_files():
    """Verifica archivos de configuración."""
    print_header("VERIFICANDO ARCHIVOS DE CONFIGURACIÓN")
    
    # Verificar config.json.example
    if os.path.exists('config.json.example'):
        print_success("config.json.example existe")
        try:
            with open('config.json.example', 'r') as f:
                example_config = json.load(f)
            print_success("config.json.example es JSON válido")
        except Exception as e:
            print_error(f"config.json.example tiene errores: {e}")
            return False
    else:
        print_error("config.json.example NO encontrado")
        return False
    
    # Verificar config.json (puede no existir, está en .gitignore)
    if os.path.exists('config.json'):
        print_success("config.json existe (local)")
        try:
            with open('config.json', 'r') as f:
                user_config = json.load(f)
            print_success("config.json es JSON válido")
        except Exception as e:
            print_error(f"config.json tiene errores: {e}")
            return False
    else:
        print_warning("config.json NO existe (se usarán valores por defecto)")
        print("  Puedes copiar config.json.example a config.json para personalizar")
    
    return True

def check_gitignore():
    """Verifica que .gitignore esté configurado correctamente."""
    print_header("VERIFICANDO .gitignore")
    
    if not os.path.exists('.gitignore'):
        print_error(".gitignore NO encontrado")
        return False
    
    print_success(".gitignore existe")
    
    # Verificar que archivos importantes estén en .gitignore
    with open('.gitignore', 'r') as f:
        gitignore_content = f.read()
    
    required_ignores = [
        'venv/',
        '__pycache__/',
        'config.json',
        'pois.json',
        '*.log',
    ]
    
    all_ok = True
    for ignore_pattern in required_ignores:
        if ignore_pattern in gitignore_content:
            print_success(f"'{ignore_pattern}' está en .gitignore")
        else:
            print_warning(f"'{ignore_pattern}' NO está en .gitignore")
            all_ok = False
    
    return all_ok

def check_imports():
    """Verifica que todos los imports funcionen correctamente."""
    print_header("VERIFICANDO IMPORTS")
    
    imports_to_test = [
        ('common.config', 'Config'),
        ('common.constants', 'POIType'),
        ('common.utils', 'normalize_telemetry'),
        ('common.colors', 'RED'),
        ('backend.storage', 'POIStorage'),
        ('backend.schemas', 'TelemetrySchema'),
        ('backend.data_server', 'TelemetryServer'),
        ('drones.drone_manager', 'DroneManager'),
        ('drones.fake_generator', 'FakeTelemetryGenerator'),
        ('ui.main', 'MainApp'),
        ('ui.telemetry_panel', 'TelemetryPanel'),
        ('ui.poi_manager', 'POIManager'),
        ('ui.map_view', 'MapView'),
    ]
    
    all_ok = True
    for module_name, item_name in imports_to_test:
        try:
            module = __import__(module_name, fromlist=[item_name])
            getattr(module, item_name)
            print_success(f"{module_name}.{item_name}")
        except Exception as e:
            print_error(f"{module_name}.{item_name} - {str(e)}")
            all_ok = False
    
    return all_ok

def check_port_availability():
    """Verifica que el puerto del servidor HTTP esté disponible."""
    print_header("VERIFICANDO PUERTO DEL SERVIDOR")
    
    import socket
    
    port = 8765
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('localhost', port))
    sock.close()
    
    if result != 0:
        print_success(f"Puerto {port} está disponible")
        return True
    else:
        print_warning(f"Puerto {port} está en uso")
        print("  Esto puede indicar que el servidor ya está corriendo")
        print("  O que otra aplicación está usando el puerto")
        return True  # No es un error crítico

def main():
    """Ejecuta todas las verificaciones."""
    print("\n" + "=" * 70)
    print("  SETUP CHECK - Sistema de Coordinación Multi-Dron")
    print("=" * 70)
    
    results = {
        'Python': check_python_version(),
        'Entorno Virtual': check_virtual_environment(),
        'Dependencias': check_dependencies(),
        'Estructura del Proyecto': check_project_structure(),
        'Archivos de Configuración': check_config_files(),
        '.gitignore': check_gitignore(),
        'Imports': check_imports(),
        'Puerto del Servidor': check_port_availability(),
    }
    
    print_header("RESUMEN")
    
    all_passed = True
    for check_name, passed in results.items():
        if passed:
            print_success(f"{check_name}")
        else:
            print_error(f"{check_name}")
            all_passed = False
    
    print("\n" + "=" * 70)
    if all_passed:
        print("  ✓ SETUP COMPLETO - Listo para desarrollo")
        print("=" * 70)
        print("\nPRÓXIMOS PASOS:")
        print("1. Activa el entorno virtual si no está activo")
        print("2. Ejecuta: python main.py")
        print("3. Para verificar funcionamiento: python diagnostico.py")
    else:
        print("  ⚠ SETUP INCOMPLETO - Revisa los errores arriba")
        print("=" * 70)
        print("\nACCIONES RECOMENDADAS:")
        print("1. Instala las dependencias faltantes: pip install -r requirements.txt")
        print("2. Crea el entorno virtual: python -m venv venv")
        print("3. Activa el entorno virtual")
        print("4. Vuelve a ejecutar este script")
    
    print()
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())

