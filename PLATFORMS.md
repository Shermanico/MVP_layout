# Guía de Ejecución en Diferentes Plataformas

Este documento explica cómo ejecutar y probar la aplicación en diferentes plataformas y modos.

## 📱 Modos de Ejecución Disponibles

### 1. Modo Desktop (Por Defecto)

**Windows/macOS/Linux:**
```bash
python main.py
```

- Abre una ventana de escritorio nativa
- Funciona en Windows, macOS y Linux
- Requiere entorno gráfico (X11 en Linux)

---

## 🌐 Modo Web (Dashboard)

### Opción A: Con navegador automático

```bash
python run_web.py
```

- Abre automáticamente el navegador en `http://localhost:8550`
- Accesible desde otros dispositivos en la red local
- Útil para demostraciones o acceso remoto

### Opción B: Solo servidor (sin abrir navegador)

```bash
python run_web_server.py
```

- Inicia el servidor sin abrir navegador
- Accede manualmente desde: `http://localhost:8550`
- Útil para servidores remotos o cuando no quieres que se abra el navegador

### Acceso desde otros dispositivos

1. **Encuentra tu IP local:**
   - Windows: `ipconfig` (busca "IPv4 Address")
   - Linux/macOS: `ifconfig` o `ip addr`
   - Ejemplo: `192.168.1.100`

2. **Accede desde otro dispositivo:**
   - En el navegador del otro dispositivo: `http://192.168.1.100:8550`
   - Asegúrate de que ambos dispositivos estén en la misma red

3. **Configurar firewall:**
   - Windows: Permitir puerto 8550 en Firewall de Windows
   - Linux: `sudo ufw allow 8550` (si usas UFW)
   - macOS: Configurar en Preferencias del Sistema > Seguridad

### Notas sobre Modo Web

- ✅ Funciona en cualquier navegador moderno (Chrome, Firefox, Safari, Edge)
- ✅ Accesible desde móviles, tablets y otros dispositivos
- ✅ El mapa HTML funciona perfectamente en navegadores
- ⚠️ El servidor HTTP interno (puerto 8765) sigue funcionando para el mapa
- ⚠️ Si accedes desde otro dispositivo, asegúrate de que el puerto 8765 también esté accesible para el mapa

---

## 🤖 Android

### Opción 1: Compilar APK

```bash
# Activar entorno virtual
source venv/bin/activate  # Linux/macOS
# o
.\venv\Scripts\Activate.ps1  # Windows

# Compilar APK
flet build apk
```

**Resultado:**
- Archivo `.apk` en la carpeta `dist/`
- Instalar en dispositivo Android: `adb install dist/app.apk`

**APK firmado (para producción):**
```bash
flet build apk --release
```

### Opción 2: Ejecutar en modo desarrollo (con Flet CLI)

```bash
# Conectar dispositivo Android vía USB
adb devices

# Ejecutar en modo desarrollo
flet run -d android
```

**Requisitos:**
- Android SDK instalado
- Dispositivo Android con modo desarrollador activado
- USB debugging habilitado

### Opción 3: Acceder vía Web desde Android

1. Ejecutar en modo web: `python run_web.py`
2. Encontrar IP de tu computadora
3. Abrir navegador en Android: `http://TU_IP:8550`

**Ventajas:**
- No requiere compilación
- Fácil de probar
- Actualizaciones instantáneas

---

## 🐧 Linux

### Ejecución Directa

```bash
# Activar entorno virtual
source venv/bin/activate

# Ejecutar aplicación
python main.py
```

### Requisitos del Sistema

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install python3 python3-venv python3-pip
sudo apt install libgtk-3-dev libgstreamer1.0-dev libgstreamer-plugins-base1.0-dev
sudo apt install libmpv-dev mpv
```

**Fedora:**
```bash
sudo dnf install python3 python3-pip
sudo dnf install gtk3-devel gstreamer1-devel gstreamer1-plugins-base-devel
sudo dnf install mpv-devel mpv
```

**Arch Linux:**
```bash
sudo pacman -S python python-pip
sudo pacman -S gtk3 gstreamer gstreamer-plugins-base
sudo pacman -S mpv
```

### Modo Web en Linux

```bash
# Ejecutar servidor web
python run_web.py

