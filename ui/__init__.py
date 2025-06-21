"""
UI-Package - Modulare Benutzeroberflaeche
Importiert alle UI-Komponenten fuer einfache Verwendung
"""

from .main_ui import MainUI
from .dialogs import CameraSelectionDialog, SettingsDialog
from .product_config_dialog import ProductConfigDialog
from .widgets import StatusIndicator, CounterWidget, ProgressIndicator
from .styles import UIStyles
from .camera_overlay_button import CameraOverlayButton  # NEU

__all__ = [
    'MainUI',
    'CameraSelectionDialog', 
    'SettingsDialog',
    'ProductConfigDialog',
    'StatusIndicator',
    'CounterWidget',
    'ProgressIndicator',
    'UIStyles',
    'CameraOverlayButton'  # NEU
]