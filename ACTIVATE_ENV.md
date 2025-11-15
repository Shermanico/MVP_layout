# Cómo Activar el Entorno Virtual

## Windows PowerShell

**IMPORTANTE**: En PowerShell, debes usar el operador de punto (`.`) para ejecutar el script en el contexto actual del shell.

### Opción 1: Usar el script helper (Recomendado)
```powershell
. .\activate_env.ps1
```

**Nota**: Observa el punto (`.`) al inicio. Esto ejecuta el script en el contexto actual del shell, permitiendo que la activación funcione.

### Opción 2: Activar directamente
```powershell
.\venv\Scripts\Activate.ps1
```

### Opción 3: Si tienes problemas de política de ejecución
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
. .\activate_env.ps1
```

## Windows Command Prompt (CMD)

```cmd
activate_env.bat
```

O directamente:
```cmd
venv\Scripts\activate.bat
```

## Linux/macOS

```bash
source activate_env.sh
```

O directamente:
```bash
source venv/bin/activate
```

## Verificar que está activado

Después de activar, deberías ver `(venv)` al inicio de tu prompt:

```
(venv) PS C:\Users\User\Desktop\cursor\New folder\MVP_layout>
```

## Desactivar

Para desactivar el entorno virtual, simplemente escribe:
```bash
deactivate
```

## Solución de Problemas

### Error: "cannot be loaded because running scripts is disabled"

Ejecuta en PowerShell (como Administrador):
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Error: "The term 'activate_env.ps1' is not recognized"

Asegúrate de usar la sintaxis correcta:
- PowerShell: `.\activate_env.ps1` o `. .\activate_env.ps1`
- CMD: `activate_env.bat`

### El entorno virtual no se activa

Verifica que el directorio `venv` existe:
```powershell
Test-Path .\venv\Scripts\Activate.ps1
```

Si devuelve `False`, crea el entorno virtual:
```powershell
python -m venv venv
```

