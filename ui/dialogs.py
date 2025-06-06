"""
Dialog-Komponenten für Kamera-Auswahl und Einstellungen
Alle Dialog-Fenster der Anwendung
"""

import os
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
    QFrame, QFileDialog, QSpinBox, QDoubleSpinBox, QCheckBox, 
    QFormLayout, QMessageBox, QListWidget
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

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
        
        webcam_label = QLabel("Webcams:")
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
        
        video_label = QLabel("Video-Datei:")
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
    """Erweiterte Einstellungen-Dialog für industriellen Workflow ohne Helligkeits-Limits."""
    
    def __init__(self, settings, parent=None):
        super().__init__(parent)
        self.settings = settings
        self.setWindowTitle("Industrielle Workflow-Einstellungen")
        self.setModal(True)
        self.resize(600, 800)
        
        self.setup_ui()
        self.load_settings()
    
    def setup_ui(self):
        """UI aufbauen."""
        layout = QVBoxLayout(self)
        
        # Form für Einstellungen
        form_layout = QFormLayout()
        
        # KI-Einstellungen
        self._create_ai_section(form_layout)
        
        # Industrieller Workflow
        self._create_workflow_section(form_layout)
        
        # Schlecht-Teil Konfiguration
        self._create_bad_parts_section(form_layout)
        
        # Helligkeitsüberwachung
        self._create_brightness_section(form_layout)
        
        # Video-Einstellungen
        self._create_video_section(form_layout)
        
        # Anzeige-Optionen
        self._create_display_section(form_layout)
        
        layout.addLayout(form_layout)
        
        # Buttons
        self._create_button_section(layout)
    
    def _create_ai_section(self, form_layout):
        """KI-Einstellungen erstellen."""
        ki_label = QLabel("KI-Einstellungen")
        ki_label.setFont(QFont("", 12, QFont.Weight.Bold))
        form_layout.addRow(ki_label)
        
        self.confidence_spin = QDoubleSpinBox()
        self.confidence_spin.setRange(0.1, 1.0)
        self.confidence_spin.setSingleStep(0.1)
        self.confidence_spin.setDecimals(2)
        form_layout.addRow("Konfidenz-Schwellwert:", self.confidence_spin)
    
    def _create_workflow_section(self, form_layout):
        """Workflow-Einstellungen erstellen."""
        workflow_label = QLabel("Industrieller Workflow")
        workflow_label.setFont(QFont("", 12, QFont.Weight.Bold))
        form_layout.addRow(workflow_label)
        
        self.motion_threshold_spin = QSpinBox()
        self.motion_threshold_spin.setRange(1, 255)
        form_layout.addRow("Motion Threshold (1-255):", self.motion_threshold_spin)
        
        self.settling_time_spin = QDoubleSpinBox()
        self.settling_time_spin.setRange(0.1, 10.0)
        self.settling_time_spin.setSingleStep(0.1)
        form_layout.addRow("Ausschwingzeit (Sekunden):", self.settling_time_spin)
        
        self.capture_time_spin = QDoubleSpinBox()
        self.capture_time_spin.setRange(0.5, 10.0)
        self.capture_time_spin.setSingleStep(0.1)
        form_layout.addRow("Aufnahmezeit (Sekunden):", self.capture_time_spin)
        
        self.blow_off_time_spin = QDoubleSpinBox()
        self.blow_off_time_spin.setRange(1.0, 30.0)
        self.blow_off_time_spin.setSingleStep(0.5)
        form_layout.addRow("Abblas-Wartezeit (Sekunden):", self.blow_off_time_spin)
    
    def _create_bad_parts_section(self, form_layout):
        """Schlecht-Teil-Konfiguration erstellen."""
        bad_parts_label = QLabel("Schlecht-Teil Konfiguration")
        bad_parts_label.setFont(QFont("", 12, QFont.Weight.Bold))
        form_layout.addRow(bad_parts_label)
        
        self.bad_part_classes_list = QListWidget()
        self.bad_part_classes_list.setMaximumHeight(100)
        form_layout.addRow("Schlecht-Teil Klassen (IDs):", self.bad_part_classes_list)
        
        # Input für neue Klassen-ID
        bad_class_input_layout = QHBoxLayout()
        self.bad_class_input = QSpinBox()
        self.bad_class_input.setRange(0, 999)
        bad_class_input_layout.addWidget(self.bad_class_input)
        
        add_bad_class_btn = QPushButton("Hinzufügen")
        add_bad_class_btn.clicked.connect(self.add_bad_class)
        bad_class_input_layout.addWidget(add_bad_class_btn)
        
        remove_bad_class_btn = QPushButton("Entfernen")
        remove_bad_class_btn.clicked.connect(self.remove_bad_class)
        bad_class_input_layout.addWidget(remove_bad_class_btn)
        
        form_layout.addRow("Klassen-ID hinzufügen:", bad_class_input_layout)
        
        self.bad_part_confidence_spin = QDoubleSpinBox()
        self.bad_part_confidence_spin.setRange(0.1, 1.0)
        self.bad_part_confidence_spin.setSingleStep(0.1)
        self.bad_part_confidence_spin.setDecimals(2)
        form_layout.addRow("Mindest-Konfidenz für Schlecht-Teile:", self.bad_part_confidence_spin)
    
    def _create_brightness_section(self, form_layout):
        """Helligkeitsüberwachung erstellen."""
        brightness_label = QLabel("Helligkeitsüberwachung")
        brightness_label.setFont(QFont("", 12, QFont.Weight.Bold))
        form_layout.addRow(brightness_label)
        
        self.brightness_low_spin = QSpinBox()
        self.brightness_low_spin.setRange(0, 254)
        self.brightness_low_spin.valueChanged.connect(self.validate_brightness_ranges)
        form_layout.addRow("Untere Schwelle:", self.brightness_low_spin)
        
        self.brightness_high_spin = QSpinBox()
        self.brightness_high_spin.setRange(1, 255)
        self.brightness_high_spin.valueChanged.connect(self.validate_brightness_ranges)
        form_layout.addRow("Obere Schwelle:", self.brightness_high_spin)
        
        self.brightness_duration_spin = QDoubleSpinBox()
        self.brightness_duration_spin.setRange(1.0, 30.0)
        self.brightness_duration_spin.setSingleStep(0.5)
        form_layout.addRow("Warndauer (Sekunden):", self.brightness_duration_spin)
    
    def _create_video_section(self, form_layout):
        """Video-Einstellungen erstellen."""
        video_label = QLabel("Video-Einstellungen")
        video_label.setFont(QFont("", 12, QFont.Weight.Bold))
        form_layout.addRow(video_label)
        
        self.width_spin = QSpinBox()
        self.width_spin.setRange(320, 1920)
        self.width_spin.setSingleStep(160)
        form_layout.addRow("Video-Breite:", self.width_spin)
        
        self.height_spin = QSpinBox()
        self.height_spin.setRange(240, 1080)
        self.height_spin.setSingleStep(120)
        form_layout.addRow("Video-Höhe:", self.height_spin)
    
    def _create_display_section(self, form_layout):
        """Anzeige-Optionen erstellen."""
        display_label = QLabel("Anzeige-Optionen")
        display_label.setFont(QFont("", 12, QFont.Weight.Bold))
        form_layout.addRow(display_label)
        
        self.show_confidence_check = QCheckBox()
        form_layout.addRow("Konfidenz anzeigen:", self.show_confidence_check)
        
        self.show_names_check = QCheckBox()
        form_layout.addRow("Klassennamen anzeigen:", self.show_names_check)
    
    def _create_button_section(self, layout):
        """Button-Sektion erstellen."""
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
    
    def validate_brightness_ranges(self):
        """Stelle sicher, dass Low < High bei Helligkeitseinstellungen."""
        low_value = self.brightness_low_spin.value()
        high_value = self.brightness_high_spin.value()
        
        # Wenn Low >= High, korrigiere automatisch
        if low_value >= high_value:
            if self.sender() == self.brightness_low_spin:
                # Low wurde geändert und ist zu hoch
                self.brightness_high_spin.setValue(low_value + 1)
            else:
                # High wurde geändert und ist zu niedrig
                self.brightness_low_spin.setValue(high_value - 1)
    
    def add_bad_class(self):
        """Schlecht-Teil Klasse hinzufügen."""
        class_id = self.bad_class_input.value()
        # Prüfe ob bereits vorhanden
        for i in range(self.bad_part_classes_list.count()):
            if self.bad_part_classes_list.item(i).text() == str(class_id):
                return  # Bereits vorhanden
        
        self.bad_part_classes_list.addItem(str(class_id))
    
    def remove_bad_class(self):
        """Ausgewählte Schlecht-Teil Klasse entfernen."""
        current_row = self.bad_part_classes_list.currentRow()
        if current_row >= 0:
            self.bad_part_classes_list.takeItem(current_row)
    
    def load_settings(self):
        """Aktuelle Einstellungen laden."""
        self.confidence_spin.setValue(self.settings.get('confidence_threshold', 0.5))
        self.motion_threshold_spin.setValue(self.settings.get('motion_threshold', 110))
        self.settling_time_spin.setValue(self.settings.get('settling_time', 1.0))
        self.capture_time_spin.setValue(self.settings.get('capture_time', 3.0))
        self.blow_off_time_spin.setValue(self.settings.get('blow_off_time', 5.0))
        
        # Schlecht-Teil Klassen laden
        bad_classes = self.settings.get('bad_part_classes', [1])
        self.bad_part_classes_list.clear()
        for class_id in bad_classes:
            self.bad_part_classes_list.addItem(str(class_id))
        
        self.bad_part_confidence_spin.setValue(self.settings.get('bad_part_min_confidence', 0.5))
        self.brightness_low_spin.setValue(self.settings.get('brightness_low_threshold', 30))
        self.brightness_high_spin.setValue(self.settings.get('brightness_high_threshold', 220))
        self.brightness_duration_spin.setValue(self.settings.get('brightness_duration_threshold', 3.0))
        self.width_spin.setValue(self.settings.get('video_width', 1280))
        self.height_spin.setValue(self.settings.get('video_height', 720))
        self.show_confidence_check.setChecked(self.settings.get('show_confidence', True))
        self.show_names_check.setChecked(self.settings.get('show_class_names', True))
    
    def save_settings(self):
        """Einstellungen speichern."""
        self.settings.set('confidence_threshold', self.confidence_spin.value())
        self.settings.set('motion_threshold', self.motion_threshold_spin.value())
        self.settings.set('settling_time', self.settling_time_spin.value())
        self.settings.set('capture_time', self.capture_time_spin.value())
        self.settings.set('blow_off_time', self.blow_off_time_spin.value())
        
        # Schlecht-Teil Klassen sammeln
        bad_classes = []
        for i in range(self.bad_part_classes_list.count()):
            bad_classes.append(int(self.bad_part_classes_list.item(i).text()))
        self.settings.set('bad_part_classes', bad_classes)
        
        self.settings.set('bad_part_min_confidence', self.bad_part_confidence_spin.value())
        self.settings.set('brightness_low_threshold', self.brightness_low_spin.value())
        self.settings.set('brightness_high_threshold', self.brightness_high_spin.value())
        self.settings.set('brightness_duration_threshold', self.brightness_duration_spin.value())
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
            self.settings.save()
            self.load_settings()