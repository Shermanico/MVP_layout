# Comandos para subir el proyecto a GitHub

## Comandos corregidos para tu caso:

```bash
# 1. Inicializar repositorio git (si no está inicializado)
git init

# 2. Agregar TODOS los archivos del proyecto (no solo README.md)
git add .

# 3. Hacer el primer commit
git commit -m "first commit: Sistema de Coordinación Multi-Dron MVP"

# 4. Cambiar nombre de rama a main (si es necesario)
git branch -M main

# 5. Agregar el repositorio remoto de GitHub
git remote add origin https://github.com/Shermanico/MVP_layout.git

# 6. Subir el código a GitHub
git push -u origin main
```

## Notas importantes:

- **NO uses** `echo "# MVP_layout" >> README.md` porque ya tienes un README.md completo
- **Usa** `git add .` en lugar de `git add README.md` para agregar todos los archivos
- El `.gitignore` ya está configurado para excluir archivos innecesarios (__pycache__, config.json, pois.json, etc.)

## Si tienes problemas de autenticación:

Si GitHub te pide autenticación, puedes usar:
- Personal Access Token (recomendado)
- O configurar SSH keys

## Verificar antes de hacer push:

```bash
# Ver qué archivos se van a subir
git status

# Ver el resumen de cambios
git status --short
```

