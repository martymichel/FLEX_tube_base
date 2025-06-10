"""
Dialog-Komponenten fuer Kamera-Auswahl und Einstellungen
Alle Dialog-Fenster der Anwendung mit Tab-basiertem Layout, Klassennamen-Support und Farbauswahl
ERWEITERT: Editierbare Modbus IP/Port Einstellungen (nur wenn getrennt)
"""

import os
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
    QFrame, QFileDialog, QSpinBox, QDoubleSpinBox, QCheckBox, 
    QFormLayout, QMessageBox, QListWidget, QTabWidget, QWidget,
    QScrollArea, QSizePolicy, QComboBox, QApplication, QColorDialog,
    QGridLayout, QLineEdit
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor

class CameraSelectionDialog(QDialog):
    """Dialog zur Kamera/Video-Auswahl."""
    
    def __init__(self, camera_manager, parent=None):
        super().__init__(parent)
        self.camera_manager = camera_manager
        self.setWindowTitle("📹 Kamera/Video auswaehlen")
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
        
        # Verfuegbare Kameras anzeigen
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
        
        video_btn = QPushButton("Video-Datei auswaehlen...")
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
        """Webcam auswaehlen."""
        self.selected_source = index
        self.accept()
    
    def select_ids_camera(self, index):
        """IDS Kamera auswaehlen."""
        self.selected_source = ('ids', index)
        self.accept()
    
    def select_video(self):
        """Video-Datei auswaehlen."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Video-Datei auswaehlen",
            "",
            "Video-Dateien (*.mp4 *.avi *.mkv *.mov);;Alle Dateien (*)"
        )
        
        if file_path:
            self.selected_source = file_path
            self.accept()
    
    def get_selected_source(self):
        """Ausgewaehlte Quelle zurueckgeben."""
        return self.selected_source

class SettingsDialog(QDialog):
    """Tab-basierter Einstellungen-Dialog mit Farbauswahl fuer Klassen und editierbaren Modbus-Einstellungen."""
    
    def __init__(self, settings, class_names=None, parent=None):
        super().__init__(parent)
        self.settings = settings
        self.class_names = class_names or {}  # Dictionary {id: name}
        self.parent_app = parent  # Referenz zur Hauptanwendung fuer Modbus-Funktionen
        self.setWindowTitle("⚙️ Einstellungen")
        self.setModal(True)
        
        # Bildschirmgröße abfragen und vermeiden, dass der Dialog zu groß wird
        screen = QApplication.primaryScreen()
        screen_geometry = screen.availableGeometry()
        max_width = int(screen_geometry.width() * 0.4)
        max_height = int(screen_geometry.height() * 0.5)
        self.setFixedSize(max_width, max_height)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMinimumSize(600, 400)  # Mindestgröße für bessere Lesbarkeit

        # 20 vordefinierte Farben fuer Klassen
        self.predefined_colors = [
            "#FF0000",  # Rot
            "#00FF00",  # Gruen
            "#0000FF",  # Blau
            "#FFFF00",  # Gelb
            "#FF00FF",  # Magenta
            "#00FFFF",  # Cyan
            "#FFA500",  # Orange
            "#800080",  # Lila
            "#FFC0CB",  # Pink
            "#A52A2A",  # Braun
            "#808080",  # Grau
            "#000000",  # Schwarz
            "#FFFFFF",  # Weiss
            "#008000",  # Dunkelgruen
            "#000080",  # Dunkelblau
            "#800000",  # Bordeaux
            "#808000",  # Olive
            "#008080",  # Tuerkis
            "#C0C0C0",  # Silber
            "#FFD700"   # Gold
        ]
        
        # Speichere ausgewaehlte Farben fuer jede Klasse
        self.class_colors = {}
        
        self.setup_ui()
        self.load_settings()
    
    def setup_ui(self):
        """UI mit Tab-Layout aufbauen."""
        layout = QVBoxLayout(self)
        
        # Tab-Widget erstellen
        self.tab_widget = QTabWidget()
        # — doppelte Tabhoehe —
        tabbar = self.tab_widget.tabBar()
        tabbar.setStyleSheet("QTabBar::tab { min-height: 44px; }")

        layout.addWidget(self.tab_widget)
        
        # Tabs erstellen
        self._create_general_tab()
        self._create_classes_assignment_tab()
        self._create_color_assignment_tab()
        self._create_interfaces_tab()  # ERWEITERT: Mit editierbaren Modbus-Einstellungen
        self._create_storage_monitoring_tab()
        
        # Button-Sektion
        self._create_button_section(layout)
    
    def _create_general_tab(self):
        """Tab 1: ⚙️ Allgemein - MIT INFO-TEXTEN"""
        tab = QWidget()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(tab)
        
        layout = QFormLayout(tab)
        layout.setSpacing(15)
        
        # Workflow
        self._add_section_header(layout, "🏭 Workflow")
        
        # Motion Threshold - MIT INFO
        motion_info = self._create_info_label(
            "Schwellwert fuer Erkennung des Foerderband-Takts. Niedrigere Werte = empfindlicher fuer Bewegung. "
            "Bestimmt, wann das Foerderband als 'in Bewegung' erkannt wird."
        )
        layout.addRow(motion_info)
        
        self.motion_threshold_spin = QSpinBox()
        self.motion_threshold_spin.setRange(1, 255)
        layout.addRow("Bandtakt Grenzwert (1-255):", self.motion_threshold_spin)
        self._add_spacer(layout)

        # Motion Decay - MIT INFO
        motion_decay_info = self._create_info_label(
            "Abklingfaktor fuer die Motion-Anzeige. Bestimmt, wie schnell der angezeigte Motion-Wert "
            "nach dem Ende einer Bewegung abfaellt. Hoehere Werte = langsameres Abklingen (traeger), "
            "niedrigere Werte = schnelleres Abklingen (reaktiver)."
        )
        layout.addRow(motion_decay_info)
        
        self.motion_decay_spin = QDoubleSpinBox()
        self.motion_decay_spin.setRange(0.001, 0.999)
        self.motion_decay_spin.setSingleStep(0.001)
        self.motion_decay_spin.setDecimals(3)
        layout.addRow("Motion Abklingfaktor (0.001-0.999):", self.motion_decay_spin)
        self._add_spacer(layout)

        # Roter Rahmen Schwellwert - MIT INFO
        red_info = self._create_info_label(
            "Mindestanzahl von schlechten Teilen, ab der der rote Rahmen angezeigt wird. "
            "Bestimmt, wann ein Ausschuss-Signal ausgeloest wird."
        )
        layout.addRow(red_info)
        
        self.red_threshold_spin = QSpinBox()
        self.red_threshold_spin.setRange(1, 20)
        layout.addRow("Roter Rahmen Schwellwert:", self.red_threshold_spin)
        self._add_spacer(layout)
        
        # Gruener Rahmen Schwellwert - MIT INFO
        green_info = self._create_info_label(
            "Mindestanzahl von guten Teilen, ab der der gruene Rahmen angezeigt wird. "
            "Bestaetigt, dass ausreichend gute Teile erkannt wurden."
        )
        layout.addRow(green_info)
        
        self.green_threshold_spin = QSpinBox()
        self.green_threshold_spin.setRange(1, 20)
        layout.addRow("Gruener Rahmen Schwellwert:", self.green_threshold_spin)
        self._add_spacer(layout)
        
        # Ausschwingzeit - MIT INFO
        settling_info = self._create_info_label(
            "Wartezeit nach Stillstand des Foerderbands, bevor die KI-Erkennung startet. "
            "Verhindert Erkennungen waehrend des Ausschwingvorgangs."
        )
        layout.addRow(settling_info)
        
        self.settling_time_spin = QDoubleSpinBox()
        self.settling_time_spin.setRange(0.1, 10.0)
        self.settling_time_spin.setSingleStep(0.1)
        layout.addRow("Ausschwingzeit (Sekunden):", self.settling_time_spin)
        self._add_spacer(layout)

        # Aufnahmezeit - MIT INFO
        capture_info = self._create_info_label(
            "Dauer der KI-Erkennung pro Zyklus. Laengere Zeit = mehr Bilder analysiert, "
            "aber langsamerer Durchsatz."
        )
        layout.addRow(capture_info)
        
        self.capture_time_spin = QDoubleSpinBox()
        self.capture_time_spin.setRange(0.5, 10.0)
        self.capture_time_spin.setSingleStep(0.1)
        layout.addRow("Aufnahmezeit (Sekunden):", self.capture_time_spin)
        self._add_spacer(layout)
        
        # Abblas-Wartezeit - MIT INFO
        blow_off_info = self._create_info_label(
            "Wartezeit nach Ausschuss-Signal, bevor der naechste Zyklus beginnt. "
            "Muss lang genug sein, damit das Abblasen vollstaendig beendet ist. "
        )
        layout.addRow(blow_off_info)
        
        self.blow_off_time_spin = QDoubleSpinBox()
        self.blow_off_time_spin.setRange(1.0, 30.0)
        self.blow_off_time_spin.setSingleStep(0.5)
        layout.addRow("Abblas-Wartezeit (Sekunden):", self.blow_off_time_spin)
        self._add_spacer(layout)
        
        self.tab_widget.addTab(scroll, "⚙️ Allgemein")
    
    def _create_classes_assignment_tab(self):
        """Tab 2: 🔍 Klassen-Zuteilung - MIT BEIDEN KONFIDENZ-EINSTELLUNGEN"""
        tab = QWidget()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(tab)
        
        layout = QVBoxLayout(tab)
        layout.setSpacing(20)
        
        # NEUE Konfidenz-Einstellungen Sektion (beide hier)
        confidence_group = QFrame()
        confidence_group.setStyleSheet("QFrame { border: 1px solid #ccc; border-radius: 5px; padding: 10px; }")
        confidence_layout = QVBoxLayout(confidence_group)
        
        confidence_title = QLabel("🎯 Konfidenz-Einstellungen")
        confidence_title.setFont(QFont("", 14, QFont.Weight.Bold))
        confidence_layout.addWidget(confidence_title)
        
        # Allgemeine Konfidenz
        general_conf_info = self._create_info_label(
            "Grundschwellwert fuer alle KI-Erkennungen. Nur Erkennungen ueber diesem Wert werden beruecksichtigt. "
            "Hoehere Werte = weniger falsche Erkennungen, aber eventuell werden echte Objekte uebersehen."
        )
        confidence_layout.addWidget(general_conf_info)
        
        general_conf_layout = QHBoxLayout()
        general_conf_layout.addWidget(QLabel("Allgemeine Konfidenz-Schwelle:"))
        self.confidence_spin = QDoubleSpinBox()
        self.confidence_spin.setRange(0.1, 1.0)
        self.confidence_spin.setSingleStep(0.1)
        self.confidence_spin.setDecimals(2)
        general_conf_layout.addWidget(self.confidence_spin)
        confidence_layout.addLayout(general_conf_layout)
        
        # Schlecht-Teil spezifische Konfidenz
        bad_conf_info = self._create_info_label(
            "Zusaetzliche Mindest-Konfidenz fuer Schlecht-Teile. Verhindert faelschliche Ausschuss-Signale "
            "durch unsichere Erkennungen. Sollte hoeher als die allgemeine Konfidenz sein."
        )
        confidence_layout.addWidget(bad_conf_info)
        
        bad_conf_layout = QHBoxLayout()
        bad_conf_layout.addWidget(QLabel("Schlecht-Teil Mindest-Konfidenz:"))
        self.bad_part_confidence_spin = QDoubleSpinBox()
        self.bad_part_confidence_spin.setRange(0.1, 1.0)
        self.bad_part_confidence_spin.setSingleStep(0.1)
        self.bad_part_confidence_spin.setDecimals(2)
        bad_conf_layout.addWidget(self.bad_part_confidence_spin)
        confidence_layout.addLayout(bad_conf_layout)
        
        layout.addWidget(confidence_group)
        
        # Schlecht-Teil Konfiguration
        bad_parts_group = QFrame()
        bad_parts_group.setStyleSheet("QFrame { border: 1px solid #ccc; border-radius: 5px; padding: 10px; }")
        bad_parts_layout = QVBoxLayout(bad_parts_group)
        
        bad_parts_title = QLabel("❌ Schlecht-Teil Klassenzuteilung")
        bad_parts_title.setFont(QFont("", 14, QFont.Weight.Bold))
        bad_parts_layout.addWidget(bad_parts_title)
        
        # Info-Text
        bad_info = self._create_info_label(
            "Waehlen Sie die Klassen aus, die als fehlerhafte/schlechte Teile behandelt werden sollen. "
            "Bei Erkennung dieser Klassen wird ein Ausschuss-Signal ausgeloest."
        )
        bad_parts_layout.addWidget(bad_info)
        
        # Klassenliste fuer schlechte Teile
        self.bad_part_classes_list = QListWidget()
        self.bad_part_classes_list.setMaximumHeight(120)
        bad_parts_layout.addWidget(QLabel("Zugeteilte Schlecht-Teil Klassen:"))
        bad_parts_layout.addWidget(self.bad_part_classes_list)
        
        # Buttons fuer schlechte Teile
        bad_buttons_layout = QHBoxLayout()
        self.bad_class_combo = self._create_class_combo()
        bad_buttons_layout.addWidget(self.bad_class_combo)
        
        add_bad_btn = QPushButton("Hinzufuegen")
        add_bad_btn.clicked.connect(self.add_bad_class)
        bad_buttons_layout.addWidget(add_bad_btn)
        
        remove_bad_btn = QPushButton("Entfernen")
        remove_bad_btn.clicked.connect(self.remove_bad_class)
        bad_buttons_layout.addWidget(remove_bad_btn)
        
        bad_parts_layout.addLayout(bad_buttons_layout)
        
        layout.addWidget(bad_parts_group)
        
        # Gut-Teil Konfiguration
        good_parts_group = QFrame()
        good_parts_group.setStyleSheet("QFrame { border: 1px solid #ccc; border-radius: 5px; padding: 10px; }")
        good_parts_layout = QVBoxLayout(good_parts_group)
        
        good_parts_title = QLabel("✅ Gut-Teil Klassenzuteilung")
        good_parts_title.setFont(QFont("", 14, QFont.Weight.Bold))
        good_parts_layout.addWidget(good_parts_title)
        
        # Info-Text
        good_info = self._create_info_label(
            "Waehlen Sie die Klassen aus, die als fehlerfreie/gute Teile behandelt werden sollen. "
            "Bei ausreichender Erkennung dieser Klassen wird ein Gut-Signal generiert."
        )
        good_parts_layout.addWidget(good_info)
        
        # Klassenliste fuer gute Teile
        self.good_part_classes_list = QListWidget()
        self.good_part_classes_list.setMaximumHeight(120)
        good_parts_layout.addWidget(QLabel("Zugeteilte Gut-Teil Klassen:"))
        good_parts_layout.addWidget(self.good_part_classes_list)
        
        # Buttons fuer gute Teile
        good_buttons_layout = QHBoxLayout()
        self.good_class_combo = self._create_class_combo()
        good_buttons_layout.addWidget(self.good_class_combo)
        
        add_good_btn = QPushButton("Hinzufuegen")
        add_good_btn.clicked.connect(self.add_good_class)
        good_buttons_layout.addWidget(add_good_btn)
        
        remove_good_btn = QPushButton("Entfernen")
        remove_good_btn.clicked.connect(self.remove_good_class)
        good_buttons_layout.addWidget(remove_good_btn)
        
        good_parts_layout.addLayout(good_buttons_layout)
        
        layout.addWidget(good_parts_group)
        layout.addStretch()
        
        self.tab_widget.addTab(scroll, "🔍 Klassen-Zuteilung")
    
    def _create_color_assignment_tab(self):
        """Tab 3: 🎨 Farbzuteilung - NUR vordefinierte Farbauswahl"""
        tab = QWidget()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(tab)
        
        layout = QVBoxLayout(tab)
        layout.setSpacing(20)
        
        # Farbzuteilung-Gruppe
        color_group = QFrame()
        color_group.setStyleSheet("QFrame { border: 1px solid #ccc; border-radius: 5px; padding: 10px; }")
        color_layout = QVBoxLayout(color_group)
        
        color_title = QLabel("🎨 Bounding Box Farben")
        color_title.setFont(QFont("", 14, QFont.Weight.Bold))
        color_layout.addWidget(color_title)
        
        # Info-Text
        color_info = self._create_info_label(
            "Waehlen Sie fuer jede Klasse eine Farbe aus der vordefinierten Auswahl. "
            "Die Farben werden in der Erkennung zur besseren Unterscheidung der Klassen verwendet."
        )
        color_layout.addWidget(color_info)
        
        # Farbraster fuer jede Klasse - NUR mit Dropdown
        if self.class_names:
            # Grid fuer Klassenfarben
            grid_widget = QWidget()
            grid_layout = QGridLayout(grid_widget)
            grid_layout.setSpacing(15)
            
            row = 0
            col = 0
            
            for class_id, class_name in self.class_names.items():
                # Klassen-Label
                class_label = QLabel(f"{class_name} (ID: {class_id})")
                class_label.setMinimumWidth(180)
                class_label.setFont(QFont("", 11, QFont.Weight.Bold))
                grid_layout.addWidget(class_label, row, col * 2)
                
                # Vordefinierte Farben-Dropdown - EINZIGE Farbauswahl
                color_preset_combo = QComboBox()
                color_preset_combo.setMinimumWidth(120)
                
                # Standard-Farbe basierend auf class_id
                default_color = self.predefined_colors[class_id % len(self.predefined_colors)]
                self.class_colors[class_id] = QColor(default_color)
                
                # Dropdown mit Farben fuellen
                for i, preset_color in enumerate(self.predefined_colors):
                    color_preset_combo.addItem(f"Farbe {i+1}", preset_color)
                    # Setze Farbe als Hintergrund fuer das Item
                    color_preset_combo.setItemData(i, QColor(preset_color), Qt.ItemDataRole.BackgroundRole)
                    color_preset_combo.setItemData(i, QColor("white"), Qt.ItemDataRole.ForegroundRole)
                
                # Standard-Auswahl setzen
                default_index = class_id % len(self.predefined_colors)
                color_preset_combo.setCurrentIndex(default_index)
                
                # Event-Handler fuer Farbauswahl
                def make_color_selector(class_id, combo):
                    def select_color():
                        selected_color = combo.currentData()
                        if selected_color:
                            self.class_colors[class_id] = QColor(selected_color)
                    return select_color
                
                color_preset_combo.currentTextChanged.connect(make_color_selector(class_id, color_preset_combo))
                grid_layout.addWidget(color_preset_combo, row, col * 2 + 1)
                
                # Layout: 2 Spalten à 2 Felder (Label + Dropdown)
                col += 1
                if col >= 2:
                    col = 0
                    row += 1
            
            color_layout.addWidget(grid_widget)
        else:
            # Fallback wenn keine Klassen geladen
            no_classes_label = QLabel("Keine Klassen verfuegbar. Bitte zuerst ein Modell laden.")
            no_classes_label.setStyleSheet("color: #888888; font-style: italic; text-align: center;")
            no_classes_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            color_layout.addWidget(no_classes_label)
        
        layout.addWidget(color_group)
        layout.addStretch()
        
        self.tab_widget.addTab(scroll, "🎨 Farbzuteilung")
        
    def _create_interfaces_tab(self):
        """Tab 4: 🔌 Schnittstellen - ERWEITERT: Mit editierbaren Modbus-Einstellungen"""
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
            "Waehlen Sie eine IDS Peak Kamera-Konfigurationsdatei (.toml), um erweiterte "
            "Kameraeinstellungen wie Belichtung, Gamma und Weissabgleich zu verwenden."
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: #7f8c8d; font-style: italic; margin-bottom: 10px;")
        layout.addRow(info_label)
        
        # Konfigurationspfad
        config_path_layout = QHBoxLayout()
        self.camera_config_path_label = QLabel("Keine Konfiguration ausgewaehlt")
        self.camera_config_path_label.setStyleSheet(
            "background-color: #f0f0f0; padding: 5px; border-radius: 3px; color: #2c3e50;"
        )
        palette = QApplication.instance().palette()
        self.camera_config_path_label.setPalette(palette)
        self.camera_config_path_label.setAutoFillBackground(True)
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
        
        # MODBUS-Einstellungen - ERWEITERT: Mit editierbaren IP/Port
        self._add_section_header(layout, "🔌 WAGO Modbus-Schnittstelle")
        
        # INFO: Verbindungsstatus
        self.modbus_connection_info = QLabel("Modbus-Status wird geladen...")
        self.modbus_connection_info.setStyleSheet("color: #2c3e50; font-weight: bold; background-color: #ecf0f1; padding: 8px; border-radius: 4px;")
        layout.addRow(self.modbus_connection_info)
        
        # NEU: IP-Adresse editierbar (nur wenn getrennt)
        modbus_ip_info = self._create_info_label(
            "IP-Adresse des WAGO Controllers. Aenderungen sind nur moeglich, wenn die Modbus-Verbindung getrennt ist."
        )
        layout.addRow(modbus_ip_info)
        
        self.modbus_ip_input = QLineEdit()
        self.modbus_ip_input.setPlaceholderText("192.168.1.100")
        self.modbus_ip_input.setStyleSheet("""
            QLineEdit {
                padding: 8px 12px;
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                font-size: 12px;
            }
            QLineEdit:disabled {
                background-color: #ecf0f1;
                color: #7f8c8d;
                border-color: #d5dbdb;
            }
        """)
        layout.addRow("WAGO IP-Adresse:", self.modbus_ip_input)
        
        # NEU: Port editierbar (nur wenn getrennt)
        modbus_port_info = self._create_info_label(
            "Modbus-TCP Port des WAGO Controllers (Standard: 502). Aenderungen sind nur moeglich, wenn die Modbus-Verbindung getrennt ist."
        )
        layout.addRow(modbus_port_info)
        
        self.modbus_port_spin = QSpinBox()
        self.modbus_port_spin.setRange(1, 65535)
        self.modbus_port_spin.setValue(502)
        self.modbus_port_spin.setStyleSheet("""
            QSpinBox {
                padding: 8px 12px;
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                font-size: 12px;
            }
            QSpinBox:disabled {
                background-color: #ecf0f1;
                color: #7f8c8d;
                border-color: #d5dbdb;
            }
        """)
        layout.addRow("Modbus-TCP Port:", self.modbus_port_spin)
        
        # Ausschuss-Signal Dauer - MIT INFO
        reject_duration_info = self._create_info_label(
            "Dauer des Ausschuss-Signals in Sekunden. Muss lang genug sein, "
            "damit das nachgelagerte System (Druckluft, Aussortierung) reagieren kann."
        )
        layout.addRow(reject_duration_info)
        
        self.reject_coil_duration_spin = QDoubleSpinBox()
        self.reject_coil_duration_spin.setRange(0.1, 10.0)
        self.reject_coil_duration_spin.setSingleStep(0.1)
        self.reject_coil_duration_spin.setDecimals(1)
        layout.addRow("Ausschuss-Signal Dauer (Sekunden):", self.reject_coil_duration_spin)
        
        self._add_spacer(layout)
        
        # Modbus-Aktionen
        self._add_section_header(layout, "🔧 WAGO Modbus-Aktionen")
        
        # Aktions-Buttons
        modbus_actions_layout = QHBoxLayout()
        
        # Controller Reset Button
        self.modbus_reset_btn = QPushButton("🔄 Controller Reset")
        self.modbus_reset_btn.setStyleSheet("""
            QPushButton {
                background-color: #e67e22;
                color: white;
                font-size: 12px;
                min-height: 35px;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #d35400;
            }
            QPushButton:disabled {
                background-color: #7f8c8d;
                color: #bdc3c7;
            }
        """)
        self.modbus_reset_btn.setToolTip("WAGO Controller zuruecksetzen (Admin-Rechte erforderlich)")
        self.modbus_reset_btn.clicked.connect(self.handle_modbus_reset)
        modbus_actions_layout.addWidget(self.modbus_reset_btn)
        
        # Neuverbindung Button
        self.modbus_reconnect_btn = QPushButton("🔌 Neuverbindung")
        self.modbus_reconnect_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                font-size: 12px;
                min-height: 35px;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:disabled {
                background-color: #7f8c8d;
                color: #bdc3c7;
            }
        """)
        self.modbus_reconnect_btn.setToolTip("Modbus neu verbinden (Admin-Rechte erforderlich)")
        self.modbus_reconnect_btn.clicked.connect(self.handle_modbus_reconnect)
        modbus_actions_layout.addWidget(self.modbus_reconnect_btn)
        
        layout.addRow("Aktionen:", modbus_actions_layout)
        
        # Status-Info
        modbus_status_info = QLabel("Diese Aktionen sind nur fuer Administratoren verfuegbar und helfen bei Verbindungsproblemen.")
        modbus_status_info.setStyleSheet("color: #7f8c8d; font-style: italic; font-size: 11px;")
        modbus_status_info.setWordWrap(True)
        layout.addRow(modbus_status_info)
        
        self.tab_widget.addTab(scroll, "🔌 Schnittstellen")
    
    def _create_storage_monitoring_tab(self):
        """Tab 5: 💾 Speicherung & Überwachung"""
        tab = QWidget()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(tab)
        
        layout = QFormLayout(tab)
        layout.setSpacing(15)
        
        # Bilderspeicherung
        self._add_section_header(layout, "📸 Bilderspeicherung")
        
        # Bilderspeicherung Info
        storage_info = self._create_info_label(
            "Speichert Bilder zur spaeteren Analyse oder Dokumentation. "
            "Schlechtbilder: Bilder mit erkannten Fehlern. Gutbilder: Bilder ohne erkannte Fehler."
        )
        layout.addRow(storage_info)
        
        self.save_bad_images_check = QCheckBox()
        layout.addRow("Schlechtbilder speichern:", self.save_bad_images_check)
        
        # Schlechtbilder-Verzeichnis
        bad_dir_layout = QHBoxLayout()
        self.bad_images_dir_input = QLabel("bad_images")
        self.bad_images_dir_input.setStyleSheet(
            "background-color: #f0f0f0; padding: 5px; border-radius: 3px; color: #2c3e50;"
        )
        palette = QApplication.instance().palette()
        self.bad_images_dir_input.setPalette(palette)
        self.bad_images_dir_input.setAutoFillBackground(True)
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
        self.good_images_dir_input.setStyleSheet(
            "background-color: #f0f0f0; padding: 5px; border-radius: 3px; color: #2c3e50;"
        )
        palette = QApplication.instance().palette()
        self.good_images_dir_input.setPalette(palette)
        self.good_images_dir_input.setAutoFillBackground(True)
        good_dir_layout.addWidget(self.good_images_dir_input, 1)
        
        good_dir_browse_btn = QPushButton("📁")
        good_dir_browse_btn.clicked.connect(self.browse_good_images_directory)
        good_dir_layout.addWidget(good_dir_browse_btn)
        
        layout.addRow("Gutbilder-Verzeichnis:", good_dir_layout)
        
        # Maximale Dateien - MIT INFO
        max_files_info = self._create_info_label(
            "Maximale Anzahl Bilder pro Verzeichnis. Bei Erreichen werden keine weiteren Bilder gespeichert. "
            "Verhindert Speicher-Überlauf bei Langzeitbetrieb."
        )
        layout.addRow(max_files_info)
        
        self.max_images_spin = QSpinBox()
        self.max_images_spin.setRange(1000, 500000)
        self.max_images_spin.setSingleStep(1000)
        self.max_images_spin.setValue(100000)
        layout.addRow("Max. Dateien pro Verzeichnis:", self.max_images_spin)
        
        self._add_spacer(layout)
        
        # Helligkeitsueberwachung
        self._add_section_header(layout, "💡 Helligkeitsueberwachung")
        
        # Helligkeitsueberwachung Info
        brightness_info = self._create_info_label(
            "Überwacht die Bildhelligkeit und stoppt die Erkennung automatisch bei schlechten Lichtverhaeltnissen. "
            "Verhindert fehlerhafte Erkennungen durch zu dunkle oder ueberbelichtete Bilder."
        )
        layout.addRow(brightness_info)
        
        self.brightness_low_spin = QSpinBox()
        self.brightness_low_spin.setRange(0, 254)
        self.brightness_low_spin.valueChanged.connect(self.validate_brightness_ranges)
        layout.addRow("Untere Schwelle (Auto-Stopp bei zu dunkel):", self.brightness_low_spin)
        
        self.brightness_high_spin = QSpinBox()
        self.brightness_high_spin.setRange(1, 255)
        self.brightness_high_spin.valueChanged.connect(self.validate_brightness_ranges)
        layout.addRow("Obere Schwelle (Auto-Stopp bei zu hell):", self.brightness_high_spin)
        
        self.brightness_duration_spin = QDoubleSpinBox()
        self.brightness_duration_spin.setRange(1.0, 30.0)
        self.brightness_duration_spin.setSingleStep(0.5)
        layout.addRow("Dauer bis Auto-Stopp (Sekunden):", self.brightness_duration_spin)
        
        self.tab_widget.addTab(scroll, "💾 Speicherung & Überwachung")
    
    def _create_info_label(self, text):
        """Erstelle ein Info-Label mit einheitlichem Styling."""
        label = QLabel(text)
        label.setWordWrap(True)
        label.setStyleSheet("""
            QLabel {
                color: #7f8c8d;
                font-style: italic;
                font-size: 11px;
                background-color: #ecf0f1;
                padding: 8px;
                border-radius: 4px;
                border-left: 3px solid #3498db;
            }
        """)
        return label
    
    def _create_class_combo(self):
        """ComboBox mit verfuegbaren Klassen erstellen."""
        combo = QComboBox()
        combo.addItem("Klasse auswaehlen...", -1)
        
        for class_id, class_name in self.class_names.items():
            combo.addItem(f"{class_name} (ID: {class_id})", class_id)
        
        return combo
    
    def _add_section_header(self, layout, title):
        header = QLabel(title)

        # Palette aus App-Theme ziehen
        palette = QApplication.instance().palette()
        header.setPalette(palette)
        header.setAutoFillBackground(True)

        header.setFont(QFont("", 12, QFont.Weight.Bold))
        layout.addRow(header)
    
    def _add_spacer(self, layout):
        """Trennlinie hinzufuegen."""
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
        
        reset_btn = QPushButton("🔄 Zuruecksetzen")
        reset_btn.setMinimumHeight(40)
        reset_btn.clicked.connect(self.reset_settings)
        button_layout.addWidget(reset_btn)
        
        # ZUSÄTZLICH: Ensure dass Button-Sektion immer sichtbar bleibt
        button_widget = QWidget()
        button_widget.setLayout(button_layout)
        button_widget.setFixedHeight(60)  # Feste Höhe für Button-Bereich
        
        layout.addWidget(button_widget)
    
    # NEU: Modbus-Verbindungsstatus updaten
    def update_modbus_connection_status(self, connected):
        """Modbus-Verbindungsstatus im Dialog aktualisieren."""
        if connected:
            self.modbus_connection_info.setText("✅ Modbus verbunden - IP/Port-Einstellungen gesperrt")
            self.modbus_connection_info.setStyleSheet("color: #27ae60; font-weight: bold; background-color: #d5f4e6; padding: 8px; border-radius: 4px;")
            # IP/Port sperren
            self.modbus_ip_input.setEnabled(False)
            self.modbus_port_spin.setEnabled(False)
        else:
            self.modbus_connection_info.setText("❌ Modbus getrennt - IP/Port-Einstellungen editierbar")
            self.modbus_connection_info.setStyleSheet("color: #e74c3c; font-weight: bold; background-color: #fadbd8; padding: 8px; border-radius: 4px;")
            # IP/Port freigeben (nur für Admin)
            can_edit = hasattr(self.parent_app, 'app') and self.parent_app.app.user_manager.can_change_modbus_settings()
            self.modbus_ip_input.setEnabled(can_edit)
            self.modbus_port_spin.setEnabled(can_edit)
    
    # Modbus-Aktions-Handler
    def handle_modbus_reset(self):
        """WAGO Controller Reset aus Einstellungen."""
        # Pruefe Admin-Rechte
        if not hasattr(self.parent_app, 'app') or not self.parent_app.app.user_manager.is_admin():
            QMessageBox.warning(
                self,
                "Zugriff verweigert",
                "Admin-Rechte erforderlich fuer Controller-Reset."
            )
            return
        
        # Bestaetigung anfordern
        reply = QMessageBox.question(
            self,
            "Controller Reset",
            "WAGO Controller zuruecksetzen?\n\nDies kann Verbindungsprobleme beheben.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                if self.parent_app.app.modbus_manager.restart_controller():
                    QMessageBox.information(
                        self,
                        "Reset erfolgreich",
                        "WAGO Controller wurde zurueckgesetzt.\nVerbindung wird neu aufgebaut..."
                    )
                    # Automatische Neuverbindung nach Reset
                    self.handle_modbus_reconnect()
                else:
                    QMessageBox.critical(
                        self,
                        "Reset fehlgeschlagen",
                        "Controller-Reset konnte nicht durchgefuehrt werden.\nPruefen Sie die Verbindung."
                    )
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Fehler",
                    f"Fehler beim Controller-Reset:\n{str(e)}"
                )
    
    def handle_modbus_reconnect(self):
        """Modbus Neuverbindung aus Einstellungen."""
        # Pruefe Admin-Rechte
        if not hasattr(self.parent_app, 'app') or not self.parent_app.app.user_manager.is_admin():
            QMessageBox.warning(
                self,
                "Zugriff verweigert",
                "Admin-Rechte erforderlich fuer Neuverbindung."
            )
            return
        
        try:
            if self.parent_app.app.modbus_manager.force_reconnect():
                # Services neu starten
                self.parent_app.app.modbus_manager.start_watchdog()
                self.parent_app.app.modbus_manager.start_coil_refresh()
                
                # UI Status aktualisieren
                self.parent_app.app.ui.update_modbus_status(True, self.parent_app.app.modbus_manager.ip_address)
                
                QMessageBox.information(
                    self,
                    "Neuverbindung erfolgreich",
                    "Modbus erfolgreich neu verbunden.\nAnwendung ist wieder betriebsbereit."
                )
            else:
                QMessageBox.critical(
                    self,
                    "Neuverbindung fehlgeschlagen",
                    "Modbus-Neuverbindung konnte nicht hergestellt werden.\nPruefen Sie die Netzwerkverbindung."
                )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Fehler",
                f"Fehler bei Neuverbindung:\n{str(e)}"
            )
    
    # Event Handler-Methoden
    def browse_camera_config_file(self):
        """IDS Peak Kamera-Konfigurationsdatei auswaehlen."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "IDS Peak Kamera-Konfigurationsdatei auswaehlen",
            "",
            "TOML-Dateien (*.toml);;Alle Dateien (*)"
        )
        
        if file_path:
            try:
                if file_path.lower().endswith('.toml'):
                    self.camera_config_path_label.setText(file_path)
                    QMessageBox.information(
                        self,
                        "Konfiguration ausgewaehlt",
                        f"IDS Peak Konfigurationsdatei ausgewaehlt:\n{os.path.basename(file_path)}\n\n"
                        "Die Konfiguration wird beim naechsten Kamera-Start angewendet."
                    )
                else:
                    QMessageBox.warning(
                        self,
                        "Ungueltige Datei",
                        "Bitte waehlen Sie eine .toml Datei aus."
                    )
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Fehler",
                    f"Fehler beim Laden der Konfigurationsdatei:\n{str(e)}"
                )
    
    def clear_camera_config(self):
        """Kamera-Konfiguration loeschen."""
        self.camera_config_path_label.setText("Keine Konfiguration ausgewaehlt")
        QMessageBox.information(
            self,
            "Konfiguration geloescht",
            "Die Kamera-Konfiguration wurde entfernt.\nStandard-Kameraeinstellungen werden verwendet."
        )
    
    def browse_bad_images_directory(self):
        """Verzeichnis fuer Schlechtbilder auswaehlen."""
        directory = QFileDialog.getExistingDirectory(
            self,
            "Verzeichnis fuer Schlechtbilder auswaehlen",
            self.bad_images_dir_input.text()
        )
        if directory:
            self.bad_images_dir_input.setText(directory)
    
    def browse_good_images_directory(self):
        """Verzeichnis fuer Gutbilder auswaehlen."""
        directory = QFileDialog.getExistingDirectory(
            self,
            "Verzeichnis fuer Gutbilder auswaehlen",
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
        """Schlecht-Teil Klasse hinzufuegen."""
        selected_id = self.bad_class_combo.currentData()
        if selected_id == -1:  # "Klasse auswaehlen..." gewaehlt
            return
        
        class_name = self.class_names.get(selected_id, f"Class {selected_id}")
        display_text = f"{class_name} (ID: {selected_id})"
        
        # Pruefe ob bereits vorhanden
        for i in range(self.bad_part_classes_list.count()):
            if self.bad_part_classes_list.item(i).data(Qt.ItemDataRole.UserRole) == selected_id:
                return  # Bereits vorhanden
        
        from PyQt6.QtWidgets import QListWidgetItem
        item = QListWidgetItem(display_text)
        item.setData(Qt.ItemDataRole.UserRole, selected_id)  # Speichere ID
        self.bad_part_classes_list.addItem(item)
    
    def remove_bad_class(self):
        """Ausgewaehlte Schlecht-Teil Klasse entfernen."""
        current_row = self.bad_part_classes_list.currentRow()
        if current_row >= 0:
            self.bad_part_classes_list.takeItem(current_row)
    
    def add_good_class(self):
        """Gut-Teil Klasse hinzufuegen."""
        selected_id = self.good_class_combo.currentData()
        if selected_id == -1:  # "Klasse auswaehlen..." gewaehlt
            return
        
        class_name = self.class_names.get(selected_id, f"Class {selected_id}")
        display_text = f"{class_name} (ID: {selected_id})"
        
        # Pruefe ob bereits vorhanden
        for i in range(self.good_part_classes_list.count()):
            if self.good_part_classes_list.item(i).data(Qt.ItemDataRole.UserRole) == selected_id:
                return  # Bereits vorhanden
        
        from PyQt6.QtWidgets import QListWidgetItem
        item = QListWidgetItem(display_text)
        item.setData(Qt.ItemDataRole.UserRole, selected_id)  # Speichere ID
        self.good_part_classes_list.addItem(item)
    
    def remove_good_class(self):
        """Ausgewaehlte Gut-Teil Klasse entfernen."""
        current_row = self.good_part_classes_list.currentRow()
        if current_row >= 0:
            self.good_part_classes_list.takeItem(current_row)
    
    def load_settings(self):
        """Aktuelle Einstellungen laden."""
        # Allgemein
        self.motion_threshold_spin.setValue(self.settings.get('motion_threshold', 110))
        self.red_threshold_spin.setValue(self.settings.get('red_threshold', 1))
        self.green_threshold_spin.setValue(self.settings.get('green_threshold', 4))
        self.settling_time_spin.setValue(self.settings.get('settling_time', 1.0))
        self.capture_time_spin.setValue(self.settings.get('capture_time', 3.0))
        self.blow_off_time_spin.setValue(self.settings.get('blow_off_time', 5.0))
        self.motion_decay_spin.setValue(self.settings.get('motion_decay_factor', 0.1))

        # Klassen-Zuteilung: BEIDE Konfidenz-Einstellungen
        self.confidence_spin.setValue(self.settings.get('confidence_threshold', 0.5))
        self.bad_part_confidence_spin.setValue(self.settings.get('bad_part_min_confidence', 0.5))
        
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
        
        # Farbzuteilung: Lade gespeicherte Klassenfarben
        saved_colors = self.settings.get('class_colors', {})
        for class_id in self.class_names.keys():
            if str(class_id) in saved_colors:
                self.class_colors[class_id] = QColor(saved_colors[str(class_id)])
            else:
                # Verwende vordefinierte Farbe als Standard
                default_color = self.predefined_colors[class_id % len(self.predefined_colors)]
                self.class_colors[class_id] = QColor(default_color)
        
        # Schnittstellen - ERWEITERT: Mit IP/Port
        camera_config_path = self.settings.get('camera_config_path', '')
        if camera_config_path:
            self.camera_config_path_label.setText(camera_config_path)
        else:
            self.camera_config_path_label.setText("Keine Konfiguration ausgewaehlt")
        
        # NEU: Modbus IP/Port laden
        self.modbus_ip_input.setText(self.settings.get('modbus_ip', '192.168.1.100'))
        self.modbus_port_spin.setValue(self.settings.get('modbus_port', 502))
        self.reject_coil_duration_spin.setValue(self.settings.get('reject_coil_duration_seconds', 1.0))
        
        # NEU: Modbus-Verbindungsstatus aktualisieren
        if hasattr(self.parent_app, 'app'):
            is_connected = self.parent_app.app.modbus_manager.is_connected()
            self.update_modbus_connection_status(is_connected)
            
            # Button-Status je nach Admin-Rechten
            is_admin = self.parent_app.app.user_manager.is_admin()
            self.modbus_reset_btn.setEnabled(is_admin)
            self.modbus_reconnect_btn.setEnabled(is_admin)
        
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
        # Allgemein
        self.settings.set('motion_threshold', self.motion_threshold_spin.value())
        self.settings.set('motion_decay_factor', self.motion_decay_spin.value())
        self.settings.set('red_threshold', self.red_threshold_spin.value())
        self.settings.set('green_threshold', self.green_threshold_spin.value())
        self.settings.set('settling_time', self.settling_time_spin.value())
        self.settings.set('capture_time', self.capture_time_spin.value())
        self.settings.set('blow_off_time', self.blow_off_time_spin.value())
        
        # Klassen-Zuteilung: BEIDE Konfidenz-Einstellungen
        self.settings.set('confidence_threshold', self.confidence_spin.value())
        self.settings.set('bad_part_min_confidence', self.bad_part_confidence_spin.value())
        
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
        
        # Farbzuteilung: Speichere Klassenfarben
        color_dict = {}
        for class_id, color in self.class_colors.items():
            color_dict[str(class_id)] = color.name()
        self.settings.set('class_colors', color_dict)
        
        # Schnittstellen - ERWEITERT: Mit IP/Port
        camera_config_text = self.camera_config_path_label.text()
        if camera_config_text == "Keine Konfiguration ausgewaehlt":
            self.settings.set('camera_config_path', '')
        else:
            self.settings.set('camera_config_path', camera_config_text)
        
        # NEU: Modbus IP/Port speichern
        self.settings.set('modbus_ip', self.modbus_ip_input.text())
        self.settings.set('modbus_port', self.modbus_port_spin.value())
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
        
        # Prüfe ob Modbus-Einstellungen geändert wurden und zeige Warnung
        if hasattr(self.parent_app, 'app'):
            current_ip = self.parent_app.app.modbus_manager.ip_address
            current_port = self.parent_app.app.modbus_manager.port
            new_ip = self.modbus_ip_input.text()
            new_port = self.modbus_port_spin.value()
            
            if (current_ip != new_ip or current_port != new_port):
                QMessageBox.information(
                    self,
                    "Modbus-Einstellungen geändert",
                    "IP-Adresse oder Port wurden geändert.\n\n"
                    "Die neuen Einstellungen werden beim nächsten Neustart der Anwendung oder "
                    "bei einer manuellen Neuverbindung wirksam."
                )
        
        self.settings.save()
        self.accept()
    
    def reset_settings(self):
        """Einstellungen zuruecksetzen."""
        reply = QMessageBox.question(
            self,
            "Einstellungen zuruecksetzen",
            "Alle Einstellungen auf Standardwerte zuruecksetzen?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.settings.reset_to_defaults()
            self.settings.save()
            self.load_settings()