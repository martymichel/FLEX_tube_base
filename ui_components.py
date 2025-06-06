"""
UI-Komponenten - einfach und benutzerfreundlich
Moderne, touch-freundliche Benutzeroberfläche
"""

import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
    QSplitter, QFrame, QFileDialog, QDialog, QSpinBox,
    QDoubleSpinBox, QCheckBox, QFormLayout, QMessageBox,
    QTableWidget, QTableWidgetItem, QHeaderView
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap, QFont, QColor
import cv2
import numpy as np

class MainUI(QWidget):
    """Hauptbenutzeroberfläche."""
    
    def __init__(self, parent_app):
        super().__init__()
        self.app = parent_app
        self.setup_ui()
        
        # Statistiken
        self.detection_counts = {}
        self.total_detections = 0
    
    def setup_ui(self):
        """UI aufbauen."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Splitter für Sidebar und Hauptbereich
        splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(splitter)
        
        # Sidebar erstellen
        sidebar = self.create_sidebar()
        
        # Hauptbereich erstellen
        main_area = self.create_main_area()
        
        # Zu Splitter hinzufügen
        splitter.addWidget(sidebar)
        splitter.addWidget(main_area)
        
        # Größenverhältnis setzen
        splitter.setSizes([350, 1000])
    
    def create_sidebar(self):
        """Sidebar mit Steuerelementen erstellen."""
        sidebar = QFrame()
        sidebar.setStyleSheet("""
            QFrame {
                background-color: #2c3e50;
                color: white;
                border-radius: 8px;
            }
            QPushButton {
                background-color: #34495e;
                color: white;
                border: none;
                padding: 15px;
                border-radius: 8px;
                font-size: 14px;
                font-weight: bold;
                min-height: 20px;
            }
            QPushButton:hover {
                background-color: #3498db;
            }
            QPushButton:pressed {
                background-color: #2980b9;
            }
            QLabel {
                color: white;
                font-size: 14px;
            }
        """)
        sidebar.setMinimumWidth(320)
        sidebar.setMaximumWidth(400)
        
        layout = QVBoxLayout(sidebar)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Titel
        title = QLabel("KI-Objekterkennung")
        title.setFont(QFont("", 18, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Modell-Sektion
        model_section = QFrame()
        model_layout = QVBoxLayout(model_section)
        
        model_label = QLabel("🤖 KI-Modell:")
        model_label.setFont(QFont("", 12, QFont.Weight.Bold))
        model_layout.addWidget(model_label)
        
        self.model_info = QLabel("Kein Modell geladen")
        self.model_info.setWordWrap(True)
        self.model_info.setStyleSheet("color: #bdc3c7; font-style: italic;")
        model_layout.addWidget(self.model_info)
        
        self.model_btn = QPushButton("📁 Modell laden")
        model_layout.addWidget(self.model_btn)
        
        layout.addWidget(model_section)
        
        # Kamera-Sektion
        camera_section = QFrame()
        camera_layout = QVBoxLayout(camera_section)
        
        camera_label = QLabel("📹 Kamera/Video:")
        camera_label.setFont(QFont("", 12, QFont.Weight.Bold))
        camera_layout.addWidget(camera_label)
        
        self.camera_info = QLabel("Keine Quelle ausgewählt")
        self.camera_info.setWordWrap(True)
        self.camera_info.setStyleSheet("color: #bdc3c7; font-style: italic;")
        camera_layout.addWidget(self.camera_info)
        
        self.camera_btn = QPushButton("🎥 Quelle wählen")
        camera_layout.addWidget(self.camera_btn)
        
        layout.addWidget(camera_section)
        
        # Statistiken
        stats_label = QLabel("📊 Erkennungen:")
        stats_label.setFont(QFont("", 12, QFont.Weight.Bold))
        layout.addWidget(stats_label)
        
        self.stats_table = QTableWidget(0, 2)
        self.stats_table.setHorizontalHeaderLabels(["Klasse", "Anzahl"])
        self.stats_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.stats_table.verticalHeader().hide()
        self.stats_table.setMaximumHeight(200)
        self.stats_table.setStyleSheet("""
            QTableWidget {
                background-color: #34495e;
                color: white;
                border: none;
                border-radius: 4px;
            }
            QHeaderView::section {
                background-color: #2c3e50;
                color: white;
                border: none;
                padding: 5px;
            }
        """)
        layout.addWidget(self.stats_table)
        
        # Frame-Zähler
        self.frame_counter = QLabel("Frames: 0")
        self.frame_counter.setStyleSheet("color: #ecf0f1; background-color: #34495e; padding: 8px; border-radius: 4px;")
        layout.addWidget(self.frame_counter)
        
        # Aktionen
        layout.addWidget(QLabel())  # Spacer
        
        self.start_btn = QPushButton("▶ Starten")
        self.start_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                font-size: 16px;
                min-height: 50px;
            }
            QPushButton:hover {
                background-color: #2ecc71;
            }
        """)
        layout.addWidget(self.start_btn)
        
        self.snapshot_btn = QPushButton("📷 Schnappschuss")
        layout.addWidget(self.snapshot_btn)
        
        self.settings_btn = QPushButton("⚙ Einstellungen")
        layout.addWidget(self.settings_btn)
        
        # Stretch am Ende
        layout.addStretch()
        
        return sidebar
    
    def create_main_area(self):
        """Hauptbereich mit Video und Status erstellen."""
        main_area = QFrame()
        main_area.setStyleSheet("""
            QFrame {
                background-color: #ecf0f1;
                border-radius: 8px;
            }
        """)
        
        layout = QVBoxLayout(main_area)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Status oben
        self.status_label = QLabel("Bereit")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setFont(QFont("", 16, QFont.Weight.Bold))
        self.status_label.setStyleSheet("""
            QLabel {
                background-color: #95a5a6;
                color: white;
                padding: 15px;
                border-radius: 8px;
                margin-bottom: 10px;
            }
        """)
        layout.addWidget(self.status_label)
        
        # Video-Bereich
        self.video_label = QLabel()
        self.video_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.video_label.setMinimumSize(640, 480)
        self.video_label.setStyleSheet("""
            QLabel {
                background-color: #34495e;
                color: white;
                border-radius: 8px;
                font-size: 18px;
            }
        """)
        self.video_label.setText("🎥\n\nKein Video")
        layout.addWidget(self.video_label, 1)  # Stretch factor 1
        
        return main_area
    
    def show_status(self, message, status_type="info"):
        """Status anzeigen.
        
        Args:
            message (str): Status-Nachricht
            status_type (str): 'info', 'success', 'error', 'ready'
        """
        self.status_label.setText(message)
        
        colors = {
            'info': '#3498db',      # Blau
            'success': '#27ae60',   # Grün
            'error': '#e74c3c',     # Rot
            'ready': '#95a5a6'      # Grau
        }
        
        color = colors.get(status_type, '#95a5a6')
        self.status_label.setStyleSheet(f"""
            QLabel {{
                background-color: {color};
                color: white;
                padding: 15px;
                border-radius: 8px;
                margin-bottom: 10px;
            }}
        """)
    
    def update_video(self, frame):
        """Video-Frame aktualisieren.
        
        Args:
            frame: OpenCV-Frame (numpy array)
        """
        try:
            # Frame zu Qt-Format konvertieren
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb_frame.shape
            bytes_per_line = ch * w
            
            # QPixmap erstellen
            from PyQt6.QtGui import QImage
            qt_image = QImage(rgb_frame.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
            pixmap = QPixmap.fromImage(qt_image)
            
            # Skalieren für Video-Label
            scaled_pixmap = pixmap.scaled(
                self.video_label.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            
            self.video_label.setPixmap(scaled_pixmap)
            
        except Exception as e:
            print(f"Fehler beim Video-Update: {e}")
    
    def update_stats(self, detections):
        """Statistiken aktualisieren.
        
        Args:
            detections: Liste der Erkennungen
        """
        # Erkennungen zählen
        for detection in detections:
            _, _, _, _, _, class_id = detection
            class_name = self.app.detection_engine.class_names.get(class_id, f"Class {class_id}")
            
            if class_name not in self.detection_counts:
                self.detection_counts[class_name] = 0
            self.detection_counts[class_name] += 1
            self.total_detections += 1
        
        # Tabelle aktualisieren
        self.stats_table.setRowCount(len(self.detection_counts))
        for row, (class_name, count) in enumerate(self.detection_counts.items()):
            self.stats_table.setItem(row, 0, QTableWidgetItem(class_name))
            self.stats_table.setItem(row, 1, QTableWidgetItem(str(count)))
    
    def update_frame_count(self, count):
        """Frame-Zähler aktualisieren."""
        self.frame_counter.setText(f"Frames: {count}")
    
    def select_model_file(self):
        """Modell-Datei auswählen Dialog.
        
        Returns:
            str oder None: Pfad zur Modell-Datei
        """
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "KI-Modell auswählen",
            "",
            "PyTorch Modelle (*.pt);;Alle Dateien (*)"
        )
        
        if file_path:
            self.model_info.setText(os.path.basename(file_path))
            self.model_info.setStyleSheet("color: #27ae60; font-weight: bold;")
            
        return file_path
    
    def select_camera_source(self):
        """Kamera/Video-Quelle auswählen Dialog.
        
        Returns:
            Quelle oder None
        """
        dialog = CameraSelectionDialog(self.app.camera_manager, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            source = dialog.get_selected_source()
            if source:
                # Info aktualisieren
                if isinstance(source, int):
                    self.camera_info.setText(f"Webcam {source}")
                elif isinstance(source, str):
                    self.camera_info.setText(os.path.basename(source))
                elif isinstance(source, tuple):
                    self.camera_info.setText(f"IDS Kamera {source[1]}")
                
                self.camera_info.setStyleSheet("color: #27ae60; font-weight: bold;")
                return source
        
        return None
    
    def open_settings_dialog(self, settings):
        """Einstellungen-Dialog öffnen."""
        dialog = SettingsDialog(settings, self)
        dialog.exec()

class CameraSelectionDialog(QDialog):
    """Dialog zur Kamera/Video-Auswahl."""
    
    def __init__(self, camera_manager, parent=None):
        super().__init__(parent)
        self.camera_manager = camera_manager
        self.setWindowTitle("Kamera/Video auswählen")
        self.setModal(True)
        self.resize(500, 400)
        
        self.selected_source = None
        self.setup_ui()
    
    def setup_ui(self):
        """UI aufbauen."""
        layout = QVBoxLayout(self)
        
        # Webcam-Sektion
        webcam_section = QFrame()
        webcam_layout = QVBoxLayout(webcam_section)
        
        webcam_label = QLabel("📹 Webcams:")
        webcam_label.setFont(QFont("", 12, QFont.Weight.Bold))
        webcam_layout.addWidget(webcam_label)
        
        # Verfügbare Kameras anzeigen
        cameras = self.camera_manager.get_available_cameras()
        for cam_type, index, name in cameras:
            btn = QPushButton(name)
            if cam_type == 'webcam':
                btn.clicked.connect(lambda checked, idx=index: self.select_webcam(idx))
            elif cam_type == 'ids':
                btn.clicked.connect(lambda checked, idx=index: self.select_ids_camera(idx))
            webcam_layout.addWidget(btn)
        
        layout.addWidget(webcam_section)
        
        # Video-Sektion
        video_section = QFrame()
        video_layout = QVBoxLayout(video_section)
        
        video_label = QLabel("🎬 Video-Datei:")
        video_label.setFont(QFont("", 12, QFont.Weight.Bold))
        video_layout.addWidget(video_label)
        
        video_btn = QPushButton("Video-Datei auswählen...")
        video_btn.clicked.connect(self.select_video)
        video_layout.addWidget(video_btn)
        
        layout.addWidget(video_section)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        cancel_btn = QPushButton("Abbrechen")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
    
    def select_webcam(self, index):
        """Webcam auswählen."""
        self.selected_source = index
        self.accept()
    
    def select_ids_camera(self, index):
        """IDS Kamera auswählen."""
        self.selected_source = ('ids', index)
        self.accept()
    
    def select_video(self):
        """Video-Datei auswählen."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Video-Datei auswählen",
            "",
            "Video-Dateien (*.mp4 *.avi *.mkv *.mov);;Alle Dateien (*)"
        )
        
        if file_path:
            self.selected_source = file_path
            self.accept()
    
    def get_selected_source(self):
        """Ausgewählte Quelle zurückgeben."""
        return self.selected_source

class SettingsDialog(QDialog):
    """Einfacher Einstellungen-Dialog."""
    
    def __init__(self, settings, parent=None):
        super().__init__(parent)
        self.settings = settings
        self.setWindowTitle("Einstellungen")
        self.setModal(True)
        self.resize(400, 300)
        
        self.setup_ui()
        self.load_settings()
    
    def setup_ui(self):
        """UI aufbauen."""
        layout = QVBoxLayout(self)
        
        # Form für Einstellungen
        form_layout = QFormLayout()
        
        # Konfidenz-Schwellwert
        self.confidence_spin = QDoubleSpinBox()
        self.confidence_spin.setRange(0.1, 1.0)
        self.confidence_spin.setSingleStep(0.1)
        self.confidence_spin.setDecimals(2)
        form_layout.addRow("Konfidenz-Schwellwert:", self.confidence_spin)
        
        # Video-Auflösung
        self.width_spin = QSpinBox()
        self.width_spin.setRange(320, 1920)
        self.width_spin.setSingleStep(160)
        form_layout.addRow("Video-Breite:", self.width_spin)
        
        self.height_spin = QSpinBox()
        self.height_spin.setRange(240, 1080)
        self.height_spin.setSingleStep(120)
        form_layout.addRow("Video-Höhe:", self.height_spin)
        
        # Anzeige-Optionen
        self.show_confidence_check = QCheckBox()
        form_layout.addRow("Konfidenz anzeigen:", self.show_confidence_check)
        
        self.show_names_check = QCheckBox()
        form_layout.addRow("Klassennamen anzeigen:", self.show_names_check)
        
        layout.addLayout(form_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        save_btn = QPushButton("Speichern")
        save_btn.clicked.connect(self.save_settings)
        button_layout.addWidget(save_btn)
        
        cancel_btn = QPushButton("Abbrechen")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        reset_btn = QPushButton("Zurücksetzen")
        reset_btn.clicked.connect(self.reset_settings)
        button_layout.addWidget(reset_btn)
        
        layout.addLayout(button_layout)
    
    def load_settings(self):
        """Aktuelle Einstellungen laden."""
        self.confidence_spin.setValue(self.settings.get('confidence_threshold', 0.5))
        self.width_spin.setValue(self.settings.get('video_width', 1280))
        self.height_spin.setValue(self.settings.get('video_height', 720))
        self.show_confidence_check.setChecked(self.settings.get('show_confidence', True))
        self.show_names_check.setChecked(self.settings.get('show_class_names', True))
    
    def save_settings(self):
        """Einstellungen speichern."""
        self.settings.set('confidence_threshold', self.confidence_spin.value())
        self.settings.set('video_width', self.width_spin.value())
        self.settings.set('video_height', self.height_spin.value())
        self.settings.set('show_confidence', self.show_confidence_check.isChecked())
        self.settings.set('show_class_names', self.show_names_check.isChecked())
        
        self.settings.save()
        self.accept()
    
    def reset_settings(self):
        """Einstellungen zurücksetzen."""
        reply = QMessageBox.question(
            self,
            "Einstellungen zurücksetzen",
            "Alle Einstellungen auf Standardwerte zurücksetzen?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.settings.reset_to_defaults()
            self.load_settings()