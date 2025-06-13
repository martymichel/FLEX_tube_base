"""
Haupt-Einstellungen Dialog
Zentrale Einstellungen mit Tab-basierter Organisation
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QTabWidget,
    QWidget, QMessageBox, QApplication
)
from PyQt6.QtCore import Qt

from .modbus_settings_dialog import ModbusSettingsTab
from .class_configuration_dialog import ClassConfigurationTab
from .reference_lines_dialog import ReferenceLinesTab
from .workflow_settings_dialog import WorkflowSettingsTab
from .camera_settings_dialog import CameraSettingsTab
from .logging_settings_dialog import LoggingSettingsTab

class SettingsDialog(QDialog):
    """Haupt-Einstellungsdialog mit Tab-basierter Organisation."""
    
    def __init__(self, settings, class_names=None, parent=None):
        super().__init__(parent)
        self.settings = settings
        self.class_names = class_names or {}
        self.original_settings = settings.data.copy()
        
        self.setWindowTitle("Einstellungen")
        self.setModal(True)
        self.resize(800, 600)
        
        self.setup_ui()
        self.load_settings()
    
    def setup_ui(self):
        """UI aufbauen."""
        layout = QVBoxLayout(self)
        
        # Tab Widget
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)
        
        # Tabs erstellen
        self.create_tabs()
        
        # Button-Layout
        button_layout = QHBoxLayout()
        
        # Info-Button
        self.info_btn = QPushButton("ℹ️ Info")
        self.info_btn.clicked.connect(self.show_info)
        button_layout.addWidget(self.info_btn)
        
        # Reset-Button
        self.reset_btn = QPushButton("🔄 Zurücksetzen")
        self.reset_btn.clicked.connect(self.reset_to_defaults)
        button_layout.addWidget(self.reset_btn)
        
        button_layout.addStretch()
        
        # Standard-Buttons
        self.cancel_btn = QPushButton("Abbrechen")
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)
        
        self.apply_btn = QPushButton("Übernehmen")
        self.apply_btn.clicked.connect(self.apply_settings)
        button_layout.addWidget(self.apply_btn)
        
        self.ok_btn = QPushButton("OK")
        self.ok_btn.clicked.connect(self.accept)
        button_layout.addWidget(self.ok_btn)
        
        layout.addLayout(button_layout)
    
    def create_tabs(self):
        """Alle Tabs erstellen."""
        # Workflow-Einstellungen
        self.workflow_tab = WorkflowSettingsTab(self.settings)
        self.tab_widget.addTab(self.workflow_tab, "⏱️ Workflow")
        
        # Kamera-Einstellungen
        self.camera_tab = CameraSettingsTab(self.settings)
        self.tab_widget.addTab(self.camera_tab, "📷 Kamera")
        
        # Klassen-Konfiguration
        self.class_tab = ClassConfigurationTab(self.settings, self.class_names)
        self.tab_widget.addTab(self.class_tab, "🎯 Klassen")
        
        # Referenzlinien
        self.reference_tab = ReferenceLinesTab(self.settings)
        self.tab_widget.addTab(self.reference_tab, "📏 Referenzlinien")
        
        # Modbus-Einstellungen
        self.modbus_tab = ModbusSettingsTab(self.settings)
        self.tab_widget.addTab(self.modbus_tab, "🔧 Modbus")
        
        # Logging-Einstellungen
        self.logging_tab = LoggingSettingsTab(self.settings)
        self.tab_widget.addTab(self.logging_tab, "📊 Logging")
    
    def load_settings(self):
        """Einstellungen in alle Tabs laden."""
        for i in range(self.tab_widget.count()):
            tab = self.tab_widget.widget(i)
            if hasattr(tab, 'load_settings'):
                tab.load_settings()
    
    def apply_settings(self):
        """Einstellungen übernehmen ohne Dialog zu schließen."""
        try:
            # Einstellungen von allen Tabs sammeln
            for i in range(self.tab_widget.count()):
                tab = self.tab_widget.widget(i)
                if hasattr(tab, 'save_settings'):
                    tab.save_settings()
            
            # Einstellungen speichern
            self.settings.save()
            
            QMessageBox.information(self, "Einstellungen", "Einstellungen wurden übernommen.")
            
        except Exception as e:
            QMessageBox.critical(self, "Fehler", f"Fehler beim Übernehmen der Einstellungen:\n{str(e)}")
    
    def accept(self):
        """Dialog mit OK schließen."""
        try:
            # Einstellungen von allen Tabs sammeln
            for i in range(self.tab_widget.count()):
                tab = self.tab_widget.widget(i)
                if hasattr(tab, 'save_settings'):
                    tab.save_settings()
            
            # Einstellungen speichern
            self.settings.save()
            
            super().accept()
            
        except Exception as e:
            QMessageBox.critical(self, "Fehler", f"Fehler beim Speichern der Einstellungen:\n{str(e)}")
    
    def reject(self):
        """Dialog abbrechen - Originaleinstellungen wiederherstellen."""
        # Originaleinstellungen wiederherstellen
        self.settings.data = self.original_settings.copy()
        super().reject()
    
    def reset_to_defaults(self):
        """Alle Einstellungen auf Standardwerte zurücksetzen."""
        reply = QMessageBox.question(
            self,
            "Einstellungen zurücksetzen",
            "Alle Einstellungen auf Standardwerte zurücksetzen?\n\n"
            "Diese Aktion kann nicht rückgängig gemacht werden.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # Standardeinstellungen laden
            self.settings.reset_to_defaults()
            
            # Alle Tabs neu laden
            self.load_settings()
            
            QMessageBox.information(self, "Zurückgesetzt", "Alle Einstellungen wurden auf Standardwerte zurückgesetzt.")
    
    def show_info(self):
        """Info-Dialog anzeigen."""
        info_text = """
        <h3>Einstellungen - Übersicht</h3>
        
        <p><b>⏱️ Workflow:</b> Zeiteinstellungen für Bewegungserkennung und Erkennungszyklen</p>
        
        <p><b>📷 Kamera:</b> Kamera-spezifische Einstellungen und Konfigurationen</p>
        
        <p><b>🎯 Klassen:</b> KI-Modell Klassen-Zuordnungen und Farben</p>
        
        <p><b>📏 Referenzlinien:</b> Sichtbare Referenzlinien im Video-Stream</p>
        
        <p><b>🔧 Modbus:</b> WAGO-Steuerung und Modbus-Kommunikation</p>
        
        <p><b>📊 Logging:</b> Datenprotokollierung und Bildspeicherung</p>
        
        <hr>
        
        <p><i>Tipp: Verwenden Sie "Übernehmen" um Änderungen zu testen, ohne den Dialog zu schließen.</i></p>
        """
        
        QMessageBox.information(self, "Einstellungen Info", info_text)
    
    def update_modbus_connection_status(self, is_connected):
        """Modbus-Verbindungsstatus in entsprechendem Tab aktualisieren."""
        if hasattr(self, 'modbus_tab'):
            self.modbus_tab.update_connection_status(is_connected)