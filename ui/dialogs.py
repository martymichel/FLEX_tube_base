"""
Dialog-Komponenten für Kamera-Auswahl und Einstellungen
Alle Dialog-Fenster der Anwendung mit Tab-basiertem Layout und Klassennamen-Support
"""

import os
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
    QFrame, QFileDialog, QSpinBox, QDoubleSpinBox, QCheckBox, 
    QFormLayout, QMessageBox, QListWidget, QTabWidget, QWidget,
    QScrollArea, QSizePolicy, QComboBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

class CameraSelectionDialog(QDialog):
    """Dialog zur Kamera/Video-Auswahl."""
    
    def __init__(self, camera_manager, parent=None):
        super().__init__(parent)
        self.camera_manager = camera_manager
        self.setWindowTitle("📹 Kamera/Video auswählen")
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
        
        webcam_label = QLabel("📷 Webcams:")
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
    """Tab-basierter Einstellungen-Dialog mit Klassennamen-Support."""
    
    def __init__(self, settings, class_names=None, parent=None):
        super().__init__(parent)
        self.settings = settings
        self.class_names = class_names or {}  # Dictionary {id: name}
        self.setWindowTitle("⚙️ Industrielle Workflow-Einstellungen")
        self.setModal(True)
        self.resize(800, 600)  # Breiteres Layout für Tabs
        
        self.setup_ui()
        self.load_settings()
    
    def setup_ui(self):
        """UI mit Tab-Layout aufbauen."""
        layout = QVBoxLayout(self)
        
        # Tab-Widget erstellen
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)
        
        # Tabs erstellen
        self._create_ai_workflow_tab()
        self._create_parts_config_tab()
        self._create_hardware_tab()
        self._create_storage_monitoring_tab()
        
        # Button-Sektion
        self._create_button_section(layout)
    
    def _create_ai_workflow_tab(self):
        """Tab 1: 🤖 KI & Workflow"""
        tab = QWidget()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(tab)
        
        layout = QFormLayout(tab)
        layout.setSpacing(15)
        
        # KI-Einstellungen
        self._add_section_header(layout, "🤖 KI-Einstellungen")
        
        self.confidence_spin = QDoubleSpinBox()
        self.confidence_spin.setRange(0.1, 1.0)
        self.confidence_spin.setSingleStep(0.1)
        self.confidence_spin.setDecimals(2)
        layout.addRow("Konfidenz-Schwellwert:", self.confidence_spin)
        
        self._add_spacer(layout)
        
        # Workflow-Einstellungen
        self._add_section_header(layout, "🏭 Industrieller Workflow")
        
        self.motion_threshold_spin = QSpinBox()
        self.motion_threshold_spin.setRange(1, 255)
        layout.addRow("Motion Threshold (1-255):", self.motion_threshold_spin)
        
        self.red_threshold_spin = QSpinBox()
        self.red_threshold_spin.setRange(1, 20)
        layout.addRow("Roter Rahmen Schwellwert:", self.red_threshold_spin)
        
        self.green_threshold_spin = QSpinBox()
        self.green_threshold_spin.setRange(1, 20)
        layout.addRow("Grüner Rahmen Schwellwert:", self.green_threshold_spin)
        
        self.settling_time_spin = QDoubleSpinBox()
        self.settling_time_spin.setRange(0.1, 10.0)
        self.settling_time_spin.setSingleStep(0.1)
        layout.addRow("Ausschwingzeit (Sekunden):", self.settling_time_spin)
        
        self.capture_time_spin = QDoubleSpinBox()
        self.capture_time_spin.setRange(0.5, 10.0)
        self.capture_time_spin.setSingleStep(0.1)
        layout.addRow("Aufnahmezeit (Sekunden):", self.capture_time_spin)
        
        self.blow_off_time_spin = QDoubleSpinBox()
        self.blow_off_time_spin.setRange(1.0, 30.0)
        self.blow_off_time_spin.setSingleStep(0.5)
        layout.addRow("Abblas-Wartezeit (Sekunden):", self.blow_off_time_spin)
        
        self.tab_widget.addTab(scroll, "🤖 KI & Workflow")
    
    def _create_parts_config_tab(self):
        """Tab 2: 🔍 Teile-Konfiguration"""
        tab = QWidget()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(tab)
        
        layout = QVBoxLayout(tab)
        layout.setSpacing(20)
        
        # Schlecht-Teil Konfiguration
        bad_parts_group = QFrame()
        bad_parts_group.setStyleSheet("QFrame { border: 1px solid #ccc; border-radius: 5px; padding: 10px; }")
        bad_parts_layout = QVBoxLayout(bad_parts_group)
        
        bad_parts_title = QLabel("❌ Schlecht-Teil Konfiguration")
        bad_parts_title.setFont(QFont("", 14, QFont.Weight.Bold))
        bad_parts_layout.addWidget(bad_parts_title)
        
        # Klassenliste für schlechte Teile
        self.bad_part_classes_list = QListWidget()
        self.bad_part_classes_list.setMaximumHeight(120)
        bad_parts_layout.addWidget(QLabel("Schlecht-Teil Klassen:"))
        bad_parts_layout.addWidget(self.bad_part_classes_list)
        
        # Buttons für schlechte Teile
        bad_buttons_layout = QHBoxLayout()
        self.bad_class_combo = self._create_class_combo()
        bad_buttons_layout.addWidget(self.bad_class_combo)
        
        add_bad_btn = QPushButton("Hinzufügen")
        add_bad_btn.clicked.connect(self.add_bad_class)
        bad_buttons_layout.addWidget(add_bad_btn)
        
        remove_bad_btn = QPushButton("Entfernen")
        remove_bad_btn.clicked.connect(self.remove_bad_class)
        bad_buttons_layout.addWidget(remove_bad_btn)
        
        bad_parts_layout.addLayout(bad_buttons_layout)
        
        # Mindest-Konfidenz
        conf_layout = QHBoxLayout()
        conf_layout.addWidget(QLabel("Mindest-Konfidenz:"))
        self.bad_part_confidence_spin = QDoubleSpinBox()
        self.bad_part_confidence_spin.setRange(0.1, 1.0)
        self.bad_part_confidence_spin.setSingleStep(0.1)
        self.bad_part_confidence_spin.setDecimals(2)
        conf_layout.addWidget(self.bad_part_confidence_spin)
        bad_parts_layout.addLayout(conf_layout)
        
        layout.addWidget(bad_parts_group)
        
        # Gut-Teil Konfiguration
        good_parts_group = QFrame()
        good_parts_group.setStyleSheet("QFrame { border: 1px solid #ccc; border-radius: 5px; padding: 10px; }")
        good_parts_layout = QVBoxLayout(good_parts_group)
        
        good_parts_title = QLabel("✅ Gut-Teil Konfiguration")
        good_parts_title.setFont(QFont("", 14, QFont.Weight.Bold))
        good_parts_layout.addWidget(good_parts_title)
        
        # Klassenliste für gute Teile
        self.good_part_classes_list = QListWidget()
        self.good_part_classes_list.setMaximumHeight(120)
        good_parts_layout.addWidget(QLabel("Gut-Teil Klassen:"))
        good_parts_layout.addWidget(self.good_part_classes_list)
        
        # Buttons für gute Teile
        good_buttons_layout = QHBoxLayout()
        self.good_class_combo = self._create_class_combo()
        good_buttons_layout.addWidget(self.good_class_combo)
        
        add_good_btn = QPushButton("Hinzufügen")
        add_good_btn.clicked.connect(self.add_good_class)
        good_buttons_layout.addWidget(add_good_btn)
        
        remove_good_btn = QPushButton("Entfernen")
        remove_good_btn.clicked.connect(self.remove_good_class)
        good_buttons_layout.addWidget(remove_good_btn)
        
        good_parts_layout.addLayout(good_buttons_layout)
        
        layout.addWidget(good_parts_group)
        layout.addStretch()
        
        self.tab_widget.addTab(scroll, "🔍 Teile-Konfiguration")
    
    def _create_hardware_tab(self):
        """Tab 3: 🔌 Hardware"""
        tab = QWidget()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(tab)
        
        layout = QFormLayout(tab)
        layout.setSpacing(15)
        
        # Kamera-Konfiguration
        self._add_section_header(layout, "📷 IDS Peak Kamera-Konfiguration")
        
        # Info-Text
        info_label = QLabel(
            "Wählen Sie eine IDS Peak Kamera-Konfigurationsdatei (.toml), um erweiterte "
            "Kameraeinstellungen wie Belichtung, Gamma und Weißabgleich zu verwenden."
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: #7f8c8d; font-style: italic; margin-bottom: 10px;")
        layout.addRow(info_label)
        
        # Konfigurationspfad
        config_path_layout = QHBoxLayout()
        self.camera_config_path_label = QLabel("Keine Konfiguration ausgewählt")
        self.camera_config_path_label.setStyleSheet("background-color: #f0f0f0; padding: 5px; border-radius: 3px;")
        self.camera_config_path_label.setWordWrap(True)
        config_path_layout.addWidget(self.camera_config_path_label, 1)
        
        camera_config_browse_btn = QPushButton("📁")
        camera_config_browse_btn.clicked.connect(self.browse_camera_config_file)
        config_path_layout.addWidget(camera_config_browse_btn)
        
        clear_config_btn = QPushButton("❌")
        clear_config_btn.clicked.connect(self.clear_camera_config)
        config_path_layout.addWidget(clear_config_btn)
        
        layout.addRow("Konfigurationsdatei:", config_path_layout)
        
        self._add_spacer(layout)
        
        # MODBUS-Einstellungen
        self._add_section_header(layout, "🔌 WAGO Modbus")
        
        self.modbus_enabled_check = QCheckBox()
        layout.addRow("Modbus aktiviert:", self.modbus_enabled_check)
        
        self.modbus_ip_input = QLabel("192.168.1.100")
        self.modbus_ip_input.setStyleSheet("background-color: #f0f0f0; padding: 5px; border-radius: 3px;")
        layout.addRow("WAGO IP-Adresse:", self.modbus_ip_input)
        
        self.reject_coil_duration_spin = QDoubleSpinBox()
        self.reject_coil_duration_spin.setRange(0.1, 10.0)
        self.reject_coil_duration_spin.setSingleStep(0.1)
        self.reject_coil_duration_spin.setDecimals(1)
        layout.addRow("Ausschuss-Signal Dauer (Sekunden):", self.reject_coil_duration_spin)
        
        self.tab_widget.addTab(scroll, "🔌 Hardware")
    
    def _create_storage_monitoring_tab(self):
        """Tab 4: 💾 Speicherung & Überwachung"""
        tab = QWidget()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(tab)
        
        layout = QFormLayout(tab)
        layout.setSpacing(15)
        
        # Bilderspeicherung
        self._add_section_header(layout, "📸 Bilderspeicherung")
        
        self.save_bad_images_check = QCheckBox()
        layout.addRow("Schlechtbilder speichern:", self.save_bad_images_check)
        
        # Schlechtbilder-Verzeichnis
        bad_dir_layout = QHBoxLayout()
        self.bad_images_dir_input = QLabel("bad_images")
        self.bad_images_dir_input.setStyleSheet("background-color: #f0f0f0; padding: 5px; border-radius: 3px;")
        bad_dir_layout.addWidget(self.bad_images_dir_input, 1)
        
        bad_dir_browse_btn = QPushButton("📁")
        bad_dir_browse_btn.clicked.connect(self.browse_bad_images_directory)
        bad_dir_layout.addWidget(bad_dir_browse_btn)
        
        layout.addRow("Schlechtbilder-Verzeichnis:", bad_dir_layout)
        
        self.save_good_images_check = QCheckBox()
        layout.addRow("Gutbilder speichern:", self.save_good_images_check)
        
        # Gutbilder-Verzeichnis
        good_dir_layout = QHBoxLayout()
        self.good_images_dir_input = QLabel("good_images")
        self.good_images_dir_input.setStyleSheet("background-color: #f0f0f0; padding: 5px; border-radius: 3px;")
        good_dir_layout.addWidget(self.good_images_dir_input, 1)
        
        good_dir_browse_btn = QPushButton("📁")
        good_dir_browse_btn.clicked.connect(self.browse_good_images_directory)
        good_dir_layout.addWidget(good_dir_browse_btn)
        
        layout.addRow("Gutbilder-Verzeichnis:", good_dir_layout)
        
        # Maximale Dateien
        self.max_images_spin = QSpinBox()
        self.max_images_spin.setRange(1000, 500000)
        self.max_images_spin.setSingleStep(1000)
        self.max_images_spin.setValue(100000)
        layout.addRow("Max. Dateien pro Verzeichnis:", self.max_images_spin)
        
        self._add_spacer(layout)
        
        # Helligkeitsüberwachung
        self._add_section_header(layout, "💡 Helligkeitsüberwachung")
        
        self.brightness_low_spin = QSpinBox()
        self.brightness_low_spin.setRange(0, 254)
        self.brightness_low_spin.valueChanged.connect(self.validate_brightness_ranges)
        layout.addRow("Untere Schwelle (Auto-Stopp):", self.brightness_low_spin)
        
        self.brightness_high_spin = QSpinBox()
        self.brightness_high_spin.setRange(1, 255)
        self.brightness_high_spin.valueChanged.connect(self.validate_brightness_ranges)
        layout.addRow("Obere Schwelle (Auto-Stopp):", self.brightness_high_spin)
        
        self.brightness_duration_spin = QDoubleSpinBox()
        self.brightness_duration_spin.setRange(1.0, 30.0)
        self.brightness_duration_spin.setSingleStep(0.5)
        layout.addRow("Dauer bis Auto-Stopp (Sekunden):", self.brightness_duration_spin)
        
        self.tab_widget.addTab(scroll, "💾 Speicherung & Überwachung")
    
    def _create_class_combo(self):
        """ComboBox mit verfügbaren Klassen erstellen."""
        combo = QComboBox()
        combo.addItem("Klasse auswählen...", -1)
        
        for class_id, class_name in self.class_names.items():
            combo.addItem(f"{class_name} (ID: {class_id})", class_id)
        
        return combo
    
    def _add_section_header(self, layout, title):
        """Sektion-Header hinzufügen."""
        header = QLabel(title)
        header.setFont(QFont("", 12, QFont.Weight.Bold))
        header.setStyleSheet("color: #2c3e50; margin: 10px 0 5px 0;")
        layout.addRow(header)
    
    def _add_spacer(self, layout):
        """Trennlinie hinzufügen."""
        spacer = QFrame()
        spacer.setFrameShape(QFrame.Shape.HLine)
        spacer.setFrameShadow(QFrame.Shadow.Sunken)
        spacer.setStyleSheet("color: #bdc3c7; margin: 10px 0;")
        layout.addRow(spacer)
    
    def _create_button_section(self, layout):
        """Button-Sektion erstellen."""
        button_layout = QHBoxLayout()
        
        save_btn = QPushButton("💾 Speichern")
        save_btn.setMinimumHeight(40)
        save_btn.clicked.connect(self.save_settings)
        button_layout.addWidget(save_btn)
        
        cancel_btn = QPushButton("❌ Abbrechen")
        cancel_btn.setMinimumHeight(40)
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        reset_btn = QPushButton("🔄 Zurücksetzen")
        reset_btn.setMinimumHeight(40)
        reset_btn.clicked.connect(self.reset_settings)
        button_layout.addWidget(reset_btn)
        
        layout.addLayout(button_layout)
    
    # Event Handler-Methoden
    def browse_camera_config_file(self):
        """IDS Peak Kamera-Konfigurationsdatei auswählen."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "IDS Peak Kamera-Konfigurationsdatei auswählen",
            "",
            "TOML-Dateien (*.toml);;Alle Dateien (*)"
        )
        
        if file_path:
            try:
                if file_path.lower().endswith('.toml'):
                    self.camera_config_path_label.setText(file_path)
                    QMessageBox.information(
                        self,
                        "Konfiguration ausgewählt",
                        f"IDS Peak Konfigurationsdatei ausgewählt:\n{os.path.basename(file_path)}\n\n"
                        "Die Konfiguration wird beim nächsten Kamera-Start angewendet."
                    )
                else:
                    QMessageBox.warning(
                        self,
                        "Ungültige Datei",
                        "Bitte wählen Sie eine .toml Datei aus."
                    )
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Fehler",
                    f"Fehler beim Laden der Konfigurationsdatei:\n{str(e)}"
                )
    
    def clear_camera_config(self):
        """Kamera-Konfiguration löschen."""
        self.camera_config_path_label.setText("Keine Konfiguration ausgewählt")
        QMessageBox.information(
            self,
            "Konfiguration gelöscht",
            "Die Kamera-Konfiguration wurde entfernt.\nStandard-Kameraeinstellungen werden verwendet."
        )
    
    def browse_bad_images_directory(self):
        """Verzeichnis für Schlechtbilder auswählen."""
        directory = QFileDialog.getExistingDirectory(
            self,
            "Verzeichnis für Schlechtbilder auswählen",
            self.bad_images_dir_input.text()
        )
        if directory:
            self.bad_images_dir_input.setText(directory)
    
    def browse_good_images_directory(self):
        """Verzeichnis für Gutbilder auswählen."""
        directory = QFileDialog.getExistingDirectory(
            self,
            "Verzeichnis für Gutbilder auswählen",
            self.good_images_dir_input.text()
        )
        if directory:
            self.good_images_dir_input.setText(directory)
    
    def validate_brightness_ranges(self):
        """Stelle sicher, dass Low < High bei Helligkeitseinstellungen."""
        low_value = self.brightness_low_spin.value()
        high_value = self.brightness_high_spin.value()
        
        if low_value >= high_value:
            if self.sender() == self.brightness_low_spin:
                self.brightness_high_spin.setValue(low_value + 1)
            else:
                self.brightness_low_spin.setValue(high_value - 1)
    
    def add_bad_class(self):
        """Schlecht-Teil Klasse hinzufügen."""
        selected_id = self.bad_class_combo.currentData()
        if selected_id == -1:  # "Klasse auswählen..." gewählt
            return
        
        class_name = self.class_names.get(selected_id, f"Class {selected_id}")
        display_text = f"{class_name} (ID: {selected_id})"
        
        # Prüfe ob bereits vorhanden
        for i in range(self.bad_part_classes_list.count()):
            if self.bad_part_classes_list.item(i).data(Qt.ItemDataRole.UserRole) == selected_id:
                return  # Bereits vorhanden
        
        from PyQt6.QtWidgets import QListWidgetItem
        item = QListWidgetItem(display_text)
        item.setData(Qt.ItemDataRole.UserRole, selected_id)  # Speichere ID
        self.bad_part_classes_list.addItem(item)
    
    def remove_bad_class(self):
        """Ausgewählte Schlecht-Teil Klasse entfernen."""
        current_row = self.bad_part_classes_list.currentRow()
        if current_row >= 0:
            self.bad_part_classes_list.takeItem(current_row)
    
    def add_good_class(self):
        """Gut-Teil Klasse hinzufügen."""
        selected_id = self.good_class_combo.currentData()
        if selected_id == -1:  # "Klasse auswählen..." gewählt
            return
        
        class_name = self.class_names.get(selected_id, f"Class {selected_id}")
        display_text = f"{class_name} (ID: {selected_id})"
        
        # Prüfe ob bereits vorhanden
        for i in range(self.good_part_classes_list.count()):
            if self.good_part_classes_list.item(i).data(Qt.ItemDataRole.UserRole) == selected_id:
                return  # Bereits vorhanden
        
        from PyQt6.QtWidgets import QListWidgetItem
        item = QListWidgetItem(display_text)
        item.setData(Qt.ItemDataRole.UserRole, selected_id)  # Speichere ID
        self.good_part_classes_list.addItem(item)
    
    def remove_good_class(self):
        """Ausgewählte Gut-Teil Klasse entfernen."""
        current_row = self.good_part_classes_list.currentRow()
        if current_row >= 0:
            self.good_part_classes_list.takeItem(current_row)
    
    def load_settings(self):
        """Aktuelle Einstellungen laden."""
        # KI & Workflow
        self.confidence_spin.setValue(self.settings.get('confidence_threshold', 0.5))
        self.motion_threshold_spin.setValue(self.settings.get('motion_threshold', 110))
        self.red_threshold_spin.setValue(self.settings.get('red_threshold', 1))
        self.green_threshold_spin.setValue(self.settings.get('green_threshold', 4))
        self.settling_time_spin.setValue(self.settings.get('settling_time', 1.0))
        self.capture_time_spin.setValue(self.settings.get('capture_time', 3.0))
        self.blow_off_time_spin.setValue(self.settings.get('blow_off_time', 5.0))
        
        # Schlecht-Teil Klassen laden (mit Namen)
        bad_classes = self.settings.get('bad_part_classes', [1])
        self.bad_part_classes_list.clear()
        for class_id in bad_classes:
            class_name = self.class_names.get(class_id, f"Class {class_id}")
            display_text = f"{class_name} (ID: {class_id})"
            
            from PyQt6.QtWidgets import QListWidgetItem
            item = QListWidgetItem(display_text)
            item.setData(Qt.ItemDataRole.UserRole, class_id)
            self.bad_part_classes_list.addItem(item)
        
        # Gut-Teil Klassen laden (mit Namen)
        good_classes = self.settings.get('good_part_classes', [0])
        self.good_part_classes_list.clear()
        for class_id in good_classes:
            class_name = self.class_names.get(class_id, f"Class {class_id}")
            display_text = f"{class_name} (ID: {class_id})"
            
            from PyQt6.QtWidgets import QListWidgetItem
            item = QListWidgetItem(display_text)
            item.setData(Qt.ItemDataRole.UserRole, class_id)
            self.good_part_classes_list.addItem(item)
        
        self.bad_part_confidence_spin.setValue(self.settings.get('bad_part_min_confidence', 0.5))
        
        # Hardware
        camera_config_path = self.settings.get('camera_config_path', '')
        if camera_config_path:
            self.camera_config_path_label.setText(camera_config_path)
        else:
            self.camera_config_path_label.setText("Keine Konfiguration ausgewählt")
        
        self.modbus_enabled_check.setChecked(self.settings.get('modbus_enabled', True))
        self.modbus_ip_input.setText(self.settings.get('modbus_ip', '192.168.1.100'))
        self.reject_coil_duration_spin.setValue(self.settings.get('reject_coil_duration_seconds', 1.0))
        
        # Speicherung & Überwachung
        self.save_bad_images_check.setChecked(self.settings.get('save_bad_images', False))
        self.save_good_images_check.setChecked(self.settings.get('save_good_images', False))
        self.bad_images_dir_input.setText(self.settings.get('bad_images_directory', 'bad_images'))
        self.good_images_dir_input.setText(self.settings.get('good_images_directory', 'good_images'))
        self.max_images_spin.setValue(self.settings.get('max_image_files', 100000))
        
        self.brightness_low_spin.setValue(self.settings.get('brightness_low_threshold', 30))
        self.brightness_high_spin.setValue(self.settings.get('brightness_high_threshold', 220))
        self.brightness_duration_spin.setValue(self.settings.get('brightness_duration_threshold', 3.0))
    
    def save_settings(self):
        """Einstellungen speichern."""
        # KI & Workflow
        self.settings.set('confidence_threshold', self.confidence_spin.value())
        self.settings.set('motion_threshold', self.motion_threshold_spin.value())
        self.settings.set('red_threshold', self.red_threshold_spin.value())
        self.settings.set('green_threshold', self.green_threshold_spin.value())
        self.settings.set('settling_time', self.settling_time_spin.value())
        self.settings.set('capture_time', self.capture_time_spin.value())
        self.settings.set('blow_off_time', self.blow_off_time_spin.value())
        
        # Schlecht-Teil Klassen sammeln (IDs extrahieren)
        bad_classes = []
        for i in range(self.bad_part_classes_list.count()):
            item = self.bad_part_classes_list.item(i)
            class_id = item.data(Qt.ItemDataRole.UserRole)
            bad_classes.append(class_id)
        self.settings.set('bad_part_classes', bad_classes)
        
        # Gut-Teil Klassen sammeln (IDs extrahieren)
        good_classes = []
        for i in range(self.good_part_classes_list.count()):
            item = self.good_part_classes_list.item(i)
            class_id = item.data(Qt.ItemDataRole.UserRole)
            good_classes.append(class_id)
        self.settings.set('good_part_classes', good_classes)
        
        self.settings.set('bad_part_min_confidence', self.bad_part_confidence_spin.value())
        
        # Hardware
        camera_config_text = self.camera_config_path_label.text()
        if camera_config_text == "Keine Konfiguration ausgewählt":
            self.settings.set('camera_config_path', '')
        else:
            self.settings.set('camera_config_path', camera_config_text)
        
        self.settings.set('modbus_enabled', self.modbus_enabled_check.isChecked())
        self.settings.set('modbus_ip', self.modbus_ip_input.text())
        self.settings.set('reject_coil_duration_seconds', self.reject_coil_duration_spin.value())
        
        # Speicherung & Überwachung
        self.settings.set('save_bad_images', self.save_bad_images_check.isChecked())
        self.settings.set('save_good_images', self.save_good_images_check.isChecked())
        self.settings.set('bad_images_directory', self.bad_images_dir_input.text())
        self.settings.set('good_images_directory', self.good_images_dir_input.text())
        self.settings.set('max_image_files', self.max_images_spin.value())
        
        self.settings.set('brightness_low_threshold', self.brightness_low_spin.value())
        self.settings.set('brightness_high_threshold', self.brightness_high_spin.value())
        self.settings.set('brightness_duration_threshold', self.brightness_duration_spin.value())
        
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