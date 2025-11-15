"""
Script de verificación para la implementación del mapa.
Verifica que:
1. El servidor HTTP esté sirviendo datos correctamente
2. El HTML generado tenga el script correcto
3. Las funciones JavaScript estén bien definidas
"""

import requests
import json
import tempfile
import os
import re

def test_http_server():
    """Verifica que el servidor HTTP esté funcionando."""
    print("=" * 60)
    print("1. VERIFICANDO SERVIDOR HTTP")
    print("=" * 60)
    
    try:
        # Intentar conectar al servidor
        response = requests.get('http://localhost:8765/api/data', timeout=2)
        if response.status_code == 200:
            data = response.json()
            drones = data.get('drones', {})
            print(f"[OK] Servidor HTTP funcionando correctamente")
            print(f"  - Drones encontrados: {len(drones)}")
            if drones:
                first_drone = list(drones.keys())[0]
                drone_data = drones[first_drone]
                print(f"  - Ejemplo DRONE_000: lat={drone_data.get('latitude', 'N/A')}, lon={drone_data.get('longitude', 'N/A')}")
            return True
        else:
            print(f"[ERROR] Servidor HTTP respondio con codigo: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("[ERROR] No se pudo conectar al servidor HTTP (esta corriendo?)")
        print("  Ejecuta: python main.py")
        return False
    except Exception as e:
        print(f"[ERROR] Error al verificar servidor: {e}")
        return False

def test_html_generation():
    """Verifica que el HTML generado tenga el script correcto."""
    print("\n" + "=" * 60)
    print("2. VERIFICANDO GENERACIÓN DE HTML")
    print("=" * 60)
    
    temp_dir = tempfile.gettempdir()
    html_files = [f for f in os.listdir(temp_dir) if f.endswith('.html') and 'tmp' in f]
    
    if not html_files:
        print("[ERROR] No se encontraron archivos HTML temporales")
        print("  Ejecuta la aplicacion primero para generar el HTML")
        return False
    
    # Tomar el archivo más reciente
    html_files.sort(key=lambda x: os.path.getmtime(os.path.join(temp_dir, x)), reverse=True)
    latest_html = os.path.join(temp_dir, html_files[0])
    
    print(f"[OK] Archivo HTML encontrado: {html_files[0]}")
    
    try:
        with open(latest_html, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Verificar que tenga el script
        checks = [
            ("IIFE (función auto-ejecutada)", r'\(function\(\)\s*\{\{'),
            ("console.log inicial", r'console\.log\([\'"]=== SCRIPT DE MAPA CARGADO ==='),
            ("Función findMapObject", r'function findMapObject\(\)\s*\{\{'),
            ("Función createDroneIconFolium", r'function createDroneIconFolium'),
            ("window.updateDrone", r'window\.updateDrone\s*=\s*function'),
            ("window.updatePOI", r'window\.updatePOI\s*=\s*function'),
            ("Función updateFromServer", r'function updateFromServer\(\)\s*\{\{'),
            ("Polling del servidor", r'http://localhost:8765/api/data'),
            ("L.divIcon", r'L\.divIcon'),
            ("Emoji de avión", r'✈'),
        ]
        
        all_passed = True
        for check_name, pattern in checks:
            if re.search(pattern, content):
                print(f"  [OK] {check_name}")
            else:
                print(f"  [ERROR] {check_name} - NO ENCONTRADO")
                all_passed = False
        
        # Verificar que no haya llaves sin escapar (error común)
        unescaped_braces = re.findall(r'(?<!\{)\{(?!\{)', content)
        if unescaped_braces:
            # Contar solo las que están dentro del script
            script_start = content.find('<script>')
            script_end = content.find('</script>', script_start)
            if script_start != -1 and script_end != -1:
                script_content = content[script_start:script_end]
                # Buscar llaves simples que no sean parte de {{ o }}
                problematic = re.findall(r'(?<!\{)\{(?![{])', script_content)
                if problematic:
                    print(f"  ⚠ Posibles llaves sin escapar encontradas: {len(problematic)}")
                    # Mostrar algunas líneas problemáticas
                    lines = script_content.split('\n')
                    for i, line in enumerate(lines[:50], 1):
                        if '{' in line and '{{' not in line and 'function' not in line:
                            print(f"    Línea {i}: {line[:80]}...")
        
        return all_passed
        
    except Exception as e:
        print(f"✗ Error al leer HTML: {e}")
        return False

def test_javascript_syntax():
    """Verifica la sintaxis JavaScript básica."""
    print("\n" + "=" * 60)
    print("3. VERIFICANDO SINTAXIS JAVASCRIPT")
    print("=" * 60)
    
    temp_dir = tempfile.gettempdir()
    html_files = [f for f in os.listdir(temp_dir) if f.endswith('.html') and 'tmp' in f]
    
    if not html_files:
        print("✗ No se encontraron archivos HTML temporales")
        return False
    
    html_files.sort(key=lambda x: os.path.getmtime(os.path.join(temp_dir, x)), reverse=True)
    latest_html = os.path.join(temp_dir, html_files[0])
    
    try:
        with open(latest_html, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extraer el script
        script_start = content.find('<script>')
        script_end = content.find('</script>', script_start)
        
        if script_start == -1 or script_end == -1:
            print("[ERROR] No se encontro el tag <script> en el HTML")
            return False
        
        script_content = content[script_start + 8:script_end]
        
        # Verificaciones básicas de sintaxis
        checks = [
            ("Paréntesis balanceados", script_content.count('(') == script_content.count(')')),
            ("Llaves balanceadas ({{)", script_content.count('{{') == script_content.count('}}')),
            ("No hay llaves simples problemáticas", 
             len(re.findall(r'(?<!\{)\{(?![{])', script_content)) < 10),  # Algunas pueden ser válidas
        ]
        
        all_passed = True
        for check_name, result in checks:
            if result:
                print(f"  [OK] {check_name}")
            else:
                print(f"  [ERROR] {check_name}")
                all_passed = False
        
        return all_passed
        
    except Exception as e:
        print(f"✗ Error al verificar sintaxis: {e}")
        return False

def main():
    """Ejecuta todas las verificaciones."""
    print("\n" + "=" * 60)
    print("VERIFICACIÓN DE IMPLEMENTACIÓN DEL MAPA")
    print("=" * 60)
    
    results = []
    
    # Verificar servidor HTTP
    results.append(("Servidor HTTP", test_http_server()))
    
    # Verificar HTML
    results.append(("Generación HTML", test_html_generation()))
    
    # Verificar sintaxis JavaScript
    results.append(("Sintaxis JavaScript", test_javascript_syntax()))
    
    # Resumen
    print("\n" + "=" * 60)
    print("RESUMEN")
    print("=" * 60)
    
    for name, passed in results:
        status = "[OK] PASO" if passed else "[ERROR] FALLO"
        print(f"{status}: {name}")
    
    all_passed = all(result[1] for result in results)
    
    if all_passed:
        print("\n[OK] Todas las verificaciones pasaron")
    else:
        print("\n[ERROR] Algunas verificaciones fallaron")
        print("\nSugerencias:")
        print("1. Asegúrate de que el servidor HTTP esté corriendo (python main.py)")
        print("2. Abre el archivo HTML en el navegador y revisa la consola (F12)")
        print("3. Verifica que no haya errores de sintaxis JavaScript")
        print("4. Revisa que los datos del servidor incluyan coordenadas válidas")
    
    return all_passed

if __name__ == '__main__':
    main()

