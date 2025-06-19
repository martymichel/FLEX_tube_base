"""
Dialog-Komponenten für Kamera-Auswahl und Einstellungen
Alle Dialog-Fenster der Anwendung mit Tab-basiertem Layout, erweiterte Klassenzuteilung und Referenzlinien
ERWEITERT: Tabellarische Klassenzuteilung mit dunklem Hintergrund und Referenzlinien-Einstellungen
testinhalt

"""

import os
import logging

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
    QFrame, QFileDialog, QSpinBox, QDoubleSpinBox, QCheckBox, 
    QFormLayout, QMessageBox, QListWidget, QTabWidget, QWidget,
    QScrollArea, QSizePolicy, QComboBox, QApplication, QColorDialog,
    QGridLayout, QTableWidget, QTableWidgetItem, QHeaderView, 
    QAbstractItemView, QLineEdit, QGroupBox, QScrollArea
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor

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
    """Tab-basierter Einstellungen-Dialog mit erweiterter tabellarischer Klassenzuteilung und Referenzlinien."""
    
    def __init__(self, settings, class_names=None, parent=None):
        super().__init__(parent)
        self.settings = settings
        self.class_names = class_names or {}  # Dictionary {id: name}
        self.parent_app = parent  # Referenz zur Hauptanwendung für Modbus-Funktionen
        self.setWindowTitle("⚙️ Einstellungen")
        self.setModal(True)
        self.resize(1000, 800) 
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.FramelessWindowHint)

        # 20 vordefinierte Farben für Klassen
        self.predefined_colors = [
            "#FF0000",  # Rot
            "#00FF00",  # Grün
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
            "#FFFFFF",  # Weiß
            "#008000",  # Dunkelgrün
            "#000080",  # Dunkelblau
            "#800000",  # Bordeaux
            "#808000",  # Olive
            "#008080",  # Türkis
            "#C0C0C0",  # Silber
            "#FFD700"   # Gold
        ]
        
        # Speichere Klassenzuteilungsdaten
        self.class_assignments_data = {}
        
        self.setup_ui()
        self.load_settings()
    
    def setup_ui(self):
        """UI mit Tab-Layout aufbauen."""
        layout = QVBoxLayout(self)
        
        # Tab-Widget erstellen
        self.tab_widget = QTabWidget()
        # — doppelte Tabhöhe —
        tabbar = self.tab_widget.tabBar()
        tabbar.setStyleSheet("QTabBar::tab { min-height: 44px; }")

        layout.addWidget(self.tab_widget)
        
        # Tabs erstellen
        self._create_general_tab()
        self._create_class_assignments_tab()  # NEUE erweiterte tabellarische Klassenzuteilung
        self._create_reference_lines_tab()    # NEUE Referenzlinien
        self._create_interfaces_tab()
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
            "Schwellwert für Erkennung des Förderband-Takts. Niedrigere Werte = empfindlicher für Bewegung. "
            "Bestimmt, wann das Förderband als 'in Bewegung' erkannt wird."
        )
        layout.addRow(motion_info)
        
        self.motion_threshold_spin = QSpinBox()
        self.motion_threshold_spin.setRange(1, 255)
        layout.addRow("Bandtakt Grenzwert (1-255):", self.motion_threshold_spin)
        self._add_cycle_arrow(layout)
        
        # Ausschwingzeit - MIT INFO
        settling_info = self._create_info_label(
            "Wartezeit nach Stillstand des Förderbands, bevor die KI-Erkennung startet. "
            "Verhindert Erkennungen während des Ausschwingvorgangs."
        )
        layout.addRow(settling_info)
        
        self.settling_time_spin = QDoubleSpinBox()
        self.settling_time_spin.setRange(0.1, 10.0)
        self.settling_time_spin.setSingleStep(0.1)
        layout.addRow("Ausschwingzeit (Sekunden):", self.settling_time_spin)
        self._add_cycle_arrow(layout)

        # Aufnahmezeit - MIT INFO
        capture_info = self._create_info_label(
            "Dauer der KI-Erkennung pro Zyklus. Längere Zeit = mehr Bilder analysiert, "
            "aber langsamerer Durchsatz."
        )
        layout.addRow(capture_info)
        
        self.capture_time_spin = QDoubleSpinBox()
        self.capture_time_spin.setRange(0.5, 10.0)
        self.capture_time_spin.setSingleStep(0.1)
        layout.addRow("Aufnahmezeit (Sekunden):", self.capture_time_spin)
        self._add_cycle_arrow(layout)
        
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
        layout.addRow("Ausschuss-Signal PULS-Dauer 8(s):", self.reject_coil_duration_spin)
        self._add_cycle_arrow(layout)

        # Verzögerung nach Abblasen - MIT INFO
        blow_off_info = self._create_info_label(
            "Verzögerung nach dem Ausschuss-Signal, bevor die Bewegungserkennung neu startet."
            " Soll sicherstellen, dass das Abblasen vollständig abgeschlossen ist."
        )
        layout.addRow(blow_off_info)

        self.wait_after_blow_off_time_spin = QDoubleSpinBox()
        self.wait_after_blow_off_time_spin.setRange(0.1, 2.0)
        self.wait_after_blow_off_time_spin.setSingleStep(0.1)
        self.wait_after_blow_off_time_spin.setDecimals(1)
        layout.addRow("Wartezeit nach Abblasen (Sekunden):", self.wait_after_blow_off_time_spin)
        self._add_cycle_arrow(layout, loop=True) # Symbol für Schleife

        # Motion-Kalibrierung
        calib_info = self._create_info_label(
            "Führt eine kurze Lernphase durch, um die Bewegungserkennung zu kalibrieren.\n"
            "Während des Lernens wird weiterhin die Standard-Methode verwendet."
        )
        layout.addRow(calib_info)

        self.motion_learning_spin = QDoubleSpinBox()
        self.motion_learning_spin.setRange(5.0, 300.0)
        self.motion_learning_spin.setSingleStep(5.0)
        layout.addRow("Kalibrierungsdauer (Sekunden):", self.motion_learning_spin)

        self.motion_calibration_btn = QPushButton("🎬 Kalibrierung starten")
        self.motion_calibration_btn.clicked.connect(self.start_motion_calibration)
        layout.addRow(self.motion_calibration_btn)     
        self._add_spacer(layout)
        
        self.tab_widget.addTab(scroll, "⚙️ Allgemein")
    
    def _create_class_assignments_tab(self):
        """Tab 2: 🎯 Klassenzuteilung - TABELLARISCH mit dunklem Hintergrund"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(15)
        
        # Header mit Info
        header_label = QLabel("🎯 Klassenzuteilung")
        header_label.setFont(QFont("", 16, QFont.Weight.Bold))  # Größere Schrift
        layout.addWidget(header_label)
        
        # Info-Text
        info_label = self._create_info_label(
            "Konfigurieren Sie für jede Klasse die Zuteilung (Gut/Schlecht/Ignorieren), erwartete Anzahl, "
            "Mindest-Konfidenz und Bounding-Box-Farbe. Gut-Teile können auch überwacht werden - bei "
            "Abweichung von der erwarteten Anzahl wird ein Ausschuss-Signal ausgelöst."
        )
        layout.addWidget(info_label)
        
        # Tabelle für Klassenzuteilungen - MIT DUNKLEM HINTERGRUND
        self.class_assignments_table = QTableWidget(0, 5)
        self.class_assignments_table.setHorizontalHeaderLabels([
            "Klassename", "Zuteilung", "Erwartete Anzahl", "Min. Konfidenz", "Farbe"
        ])
        
        # DUNKLER TABELLEN-STYLE mit größerer Schrift und touch-freundlichen Elementen
        self.class_assignments_table.setStyleSheet("""
            QTableWidget {
                background: rgba(44, 62, 80, 0.95);
                color: #e2e8f0;
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 4px;
                font-size: 14px;
                gridline-color: rgba(255, 255, 255, 0.1);
                selection-background-color: rgba(52, 152, 219, 0.3);
            }
            QHeaderView::section {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                        stop: 0 #4a5568, stop: 1 #2d3748);
                color: white;
                border: none;
                padding: 12px;
                font-size: 14px;
                font-weight: 600;
                text-transform: uppercase;
                min-height: 45px;
            }
            QTableWidget::item {
                padding: 6px;
                border: none;
                color: white;
                min-height: 45px;
                text-align: center;
            }
            QTableWidget::item:selected {
                background: rgba(52, 152, 219, 0.4);
                color: white;
            }
            QComboBox, QSpinBox, QDoubleSpinBox, QPushButton {
                background-color: #34495e;
                color: white;
                border: 1px solid #7f8c8d;
                padding: 0px 12px;
                border-radius: 4px;
                font-size: 14px;
                min-height: 38px;
                max-height: 38px;
            }
            QComboBox {
                padding-right: 35px;
            }
            QComboBox:drop-down {
                border: none;
                width: 30px;
                border-left: 1px solid #7f8c8d;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 8px solid transparent;
                border-right: 8px solid transparent;
                border-top: 8px solid white;
                margin: 5px;
            }
            QComboBox:hover, QSpinBox:hover, QDoubleSpinBox:hover, QPushButton:hover {
                background-color: #3e5368;
                border-color: #95a5a6;
            }
            QSpinBox::up-button, QSpinBox::down-button,
            QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {
                width: 25px;
                height: 15px;
                border: none;
                background-color: #4a5568;
            }
            QSpinBox::up-button:hover, QSpinBox::down-button:hover,
            QDoubleSpinBox::up-button:hover, QDoubleSpinBox::down-button:hover {
                background-color: #5a6878;
            }
            QSpinBox::up-arrow, QDoubleSpinBox::up-arrow {
                image: none;
                border-left: 6px solid transparent;
                border-right: 6px solid transparent;
                border-bottom: 6px solid white;
            }
            QSpinBox::down-arrow, QDoubleSpinBox::down-arrow {
                image: none;
                border-left: 6px solid transparent;
                border-right: 6px solid transparent;
                border-top: 6px solid white;
            }
        """)
        
        # Tabellen-Konfiguration mit angepassten Zeilenhöhen
        header = self.class_assignments_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)  # Klassename
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)    # Zuteilung
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)    # Anzahl
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)    # Konfidenz
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)    # Farbe
        
        self.class_assignments_table.setColumnWidth(1, 220)  # Zuteilung (breiter für größere Schrift)
        self.class_assignments_table.setColumnWidth(2, 200)  # Anzahl (breiter)
        self.class_assignments_table.setColumnWidth(3, 200)  # Konfidenz (breiter)
        self.class_assignments_table.setColumnWidth(4, 100)  # Farbe (breiter für Color Box)

        # Zeilenhöhe auf mindestens 45px setzen
        vertical_header = self.class_assignments_table.verticalHeader()
        vertical_header.setDefaultSectionSize(48)
        vertical_header.setMinimumSectionSize(45)
        
        # Sicherstellen, dass Widgets in Zellen zentriert werden
        self.class_assignments_table.setWordWrap(False)

        self.class_assignments_table.setEditTriggers(QAbstractItemView.EditTrigger.DoubleClicked |
                                                    QAbstractItemView.EditTrigger.SelectedClicked)
        
        self.class_assignments_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.class_assignments_table.setShowGrid(True)

        self.class_assignments_table.setMinimumHeight(400)
        
        layout.addWidget(self.class_assignments_table)
        
        # Button-Leiste für Tabelle mit größeren, touch-freundlicheren Buttons
        table_buttons_layout = QHBoxLayout()
        
        self.add_class_btn = QPushButton("➕ Klasse hinzufügen")
        self.add_class_btn.setFont(QFont("", 14))
        self.add_class_btn.setMinimumHeight(45)
        self.add_class_btn.clicked.connect(self.add_class_assignment)
        table_buttons_layout.addWidget(self.add_class_btn)
        
        self.remove_class_btn = QPushButton("➖ Klasse entfernen")
        self.remove_class_btn.setFont(QFont("", 14))
        self.remove_class_btn.setMinimumHeight(45)
        self.remove_class_btn.clicked.connect(self.remove_class_assignment)
        table_buttons_layout.addWidget(self.remove_class_btn)
        
        self.reset_table_btn = QPushButton("🔄 Zurücksetzen")
        self.reset_table_btn.setFont(QFont("", 14))
        self.reset_table_btn.setMinimumHeight(45)
        self.reset_table_btn.clicked.connect(self.reset_class_assignments)
        table_buttons_layout.addWidget(self.reset_table_btn)
        
        table_buttons_layout.addStretch()
        layout.addLayout(table_buttons_layout)
        
        # Legende mit größerer Schrift
        legend_label = self._create_info_label(
            "💡 Legende:\n"
            "• Gut: Bei Abweichung von erwarteter Anzahl → Ausschuss\n"
            "• Schlecht: Bei Erkennung → sofortiger Ausschuss\n"
            "• Ignorieren: Klasse wird nicht bewertet\n"
            "• Erwartete Anzahl: -1 = beliebig, >0 = exakte Anzahl"
        )
        # Schriftgröße für Legende anpassen falls _create_info_label das nicht bereits macht
        legend_font = legend_label.font()
        legend_font.setPointSize(13)
        legend_label.setFont(legend_font)
        layout.addWidget(legend_label)
        
        self.tab_widget.addTab(tab, "🎯 Klassenzuteilung")
    
    def _create_reference_lines_tab(self):
        """Tab 3: 📏 Referenzlinien"""
        tab = QWidget()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(tab)
        
        layout = QVBoxLayout(tab)
        layout.setSpacing(15)
        
        # Header
        header_label = QLabel("📏 Referenzlinien")
        header_label.setFont(QFont("", 14, QFont.Weight.Bold))
        layout.addWidget(header_label)
        
        # Info-Text
        info_label = self._create_info_label(
            "Referenzlinien werden als Laser-ähnliche Linien über das Video gelegt und helfen bei der "
            "visuellen Ausrichtung und Positionierung von Objekten. Bis zu 4 Linien können konfiguriert werden."
        )
        layout.addWidget(info_label)
        
        # Linien-Konfiguration
        self.reference_line_widgets = []
        
        for i in range(4):
            line_frame = self._create_reference_line_config(i)
            layout.addWidget(line_frame)
        
        layout.addStretch()
        
        self.tab_widget.addTab(scroll, "📏 Referenzlinien")
    
    def _create_reference_line_config(self, line_index):
        """Konfiguration für eine einzelne Referenzlinie."""
        frame = QFrame()
        frame.setStyleSheet("QFrame { border: 1px solid #ccc; border-radius: 5px; padding: 10px; }")
        layout = QFormLayout(frame)
        
        # Header
        header = QLabel(f"Linie {line_index + 1}")
        header.setFont(QFont("", 12, QFont.Weight.Bold))
        layout.addRow(header)
        
        # Widgets für diese Linie
        widgets = {}
        
        # Aktiviert
        widgets['enabled'] = QCheckBox("Linie aktivieren")
        layout.addRow(widgets['enabled'])
        
        # Typ
        widgets['type'] = QComboBox()
        widgets['type'].addItems(["horizontal", "vertical"])
        layout.addRow("Richtung:", widgets['type'])
        
        # Position
        widgets['position'] = QDoubleSpinBox()
        widgets['position'].setRange(0, 100)
        widgets['position'].setDecimals(1)
        widgets['position'].setSingleStep(0.1)        
        widgets['position'].setSuffix(" %")
        layout.addRow("Position (0-100%):", widgets['position'])
        
        # Farbe
        widgets['color'] = QComboBox()
        widgets['color'].addItems(["red", "green", "blue", "yellow", "cyan", "magenta", "white", "orange"])
        layout.addRow("Farbe:", widgets['color'])
        
        # Dicke
        widgets['thickness'] = QDoubleSpinBox()
        widgets['thickness'].setRange(0.5, 10.0)
        widgets['thickness'].setDecimals(1)
        widgets['thickness'].setSingleStep(0.1)
        widgets['thickness'].setSuffix(" px")
        layout.addRow("Dicke:", widgets['thickness'])

        # Transparenz
        widgets['alpha'] = QSpinBox()
        widgets['alpha'].setRange(0, 255)
        layout.addRow("Transparenz (0-255):", widgets['alpha'])        
        
        self.reference_line_widgets.append(widgets)
        return frame
        
    def _create_interfaces_tab(self):
        """Tab 4: 🔌 Schnittstellen (ehemals Hardware)"""
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
        
        # MODBUS-Einstellungen
        self._add_section_header(layout, "🔌 WAGO Modbus-Schnittstelle")
        
        # IP-Adresse (nur Anzeige)
        self.modbus_ip_input = QLabel()
        self.modbus_ip_input.setStyleSheet(
            "background-color: #f0f0f0; padding: 5px; border-radius: 3px; color: #2c3e50;"
        )

        # Modbus IP-Adresse editierbar
        self.modbus_ip_input = QLineEdit()
        self.modbus_ip_input.setPlaceholderText("xxx.xxx.xxx.xxx")
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
        layout.addRow("Modbus IP: (nach Neustart übernommen)", self.modbus_ip_input)
        
        # NEU: Port editierbar (nur wenn getrennt)
        modbus_port_info = self._create_info_label(
            "Modbus-TCP Port des WAGO Controllers (Standard: 502). Aenderungen sind nur moeglich, wenn die Modbus-Verbindung getrennt ist.\nEine Aenderung der IP-Adresse oder des Ports erfordert einen Neustart der Anwendung, um wirksam zu werden."
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
        self.modbus_reset_btn.setToolTip("WAGO Controller zurücksetzen (Admin-Rechte erforderlich)")
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
        modbus_status_info = QLabel("Diese Aktionen sind nur für Administratoren verfügbar und helfen bei Verbindungsproblemen.")
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
            "Speichert Bilder zur späteren Analyse oder Dokumentation. "
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
        self.max_images_spin.setRange(1, 100000)
        self.max_images_spin.setSingleStep(1000)
        self.max_images_spin.setValue(10000)
        layout.addRow("Max. Dateien pro Verzeichnis:", self.max_images_spin)
        
        self._add_spacer(layout)
        
        # Helligkeitsüberwachung
        self._add_section_header(layout, "💡 Helligkeitsüberwachung")
        
        # Helligkeitsüberwachung Info
        brightness_info = self._create_info_label(
            "Überwacht die Bildhelligkeit und stoppt die Erkennung automatisch bei schlechten Lichtverhältnissen. "
            "Verhindert fehlerhafte Erkennungen durch zu dunkle oder überbelichtete Bilder."
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
    
    def _add_section_header(self, layout, title):
        header = QLabel(title)

        # Palette aus App-Theme ziehen
        palette = QApplication.instance().palette()
        header.setPalette(palette)
        header.setAutoFillBackground(True)

        header.setFont(QFont("", 12, QFont.Weight.Bold))
        layout.addRow(header)
    
    def _add_spacer(self, layout):
        """Trennlinie hinzufügen."""
        spacer = QFrame()
        spacer.setFrameShape(QFrame.Shape.HLine)
        spacer.setFrameShadow(QFrame.Shadow.Sunken)
        spacer.setStyleSheet("color: #bdc3c7; margin: 10px 0;")
        layout.addRow(spacer)

    def _add_cycle_arrow(self, layout, loop=False):
        """Pfeil zur Visualisierung des Arbeitszyklus hinzufügen."""
        arrow = QLabel("↓" if not loop else "↻")
        arrow.setAlignment(Qt.AlignmentFlag.AlignCenter)
        arrow.setStyleSheet("color: #7f8c8d; font-size: 16px; margin: 0;")
        layout.addRow(arrow)
    
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
    
    # =============================================================================
    # ERWEITERTE KLASSENZUTEILUNG - TABELLEN-MANAGEMENT
    # =============================================================================
    
    def add_class_assignment(self):
        """Neue Klassenzeile hinzufügen."""
        if not self.class_names:
            QMessageBox.warning(self, "Keine Klassen", "Bitte laden Sie zuerst ein Modell mit Klassen.")
            return
        
        # Verfügbare Klassen finden (noch nicht in Tabelle)
        used_classes = set()
        for row in range(self.class_assignments_table.rowCount()):
            class_item = self.class_assignments_table.item(row, 0)
            if class_item:
                # Extrahiere Class ID aus Text wie "person (ID: 0)"
                try:
                    text = class_item.text()
                    if "(ID: " in text:
                        class_id = int(text.split("(ID: ")[1].split(")")[0])
                        used_classes.add(class_id)
                except:
                    pass
        
        available_classes = [(id, name) for id, name in self.class_names.items() if id not in used_classes]
        
        if not available_classes:
            QMessageBox.information(self, "Alle Klassen zugewiesen", 
                                  "Alle verfügbaren Klassen sind bereits in der Tabelle.")
            return
        
        # Erste verfügbare Klasse verwenden
        class_id, class_name = available_classes[0]
        self._add_class_row(class_id, class_name, 'ignore', -1, 0.5, '#808080')
    
    def _add_class_row(self, class_id, class_name, assignment, expected_count, min_confidence, color):
        """Einzelne Klassenzeile zur Tabelle hinzufügen."""
        row = self.class_assignments_table.rowCount()
        self.class_assignments_table.insertRow(row)
        
        # Spalte 0: Klassename (nicht editierbar)
        name_item = QTableWidgetItem(f"{class_name} (ID: {class_id})")
        name_item.setFlags(name_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        self.class_assignments_table.setItem(row, 0, name_item)
        
        # Spalte 1: Zuteilung (ComboBox)
        assignment_combo = QComboBox()
        assignment_combo.addItems(["ignore", "good", "bad"])
        assignment_combo.setCurrentText(assignment)
        self.class_assignments_table.setCellWidget(row, 1, assignment_combo)
        
        # Spalte 2: Erwartete Anzahl (SpinBox)
        count_spin = QSpinBox()
        count_spin.setRange(-1, 100)
        count_spin.setSpecialValueText("beliebig")
        count_spin.setValue(expected_count)
        self.class_assignments_table.setCellWidget(row, 2, count_spin)
        
        # Spalte 3: Min. Konfidenz (DoubleSpinBox)
        conf_spin = QDoubleSpinBox()
        conf_spin.setRange(0.1, 1.0)
        conf_spin.setSingleStep(0.1)
        conf_spin.setDecimals(2)
        conf_spin.setValue(min_confidence)
        self.class_assignments_table.setCellWidget(row, 3, conf_spin)
        
        # Spalte 4: Farbe (Button)
        color_btn = QPushButton()
        color_btn.setStyleSheet(f"background-color: {color}; min-height: 25px;")
        color_btn.clicked.connect(lambda: self._select_color_for_row(row))
        self.class_assignments_table.setCellWidget(row, 4, color_btn)
    
    def _select_color_for_row(self, row):
        """Farbauswahl für bestimmte Zeile."""
        # Einfache Farbauswahl aus vordefinierten Farben
        from PyQt6.QtWidgets import QInputDialog
        
        colors = {
            "Rot": "#FF0000",
            "Grün": "#00FF00", 
            "Blau": "#0000FF",
            "Gelb": "#FFFF00",
            "Magenta": "#FF00FF",
            "Cyan": "#00FFFF",
            "Orange": "#FFA500",
            "Lila": "#800080",
            "Pink": "#FFC0CB",
            "Braun": "#A52A2A",
            "Grau": "#808080",
            "Schwarz": "#000000",
            "Weiß": "#FFFFFF"
        }
        
        color_name, ok = QInputDialog.getItem(
            self, "Farbe wählen", "Wählen Sie eine Farbe:", 
            list(colors.keys()), 0, False
        )
        
        if ok and color_name:
            color_hex = colors[color_name]
            color_btn = self.class_assignments_table.cellWidget(row, 4)
            if color_btn:
                color_btn.setStyleSheet(f"background-color: {color_hex}; min-height: 25px;")
    
    def remove_class_assignment(self):
        """Ausgewählte Klassenzeile entfernen."""
        current_row = self.class_assignments_table.currentRow()
        if current_row >= 0:
            self.class_assignments_table.removeRow(current_row)
    
    def reset_class_assignments(self):
        """Klassenzuteilungen zurücksetzen."""
        reply = QMessageBox.question(
            self, "Zurücksetzen", 
            "Alle Klassenzuteilungen zurücksetzen?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.class_assignments_table.setRowCount(0)
    
    # =============================================================================
    # MODBUS-AKTIONS-HANDLER
    # =============================================================================
    
    def handle_modbus_reset(self):
        """WAGO Controller Reset aus Einstellungen."""
        # Prüfe Admin-Rechte
        if not hasattr(self.parent_app, 'app') or not self.parent_app.app.user_manager.is_admin():
            QMessageBox.warning(
                self,
                "Zugriff verweigert",
                "Admin-Rechte erforderlich für Controller-Reset."
            )
            return
        
        # Bestätigung anfordern
        reply = QMessageBox.question(
            self,
            "Controller Reset",
            "WAGO Controller zurücksetzen?\n\nDies kann Verbindungsprobleme beheben.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                if self.parent_app.app.modbus_manager.restart_controller():
                    QMessageBox.information(
                        self,
                        "Reset erfolgreich",
                        "WAGO Controller wurde zurückgesetzt.\nVerbindung wird neu aufgebaut..."
                    )
                    # Automatische Neuverbindung nach Reset
                    self.handle_modbus_reconnect()
                else:
                    QMessageBox.critical(
                        self,
                        "Reset fehlgeschlagen",
                        "Controller-Reset konnte nicht durchgeführt werden.\nPrüfen Sie die Verbindung."
                    )
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Fehler",
                    f"Fehler beim Controller-Reset:\n{str(e)}"
                )
    
    def handle_modbus_reconnect(self):
        """Modbus Neuverbindung aus Einstellungen."""
        # Prüfe Admin-Rechte
        if not hasattr(self.parent_app, 'app') or not self.parent_app.app.user_manager.is_admin():
            QMessageBox.warning(
                self,
                "Zugriff verweigert",
                "Admin-Rechte erforderlich für Neuverbindung."
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
                    "Modbus-Neuverbindung konnte nicht hergestellt werden.\nPrüfen Sie die Netzwerkverbindung."
                )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Fehler",
                f"Fehler bei Neuverbindung:\n{str(e)}"
            )
    
    def update_modbus_connection_status(self, connected):
        """Modbus-Verbindungsstatus in den Buttons aktualisieren."""
        # Buttons nur aktivieren wenn Admin, verbunden und Detection nicht läuft
        is_admin = hasattr(self.parent_app, 'app') and self.parent_app.app.user_manager.is_admin()
        detection_running = hasattr(self.parent_app, 'app') and self.parent_app.app.running
        enabled = is_admin and not detection_running

        self.modbus_reset_btn.setEnabled(enabled)
        self.modbus_reconnect_btn.setEnabled(enabled)

        # Tooltips entsprechend aktualisieren
        if detection_running:
            hint = " (gesperrt während Detection)"
        else:
            hint = ""

        if connected:
            self.modbus_reset_btn.setToolTip(f"WAGO Controller zurücksetzen (Admin){hint}")
            self.modbus_reconnect_btn.setToolTip(f"Modbus neu verbinden (Admin){hint}")
        else:
            self.modbus_reset_btn.setToolTip(f"WAGO Controller zurücksetzen (Admin) - GETRENNT{hint}")
            self.modbus_reconnect_btn.setToolTip(f"Modbus neu verbinden (Admin) - GETRENNT{hint}")

    def start_motion_calibration(self):
        """Kalibrierung der Bewegungserkennung starten."""
        duration = self.motion_learning_spin.value()
        if hasattr(self.parent_app, 'app'):
            self.parent_app.app.motion_manager.start_calibration(duration)
        QMessageBox.information(
            self,
            "Kalibrierung gestartet",
            f"Die Kalibrierung läuft nun für {duration:.0f} Sekunden."
        )

    # =============================================================================
    # EVENT HANDLER-METHODEN
    # =============================================================================
    
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
    
    def load_settings(self):
        """Aktuelle Einstellungen laden."""
        # Allgemein
        self.motion_threshold_spin.setValue(self.settings.get('motion_threshold', 110))
        self.settling_time_spin.setValue(self.settings.get('settling_time', 1.0))
        self.capture_time_spin.setValue(self.settings.get('capture_time', 3.0))
        self.reject_coil_duration_spin.setValue(self.settings.get('reject_coil_duration_seconds', 1.0))
        self.wait_after_blow_off_time_spin.setValue(self.settings.get('wait_after_blow_off_time', 0.5))
        self.motion_learning_spin.setValue(self.settings.get('motion_learning_seconds', 60.0))
        
        # Erweiterte Klassenzuteilungen laden
        self._load_class_assignments()
        
        # Referenzlinien laden
        self._load_reference_lines()
        
        # Schnittstellen
        camera_config_path = self.settings.get('camera_config_path', '')
        if camera_config_path:
            self.camera_config_path_label.setText(camera_config_path)
        else:
            self.camera_config_path_label.setText("Keine Konfiguration ausgewählt")
        
        # MODBUS: IP aus aktuellem Modbus-Manager lesen
        ip_value = self.settings.get('modbus_ip', '192.168.1.100')
        detection_running = False
        if hasattr(self.parent_app, 'app'):
            ip_value = self.parent_app.app.modbus_manager.ip_address
            detection_running = self.parent_app.app.running

        self.modbus_ip_input.setText(ip_value)
        self.modbus_ip_input.setEnabled(not detection_running)

        self.modbus_port_spin.setValue(self.settings.get('modbus_port', 502))
        self.modbus_port_spin.setEnabled(not detection_running)
        
        # Modbus-Buttons je nach Admin- und Detection-Status aktualisieren
        if hasattr(self.parent_app, 'app'):
            is_connected = self.parent_app.app.modbus_manager.is_connected()
            self.update_modbus_connection_status(is_connected)
        
        # Speicherung & Überwachung
        self.save_bad_images_check.setChecked(self.settings.get('save_bad_images', False))
        self.save_good_images_check.setChecked(self.settings.get('save_good_images', False))
        self.bad_images_dir_input.setText(self.settings.get('bad_images_directory', 'bad_images'))
        self.good_images_dir_input.setText(self.settings.get('good_images_directory', 'good_images'))
        self.max_images_spin.setValue(self.settings.get('max_image_files', 100000))
        
        self.brightness_low_spin.setValue(self.settings.get('brightness_low_threshold', 30))
        self.brightness_high_spin.setValue(self.settings.get('brightness_high_threshold', 220))
        self.brightness_duration_spin.setValue(self.settings.get('brightness_duration_threshold', 3.0))
    
    def _load_class_assignments(self):
        """Erweiterte Klassenzuteilungen in die Tabelle laden."""
        self.class_assignments_table.setRowCount(0)
        
        class_assignments = self.settings.get('class_assignments', {})
        
        if not class_assignments and self.class_names:
            # Fallback: Migration von alten Einstellungen
            self.settings.migrate_legacy_settings()
            class_assignments = self.settings.get('class_assignments', {})
        
        # Lade Daten in Tabelle
        for class_id_str, assignment_data in class_assignments.items():
            try:
                class_id = int(class_id_str)
                if class_id in self.class_names:
                    class_name = self.class_names[class_id]
                    assignment = assignment_data.get('assignment', 'ignore')
                    expected_count = assignment_data.get('expected_count', -1)
                    min_confidence = assignment_data.get('min_confidence', 0.5)
                    color = assignment_data.get('color', '#808080')
                    
                    self._add_class_row(class_id, class_name, assignment, expected_count, min_confidence, color)
            except (ValueError, KeyError):
                continue
    
    def _load_reference_lines(self):
        """Referenzlinien-Einstellungen laden."""
        reference_lines = self.settings.get('reference_lines', [])
        
        for i, line_config in enumerate(reference_lines[:4]):  # Max 4 Linien
            if i < len(self.reference_line_widgets):
                widgets = self.reference_line_widgets[i]
                
                widgets['enabled'].setChecked(line_config.get('enabled', False))
                widgets['type'].setCurrentText(line_config.get('type', 'horizontal'))
                widgets['position'].setValue(line_config.get('position', 50.0))
                widgets['color'].setCurrentText(line_config.get('color', 'red'))
                widgets['thickness'].setValue(line_config.get('thickness', 2.0))
                widgets['alpha'].setValue(line_config.get('alpha', 200))
    
    def save_settings(self):
        """Einstellungen speichern."""
        # Allgemein
        self.settings.set('motion_threshold', self.motion_threshold_spin.value())
        self.settings.set('settling_time', self.settling_time_spin.value())
        self.settings.set('capture_time', self.capture_time_spin.value())
        self.settings.set('reject_coil_duration_seconds', self.reject_coil_duration_spin.value())
        self.settings.set('wait_after_blow_off_time', self.wait_after_blow_off_time_spin.value())
        self.settings.set('motion_learning_seconds', self.motion_learning_spin.value())
        
        # Erweiterte Klassenzuteilungen speichern
        self._save_class_assignments()
        
        # Referenzlinien speichern
        self._save_reference_lines()
        
        # Schnittstellen
        camera_config_text = self.camera_config_path_label.text()
        if camera_config_text == "Keine Konfiguration ausgewählt":
            self.settings.set('camera_config_path', '')
        else:
            self.settings.set('camera_config_path', camera_config_text)
        
        # MODBUS: Nur IP speichern
        self.settings.set('modbus_ip', self.modbus_ip_input.text())
        
        # Speicherung & Überwachung
        self.settings.set('save_bad_images', self.save_bad_images_check.isChecked())
        self.settings.set('save_good_images', self.save_good_images_check.isChecked())
        self.settings.set('bad_images_directory', self.bad_images_dir_input.text())
        self.settings.set('good_images_directory', self.good_images_dir_input.text())
        self.settings.set('max_image_files', self.max_images_spin.value())
        # Helligkeitsüberwachung
        self.settings.set('brightness_low_threshold', self.brightness_low_spin.value())
        self.settings.set('brightness_high_threshold', self.brightness_high_spin.value())
        self.settings.set('brightness_duration_threshold', self.brightness_duration_spin.value())
        
        self.settings.save()
        # Apply changes immediately to running engine and image saver
        if self.parent_app and hasattr(self.parent_app, "app"):
            app = self.parent_app.app
            if hasattr(app, "image_saver"):
                app.image_saver.update_settings(self.settings.data)            
            if hasattr(app, "detection_engine") and app.detection_engine.model_loaded:
                app.apply_class_settings_to_engine()
                threshold = self.settings.get('confidence_threshold', 0.5)
                app.detection_engine.set_confidence_threshold(threshold)
        self.accept()
    
    def _save_class_assignments(self):
        """Klassenzuteilungen aus Tabelle speichern."""
        class_assignments = {}
        
        for row in range(self.class_assignments_table.rowCount()):
            try:
                # Extrahiere Class ID aus Klassename
                name_item = self.class_assignments_table.item(row, 0)
                if not name_item:
                    continue
                
                text = name_item.text()
                if "(ID: " not in text:
                    continue
                
                class_id = int(text.split("(ID: ")[1].split(")")[0])
                
                # Hole Werte aus Widgets
                assignment_combo = self.class_assignments_table.cellWidget(row, 1)
                count_spin = self.class_assignments_table.cellWidget(row, 2)
                conf_spin = self.class_assignments_table.cellWidget(row, 3)
                color_btn = self.class_assignments_table.cellWidget(row, 4)
                
                if not all([assignment_combo, count_spin, conf_spin, color_btn]):
                    continue
                
                # Extrahiere Farbe aus Button-Style
                style = color_btn.styleSheet()
                color = '#808080'  # Default
                if 'background-color:' in style:
                    try:
                        color = style.split('background-color:')[1].split(';')[0].strip()
                    except:
                        pass
                
                class_assignments[str(class_id)] = {
                    'assignment': assignment_combo.currentText(),
                    'expected_count': count_spin.value(),
                    'min_confidence': conf_spin.value(),
                    'color': color
                }
                
            except (ValueError, AttributeError) as e:
                continue
        
        self.settings.set('class_assignments', class_assignments)
    
    def _save_reference_lines(self):
        """Referenzlinien-Konfiguration speichern."""
        reference_lines = []
        
        for widgets in self.reference_line_widgets:
            line_config = {
                'enabled': widgets['enabled'].isChecked(),
                'type': widgets['type'].currentText(),
                'position': widgets['position'].value(),
                'color': widgets['color'].currentText(),
                'thickness': widgets['thickness'].value(),
                'alpha': widgets['alpha'].value()
            }
            reference_lines.append(line_config)
        
        self.settings.set('reference_lines', reference_lines)
        
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