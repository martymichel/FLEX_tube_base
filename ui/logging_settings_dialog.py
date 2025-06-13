"""
Logging-Einstellungen Dialog
Datenprotokollierung und Bildspeicherung
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QFormLayout,
    QLineEdit, QPushButton, QLabel, QCheckBox, QSpinBox,
    QFileDialog, QTextEdit, QTabWidget, QComboBox, QMessageBox,
    QTableWidget, QTableWidgetItem, QHeaderView
)
from PyQt6.QtCore import Qt
import os

class LoggingSettingsTab(QWidget):
    """Tab für Logging-Einstellungen."""
    
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
        
        # Bildspeicherung Tab
        images_tab = self.create_images_tab()
        tab_widget.addTab(images_tab, "Bildspeicherung")
        
        # Parquet-Logging Tab
        parquet_tab = self.create_parquet_tab()
        tab_widget.addTab(parquet_tab, "Parquet-Logs")
        
        # Log-Dateien Tab
        files_tab = self.create_files_tab()
        tab_widget.addTab(files_tab, "Log-Dateien")
        
        # System-Logging Tab
        system_tab = self.create_system_tab()
        tab_widget.addTab(system_tab, "System-Logs")
    
    def create_images_tab(self):
        """Bildspeicherung Tab erstellen."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Bildspeicherung aktivieren
        enable_group = QGroupBox("Bildspeicherung")
        enable_layout = QFormLayout(enable_group)
        
        self.save_bad_images = QCheckBox("Schlechtbilder speichern")
        enable_layout.addRow(self.save_bad_images)
        
        self.save_good_images = QCheckBox("Gutbilder speichern")
        enable_layout.addRow(self.save_good_images)
        
        layout.addWidget(enable_group)
        
        # Verzeichnis-Einstellungen
        dirs_group = QGroupBox("Verzeichnisse")
        dirs_layout = QFormLayout(dirs_group)
        
        # Schlechtbilder-Verzeichnis
        bad_dir_layout = QHBoxLayout()
        self.bad_images_dir = QLineEdit()
        self.bad_images_dir.setPlaceholderText("bad_images")
        bad_dir_layout.addWidget(self.bad_images_dir)
        
        self.browse_bad_dir_btn = QPushButton("📁")
        self.browse_bad_dir_btn.clicked.connect(self.browse_bad_images_dir)
        bad_dir_layout.addWidget(self.browse_bad_dir_btn)
        
        dirs_layout.addRow("Schlechtbilder:", bad_dir_layout)
        
        # Gutbilder-Verzeichnis
        good_dir_layout = QHBoxLayout()
        self.good_images_dir = QLineEdit()
        self.good_images_dir.setPlaceholderText("good_images")
        good_dir_layout.addWidget(self.good_images_dir)
        
        self.browse_good_dir_btn = QPushButton("📁")
        self.browse_good_dir_btn.clicked.connect(self.browse_good_images_dir)
        good_dir_layout.addWidget(self.browse_good_dir_btn)
        
        dirs_layout.addRow("Gutbilder:", good_dir_layout)
        
        layout.addWidget(dirs_group)
        
        # Datei-Limits
        limits_group = QGroupBox("Datei-Limits")
        limits_layout = QFormLayout(limits_group)
        
        self.max_image_files = QSpinBox()
        self.max_image_files.setRange(100, 1000000)
        self.max_image_files.setValue(10000)
        limits_layout.addRow("Max. Dateien pro Verzeichnis:", self.max_image_files)
        
        layout.addWidget(limits_group)
        
        # Bildspeicherung-Info
        info_group = QGroupBox("Information")
        info_layout = QVBoxLayout(info_group)
        
        info_text = QTextEdit()
        info_text.setReadOnly(True)
        info_text.setMaximumHeight(100)
        info_text.setText("""
        Bildspeicherung:
        • Bilder werden mit Zeitstempel gespeichert
        • Automatische Begrenzung der Dateienanzahl
        • Separate Verzeichnisse für gute und schlechte Teile
        • Bilder werden OHNE Bounding Boxes gespeichert (Original)
        """)
        info_layout.addWidget(info_text)
        
        layout.addWidget(info_group)
        layout.addStretch()
        
        return widget
    
    def create_parquet_tab(self):
        """Parquet-Logging Tab erstellen."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Parquet-Logging aktivieren
        enable_group = QGroupBox("Parquet-Logging")
        enable_layout = QFormLayout(enable_group)
        
        self.parquet_log_enabled = QCheckBox("Parquet-Logging aktivieren")
        enable_layout.addRow(self.parquet_log_enabled)
        
        layout.addWidget(enable_group)
        
        # Parquet-Einstellungen
        parquet_group = QGroupBox("Einstellungen")
        parquet_layout = QFormLayout(parquet_group)
        
        # Log-Verzeichnis
        log_dir_layout = QHBoxLayout()
        self.parquet_log_dir = QLineEdit()
        self.parquet_log_dir.setPlaceholderText("logs/detection_events")
        log_dir_layout.addWidget(self.parquet_log_dir)
        
        self.browse_log_dir_btn = QPushButton("📁")
        self.browse_log_dir_btn.clicked.connect(self.browse_parquet_log_dir)
        log_dir_layout.addWidget(self.browse_log_dir_btn)
        
        parquet_layout.addRow("Log-Verzeichnis:", log_dir_layout)
        
        # Max. Dateien
        self.parquet_max_files = QSpinBox()
        self.parquet_max_files.setRange(10, 10000000)
        self.parquet_max_files.setValue(1000000)
        parquet_layout.addRow("Max. Log-Dateien:", self.parquet_max_files)
        
        layout.addWidget(parquet_group)
        
        # Parquet-Info
        info_group = QGroupBox("Parquet-Format Information")
        info_layout = QVBoxLayout(info_group)
        
        info_text = QTextEdit()
        info_text.setReadOnly(True)
        info_text.setMaximumHeight(120)
        info_text.setText("""
        Parquet-Logging Features:
        • Tagebasierte Dateien (detection_events_YYYY-MM-DD.parquet)
        • Komprimierte Speicherung mit Snappy-Kompression
        • Strukturierte Event-Daten mit JSON-Details
        • Kompatibel mit pandas, Apache Spark, etc.
        • Automatische Bereinigung alter Dateien
        • Viewer-Tool: parquete_file_opener.py
        """)
        info_layout.addWidget(info_text)
        
        layout.addWidget(info_group)
        
        # Parquet-Viewer
        viewer_group = QGroupBox("Parquet-Viewer")
        viewer_layout = QVBoxLayout(viewer_group)
        
        self.open_viewer_btn = QPushButton("📊 Parquet-Viewer öffnen")
        self.open_viewer_btn.clicked.connect(self.open_parquet_viewer)
        viewer_layout.addWidget(self.open_viewer_btn)
        
        layout.addWidget(viewer_group)
        layout.addStretch()
        
        return widget
    
    def create_files_tab(self):
        """Log-Dateien Tab erstellen."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Aktuelle Log-Dateien
        files_group = QGroupBox("Verfügbare Log-Dateien")
        files_layout = QVBoxLayout(files_group)
        
        # Refresh-Button
        refresh_layout = QHBoxLayout()
        self.refresh_files_btn = QPushButton("🔄 Aktualisieren")
        self.refresh_files_btn.clicked.connect(self.refresh_log_files)
        refresh_layout.addWidget(self.refresh_files_btn)
        refresh_layout.addStretch()
        
        files_layout.addLayout(refresh_layout)
        
        # Dateien-Tabelle
        self.files_table = QTableWidget()
        self.files_table.setColumnCount(4)
        self.files_table.setHorizontalHeaderLabels([
            "Dateiname", "Größe (MB)", "Geändert", "Aktion"
        ])
        
        header = self.files_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        
        files_layout.addWidget(self.files_table)
        
        layout.addWidget(files_group)
        
        # Bereinigung
        cleanup_group = QGroupBox("Bereinigung")
        cleanup_layout = QVBoxLayout(cleanup_group)
        
        cleanup_buttons = QHBoxLayout()
        
        self.cleanup_old_btn = QPushButton("🗑️ Alte Dateien löschen")
        self.cleanup_old_btn.clicked.connect(self.cleanup_old_files)
        cleanup_buttons.addWidget(self.cleanup_old_btn)
        
        self.cleanup_all_btn = QPushButton("⚠️ Alle Logs löschen")
        self.cleanup_all_btn.clicked.connect(self.cleanup_all_files)
        self.cleanup_all_btn.setStyleSheet("background-color: #e74c3c; color: white;")
        cleanup_buttons.addWidget(self.cleanup_all_btn)
        
        cleanup_layout.addLayout(cleanup_buttons)
        layout.addWidget(cleanup_group)
        
        layout.addStretch()
        
        return widget
    
    def create_system_tab(self):
        """System-Logging Tab erstellen."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Log-Level
        level_group = QGroupBox("Log-Level")
        level_layout = QFormLayout(level_group)
        
        self.log_level = QComboBox()
        self.log_level.addItems(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
        self.log_level.setCurrentText("INFO")
        level_layout.addRow("Log-Level:", self.log_level)
        
        layout.addWidget(level_group)
        
        # System-Log-Info
        info_group = QGroupBox("System-Logging Information")
        info_layout = QVBoxLayout(info_group)
        
        info_text = QTextEdit()
        info_text.setReadOnly(True)
        info_text.setMaximumHeight(150)
        info_text.setText("""
        System-Logging Levels:
        
        • DEBUG: Detaillierte Informationen für Debugging
        • INFO: Allgemeine Informationen über Programmablauf
        • WARNING: Warnungen über potentielle Probleme
        • ERROR: Fehler die das Programm beeinträchtigen
        • CRITICAL: Schwere Fehler die das Programm stoppen
        
        Empfehlung: INFO für normalen Betrieb, DEBUG für Problemanalyse
        """)
        info_layout.addWidget(info_text)
        
        layout.addWidget(info_group)
        layout.addStretch()
        
        return widget
    
    def browse_bad_images_dir(self):
        """Schlechtbilder-Verzeichnis durchsuchen."""
        dir_path = QFileDialog.getExistingDirectory(
            self,
            "Schlechtbilder-Verzeichnis auswählen",
            self.bad_images_dir.text() or "bad_images"
        )
        if dir_path:
            self.bad_images_dir.setText(dir_path)
    
    def browse_good_images_dir(self):
        """Gutbilder-Verzeichnis durchsuchen."""
        dir_path = QFileDialog.getExistingDirectory(
            self,
            "Gutbilder-Verzeichnis auswählen",
            self.good_images_dir.text() or "good_images"
        )
        if dir_path:
            self.good_images_dir.setText(dir_path)
    
    def browse_parquet_log_dir(self):
        """Parquet-Log-Verzeichnis durchsuchen."""
        dir_path = QFileDialog.getExistingDirectory(
            self,
            "Parquet-Log-Verzeichnis auswählen",
            self.parquet_log_dir.text() or "logs/detection_events"
        )
        if dir_path:
            self.parquet_log_dir.setText(dir_path)
    
    def open_parquet_viewer(self):
        """Parquet-Viewer öffnen."""
        try:
            import subprocess
            import sys
            
            # Versuche den Parquet-Viewer zu starten
            viewer_path = "parquete_file_opener.py"
            if os.path.exists(viewer_path):
                subprocess.Popen([sys.executable, viewer_path])
                QMessageBox.information(self, "Viewer", "Parquet-Viewer wird geöffnet...")
            else:
                QMessageBox.warning(self, "Viewer", "Parquet-Viewer nicht gefunden (parquete_file_opener.py)")
                
        except Exception as e:
            QMessageBox.critical(self, "Fehler", f"Fehler beim Öffnen des Viewers:\n{str(e)}")
    
    def refresh_log_files(self):
        """Log-Dateien aktualisieren."""
        # Hier würde normalerweise die Liste der Log-Dateien aktualisiert
        self.files_table.setRowCount(0)
        
        # Beispiel-Einträge (in echter Implementierung aus detection_logger holen)
        example_files = [
            ("detection_events_2025-01-06.parquet", 2.5, "2025-01-06 15:30"),
            ("detection_events_2025-01-05.parquet", 4.1, "2025-01-05 23:59"),
            ("detection_events_2025-01-04.parquet", 3.8, "2025-01-04 23:59"),
        ]
        
        for i, (filename, size, modified) in enumerate(example_files):
            self.files_table.insertRow(i)
            
            self.files_table.setItem(i, 0, QTableWidgetItem(filename))
            self.files_table.setItem(i, 1, QTableWidgetItem(f"{size:.1f}"))
            self.files_table.setItem(i, 2, QTableWidgetItem(modified))
            
            # Aktion-Button
            action_btn = QPushButton("📊 Öffnen")
            action_btn.clicked.connect(lambda checked, f=filename: self.open_log_file(f))
            self.files_table.setCellWidget(i, 3, action_btn)
    
    def open_log_file(self, filename):
        """Spezifische Log-Datei öffnen."""
        QMessageBox.information(self, "Datei öffnen", f"Öffne {filename} im Parquet-Viewer...")
    
    def cleanup_old_files(self):
        """Alte Log-Dateien löschen."""
        reply = QMessageBox.question(
            self,
            "Alte Dateien löschen",
            "Alte Log-Dateien löschen?\n\n"
            "Dies löscht Dateien die das eingestellte Limit überschreiten.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            QMessageBox.information(self, "Bereinigung", "Alte Dateien wurden gelöscht.")
    
    def cleanup_all_files(self):
        """Alle Log-Dateien löschen."""
        reply = QMessageBox.question(
            self,
            "⚠️ WARNUNG ⚠️",
            "ALLE Log-Dateien löschen?\n\n"
            "Diese Aktion kann NICHT rückgängig gemacht werden!\n"
            "Alle Erkennungsdaten gehen verloren!",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # Zweite Bestätigung
            reply2 = QMessageBox.question(
                self,
                "Letzte Bestätigung",
                "Sind Sie WIRKLICH sicher?\n\nAlle Daten werden unwiderruflich gelöscht!",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply2 == QMessageBox.StandardButton.Yes:
                QMessageBox.information(self, "Bereinigung", "Alle Log-Dateien wurden gelöscht.")
    
    def load_settings(self):
        """Einstellungen laden."""
        # Bildspeicherung
        self.save_bad_images.setChecked(self.settings.get('save_bad_images', False))
        self.save_good_images.setChecked(self.settings.get('save_good_images', False))
        self.bad_images_dir.setText(self.settings.get('bad_images_directory', 'bad_images'))
        self.good_images_dir.setText(self.settings.get('good_images_directory', 'good_images'))
        self.max_image_files.setValue(self.settings.get('max_image_files', 10000))
        
        # Parquet-Logging
        self.parquet_log_enabled.setChecked(self.settings.get('parquet_log_enabled', True))
        self.parquet_log_dir.setText(self.settings.get('parquet_log_directory', 'logs/detection_events'))
        self.parquet_max_files.setValue(self.settings.get('parquet_log_max_files', 1000000))
        
        # System-Logging
        self.log_level.setCurrentText(self.settings.get('log_level', 'INFO'))
        
        # Log-Dateien aktualisieren
        self.refresh_log_files()
    
    def save_settings(self):
        """Einstellungen speichern."""
        # Bildspeicherung
        self.settings.set('save_bad_images', self.save_bad_images.isChecked())
        self.settings.set('save_good_images', self.save_good_images.isChecked())
        self.settings.set('bad_images_directory', self.bad_images_dir.text())
        self.settings.set('good_images_directory', self.good_images_dir.text())
        self.settings.set('max_image_files', self.max_image_files.value())
        
        # Parquet-Logging
        self.settings.set('parquet_log_enabled', self.parquet_log_enabled.isChecked())
        self.settings.set('parquet_log_directory', self.parquet_log_dir.text())
        self.settings.set('parquet_log_max_files', self.parquet_max_files.value())
        
        # System-Logging
        self.settings.set('log_level', self.log_level.currentText())