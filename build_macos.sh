#!/bin/bash
# Script de compilación para macOS
# Activa el venv y compila la aplicación

echo "========================================"
echo "Compilando aplicación para macOS"
echo "========================================"
echo ""

# Activar entorno virtual
echo "Activando entorno virtual..."
source venv/bin/activate

# Verificar que Flet está instalado
echo "Verificando Flet CLI..."
if ! command -v flet &> /dev/null; then
    echo "ERROR: Flet CLI no está instalado"
    echo "Instalando flet[all]..."
    pip install 'flet[all]'
fi

FLET_VERSION=$(flet --version)
echo "Flet CLI: $FLET_VERSION"
echo ""

# Verificar requisitos de macOS
echo "Verificando requisitos de macOS..."
if ! command -v xcodebuild &> /dev/null; then
    echo "ADVERTENCIA: Xcode no encontrado. Es necesario para compilar en macOS."
    echo "Instala Xcode desde la App Store."
fi

# Compilar
echo "Iniciando compilación..."
echo "Esto puede tardar varios minutos en la primera ejecución..."
echo ""

flet build macos

if [ $? -eq 0 ]; then
    echo ""
    echo "========================================"
    echo "✓ Compilación exitosa!"
    echo "========================================"
    echo "El paquete .app se encuentra en: dist/"
else
    echo ""
    echo "========================================"
    echo "✗ Error en la compilación"
    echo "========================================"
fi