# O solo servidor (sin abrir navegador)
python run_web_server.py
```

### Compilar Ejecutable para Linux

```bash
# Activar entorno virtual
source venv/bin/activate

# Compilar
flet build linux

# O usar script
./build_linux.sh
```

**Resultado:**
- Ejecutable independiente en `dist/`
- No requiere Python instalado en el sistema destino
- Tamaño aproximado: 50-100 MB

---

## 📊 Comparación de Modos

| Modo | Plataforma | Acceso | Requisitos | Uso Recomendado |
|------|-----------|--------|------------|-----------------|
| **Desktop** | Windows/macOS/Linux | Local | Entorno gráfico | Desarrollo, uso local |
| **Web** | Cualquier navegador | Red local/Internet | Navegador | Demos, acceso remoto, móviles |
| **Android APK** | Android | Instalado | Compilación | Distribución, uso móvil |
| **Linux Executable** | Linux | Local | Ninguno (standalone) | Distribución sin Python |

---

## 🔧 Configuración Avanzada

### Cambiar Puerto del Servidor Web

Edita `run_web.py` o `run_web_server.py`:
```python
ft.app(
    target=main,
    view=ft.AppView.WEB_BROWSER,
    port=8080,  # Cambiar puerto aquí
    host="0.0.0.0"
)
```

### Acceso desde Internet (No Recomendado para Producción)

⚠️ **Advertencia de Seguridad:** Exponer la aplicación a Internet sin autenticación es un riesgo de seguridad.

Si necesitas acceso desde Internet:

1. **Usar túnel (recomendado):**
   ```bash
   # Usar ngrok o similar
   ngrok http 8550
   ```

2. **Configurar firewall y router:**
   - Abrir puerto en router
   - Configurar port forwarding
   - Usar autenticación (no incluido en esta aplicación)

### Servidor HTTP Interno (Puerto 8765)

El servidor HTTP interno que sirve datos del mapa usa el puerto 8765. Si accedes desde otro dispositivo:

- **Mismo dispositivo:** `http://localhost:8765/api/data` funciona
- **Otro dispositivo:** Necesitas usar la IP del servidor: `http://TU_IP:8765/api/data`

**Nota:** El código JavaScript en el mapa actualmente usa `localhost:8765`. Para acceso remoto, necesitarías modificar `ui/map_view.py` para usar la IP del servidor.

---

## 🐛 Solución de Problemas

### Modo Web no inicia

- Verificar que el puerto 8550 no esté en uso: `netstat -an | grep 8550`
- Cambiar puerto en `run_web.py`
- Verificar firewall

### Android: APK no se instala

- Verificar que "Instalar desde fuentes desconocidas" esté habilitado
- Verificar que el APK no esté corrupto
- Probar con `adb install -r dist/app.apk`

### Linux: No se abre ventana

- Verificar que X11 esté corriendo: `echo $DISPLAY`
- En servidor sin GUI, usar modo web: `python run_web_server.py`
- Verificar permisos de ejecución

### Acceso remoto no funciona

- Verificar que ambos dispositivos estén en la misma red
- Verificar firewall en ambos dispositivos
- Verificar que la IP sea correcta
- Probar con `ping` entre dispositivos

---

## 📝 Ejemplos de Uso

### Desarrollo Local
```bash
python main.py  # Modo desktop
```

### Demo en Hackathon
```bash
python run_web.py  # Abre en navegador, accesible desde otros dispositivos
```

### Servidor Remoto
```bash
python run_web_server.py  # Solo servidor, accede desde http://IP:8550
```

### Distribución Android
```bash
flet build apk --release  # APK firmado para Play Store
```

### Distribución Linux
```bash
flet build linux  # Ejecutable standalone
```

---

## 🔗 Referencias

- [Flet Web Mode](https://flet.dev/docs/guides/python/deploying-web-app/)
- [Flet Mobile](https://flet.dev/docs/guides/python/packaging-mobile-app/)
- [Flet Packaging](https://flet.dev/docs/cookbook/packaging-desktop-app/)

