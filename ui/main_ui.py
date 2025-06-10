"""
Hauptbenutzeroberflaeche - FINALE Version mit einheitlichen Status-Proportionen und rotem Blinken
Angepasst: Status-Titel ohne farbige Boxen, 1/3 zu 2/3 Proportionen, rotes Blinken bei Schlechtteilen
"""

import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
    QSplitter, QFrame, QTableWidget, QTableWidgetItem, QHeaderView, 
    QToolButton, QScrollArea, QMessageBox, QDialog
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPixmap, QFont
import cv2
import numpy as np
import logging

# Lokale Importe
from .dialogs import CameraSelectionDialog, SettingsDialog

class MainUI(QWidget):
    """Hauptbenutzeroberflaeche mit einheitlichen Status-Proportionen und rotem Blinken."""
    
    def __init__(self, parent_app):
        super().__init__()
        self.app = parent_app
        self.sidebar_visible = True
        self.brightness_warning_visible = False
        
        # Counter-Statistiken
        self.session_good_parts = 0
        self.session_bad_parts = 0
        self.session_total_cycles = 0
        
        # Rotes Blinken - Timer fuer Animation
        self.flash_timer = QTimer()
        self.flash_timer.timeout.connect(self._flash_step)
        self.flash_count = 0
        self.is_flashing = False
        
        self.setup_ui()
        
        # User Manager Signale verbinden fuer Auto-Updates
        if hasattr(self.app, 'user_manager'):
            self.app.user_manager.user_status_changed.connect(self.on_user_status_changed)
    
    def setup_ui(self):
        """UI aufbauen."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Splitter fuer Sidebar und Hauptbereich
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(self.splitter)
        
        # Sidebar erstellen
        sidebar = self.create_sidebar()
        
        # Hauptbereich erstellen
        main_area = self.create_main_area()
        
        # Zu Splitter hinzufuegen
        self.splitter.addWidget(sidebar)
        self.splitter.addWidget(main_area)
        
        # Groessenverhaeltnis setzen
        self.splitter.setSizes([350, 1000])
    
    def create_sidebar(self):
        """Kompakte Sidebar mit einheitlichen Status-Proportionen erstellen - OPTIMIERT für kleine Bildschirme."""
        self.sidebar = QFrame()
        self.sidebar.setStyleSheet("""
            QFrame {
                background-color: #2c3e50;
                color: white;
                border-radius: 4px;
            }
            QPushButton {
                background-color: #34495e;
                color: white;
                border: none;
                padding: 5px 15px;
                border-radius: 4px;
                font-size: 12px;
                font-weight: bold;
                min-height: 12px;
            }
            QPushButton:hover {
                background-color: #3498db;
            }
            QPushButton:pressed {
                background-color: #2980b9;
            }
            QPushButton:disabled {
                background-color: #7f8c8d;
                color: #bdc3c7;
            }
            QLabel {
                color: white;
                font-size: 12px;     /* REDUZIERT: Von 13px */
            }
        """)
        self.sidebar.setMinimumWidth(300)
        self.sidebar.setMaximumWidth(380)
        
        # KOMPAKTES Layout - REDUZIERTE Abstände
        sidebar_content = QWidget()
        layout = QVBoxLayout(sidebar_content)
        layout.setSpacing(15)  # REDUZIERT: Von 25 auf 15
        layout.setContentsMargins(15, 15, 15, 15)  # REDUZIERT: Von 20 auf 15
        
        # REIHENFOLGE (kompakter):
        # 1. Benutzer-Status
        self._create_login_status_section(layout)
        
        # 2. Aktionen
        self._create_actions_section(layout)
        
        # 3. KI-Modell
        self._create_model_status_section(layout)
        
        # 4. Kamera-Video
        self._create_camera_status_section(layout)
        
        # 5. Letzte Erkennung - KOMPAKTER
        self._create_stats_section(layout)
        
        # 6. Status Grenzwerte + WAGO Modbus - KOMPAKTER
        self._create_united_status_section(layout)
        
        # KEIN Stretch mehr - macht die Sidebar flexibler
        
        # 7. ESC Hinweis + Footer ganz unten - KOMPAKTER
        self._create_esc_hint(layout)
        
        # Content direkt zu Sidebar hinzufügen
        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.addWidget(sidebar_content)
            
        return self.sidebar

    def _create_login_status_section(self, layout):
        """Login-Status-Button - KOMPAKTER."""
        self.login_status_btn = QPushButton("Benutzerstatus: Operator")
        self.login_status_btn.setMinimumHeight(35)  # REDUZIERT: Von 45 auf 35
        self.login_status_btn.setStyleSheet("""
            QPushButton {
                background-color: #34495e;
                color: white;
                border: 2px solid #5d6d7e;
                padding: 5px 20px;
                border-radius: 4px;
                font-size: 14px;
                font-weight: bold;
                text-align: center;
            }
            QPushButton:hover {
                background-color: #3498db;
                border-color: #2e86de;
            }
            QPushButton:pressed {
                background-color: #2980b9;
            }
        """)
        self.login_status_btn.setToolTip("Klicken für Admin-Login/Logout")
        layout.addWidget(self.login_status_btn)

    def _create_model_status_section(self, layout):
        """KI-Modell Status-Button - KOMPAKTER."""
        self.model_btn = QPushButton("Kein Modell geladen")
        self.model_btn.setMinimumHeight(35)  # REDUZIERT: Von 45 auf 35
        self.model_btn.setStyleSheet("""
            QPushButton {
                background-color: #34495e;
                color: #bdc3c7;
                border: 2px solid #5d6d7e;
                padding: 5px 20px;
                border-radius: 4px;
                font-size: 12px;
                font-weight: bold;
                text-align: left;
            }
            QPushButton:hover {
                background-color: #3498db;
                border-color: #2e86de;
                color: white;
            }
            QPushButton:pressed {
                background-color: #2980b9;
            }
            QPushButton:disabled {
                background-color: #7f8c8d;
                color: #bdc3c7;
                border-color: #95a5a6;
            }
        """)
        self.model_btn.setToolTip("Klicken um Modell zu laden")
        layout.addWidget(self.model_btn)

    def _create_camera_status_section(self, layout):
        """Kamera-Video Status-Button - KOMPAKTER."""
        self.camera_btn = QPushButton("Modus wählen")
        self.camera_btn.setMinimumHeight(35)  # REDUZIERT: Von 45 auf 35
        self.camera_btn.setStyleSheet("""
            QPushButton {
                background-color: #34495e;
                color: #bdc3c7;
                border: 2px solid #5d6d7e;
                padding: 5px 20px;
                border-radius: 4px;
                font-size: 12px;
                font-weight: bold;
                text-align: left;
            }
            QPushButton:hover {
                background-color: #3498db;
                border-color: #2e86de;
                color: white;
            }
            QPushButton:pressed {
                background-color: #2980b9;
            }
            QPushButton:disabled {
                background-color: #7f8c8d;
                color: #bdc3c7;
                border-color: #95a5a6;
            }
        """)
        self.camera_btn.setToolTip("Klicken um Kamera oder Video auszuwählen")
        layout.addWidget(self.camera_btn)

    def _create_actions_section(self, layout):
        """Aktionen - KOMPAKTER."""
        actions_layout = QVBoxLayout()
        actions_layout.setSpacing(8)  # REDUZIERT: Von 12 auf 8

        self.start_btn = QPushButton("▶ Live Detection STARTEN")
        self.start_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                font-size: 14px;
                font-weight: bold;
                min-height: 30px;
                padding: 5px 20px;
                border-radius: 4px;
                color: white;
            }
            QPushButton:hover {
                background-color: #2ecc71;
            }
        """)
        actions_layout.addWidget(self.start_btn)
        
        self.snapshot_btn = QPushButton("Schnappschuss")
        self.snapshot_btn.setStyleSheet("""
            QPushButton {
                padding: 12px 20px;  /* REDUZIERT */
                border-radius: 4px;
                min-height: 25px;    /* NEU: Kleinere Mindesthöhe */
            }
        """)
        actions_layout.addWidget(self.snapshot_btn)
        layout.addLayout(actions_layout)

    def _create_stats_section(self, layout):
        """Statistiken - KOMPAKTER für kleine Bildschirme."""
        self.last_cycle_table = QTableWidget(0, 5)
        self.last_cycle_table.setHorizontalHeaderLabels(["Klasse", "Img", "Min", "Max", "Anz"])
        self.last_cycle_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.last_cycle_table.verticalHeader().hide()
        self.last_cycle_table.setMaximumHeight(160)  # REDUZIERT: Von 220 auf 160
        self.last_cycle_table.setMinimumHeight(120)  # REDUZIERT: Von 180 auf 120
        self.last_cycle_table.setStyleSheet("""
            QTableWidget {
                background: rgba(255, 255, 255, 0.05);
                color: #e2e8f0;
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 4px;
                font-size: 9px;      /* REDUZIERT: Von 10px */
                gridline-color: rgba(255, 255, 255, 0.1);
            }
            QHeaderView::section {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                        stop: 0 #4a5568, stop: 1 #2d3748);
                color: white;
                border: none;
                padding: 3px;        /* REDUZIERT: Von 4px */
                font-size: 9px;      /* REDUZIERT: Von 10px */
                font-weight: 600;
                text-transform: uppercase;
            }
            QTableWidget::item {
                padding: 2px 3px;   /* REDUZIERT */
                border: none;
            }
            QTableWidget::item:selected {
                background: rgba(255, 255, 255, 0.1);
            }
        """)
        layout.addWidget(self.last_cycle_table)

    def _create_united_status_section(self, layout):
        """VEREINT: Status Grenzwerte + WAGO Modbus - KOMPAKTER für kleine Bildschirme."""
        status_layout = QVBoxLayout()
        status_layout.setSpacing(8)  # REDUZIERT: Von 12 auf 8
        
        # Kompakte Hilfsfunktion für Status-Zeilen
        def _add_compact_status_row(label_text, value_widget, tooltip_text=""):
            row_layout = QHBoxLayout()
            row_layout.setSpacing(5)
            
            label = QLabel(label_text)
            label.setStyleSheet("color: white; background: transparent; font-size: 11px;")  # Kleinere Schrift
            if tooltip_text:
                label.setToolTip(tooltip_text)
            row_layout.addWidget(label, 1)
            
            value_widget.setStyleSheet(value_widget.styleSheet().replace("padding: 8px 15px", "padding: 6px 12px"))  # Kompakter
            row_layout.addWidget(value_widget, 2)
            
            status_layout.addLayout(row_layout)
        
        # --- STATUS GRENZWERTE TEIL - KOMPAKT ---
        
        # Workflow-Status
        self.workflow_info = QLabel("BEREIT")
        self.workflow_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.workflow_info.setStyleSheet("""
            background-color: #34495e;
            color: white;
            padding: 5px 12px;
            border-radius: 4px;
            font-weight: bold;
            font-size: 11px;
        """)
        _add_compact_status_row("Workflow:", self.workflow_info)
        
        # Motion-Wert
        self.motion_info = QLabel("--")
        self.motion_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.motion_info.setStyleSheet("""
            background-color: #34495e;
            padding: 5px 12px;
            border-radius: 4px;
            font-weight: bold;
            font-size: 11px;
            min-width: 50px;
        """)
        _add_compact_status_row("Bewegung:", self.motion_info)
        
        # Helligkeit
        self.brightness_info = QLabel("--")
        self.brightness_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.brightness_info.setStyleSheet("""
            background-color: #34495e;
            padding: 5px 12px;
            border-radius: 4px;
            font-weight: bold;
            font-size: 11px;
            min-width: 50px;
        """)
        _add_compact_status_row("Helligkeit:", self.brightness_info)
        
        # Helligkeitswarnung - KOMPAKTER
        self.brightness_warning = QLabel("Beleuchtung prüfen!")
        self.brightness_warning.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.brightness_warning.setStyleSheet("""
            background-color: #e74c3c;
            color: white;
            padding: 5px 12px;  /* REDUZIERT */
            border-radius: 4px;
            font-weight: bold;
            font-size: 10px;    /* REDUZIERT: Von 11px */
        """)
        self.brightness_warning.setVisible(False)
        status_layout.addWidget(self.brightness_warning)
        
        # --- WAGO MODBUS TEIL - KOMPAKT ---
        
        # WAGO Status
        self.modbus_status = QLabel("Getrennt")
        self.modbus_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.modbus_status.setStyleSheet("""
            background-color: #e74c3c;
            color: white;
            padding: 5px 12px;  /* REDUZIERT */
            border-radius: 4px;
            font-weight: bold;
            font-size: 10px;    /* REDUZIERT: Von 11px */
        """)
        _add_compact_status_row("WAGO:", self.modbus_status)
        
        # IP-Adresse
        self.modbus_ip = QLabel("192.168.1.100")
        self.modbus_ip.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.modbus_ip.setStyleSheet("""
            background-color: #34495e;
            padding: 5px 12px;  /* REDUZIERT */
            border-radius: 4px;
            font-size: 10px;    /* REDUZIERT: Von 11px */
        """)
        _add_compact_status_row("IP:", self.modbus_ip)
        
        # Coils - KOMPAKTER
        coils_layout = QHBoxLayout()
        coils_label = QLabel("Coils:")
        coils_label.setStyleSheet("color: white; background: transparent; font-size: 11px;")
        coils_layout.addWidget(coils_label, 1)
        
        coil_container = QWidget()
        coil_container_layout = QHBoxLayout(coil_container)
        coil_container_layout.setContentsMargins(0, 0, 0, 0)
        coil_container_layout.setSpacing(4)  # REDUZIERT: Von 5 auf 4
        
        # Kleinere Coil-Indikatoren
        self.reject_coil_indicator = QLabel("A")
        self.reject_coil_indicator.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.reject_coil_indicator.setFixedSize(18, 18)  # REDUZIERT: Von 22x22 auf 18x18
        self.reject_coil_indicator.setStyleSheet("""
            background-color: #7f8c8d;
            color: white;
            border-radius: 9px;  /* Angepasst an neue Größe */
            font-weight: bold;
            font-size: 8px;      /* REDUZIERT: Von 9px */
        """)
        self.reject_coil_indicator.setToolTip("Ausschuss Modbus Ausgang")
        coil_container_layout.addWidget(self.reject_coil_indicator)
        
        self.detection_coil_indicator = QLabel("P")
        self.detection_coil_indicator.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.detection_coil_indicator.setFixedSize(18, 18)  # REDUZIERT: Von 22x22 auf 18x18
        self.detection_coil_indicator.setStyleSheet("""
            background-color: #7f8c8d;
            color: white;
            border-radius: 9px;  /* Angepasst an neue Größe */
            font-weight: bold;
            font-size: 8px;      /* REDUZIERT: Von 9px */
        """)
        self.detection_coil_indicator.setToolTip("Detection Active Modbus Ausgang")
        coil_container_layout.addWidget(self.detection_coil_indicator)
        
        coil_container_layout.addStretch()
        coils_layout.addWidget(coil_container, 2)
        status_layout.addLayout(coils_layout)
        
        layout.addLayout(status_layout)

    def _create_esc_hint(self, layout):    
        # BEENDEN Button mit Bestätigungsdialog - KOMPAKTER
        self.quit_btn = QPushButton("SOFTWARE BEENDEN")
        self.quit_btn.setStyleSheet("""
            QPushButton {
                background-color: #152b4a;
                color: white;
                font-size: 12px;
                font-weight: bold;
                min-height: 20px;
                border: 2px solid #0d1b2e;
                padding: 10px 20px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #0d1b2e;
                border: 2px solid #0d1b2e;
            }
            QPushButton:pressed {
                background-color: #0d1b2e;
            }
        """)
        self.quit_btn.setToolTip("Anwendung beenden (ESC)")
        self.quit_btn.clicked.connect(self._confirm_quit)  # NEU: Bestätigungsdialog
        layout.addWidget(self.quit_btn)

        # ESC-Hinweis - KOMPAKTER
        esc_hint = QLabel("ESC = Applikation sofort Beenden")
        esc_hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        esc_hint.setStyleSheet("""
            color: #7f8c8d; 
            font-style: italic; 
            font-size: 10px;
            padding: 8px;
            margin: 8px 0;
        """)
        layout.addWidget(esc_hint)
        
        # INSPECTUBE Footer - KOMPAKTER
        self.footer_label = QPushButton("INSPECTUBE by Michel Marty")
        self.footer_label.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #7f8c8d;
                border: none;
                font-size: 10px;    
                padding: 8px; 
                text-align: center;
            }
            QPushButton:hover {
                color: #3498db;
            }
            QPushButton:pressed {
                color: #2980b9;
            }
        """)
        self.footer_label.setToolTip("Klicken für ein Lächeln 😊")
        self.footer_label.clicked.connect(self._show_smiley)
        layout.addWidget(self.footer_label)

    def _confirm_quit(self):
        """Bestätigungsdialog vor dem Beenden der Anwendung."""
        reply = QMessageBox.question(
            self,
            "Anwendung beenden",
            "Sind Sie sicher, dass Sie die Anwendung beenden möchten?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No  # Standard ist "Nein"
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # Hier die ursprüngliche Quit-Logik aufrufen
            if hasattr(self.app, 'quit_application'):
                self.app.quit_application()
            else:
                self.app.quit()

    def _show_smiley(self):
        """Zeigt einen kleinen Smiley wenn auf den Footer geklickt wird."""
        original_text = self.footer_label.text()
        self.footer_label.setText("INSPECTUBE by Michel Marty 😊")
        
        # Timer um nach 2 Sekunden zurückzusetzen
        QTimer.singleShot(2000, lambda: self.footer_label.setText(original_text))
    
    def on_user_status_changed(self, new_status):
        """Callback fuer User-Status-Änderungen."""
        self.update_user_interface()
        if new_status == "Operator":
            self.app.ui.show_status("Automatischer Logout - Operator-Modus", "warning")
    
    def create_main_area(self):
        """Hauptbereich mit optimiertem Header-Layout erstellen."""
        main_area = QFrame()
        # Standard-Styling fuer Main Area
        self.default_main_area_style = """
            QFrame {
                background-color: #ecf0f1;
                border-radius: 8px;
            }
        """
        main_area.setStyleSheet(self.default_main_area_style)
        
        layout = QVBoxLayout(main_area)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Header mit: [Menue-Button] [⚙️ Einstellungen] [Status] [Counter]
        header_layout = QHBoxLayout()
        header_layout.setSpacing(20)
        
        # 1. Sidebar Toggle Button (hoeher wie Status/Counter)
        self.sidebar_toggle_btn = QToolButton()
        self.sidebar_toggle_btn.setText("≡")
        self.sidebar_toggle_btn.setStyleSheet("""
            QToolButton {
                background-color: #3498db;
                color: white;
                border: none;
                font-size: 20px;
                padding: 8px;
                border-radius: 4px;
                min-width: 60px;
                min-height: 60px;
            }
            QToolButton:hover {
                background-color: #2980b9;
            }
        """)
        header_layout.addWidget(self.sidebar_toggle_btn, 0, Qt.AlignmentFlag.AlignLeft)
        
        # 2. Einstellungen-Button (hoeher wie Status/Counter)
        self.settings_btn = QPushButton("⚙️")
        self.settings_btn.setStyleSheet("""
            QPushButton {
                background-color: #8e44ad;
                color: white;
                border: none;
                font-size: 20px;
                padding: 8px;
                border-radius: 4px;
                min-width: 60px;
                min-height: 60px;
            }
            QPushButton:hover {
                background-color: #7d3c98;
            }
            QPushButton:pressed {
                background-color: #6c3483;
            }
            QPushButton:disabled {
                background-color: #7f8c8d;
                color: #bdc3c7;
            }
        """)
        self.settings_btn.setToolTip("Einstellungen (Admin-Rechte erforderlich)")
        header_layout.addWidget(self.settings_btn, 0, Qt.AlignmentFlag.AlignLeft)
        
        # 3. STATUS IN DER MITTE (zwischen Buttons und Counter)
        self.status_label = QLabel("Bereit")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setFont(QFont("", 16, QFont.Weight.Bold))
        self.status_label.setStyleSheet("""
            QLabel {
                background-color: #95a5a6;
                color: white;
                padding: 15px;
                border-radius: 8px;
            }
        """)
        header_layout.addWidget(self.status_label, 1)  # Stretch factor 1 fuer die Mitte
        
        # 4. KOMPAKTER COUNTER (rechts oben)
        self._create_compact_counter_section(header_layout)
        
        layout.addLayout(header_layout)
        
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
        self.video_label.setText("Kein Stream verfuegbar")
        layout.addWidget(self.video_label, 1)
        
        # Referenz fuer das Main Area Frame speichern (fuer Blinken)
        self.main_area_frame = main_area
        
        return main_area
    
    def _create_compact_counter_section(self, header_layout):
        """KOMPAKTER Counter-Sektion im Header erstellen"""
        from PyQt6.QtWidgets import QGraphicsDropShadowEffect, QWidget, QFrame, QHBoxLayout, QVBoxLayout, QLabel, QPushButton
        from PyQt6.QtCore import Qt
        from PyQt6.QtGui import QColor, QFont

        # Frame mit Schatten und Hintergrund
        self.counter_frame = QFrame()
        self.counter_frame.setStyleSheet("""
            QFrame {
                background-color: #34495e;
                border-radius: 8px;
                padding: 4px 8px;
            }
            QLabel {
                color: white;
                font-weight: bold;
                background: transparent;
            }
        """)
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(10)
        shadow.setColor(QColor(80, 80, 80, 80))
        shadow.setOffset(0, 2)
        self.counter_frame.setGraphicsEffect(shadow)

        # Hauptlayout ohne Raender, Platz zwischen Sektionen
        counter_layout = QHBoxLayout(self.counter_frame)
        counter_layout.setContentsMargins(0, 0, 0, 0)
        counter_layout.setSpacing(30)

        # Monospace-Font fuer Zahlen
        counter_font = QFont("Consolas", 28, QFont.Weight.Bold)
        if not counter_font.exactMatch():
            counter_font = QFont("Courier New", 28, QFont.Weight.Bold)

        def _add_spaced_section(title, count_attr, percent_attr, color):
            # Vertikales Layout mit minimalem Abstand
            container = QWidget()
            vbox = QVBoxLayout(container)
            vbox.setContentsMargins(0, 0, 0, 0)
            vbox.setSpacing(2)  # minimaler Abstand
            vbox.setAlignment(Qt.AlignmentFlag.AlignHCenter)

            lbl_title = QLabel(title)
            lbl_title.setFont(QFont("", 10, QFont.Weight.Bold))
            lbl_title.setStyleSheet(f"color: {color};")
            lbl_title.setAlignment(Qt.AlignmentFlag.AlignCenter)

            setattr(self, count_attr, QLabel("0"))
            lbl_count = getattr(self, count_attr)
            lbl_count.setFont(counter_font)
            lbl_count.setStyleSheet(f"color: {color};")
            lbl_count.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl_count.setMinimumWidth(120)

            setattr(self, percent_attr, QLabel("--"))
            lbl_percent = getattr(self, percent_attr)
            lbl_percent.setFont(QFont("", 16, QFont.Weight.Bold))
            lbl_percent.setStyleSheet(f"color: {color};")
            lbl_percent.setAlignment(Qt.AlignmentFlag.AlignCenter)

            # Widgets hinzufuegen mit minimalem Abstand
            vbox.addWidget(lbl_title)
            vbox.addWidget(lbl_count)
            vbox.addWidget(lbl_percent)

            counter_layout.addWidget(container)

        # Gesamtzyklen
        _add_spaced_section("Zyklen", "total_cycles_counter", "total_cycles_percent", "#7dcbff")
        # OK-Teile
        _add_spaced_section("OK", "good_parts_counter", "good_parts_percent", "#4fff98")
        # Nicht OK
        _add_spaced_section("Nicht OK", "bad_parts_counter", "bad_parts_percent", "#ff7e70")

        # Reset-Button nur fuer Admin
        self.reset_counter_btn = QPushButton("Reset")
        self.reset_counter_btn.setStyleSheet("""
            QPushButton {
                background-color: #7f8c8d;
                color: white;
                border: none;
                padding: 8px 12px;
                border-radius: 4px;
                font-size: 10px;
            }
            QPushButton:hover {
                background-color: #95a5a6;
            }
            QPushButton:disabled {
                background-color: #5d6d7e;
                color: #bdc3c7;
            }
        """)
        self.reset_counter_btn.clicked.connect(self.reset_session_counter)
        self.reset_counter_btn.setToolTip("Counter zuruecksetzen (Admin-Rechte erforderlich)")
        counter_layout.addWidget(self.reset_counter_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        # Hohe begrenzen
        self.counter_frame.setMaximumHeight(140)
        header_layout.addWidget(self.counter_frame, 0, Qt.AlignmentFlag.AlignRight)

    def update_counters_with_formatting(self, good_count, bad_count, total_count):
        """Counter mit Formatierung fuer grosse Zahlen aktualisieren."""
        # Zahlenformatierung mit Tausendertrennzeichen (optional)
        self.good_parts_counter.setText(f"{good_count:,}")
        self.bad_parts_counter.setText(f"{bad_count:,}")
        self.total_cycles_counter.setText(f"{total_count:,}")
        
        # Prozentanzeigen aktualisieren
        if total_count > 0:
            good_percent = round((good_count / total_count) * 100, 1)
            bad_percent = round((bad_count / total_count) * 100, 1)
            self.good_parts_percent.setText(f"{good_percent}%")
            self.bad_parts_percent.setText(f"{bad_percent}%")
        else:
            self.good_parts_percent.setText("--")
            self.bad_parts_percent.setText("--")
    
    def flash_red_on_bad_part_detection(self):
        """Startet rotes Blinken bei Schlecht-Teil-Erkennung."""
        if self.is_flashing:
            return  # Bereits am Blinken
        
        logging.info("Starte rotes Blinken bei Schlecht-Teil-Erkennung")
        self.is_flashing = True
        self.flash_count = 0
        
        # Timer fuer 100ms Intervalle (10 Blinks in 1 Sekunde)
        self.flash_timer.start(100)
    
    def _flash_step(self):
        """Ein Schritt des Blinkens (wird alle 100ms aufgerufen)."""
        if self.flash_count >= 10:  # 10 Blinks = 1 Sekunde
            # Blinken beenden
            self.flash_timer.stop()
            self.is_flashing = False
            self.flash_count = 0
            
            # Zurueck zu normalen Farben
            self._reset_flash_colors()
            return
        
        # Blinken zwischen rot und normal
        if self.flash_count % 2 == 0:
            # Rote Phase
            self._set_flash_red()
        else:
            # Normale Phase
            self._reset_flash_colors()
        
        self.flash_count += 1
    
    # MODBUS UI-Update-Methoden
    def update_modbus_status(self, connected, ip_address):
        """WAGO Modbus Status aktualisieren."""
        if connected:
            self.modbus_status.setText("Verbunden")
            self.modbus_status.setStyleSheet("""
                background-color: #27ae60;
                color: white;
                padding: 6px 15px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 11px;
            """)
        else:
            self.modbus_status.setText("Getrennt")
            self.modbus_status.setStyleSheet("""
                background-color: #e74c3c;
                color: white;
                padding: 6px 15px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 11px;
            """)
        
        self.modbus_ip.setText(ip_address)
    
    def update_coil_status(self, reject_active=False, detection_active=False):
        """Coil-Status-Indikatoren aktualisieren."""
        # Reject Coil (Ausschuss)
        if reject_active:
            self.reject_coil_indicator.setStyleSheet("""
                background-color: #e74c3c;
                color: white;
                border-radius: 11px;
                font-weight: bold;
                font-size: 9px;
            """)
        else:
            self.reject_coil_indicator.setStyleSheet("""
                background-color: #7f8c8d;
                color: white;
                border-radius: 11px;
                font-weight: bold;
                font-size: 9px;
            """)
        
        # Detection Active Coil
        if detection_active:
            self.detection_coil_indicator.setStyleSheet("""
                background-color: #27ae60;
                color: white;
                border-radius: 11px;
                font-weight: bold;
                font-size: 9px;
            """)
        else:
            self.detection_coil_indicator.setStyleSheet("""
                background-color: #7f8c8d;
                color: white;
                border-radius: 11px;
                font-weight: bold;
                font-size: 9px;
            """)
    
    # Standard UI-Update-Methoden
    def reset_session_counter(self):
        """Session-Counter zuruecksetzen - NEU: NUR FÜR ADMIN."""
        # Pruefe Admin-Rechte
        if not self.app.user_manager.can_reset_counter():
            self.show_status("Admin-Rechte erforderlich fuer Counter-Reset", "error")
            return
        
        # Bestaetigung anfordern
        reply = QMessageBox.question(
            self,
            "Counter zuruecksetzen",
            "Session-Counter auf Null zuruecksetzen?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.session_good_parts = 0
            self.session_bad_parts = 0
            self.session_total_cycles = 0
            self.update_counter_display()
            self.show_status("Session-Counter zurueckgesetzt", "info")
            logging.info("Session-Counter von Admin zurueckgesetzt")
    
    def update_counter_display(self):
        """Counter-Anzeige aktualisieren - ERWEITERT mit Prozentangaben."""
        self.good_parts_counter.setText(str(self.session_good_parts))
        self.bad_parts_counter.setText(str(self.session_bad_parts))
        self.total_cycles_counter.setText(str(self.session_total_cycles))
        
        # Prozentangaben berechnen
        if self.session_total_cycles > 0:
            good_percent = (self.session_good_parts / self.session_total_cycles) * 100
            bad_percent = (self.session_bad_parts / self.session_total_cycles) * 100
            
            self.good_parts_percent.setText(f"{good_percent:.1f}%")
            self.bad_parts_percent.setText(f"{bad_percent:.1f}%")
        else:
            self.good_parts_percent.setText("--")
            self.bad_parts_percent.setText("--")
    
    def increment_session_counters(self, bad_parts_detected):
        """Session-Counter nach Zyklus aktualisieren."""
        self.session_total_cycles += 1
        
        if bad_parts_detected:
            self.session_bad_parts += 1
            # Update Coil-Status fuer visuelles Feedback
            self.update_coil_status(reject_active=True, detection_active=True)
            
            # NEU: Rotes Blinken bei Schlecht-Teil-Erkennung
            self.flash_red_on_bad_part_detection()
        else:
            self.session_good_parts += 1
        
        self.update_counter_display()
    
    def toggle_sidebar(self):
        """Sidebar ein-/ausblenden."""
        if self.sidebar_visible:
            # Sidebar ausblenden
            self.splitter.setSizes([0, 1000])
            self.sidebar_visible = False
            self.sidebar_toggle_btn.setText("≡")
        else:
            # Sidebar einblenden
            self.splitter.setSizes([350, 1000])
            self.sidebar_visible = True
            self.sidebar_toggle_btn.setText("‹")
    
    def update_user_interface(self):
        """UI basierend auf Benutzerlevel aktualisieren."""
        user_level = self.app.user_manager.get_user_level_text()
        
        # NEU: Breiter Login-Status-Button aktualisieren
        self.login_status_btn.setText(user_level)
        
        if self.app.user_manager.is_admin():
            # Admin-Style: Gruen
            self.login_status_btn.setStyleSheet("""
                QPushButton {
                    background-color: #27ae60;
                    color: white;
                    border: 2px solid #229954;
                    padding: 15px 25px;
                    border-radius: 4px;
                    font-size: 16px;
                    font-weight: bold;
                    text-align: center;
                }
                QPushButton:hover {
                    background-color: #2ecc71;
                    border-color: #27ae60;
                }
                QPushButton:pressed {
                    background-color: #229954;
                }
            """)
            self.login_status_btn.setToolTip("Admin eingeloggt - Klicken fuer Logout")
        else:
            # Operator-Style: Grau
            self.login_status_btn.setStyleSheet("""
                QPushButton {
                    background-color: #34495e;
                    color: white;
                    border: 2px solid #5d6d7e;
                    padding: 15px 25px;
                    border-radius: 4px;
                    font-size: 16px;
                    font-weight: bold;
                    text-align: center;
                }
                QPushButton:hover {
                    background-color: #3498db;
                    border-color: #2e86de;
                }
                QPushButton:pressed {
                    background-color: #2980b9;
                }
            """)
            self.login_status_btn.setToolTip("Operator-Modus - Klicken fuer Admin-Login")
        
        # Buttons aktivieren/deaktivieren
        can_admin = self.app.user_manager.is_admin()
        self.model_btn.setEnabled(can_admin)
        self.camera_btn.setEnabled(can_admin)
        self.settings_btn.setEnabled(can_admin)  # NEU: Einstellungen-Button im Header
        
        # Reset-Button fuer Counter - NEU: NUR FÜR ADMIN
        self.reset_counter_btn.setEnabled(can_admin)
    
    def update_workflow_status(self, status):
        """Workflow-Status aktualisieren."""
        self.workflow_info.setText(status)
        
        # Farbe je nach Status
        colors = {
            'BEREIT': "#757575",      # Grau
            'BANDTAKT': '#757575',     # Grau  
            'AUSSCHWINGEN': "#757575",   # Grau
            'DETEKTION': "#23aeff",  # Blau
            'ABBLASEN': '#e74c3c'     # Rot
        }
        
        color = colors.get(status, '#34495e')
        self.workflow_info.setStyleSheet(f"""
            background-color: {color};
            color: white;
            padding: 8px 15px;
            border-radius: 4px;
            font-weight: bold;
        """)
    
    def show_status(self, message, status_type="info"):
        """Status im Header anzeigen."""
        self.status_label.setText(message)
        
        colors = {
            'info': "#757575",      # Grau
            'success': "#757575",      # Grau
            'error': '#e74c3c',     # Rot
            'ready': "#757575",     # Grau
            'warning': '#f39c12'    # Orange
        }
        
        color = colors.get(status_type, '#95a5a6')
        self.status_label.setStyleSheet(f"""
            QLabel {{
                background-color: {color};
                color: white;
                padding: 15px;
                border-radius: 8px;
            }}
        """)
    
    def update_motion(self, motion_value):
        """Motion-Wert aktualisieren."""
        self.motion_info.setText(f"{motion_value:.0f}")
        
        # Farbe des Hintergrunds immer gleich
        color = "#878787"
        
        self.motion_info.setStyleSheet(f"""
            background-color: {color};
            color: white;
            padding: 8px 15px;
            border-radius: 4px;
            font-weight: bold;
            min-width: 60px;
        """)
    
    def update_brightness(self, brightness):
        """Helligkeitsanzeige aktualisieren."""
        self.brightness_info.setText(f"{brightness:.0f}")
        
        # Farbe des Hintergrunds immer gleich
        color = "#878787"
        
        self.brightness_info.setStyleSheet(f"""
            background-color: {color};
            color: white;
            padding: 8px 15px;
            border-radius: 4px;
            font-weight: bold;
            min-width: 60px;
        """)
    
    def show_brightness_warning(self, message):
        """Helligkeitswarnung anzeigen."""
        self.brightness_warning.setText(message)
        self.brightness_warning.setVisible(True)
    
    def hide_brightness_warning(self):
        """Helligkeitswarnung ausblenden."""
        self.brightness_warning.setVisible(False)
    
    def update_last_cycle_stats(self, last_cycle_stats):
        """Letzte Erkennungen aktualisieren - ERWEITERT: Mit Img und Anz-Spalten."""
        # Detaillierte Tabelle fuer LETZTEN Zyklus aktualisieren - ERWEITERT
        self.last_cycle_table.setRowCount(len(last_cycle_stats))
        
        for row, (class_name, stats) in enumerate(last_cycle_stats.items()):
            # Klasse
            self.last_cycle_table.setItem(row, 0, QTableWidgetItem(class_name))
            
            # Img (Gesamtanzahl Bilder im Zyklus)
            cycle_image_count = self.app.cycle_image_count if hasattr(self.app, 'cycle_image_count') else 0
            img_item = QTableWidgetItem(str(cycle_image_count))
            img_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.last_cycle_table.setItem(row, 1, img_item)
            
            # Min Konfidenz im letzten Zyklus
            min_conf = stats.get('min_confidence', 0.0)
            if min_conf == 1.0:  # Kein Wert gesetzt
                min_conf = 0.0
            min_conf_item = QTableWidgetItem(f"{min_conf:.2f}")
            min_conf_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.last_cycle_table.setItem(row, 2, min_conf_item)
            
            # Max Konfidenz im letzten Zyklus
            max_conf_item = QTableWidgetItem(f"{stats['max_confidence']:.2f}")
            max_conf_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.last_cycle_table.setItem(row, 3, max_conf_item)
            
            # Anz (Durchschnittliche Anzahl pro Bild)
            total_detections = stats.get('total_detections', 0)
            if cycle_image_count > 0:
                avg_detections_per_image = total_detections / cycle_image_count
                avg_rounded = round(avg_detections_per_image)  # Auf Integer runden
            else:
                avg_rounded = 0
            
            anz_item = QTableWidgetItem(str(avg_rounded))
            anz_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.last_cycle_table.setItem(row, 4, anz_item)
    
    def update_video(self, frame):
        """Video-Frame aktualisieren."""
        try:
            # Frame zu Qt-Format konvertieren
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb_frame.shape
            bytes_per_line = ch * w
            
            # QPixmap erstellen
            from PyQt6.QtGui import QImage
            qt_image = QImage(rgb_frame.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
            pixmap = QPixmap.fromImage(qt_image)
            
            # Skalieren fuer Video-Label
            scaled_pixmap = pixmap.scaled(
                self.video_label.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            
            self.video_label.setPixmap(scaled_pixmap)
            
        except Exception as e:
            print(f"Fehler beim Video-Update: {e}")
    
    # STATUS-BUTTON UPDATE-METHODEN (NEU: ANGEPASST AUF BLAU)
    def update_model_status(self, model_path):
        """Model-Status-Button aktualisieren - BLAU statt Gruen."""
        if model_path and os.path.exists(model_path):
            model_name = os.path.basename(model_path)
            self.model_btn.setText(f"Modell: {model_name}")
            self.model_btn.setStyleSheet("""
                QPushButton {
                    background-color: #3498db;
                    color: white;
                    border: 2px solid #2980b9;
                    padding: 15px 25px;
                    border-radius: 4px;
                    font-size: 13px;
                    font-weight: bold;
                    text-align: center;
                }
                QPushButton:hover {
                    background-color: #5dade2;
                    border-color: #3498db;
                }
                QPushButton:pressed {
                    background-color: #2980b9;
                }
                QPushButton:disabled {
                    background-color: #7f8c8d;
                    color: #bdc3c7;
                    border-color: #95a5a6;
                }
            """)
            self.model_btn.setToolTip(f"Modell geladen: {model_name}\nKlicken um zu aendern")
        else:
            self.model_btn.setText("Kein Modell geladen")
            self.model_btn.setStyleSheet("""
                QPushButton {
                    background-color: #34495e;
                    color: #bdc3c7;
                    border: 2px solid #5d6d7e;
                    padding: 15px 25px;
                    border-radius: 4px;
                    font-size: 13px;
                    font-weight: bold;
                    text-align: left;
                }
                QPushButton:hover {
                    background-color: #3498db;
                    border-color: #2e86de;
                    color: white;
                }
                QPushButton:pressed {
                    background-color: #2980b9;
                }
                QPushButton:disabled {
                    background-color: #7f8c8d;
                    color: #bdc3c7;
                    border-color: #95a5a6;
                }
            """)
            self.model_btn.setToolTip("Klicken um Modell zu laden")
    
    def update_camera_status(self, source_info, source_type):
        """Camera-Status-Button aktualisieren - BLAU statt Gruen."""
        if source_info is not None:
            if source_type == 'webcam':
                display_text = f"Webcam: {source_info}"
            elif source_type == 'video':
                video_name = os.path.basename(source_info)
                display_text = f"Video: {video_name}"
            elif source_type == 'ids':
                display_text = f"IDS Kamera: {source_info}"
            else:
                display_text = f"Quelle: {source_info}"
                
            self.camera_btn.setText(display_text)

            self.camera_btn.setStyleSheet("""
                QPushButton {
                    background-color: #3498db;
                    color: white;
                    border: 2px solid #2980b9;
                    padding: 15px 25px;
                    border-radius: 4px;
                    font-size: 13px;
                    font-weight: bold;
                    text-align: center;
                }
                QPushButton:hover {
                    background-color: #5dade2;
                    border-color: #3498db;
                }
                QPushButton:pressed {
                    background-color: #2980b9;
                }
                QPushButton:disabled {
                    background-color: #7f8c8d;
                    color: #bdc3c7;
                    border-color: #95a5a6;
                }
            """)
            self.camera_btn.setToolTip(f"Quelle konfiguriert: {display_text}\nKlicken um zu aendern")
        else:
            self.camera_btn.setText("Modus waehlen")
            self.camera_btn.setStyleSheet("""
                QPushButton {
                    background-color: #34495e;
                    color: #bdc3c7;
                    border: 2px solid #5d6d7e;
                    padding: 15px 25px;
                    border-radius: 4px;
                    font-size: 13px;
                    font-weight: bold;
                    text-align: left;
                }
                QPushButton:hover {
                    background-color: #3498db;
                    border-color: #2e86de;
                    color: white;
                }
                QPushButton:pressed {
                    background-color: #2980b9;
                }
                QPushButton:disabled {
                    background-color: #7f8c8d;
                    color: #bdc3c7;
                    border-color: #95a5a6;
                }
            """)
            self.camera_btn.setToolTip("Klicken um Kamera oder Video auszuwaehlen")
    
    # Dialog-Handler
    def select_model_file(self):
        """Modell-Datei auswaehlen Dialog."""
        from PyQt6.QtWidgets import QFileDialog
        
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "KI-Modell auswaehlen",
            "",
            "PyTorch Modelle (*.pt);;Alle Dateien (*)"
        )
        
        if file_path:
            self.update_model_status(file_path)
            
        return file_path
    
    def select_camera_source(self):
        """Kamera/Video-Quelle auswaehlen Dialog."""
        dialog = CameraSelectionDialog(self.app.camera_manager, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            source = dialog.get_selected_source()
            if source:
                # Status-Button aktualisieren basierend auf Quelle
                if isinstance(source, int):
                    self.update_camera_status(source, 'webcam')
                elif isinstance(source, str):
                    self.update_camera_status(source, 'video')
                elif isinstance(source, tuple):
                    self.update_camera_status(source[1], 'ids')
                
                return source
        
        return None
    
    def open_settings_dialog(self, settings):
        """Einstellungen-Dialog oeffnen - ANGEPASST: Mit class_names."""
        # Hole die aktuellen Klassennamen vom detection_engine
        class_names = {}
        if hasattr(self.app, 'detection_engine') and hasattr(self.app.detection_engine, 'class_names'):
            class_names = self.app.detection_engine.class_names
        
        dialog = SettingsDialog(settings, class_names, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Warnung wenn Erkennung laeuft
            if self.app.running:
                QMessageBox.information(
                    self,
                    "Einstellungen geaendert",
                    "Einstellungen wurden gespeichert.\n\nBitte stoppen Sie die Erkennung und starten Sie sie neu, damit die Änderungen wirksam werden."
                )