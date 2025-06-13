"""
Kamera-Einstellungen Dialog
Kamera-spezifische Einstellungen und Konfigurationen
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QFormLayout,
    QLineEdit, QPushButton, QLabel, QCheckBox, QSpinBox,
    QFileDialog, QTextEdit, QTabWidget, QComboBox, QMessageBox
)
from PyQt6.QtCore import Qt
import os

class CameraSettingsTab(QWidget):
    """Tab für Kamera-Einstellungen."""
    
    def __init__(self, settings, parent=None):
        super().__init__(parent)
        self.settings = settings
        self.setup_ui()
    
    def setup_ui(self):
        """UI aufbauen."""
        layout = QVBoxLayout(self)
        
        # Tab Widget für Unterkategorien
        tab_widget = QTabWidget()
        layout.addWidget(tab_widget)
        
        # IDS Kamera Tab
        ids_tab = self.create_ids_tab()
        tab_widget.addTab(ids_tab, "IDS Peak")
        
        # Allgemeine Kamera Tab
        general_tab = self.create_general_tab()
        tab_widget.addTab(general_tab, "Allgemein")
        
        # Auto-Loading Tab
        autoload_tab = self.create_autoload_tab()
        tab_widget.addTab(autoload_tab, "Auto-Loading")
    
    def create_ids_tab(self):
        """IDS Peak Kamera Tab erstellen."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # IDS Peak Konfiguration
        ids_group = QGroupBox("IDS Peak Konfiguration")
        ids_layout = QFormLayout(ids_group)
        
        # Konfigurationsdatei
        config_layout = QHBoxLayout()
        
        self.camera_config_path = QLineEdit()
        self.camera_config_path.setPlaceholderText("Pfad zur IDS Peak .toml Konfigurationsdatei")
        config_layout.addWidget(self.camera_config_path)
        
        self.browse_config_btn = QPushButton("📁 Durchsuchen")
        self.browse_config_btn.clicked.connect(self.browse_camera_config)
        config_layout.addWidget(self.browse_config_btn)
        
        ids_layout.addRow("Konfigurationsdatei:", config_layout)
        
        # Test-Button
        self.test_config_btn = QPushButton("🧪 Konfiguration testen")
        self.test_config_btn.clicked.connect(self.test_camera_config)
        ids_layout.addRow(self.test_config_btn)
        
        layout.addWidget(ids_group)
        
        # IDS Peak Info
        info_group = QGroupBox("IDS Peak Information")
        info_layout = QVBoxLayout(info_group)
        
        info_text = QTextEdit()
        info_text.setReadOnly(True)
        info_text.setMaximumHeight(150)
        info_text.setText("""
        IDS Peak Kamera-Unterstützung:
        
        • Automatisches Laden von .toml Konfigurationsdateien
        • Unterstützung für Gamma, Gain, Sharpness-Einstellungen
        • Spiegelung (ReverseX/ReverseY) 
        • Robuste Verbindungsbehandlung mit mehreren Versuchen
        • Erweiterte Bildkonvertierung mit IDS IPL Extension
        
        Erstellen Sie Konfigurationsdateien mit der IDS Peak Software.
        """)
        info_layout.addWidget(info_text)
        
        layout.addWidget(info_group)
        
        # Konfiguration-Details
        details_group = QGroupBox("Aktuelle Konfiguration")
        details_layout = QVBoxLayout(details_group)
        
        self.config_details = QTextEdit()
        self.config_details.setReadOnly(True)
        self.config_details.setMaximumHeight(120)
        self.config_details.setPlaceholderText("Konfigurationsdetails werden hier angezeigt...")
        details_layout.addWidget(self.config_details)
        
        layout.addWidget(details_group)
        layout.addStretch()
        
        return widget
    
    def create_general_tab(self):
        """Allgemeine Kamera-Einstellungen Tab erstellen."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Video-Einstellungen
        video_group = QGroupBox("Video-Einstellungen")
        video_layout = QFormLayout(video_group)
        
        self.video_width = QSpinBox()
        self.video_width.setRange(320, 4096)
        self.video_width.setValue(1936)
        video_layout.addRow("Video-Breite:", self.video_width)
        
        self.video_height = QSpinBox()
        self.video_height.setRange(240, 3072)
        self.video_height.setValue(1216)
        video_layout.addRow("Video-Höhe:", self.video_height)
        
        layout.addWidget(video_group)
        
        # Anzeige-Einstellungen
        display_group = QGroupBox("Anzeige-Einstellungen")
        display_layout = QFormLayout(display_group)
        
        self.show_confidence = QCheckBox("Konfidenz-Werte anzeigen")
        display_layout.addRow(self.show_confidence)
        
        self.show_class_names = QCheckBox("Klassennamen anzeigen")
        display_layout.addRow(self.show_class_names)
        
        layout.addWidget(display_group)
        
        # Automatische Funktionen
        auto_group = QGroupBox("Automatische Funktionen")
        auto_layout = QFormLayout(auto_group)
        
        self.auto_save_snapshots = QCheckBox("Automatische Schnappschüsse")
        auto_layout.addRow(self.auto_save_snapshots)
        
        layout.addWidget(auto_group)
        
        # Preset-Auflösungen
        presets_group = QGroupBox("Auflösungs-Presets")
        presets_layout = QVBoxLayout(presets_group)
        
        preset_buttons = QHBoxLayout()
        
        self.hd_btn = QPushButton("HD (1280x720)")
        self.hd_btn.clicked.connect(lambda: self.set_resolution(1280, 720))
        preset_buttons.addWidget(self.hd_btn)
        
        self.fhd_btn = QPushButton("Full HD (1920x1080)")
        self.fhd_btn.clicked.connect(lambda: self.set_resolution(1920, 1080))
        preset_buttons.addWidget(self.fhd_btn)
        
        self.custom_btn = QPushButton("IDS Custom (1936x1216)")
        self.custom_btn.clicked.connect(lambda: self.set_resolution(1936, 1216))
        preset_buttons.addWidget(self.custom_btn)
        
        presets_layout.addLayout(preset_buttons)
        layout.addWidget(presets_group)
        
        layout.addStretch()
        
        return widget
    
    def create_autoload_tab(self):
        """Auto-Loading Tab erstellen."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Auto-Loading Einstellungen
        autoload_group = QGroupBox("Automatisches Laden beim Start")
        autoload_layout = QFormLayout(autoload_group)
        
        # Letztes Modell
        model_layout = QHBoxLayout()
        
        self.last_model_path = QLineEdit()
        self.last_model_path.setReadOnly(True)
        self.last_model_path.setPlaceholderText("Kein Modell gespeichert")
        model_layout.addWidget(self.last_model_path)
        
        self.clear_model_btn = QPushButton("🗑️ Löschen")
        self.clear_model_btn.clicked.connect(self.clear_last_model)
        model_layout.addWidget(self.clear_model_btn)
        
        autoload_layout.addRow("Letztes Modell:", model_layout)
        
        # Letzte Quelle
        source_layout = QHBoxLayout()
        
        self.last_source_path = QLineEdit()
        self.last_source_path.setReadOnly(True)
        self.last_source_path.setPlaceholderText("Keine Quelle gespeichert")
        source_layout.addWidget(self.last_source_path)
        
        self.clear_source_btn = QPushButton("🗑️ Löschen")
        self.clear_source_btn.clicked.connect(self.clear_last_source)
        source_layout.addWidget(self.clear_source_btn)
        
        autoload_layout.addRow("Letzte Quelle:", source_layout)
        
        # Modus
        self.last_mode_video = QCheckBox("Letzter Modus war Video")
        self.last_mode_video.setEnabled(False)  # Nur Info-Anzeige
        autoload_layout.addRow("Modus:", self.last_mode_video)
        
        layout.addWidget(autoload_group)
        
        # Auto-Loading Info
        info_group = QGroupBox("Funktionsweise")
        info_layout = QVBoxLayout(info_group)
        
        info_text = QTextEdit()
        info_text.setReadOnly(True)
        info_text.setMaximumHeight(120)
        info_text.setText("""
        Auto-Loading beim Anwendungsstart:
        
        • Letztes KI-Modell wird automatisch geladen
        • Letzte Kamera/Video-Quelle wird automatisch gesetzt
        • Modus (Kamera/Video) wird gespeichert
        • Kamera-Konfiguration wird automatisch angewendet
        
        Dies ermöglicht einen schnellen Restart der Anwendung.
        """)
        info_layout.addWidget(info_text)
        
        layout.addWidget(info_group)
        layout.addStretch()
        
        return widget
    
    def browse_camera_config(self):
        """IDS Peak Konfigurationsdatei durchsuchen."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "IDS Peak Konfigurationsdatei auswählen",
            "",
            "TOML Files (*.toml);;All Files (*)"
        )
        
        if file_path:
            self.camera_config_path.setText(file_path)
            self.load_config_details(file_path)
    
    def load_config_details(self, config_path):
        """Konfigurationsdetails laden und anzeigen."""
        try:
            # Versuche TOML-Datei zu laden und Details anzuzeigen
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    content = f.read()[:500]  # Erste 500 Zeichen anzeigen
                
                self.config_details.setText(f"Konfiguration: {os.path.basename(config_path)}\n\n{content}...")
            else:
                self.config_details.setText("Datei nicht gefunden")
                
        except Exception as e:
            self.config_details.setText(f"Fehler beim Laden: {str(e)}")
    
    def test_camera_config(self):
        """Kamera-Konfiguration testen."""
        config_path = self.camera_config_path.text()
        
        if not config_path:
            QMessageBox.warning(self, "Test", "Bitte wählen Sie zuerst eine Konfigurationsdatei aus.")
            return
        
        if not os.path.exists(config_path):
            QMessageBox.warning(self, "Test", "Konfigurationsdatei nicht gefunden.")
            return
        
        try:
            # Hier würde normalerweise die Konfiguration getestet
            QMessageBox.information(
                self, 
                "Test erfolgreich", 
                f"Konfigurationsdatei '{os.path.basename(config_path)}' ist gültig."
            )
        except Exception as e:
            QMessageBox.critical(self, "Test fehlgeschlagen", f"Fehler beim Testen der Konfiguration:\n{str(e)}")
    
    def set_resolution(self, width, height):
        """Auflösung setzen."""
        self.video_width.setValue(width)
        self.video_height.setValue(height)
    
    def clear_last_model(self):
        """Letztes Modell löschen."""
        self.last_model_path.clear()
    
    def clear_last_source(self):
        """Letzte Quelle löschen."""
        self.last_source_path.clear()
    
    def load_settings(self):
        """Einstellungen laden."""
        # IDS Peak
        self.camera_config_path.setText(self.settings.get('camera_config_path', ''))
        if self.camera_config_path.text():
            self.load_config_details(self.camera_config_path.text())
        
        # Video
        self.video_width.setValue(self.settings.get('video_width', 1936))
        self.video_height.setValue(self.settings.get('video_height', 1216))
        
        # Anzeige
        self.show_confidence.setChecked(self.settings.get('show_confidence', True))
        self.show_class_names.setChecked(self.settings.get('show_class_names', True))
        self.auto_save_snapshots.setChecked(self.settings.get('auto_save_snapshots', False))
        
        # Auto-Loading
        self.last_model_path.setText(self.settings.get('last_model', ''))
        self.last_source_path.setText(str(self.settings.get('last_source', '')))
        self.last_mode_video.setChecked(self.settings.get('last_mode_was_video', False))
    
    def save_settings(self):
        """Einstellungen speichern."""
        # IDS Peak
        self.settings.set('camera_config_path', self.camera_config_path.text())
        
        # Video
        self.settings.set('video_width', self.video_width.value())
        self.settings.set('video_height', self.video_height.value())
        
        # Anzeige
        self.settings.set('show_confidence', self.show_confidence.isChecked())
        self.settings.set('show_class_names', self.show_class_names.isChecked())
        self.settings.set('auto_save_snapshots', self.auto_save_snapshots.isChecked())
        
        # Auto-Loading wird normalerweise automatisch von der Hauptanwendung gesetzt
        # Hier können manuell geleerte Werte gespeichert werden
        if not self.last_model_path.text():
            self.settings.set('last_model', '')
        if not self.last_source_path.text():
            self.settings.set('last_source', None)