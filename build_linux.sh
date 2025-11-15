#!/bin/bash
# Script de compilación para Linux
# Activa el venv y compila la aplicación

echo "========================================"
echo "Compilando aplicación para Linux"
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

# Compilar
echo "Iniciando compilación..."
echo "Esto puede tardar varios minutos en la primera ejecución..."
echo ""

flet build linux

if [ $? -eq 0 ]; then
    echo ""
    echo "========================================"
    echo "✓ Compilación exitosa!"
    echo "========================================"
    echo "El ejecutable se encuentra en: dist/"
else
    echo ""
    echo "========================================"
    echo "✗ Error en la compilación"
    echo "========================================"
fi

