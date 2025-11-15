# Script de compilación para Windows
# Activa el venv y compila la aplicación

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Compilando aplicación para Windows" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Activar entorno virtual
Write-Host "Activando entorno virtual..." -ForegroundColor Yellow
& ".\venv\Scripts\Activate.ps1"

# Verificar que Flet está instalado
Write-Host "Verificando Flet CLI..." -ForegroundColor Yellow
$fletVersion = flet --version 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Flet CLI no está instalado" -ForegroundColor Red
    Write-Host "Instalando flet[all]..." -ForegroundColor Yellow
    pip install 'flet[all]'
}

Write-Host "Flet CLI: $fletVersion" -ForegroundColor Green
Write-Host ""

# Compilar
Write-Host "Iniciando compilación..." -ForegroundColor Yellow
Write-Host "Esto puede tardar varios minutos en la primera ejecución..." -ForegroundColor Yellow
Write-Host ""

flet build windows

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "✓ Compilación exitosa!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "El ejecutable se encuentra en: dist/" -ForegroundColor Cyan
} else {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Red
    Write-Host "✗ Error en la compilación" -ForegroundColor Red
    Write-Host "========================================" -ForegroundColor Red
}

