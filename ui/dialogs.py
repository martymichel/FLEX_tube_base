"""
Dialog-Sammlung - Importiert alle Dialog-Module
Zentrale Importdatei für alle Dialog-Komponenten
"""

# Hauptdialoge
from .camera_selection_dialog import CameraSelectionDialog
from .settings_dialog import SettingsDialog

# Tab-Module für Settings
from .modbus_settings_dialog import ModbusSettingsTab
from .class_configuration_dialog import ClassConfigurationTab
from .reference_lines_dialog import ReferenceLinesTab
from .workflow_settings_dialog import WorkflowSettingsTab
from .camera_settings_dialog import CameraSettingsTab
from .logging_settings_dialog import LoggingSettingsTab

__all__ = [
    # Hauptdialoge
    'CameraSelectionDialog',
    'SettingsDialog',
    
    # Tab-Module
    'ModbusSettingsTab',
    'ClassConfigurationTab', 
    'ReferenceLinesTab',
    'WorkflowSettingsTab',
    'CameraSettingsTab',
    'LoggingSettingsTab'
]