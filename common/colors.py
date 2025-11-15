"""
Constantes de color para componentes UI de Flet.
Usa colores del tema de Flet para adaptarse automáticamente a modo claro/oscuro.
"""
import flet as ft

# Colores Material Design (funcionan en ambos modos)
RED = "#F44336"
GREEN = "#4CAF50"
BLUE = "#2196F3"
AMBER = "#FFC107"
GREY = "#9E9E9E"

# Funciones para obtener colores adaptativos del tema
def get_surface_color(page: ft.Page):
    """Obtiene el color de superficie según el tema."""
    if not page:
        return SURFACE
    if page.theme_mode == ft.ThemeMode.DARK:
        # En modo oscuro, usar SURFACE (fondo oscuro)
        return ft.Colors.SURFACE
    # En modo claro, usar SURFACE (fondo claro)
    return ft.Colors.SURFACE

def get_surface_variant_color(page: ft.Page):
    """Obtiene el color de superficie variante según el tema."""
    if not page:
        return SURFACE_VARIANT
    if page.theme_mode == ft.ThemeMode.DARK:
        # En modo oscuro, usar SURFACE_CONTAINER_HIGHEST (un poco más claro que SURFACE)
        return ft.Colors.SURFACE_CONTAINER_HIGHEST
    # En modo claro, usar un gris muy claro como variante
    return ft.Colors.GREY_50

def get_text_color(page: ft.Page):
    """Obtiene el color de texto principal según el tema."""
    if not page:
        return "#000000"  # Negro por defecto para modo claro
    # En modo oscuro, usar blanco o gris muy claro para mejor contraste
    if page.theme_mode == ft.ThemeMode.DARK:
        return ft.Colors.WHITE  # Blanco para mejor legibilidad en modo oscuro
    # En modo claro, usar ON_SURFACE (negro o gris oscuro)
    return ft.Colors.ON_SURFACE

def get_text_secondary_color(page: ft.Page):
    """Obtiene el color de texto secundario según el tema."""
    if not page:
        return GREY_600  # Gris oscuro por defecto para modo claro
    # En modo oscuro, usar un gris más claro para mejor contraste
    if page.theme_mode == ft.ThemeMode.DARK:
        # Usar GREY_300 o GREY_400 para mejor visibilidad en modo oscuro
        return ft.Colors.GREY_300  # Gris claro que se ve bien sobre fondo oscuro
    # En modo claro, usar ON_SURFACE_VARIANT o un gris oscuro
    return ft.Colors.ON_SURFACE_VARIANT

def get_background_color(page: ft.Page):
    """Obtiene el color de fondo según el tema."""
    if not page:
        return BLUE_GREY_50
    # En modo oscuro, usar SURFACE (fondo oscuro)
    if page.theme_mode == ft.ThemeMode.DARK:
        return ft.Colors.SURFACE
    # En modo claro, usar un fondo muy claro
    return ft.Colors.GREY_50

# Colores legacy (para compatibilidad, pero mejor usar las funciones arriba)
# Estos se mantienen para componentes que aún no usan el sistema de temas
GREY_200 = "#EEEEEE"
GREY_300 = "#E0E0E0"
GREY_600 = "#757575"
BLUE_700 = "#1976D2"
SURFACE = "#FFFFFF"
SURFACE_VARIANT = "#F5F5F5"
BLUE_GREY_50 = "#ECEFF1"

