"""
Dialog-Sammlung - Importiert alle Dialog-Module  
Zentrale Importdatei für alle Dialog-Komponenten
GEFIXT: Korrekte Imports für aufgeteilte Dialog-Module
"""

# Hauptdialoge
from .camera_selection_dialog import CameraSelectionDialog
from .settings_dialog import SettingsDialog

# Tab-Module für Settings - NICHT MEHR VERWENDETE IMPORTS ENTFERNT
# Diese existieren nicht mehr als separate Module, sondern sind in settings_dialog.py integriert

__all__ = [
    # Hauptdialoge
    'CameraSelectionDialog',
    'SettingsDialog'
]