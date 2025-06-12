"""
Dialog-Komponenten für Kamera-Auswahl und Einstellungen
Alle Dialog-Fenster der Anwendung mit Tab-basiertem Layout und erweiterter tabellarischer Klassenzuteilung
ERWEITERT: Tabellarische Klassenzuteilung mit Gut/Schlecht, Anzahl, Farbe und Konfidenz in einem Tab
"""

import os
import logging

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
    QFrame, QFileDialog, QSpinBox, QDoubleSpinBox, QCheckBox, 
    QFormLayout, QMessageBox, QListWidget, QTabWidget, QWidget,
    QScrollArea, QSizePolicy, QComboBox, QApplication, QColorDialog,
    QGridLayout, QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QLineEdit, QSlider
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
    """Tab-basierter Einstellungen-Dialog mit erweiterter tabellarischer Klassenzuteilung."""
    
    def __init__(self, settings, class_names=None, parent=None):
        super().__init__(parent)
        self.settings = settings
        self.class_names = class_names or {}  # Dictionary {id: name}
        self.parent_app = parent  # Referenz zur Hauptanwendung für Modbus-Funktionen
        self.setWindowTitle("⚙️ Einstellungen")
        self.setModal(True)
        self.resize(1000, 900)  # Breiter für Tabelle
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.FramelessWindowHint)

        # Vordefinierte Farben für Klassen
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
        
        # Migration ausführen falls nötig
        self.settings.migrate_legacy_settings()
        
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
        self._create_advanced_class_assignment_tab()  # NEUER erweiterte Klassen-Tab
        self._create_interfaces_tab()
        self._create_storage_monitoring_tab()
        self._create_reference_lines_tab()  # Referenzlinien in eigenen Tab
        
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
        self._add_spacer(layout)

        # Motion Decay - MIT INFO
        motion_decay_info = self._create_info_label(
            "Abklingfaktor für die Motion-Anzeige. Bestimmt, wie schnell der angezeigte Motion-Wert "
            "nach dem Ende einer Bewegung abfällt. Höhere Werte = langsameres Abklingen (träger), "
            "niedrigere Werte = schnelleres Abklingen (reaktiver)."
        )
        layout.addRow(motion_decay_info)
        
        self.motion_decay_spin = QDoubleSpinBox()
        self.motion_decay_spin.setRange(0.001, 0.999)
        self.motion_decay_spin.setSingleStep(0.001)
        self.motion_decay_spin.setDecimals(3)
        layout.addRow("Motion Abklingfaktor (0.001-0.999):", self.motion_decay_spin)
        self._add_spacer(layout)

        # Allgemeine Konfidenz - MIT INFO
        general_conf_info = self._create_info_label(
            "Grundschwellwert für alle KI-Erkennungen. Nur Erkennungen über diesem Wert werden berücksichtigt. "
            "Höhere Werte = weniger falsche Erkennungen, aber eventuell werden echte Objekte übersehen."
        )
        layout.addRow(general_conf_info)
        
        self.confidence_spin = QDoubleSpinBox()
        self.confidence_spin.setRange(0.1, 1.0)
        self.confidence_spin.setSingleStep(0.1)
        self.confidence_spin.setDecimals(2)
        layout.addRow("Allgemeine Konfidenz-Schwelle:", self.confidence_spin)
        self._add_spacer(layout)

        # Roter Rahmen Schwellwert - MIT INFO
        red_info = self._create_info_label(
            "Mindestanzahl von schlechten Teilen, ab der der rote Rahmen angezeigt wird. "
            "Bestimmt, wann ein Ausschuss-Signal ausgelöst wird."
        )
        layout.addRow(red_info)
        
        self.red_threshold_spin = QSpinBox()
        self.red_threshold_spin.setRange(1, 20)
        layout.addRow("Roter Rahmen Schwellwert:", self.red_threshold_spin)
        self._add_spacer(layout)
        
        # Grüner Rahmen Schwellwert - MIT INFO
        green_info = self._create_info_label(
            "Mindestanzahl von guten Teilen, ab der der grüne Rahmen angezeigt wird. "
            "Bestätigt, dass ausreichend gute Teile erkannt wurden."
        )
        layout.addRow(green_info)
        
        self.green_threshold_spin = QSpinBox()
        self.green_threshold_spin.setRange(1, 20)
        layout.addRow("Grüner Rahmen Schwellwert:", self.green_threshold_spin)
        self._add_spacer(layout)
        
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
        self._add_spacer(layout)

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
        self._add_spacer(layout)
        
        # Abblas-Wartezeit - MIT INFO
        blow_off_info = self._create_info_label(
            "Wartezeit nach Ausschuss-Signal, bevor der nächste Zyklus beginnt. "
            "Muss lang genug sein, damit das Abblasen vollständig beendet ist. "
        )
        layout.addRow(blow_off_info)
        
        self.blow_off_time_spin = QDoubleSpinBox()
        self.blow_off_time_spin.setRange(1.0, 30.0)
        self.blow_off_time_spin.setSingleStep(0.5)
        layout.addRow("Abblas-Wartezeit (Sekunden):", self.blow_off_time_spin)
        self._add_spacer(layout)
        
        self.tab_widget.addTab(scroll, "⚙️ Allgemein")
    
    def _create_advanced_class_assignment_tab(self):
        """Tab 2: 🎯 Erweiterte Klassen-Zuteilung - TABELLARISCH mit allen Funktionen"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(20)
        
        # Header
        header_label = QLabel("🎯 Erweiterte Klassen-Zuteilung")
        header_label.setFont(QFont("", 16, QFont.Weight.Bold))
        layout.addWidget(header_label)
        
        # Info-Text
        info_text = self._create_info_label(
            "Konfigurieren Sie jede Klasse einzeln: Zuteilung (Gut/Schlecht/Ignorieren), erwartete Anzahl, "
            "Mindest-Konfidenz und Bounding Box-Farbe. Abweichungen von der erwarteten Anzahl bei Gut-Teilen "
            "können ebenfalls als Ausschuss behandelt werden."
        )
        layout.addWidget(info_text)
        
        # Tabelle für Klassenzuteilung
        self._create_class_assignment_table(layout)
        
        # Buttons unter der Tabelle
        button_layout = QHBoxLayout()
        
        self.add_class_btn = QPushButton("➕ Klasse hinzufügen")
        self.add_class_btn.clicked.connect(self.add_class_assignment)
        button_layout.addWidget(self.add_class_btn)
        
        self.remove_class_btn = QPushButton("➖ Klasse entfernen")
        self.remove_class_btn.clicked.connect(self.remove_class_assignment)
        button_layout.addWidget(self.remove_class_btn)
        
        button_layout.addStretch()
        
        self.reset_table_btn = QPushButton("🔄 Tabelle zurücksetzen")
        self.reset_table_btn.clicked.connect(self.reset_class_table)
        button_layout.addWidget(self.reset_table_btn)
        
        layout.addLayout(button_layout)
        
        # Legende
        legend_label = QLabel("""
        <b>Legende:</b><br>
        • <b>Zuteilung:</b> Gut = positive Teile, Schlecht = Ausschuss, Ignorieren = nicht bewerten<br>
        • <b>Erwartete Anzahl:</b> -1 = beliebig, >0 = exakte Anzahl erwartet<br>
        • <b>Konfidenz:</b> Mindest-Konfidenz für diese Klasse (überschreibt allgemeine Einstellung)<br>
        • <b>Farbe:</b> Bounding Box-Farbe für diese Klasse
        """)
        legend_label.setWordWrap(True)
        legend_label.setStyleSheet("color: #7f8c8d; font-size: 11px; background-color: #f8f9fa; padding: 10px; border-radius: 4px;")
        layout.addWidget(legend_label)
        
        self.tab_widget.addTab(tab, "🎯 Klassen-Zuteilung")
    
    def _create_class_assignment_table(self, layout):
        """Erstelle die Klassenzuteilungs-Tabelle."""
        self.class_table = QTableWidget(0, 5)
        self.class_table.setHorizontalHeaderLabels([
            "Klassename", "Zuteilung", "Erwartete Anzahl", "Min. Konfidenz", "Farbe"
        ])
        
        # Spaltenbreiten optimieren
        header = self.class_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)  # Klassename
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)  # Zuteilung
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # Anzahl
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # Konfidenz
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)  # Farbe
        
        # Tabellen-Eigenschaften
        self.class_table.setAlternatingRowColors(True)
        self.class_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.class_table.setMinimumHeight(300)
        
        # Style für bessere Sichtbarkeit
        self.class_table.setStyleSheet("""
            QTableWidget {
                gridline-color: #ddd;
                background-color: white;
                border: 1px solid #ccc;
                border-radius: 4px;
            }
            QHeaderView::section {
                background-color: #f0f0f0;
                border: 1px solid #ccc;
                padding: 8px;
                font-weight: bold;
            }
        """)
        
        layout.addWidget(self.class_table)
    
    def add_class_assignment(self):
        """Neue Klassenzuteilung hinzufügen."""
        # Verfügbare Klassen ermitteln (die noch nicht in der Tabelle sind)
        used_classes = set()
        for row in range(self.class_table.rowCount()):
            class_item = self.class_table.item(row, 0)
            if class_item and hasattr(class_item, 'class_id'):
                used_classes.add(class_item.class_id)
        
        available_classes = []
        for class_id, class_name in self.class_names.items():
            if class_id not in used_classes:
                available_classes.append((class_id, class_name))
        
        if not available_classes:
            QMessageBox.information(self, "Info", "Alle verfügbaren Klassen sind bereits zugewiesen.")
            return
        
        # Dialog zur Klassenwahl
        from PyQt6.QtWidgets import QInputDialog
        class_choices = [f"{name} (ID: {id})" for id, name in available_classes]
        choice, ok = QInputDialog.getItem(
            self, "Klasse auswählen", "Welche Klasse hinzufügen?", class_choices, 0, False
        )
        
        if ok and choice:
            # Extrahiere class_id aus der Auswahl
            selected_class_id = available_classes[class_choices.index(choice)][0]
            selected_class_name = available_classes[class_choices.index(choice)][1]
            
            # Neue Zeile hinzufügen
            self._add_table_row(selected_class_id, selected_class_name, 'ignore', -1, 0.5, '#808080')
    
    def remove_class_assignment(self):
        """Ausgewählte Klassenzuteilung entfernen."""
        current_row = self.class_table.currentRow()
        if current_row >= 0:
            self.class_table.removeRow(current_row)
        else:
            QMessageBox.information(self, "Info", "Bitte wählen Sie eine Zeile zum Entfernen aus.")
    
    def reset_class_table(self):
        """Tabelle zurücksetzen."""
        reply = QMessageBox.question(
            self, "Tabelle zurücksetzen", 
            "Alle Klassenzuteilungen zurücksetzen und von verfügbaren Klassen neu aufbauen?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.class_table.setRowCount(0)
            self._populate_table_from_available_classes()
    
    def _add_table_row(self, class_id, class_name, assignment, expected_count, min_confidence, color):
        """Füge eine Zeile zur Klassenzuteilungs-Tabelle hinzu."""
        row = self.class_table.rowCount()
        self.class_table.insertRow(row)
        
        # Klassename (nicht editierbar)
        name_item = QTableWidgetItem(f"{class_name} (ID: {class_id})")
        name_item.setFlags(name_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        name_item.class_id = class_id  # Speichere class_id als Attribut
        self.class_table.setItem(row, 0, name_item)
        
        # Zuteilung (ComboBox)
        assignment_combo = QComboBox()
        assignment_combo.addItems(["ignore", "good", "bad"])
        assignment_combo.setCurrentText(assignment)
        self.class_table.setCellWidget(row, 1, assignment_combo)
        
        # Erwartete Anzahl (SpinBox)
        count_spin = QSpinBox()
        count_spin.setRange(-1, 999)
        count_spin.setSpecialValueText("beliebig")
        count_spin.setValue(expected_count)
        self.class_table.setCellWidget(row, 2, count_spin)
        
        # Min. Konfidenz (DoubleSpinBox)
        conf_spin = QDoubleSpinBox()
        conf_spin.setRange(0.1, 1.0)
        conf_spin.setSingleStep(0.1)
        conf_spin.setDecimals(2)
        conf_spin.setValue(min_confidence)
        self.class_table.setCellWidget(row, 3, conf_spin)
        
        # Farbe (Button)
        color_btn = QPushButton()
        color_btn.setStyleSheet(f"background-color: {color}; min-height: 25px;")
        color_btn.clicked.connect(lambda: self._choose_color_for_row(row))
        color_btn.color_value = color
        self.class_table.setCellWidget(row, 4, color_btn)
    
    def _choose_color_for_row(self, row):
        """Farbauswahl für eine bestimmte Zeile."""
        # Hole aktuellen Color-Button
        color_btn = self.class_table.cellWidget(row, 4)
        if not color_btn:
            return
        
        # Dialog mit vordefinierten Farben
        from PyQt6.QtWidgets import QDialog, QGridLayout, QPushButton
        
        color_dialog = QDialog(self)
        color_dialog.setWindowTitle("Farbe auswählen")
        color_dialog.setModal(True)
        
        grid_layout = QGridLayout(color_dialog)
        
        # Vordefinierte Farben als Buttons
        for i, color in enumerate(self.predefined_colors):
            btn = QPushButton()
            btn.setStyleSheet(f"background-color: {color}; min-width: 40px; min-height: 40px; border: 2px solid #333;")
            btn.clicked.connect(lambda checked, c=color: self._set_color_and_close(color_btn, c, color_dialog))
            
            row_pos = i // 5
            col_pos = i % 5
            grid_layout.addWidget(btn, row_pos, col_pos)
        
        color_dialog.exec()
    
    def _set_color_and_close(self, color_btn, color, dialog):
        """Setze Farbe und schließe Dialog."""
        color_btn.setStyleSheet(f"background-color: {color}; min-height: 25px;")
        color_btn.color_value = color
        dialog.accept()
    
    def _populate_table_from_available_classes(self):
        """Befülle Tabelle mit allen verfügbaren Klassen."""
        for class_id, class_name in self.class_names.items():
            # Standard-Werte
            assignment = 'ignore'
            expected_count = -1
            min_confidence = 0.5
            color = self.predefined_colors[class_id % len(self.predefined_colors)]
            
            self._add_table_row(class_id, class_name, assignment, expected_count, min_confidence, color)
    
    def _create_interfaces_tab(self):
        """Tab 3: 🔌 Schnittstellen (ehemals Hardware)"""
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
        
        # INFO: Modbus ist immer aktiviert
        modbus_info = QLabel("Modbus ist für den Betrieb immer aktiviert.")
        modbus_info.setStyleSheet("color: #2c3e50; font-weight: bold; background-color: #ecf0f1; padding: 8px; border-radius: 4px;")
        layout.addRow(modbus_info)
        
        # IP-Adresse (nur Anzeige)
        self.modbus_ip_input = QLabel("192.168.1.100")
        self.modbus_ip_input.setStyleSheet(
            "background-color: #f0f0f0; padding: 5px; border-radius: 3px; color: #2c3e50;"
        )
        layout.addRow(modbus_info, self.modbus_ip_input)
        # Modbus IP-Adresse editierbar
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
        """Tab 4: 💾 Speicherung & Überwachung"""
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
        self.max_images_spin.setRange(1000, 500000)
        self.max_images_spin.setSingleStep(1000)
        self.max_images_spin.setValue(100000)
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
    
    def _create_reference_lines_tab(self):
        """Tab 5: 📏 Referenzlinien"""
        tab = QWidget()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(tab)
        
        layout = QVBoxLayout(tab)
        layout.setSpacing(20)
        
        # Header
        header_label = QLabel("📏 Referenzlinien-Konfiguration")
        header_label.setFont(QFont("", 16, QFont.Weight.Bold))
        layout.addWidget(header_label)
        
        # Info-Text
        info_text = self._create_info_label(
            "Konfigurieren Sie bis zu 4 Referenzlinien, die als Overlay über den Video-Stream gelegt werden. "
            "Diese helfen bei der visuellen Orientierung und zeigen optimale Objektpositionen an."
        )
        layout.addWidget(info_text)
        
        # Container für alle 4 Linien
        self.reference_line_widgets = []
        
        for i in range(4):
            line_group = self._create_reference_line_group(i + 1)
            layout.addWidget(line_group)
            
        layout.addStretch()
        
        self.tab_widget.addTab(scroll, "📏 Referenzlinien")
    
    def _create_reference_line_group(self, line_number):
        """Erstelle Gruppe für eine Referenzlinie."""
        group = QFrame()
        group.setStyleSheet("QFrame { border: 1px solid #ccc; border-radius: 5px; padding: 10px; }")
        
        layout = QFormLayout(group)
        
        # Header
        header = QLabel(f"Linie {line_number}")
        header.setFont(QFont("", 12, QFont.Weight.Bold))
        layout.addRow(header)
        
        # Enabled Checkbox
        enabled_check = QCheckBox("Aktiviert")
        layout.addRow("Status:", enabled_check)
        
        # Typ (Horizontal/Vertikal)
        type_combo = QComboBox()
        type_combo.addItems(["horizontal", "vertical"])
        layout.addRow("Typ:", type_combo)
        
        # Position (Slider + SpinBox kombiniert)
        position_layout = QHBoxLayout()
        position_slider = QSlider(Qt.Orientation.Horizontal)
        position_slider.setRange(0, 100)
        position_slider.setValue(50)
        position_layout.addWidget(position_slider, 3)
        
        position_spin = QSpinBox()
        position_spin.setRange(0, 100)
        position_spin.setSuffix("%")
        position_spin.setValue(50)
        position_layout.addWidget(position_spin, 1)
        
        # Slider und SpinBox verknüpfen
        position_slider.valueChanged.connect(position_spin.setValue)
        position_spin.valueChanged.connect(position_slider.setValue)
        
        layout.addRow("Position:", position_layout)
        
        # Farbe
        color_combo = QComboBox()
        color_combo.addItems(["red", "green", "blue", "yellow", "cyan", "magenta", "white", "orange"])
        layout.addRow("Farbe:", color_combo)
        
        # Dicke
        thickness_spin = QSpinBox()
        thickness_spin.setRange(1, 10)
        thickness_spin.setValue(2)
        layout.addRow("Dicke (Pixel):", thickness_spin)
        
        # Widgets speichern für späteren Zugriff
        widgets = {
            'enabled': enabled_check,
            'type': type_combo,
            'position_slider': position_slider,
            'position_spin': position_spin,
            'color': color_combo,
            'thickness': thickness_spin
        }
        
        self.reference_line_widgets.append(widgets)
        
        return group
    
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
    
    # Modbus-Aktions-Handler
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
    
    def update_modbus_connection_status(self, connected):
        """Update Modbus connection status for dialog buttons."""
        # Implementierung falls notwendig für zukünftige Erweiterungen
        pass
    
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
        self.confidence_spin.setValue(self.settings.get('confidence_threshold', 0.5))

        # Erweiterte Klassenzuteilung - Lade aus class_assignments
        self.class_table.setRowCount(0)  # Tabelle zurücksetzen
        
        class_assignments = self.settings.get('class_assignments', {})
        if class_assignments:
            # Lade aus neuer Struktur
            for class_id_str, assignment_data in class_assignments.items():
                try:
                    class_id = int(class_id_str)
                    if class_id in self.class_names:
                        class_name = self.class_names[class_id]
                        assignment = assignment_data.get('assignment', 'ignore')
                        expected_count = assignment_data.get('expected_count', -1)
                        min_confidence = assignment_data.get('min_confidence', 0.5)
                        color = assignment_data.get('color', '#808080')
                        
                        self._add_table_row(class_id, class_name, assignment, expected_count, min_confidence, color)
                except (ValueError, KeyError) as e:
                    logging.warning(f"Fehler beim Laden der Klassenzuteilung für {class_id_str}: {e}")
        else:
            # Fallback: Befülle mit allen verfügbaren Klassen
            self._populate_table_from_available_classes()
        
        # Schnittstellen
        camera_config_path = self.settings.get('camera_config_path', '')
        if camera_config_path:
            self.camera_config_path_label.setText(camera_config_path)
        else:
            self.camera_config_path_label.setText("Keine Konfiguration ausgewählt")
        
        # MODBUS: Nur IP und Dauer laden
        self.modbus_ip_input.setText(self.settings.get('modbus_ip', '192.168.1.100'))
        self.modbus_port_spin.setValue(self.settings.get('modbus_port', 502))
        self.reject_coil_duration_spin.setValue(self.settings.get('reject_coil_duration_seconds', 1.0))
        
        # Modbus-Buttons je nach Admin-Status aktivieren/deaktivieren
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
        
        # Referenzlinien
        reference_lines = self.settings.get('reference_lines', [])
        for i, line_config in enumerate(reference_lines):
            if i < len(self.reference_line_widgets):
                widgets = self.reference_line_widgets[i]
                widgets['enabled'].setChecked(line_config.get('enabled', False))
                widgets['type'].setCurrentText(line_config.get('type', 'horizontal'))
                position = line_config.get('position', 50)
                widgets['position_slider'].setValue(position)
                widgets['position_spin'].setValue(position)
                widgets['color'].setCurrentText(line_config.get('color', 'red'))
                widgets['thickness'].setValue(line_config.get('thickness', 2))
    
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
        self.settings.set('confidence_threshold', self.confidence_spin.value())
        
        # Erweiterte Klassenzuteilung - Speichere in class_assignments
        class_assignments = {}
        
        for row in range(self.class_table.rowCount()):
            # Hole class_id aus erstem Item
            name_item = self.class_table.item(row, 0)
            if not name_item or not hasattr(name_item, 'class_id'):
                continue
                
            class_id = name_item.class_id
            
            # Hole Widgets aus den Zellen
            assignment_combo = self.class_table.cellWidget(row, 1)
            count_spin = self.class_table.cellWidget(row, 2)
            conf_spin = self.class_table.cellWidget(row, 3)
            color_btn = self.class_table.cellWidget(row, 4)
            
            if all([assignment_combo, count_spin, conf_spin, color_btn]):
                class_assignments[str(class_id)] = {
                    'assignment': assignment_combo.currentText(),
                    'expected_count': count_spin.value(),
                    'min_confidence': conf_spin.value(),
                    'color': getattr(color_btn, 'color_value', '#808080')
                }
        
        self.settings.set('class_assignments', class_assignments)
        
        # Schnittstellen
        camera_config_text = self.camera_config_path_label.text()
        if camera_config_text == "Keine Konfiguration ausgewählt":
            self.settings.set('camera_config_path', '')
        else:
            self.settings.set('camera_config_path', camera_config_text)
        
        # MODBUS: Nur IP und Dauer speichern
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
        
        # Referenzlinien
        reference_lines = []
        for widgets in self.reference_line_widgets:
            line_config = {
                'enabled': widgets['enabled'].isChecked(),
                'type': widgets['type'].currentText(),
                'position': widgets['position_spin'].value(),
                'color': widgets['color'].currentText(),
                'thickness': widgets['thickness'].value()
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