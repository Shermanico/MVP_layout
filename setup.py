"""
Script de setup automático para el proyecto.
Ejecuta: python setup.py
"""
import os
import sys
import subprocess
from pathlib import Path

def run_command(cmd, description):
    """Ejecuta un comando y muestra el resultado."""
    print(f"\n{description}...")
    print(f"Ejecutando: {cmd}")
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        print(f"✓ {description} completado")
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Error en {description}")
        if e.stdout:
            print(e.stdout)
        if e.stderr:
            print(e.stderr)
        return False

def main():
    """Ejecuta el setup completo."""
    print("=" * 70)
    print("  SETUP AUTOMÁTICO - Sistema de Coordinación Multi-Dron")
    print("=" * 70)
    
    # Verificar Python
    if sys.version_info < (3, 10):
        print(f"\n✗ Python 3.10+ requerido. Versión actual: {sys.version}")
        return 1
    
    print(f"\n✓ Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
    
    # Verificar si venv existe
    venv_path = Path("venv")
    venv_exists = venv_path.exists()
    
    if not venv_exists:
        print("\n📦 Creando entorno virtual...")
        if not run_command("python -m venv venv", "Crear entorno virtual"):
            return 1
    else:
        print("\n✓ Entorno virtual ya existe")
    
    # Determinar comando de activación según OS
    if sys.platform == "win32":
        pip_cmd = "venv\\Scripts\\pip.exe"
        python_cmd = "venv\\Scripts\\python.exe"
    else:
        pip_cmd = "venv/bin/pip"
        python_cmd = "venv/bin/python"
    
    # Verificar que pip existe
    if not Path(pip_cmd).exists():
        print(f"\n✗ No se encontró pip en {pip_cmd}")
        return 1
    
    # Actualizar pip
    print("\n📦 Actualizando pip...")
    run_command(f"{python_cmd} -m pip install --upgrade pip", "Actualizar pip")
    
    # Instalar dependencias
    print("\n📦 Instalando dependencias...")
    if not run_command(f"{pip_cmd} install -r requirements.txt", "Instalar dependencias"):
        print("\n⚠ Algunas dependencias pueden no haberse instalado correctamente")
        print("  Intenta manualmente: pip install -r requirements.txt")
    
    # Verificar instalación
    print("\n🔍 Verificando instalación...")
    if not run_command(f"{python_cmd} setup_check.py", "Verificar setup"):
        print("\n⚠ El setup puede tener problemas. Revisa los mensajes arriba.")
    
    print("\n" + "=" * 70)
    print("  SETUP COMPLETADO")
    print("=" * 70)
    print("\nPRÓXIMOS PASOS:")
    print("\n1. Activa el entorno virtual:")
    if sys.platform == "win32":
        print("   PowerShell: . .\\venv\\Scripts\\Activate.ps1")
        print("   CMD: venv\\Scripts\\activate.bat")
    else:
        print("   source venv/bin/activate")
    
    print("\n2. Verifica el setup:")
    print("   python setup_check.py")
    
    print("\n3. Ejecuta la aplicación:")
    print("   python main.py")
    
    print("\n4. Para diagnóstico:")
    print("   python diagnostico.py")
    print()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())

