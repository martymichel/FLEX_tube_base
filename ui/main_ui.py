"""
Hauptbenutzeroberfläche - FINALE Version mit Einstellungen-Button, Admin-Reset, und Login-Status-Button
Kompakt und fokussiert mit erweiterter Statistik-Tabelle und kompaktem Session Counter
ERWEITERT: Modbus-Reset/Reconnect Buttons aus Sidebar entfernt
"""

import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
    QSplitter, QFrame, QTableWidget, QTableWidgetItem, QHeaderView, 
    QToolButton, QGroupBox, QScrollArea, QMessageBox, QDialog
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPixmap, QFont
import cv2
import numpy as np
import logging

# Lokale Importe
from .dialogs import CameraSelectionDialog, SettingsDialog

class MainUI(QWidget):
    """Hauptbenutzeroberfläche mit kompakter Sidebar, erweiterter Statistik-Tabelle und kompaktem Session Counter."""
    
    def __init__(self, parent_app):
        super().__init__()
        self.app = parent_app
        self.sidebar_visible = True
        self.brightness_warning_visible = False
        
        # Counter-Statistiken
        self.session_good_parts = 0
        self.session_bad_parts = 0
        self.session_total_cycles = 0
        
        self.setup_ui()
        
        # User Manager Signale verbinden für Auto-Updates
        if hasattr(self.app, 'user_manager'):
            self.app.user_manager.user_status_changed.connect(self.on_user_status_changed)
    
    def setup_ui(self):
        """UI aufbauen."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Splitter für Sidebar und Hauptbereich
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(self.splitter)
        
        # Sidebar erstellen
        sidebar = self.create_sidebar()
        
        # Hauptbereich erstellen
        main_area = self.create_main_area()
        
        # Zu Splitter hinzufügen
        self.splitter.addWidget(sidebar)
        self.splitter.addWidget(main_area)
        
        # Größenverhältnis setzen
        self.splitter.setSizes([350, 1000])
    
    def create_sidebar(self):
        """Kompakte Sidebar mit Steuerelementen erstellen."""
        self.sidebar = QFrame()
        self.sidebar.setStyleSheet("""
            QFrame {
                background-color: #2c3e50;
                color: white;
                border-radius: 8px;
            }
            QPushButton {
                background-color: #34495e;
                color: white;
                border: none;
                padding: 10px;
                border-radius: 6px;
                font-size: 13px;
                font-weight: bold;
                min-height: 15px;
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
                font-size: 13px;
            }
            QGroupBox {
                font-weight: bold;
                border: 1px solid #34495e;
                border-radius: 6px;
                margin-top: 8px;
                padding-top: 8px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top center;
                padding: 0 4px;
                background-color: #34495e;
                border-radius: 3px;
                font-size: 12px;
            }
        """)
        self.sidebar.setMinimumWidth(300)
        self.sidebar.setMaximumWidth(380)
        
        # Scrollbereich für Sidebar
        scroll = QScrollArea()
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        sidebar_content = QWidget()
        layout = QVBoxLayout(sidebar_content)
        layout.setSpacing(10)  # Kompakter Abstand
        layout.setContentsMargins(15, 15, 15, 15)  # Kompakte Ränder
        
        # NEUER Breiter Login-Status-Button (kein separates Label mehr)
        self._create_login_status_section(layout)
        
        # WAGO Modbus Status (OHNE Reset/Reconnect Buttons)
        self._create_modbus_section(layout)
        
        # Workflow-Status mit Motion und Helligkeit
        self._create_sensors_section(layout)
        
        # Modell-Sektion
        self._create_model_section(layout)
        
        # Kamera-Sektion
        self._create_camera_section(layout)
        
        # Letzte Erkennung - ERWEITERT
        self._create_stats_section(layout)
        
        # Aktionen (OHNE Einstellungen-Button)
        self._create_actions_section(layout)
        
        # BEENDEN Button (eigene Sektion am Ende)
        self._create_quit_section(layout)
        
        # Stretch am Ende
        layout.addStretch()
        
        # Sidebar-Content zu Scroll hinzufügen
        scroll.setWidget(sidebar_content)
        
        # Scroll zu Sidebar hinzufügen
        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.addWidget(scroll)
        
        return self.sidebar
    
    def _create_login_status_section(self, layout):
        """NEUER: Breiter Login-Status-Button (ersetzt separates Label + Button)."""
        login_group = QGroupBox("Benutzer-Status")
        login_layout = QVBoxLayout(login_group)
        login_layout.setSpacing(5)
        
        # Breiter Status-Button der gleichzeitig Login/Logout macht
        self.login_status_btn = QPushButton("Operator")
        self.login_status_btn.setMinimumHeight(45)  # Deutlich höher
        self.login_status_btn.setStyleSheet("""
            QPushButton {
                background-color: #34495e;
                color: white;
                border: 2px solid #5d6d7e;
                padding: 12px;
                border-radius: 8px;
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
        self.login_status_btn.setToolTip("Klicken für Admin-Login/Logout")
        login_layout.addWidget(self.login_status_btn)
        
        layout.addWidget(login_group)
    
    def on_user_status_changed(self, new_status):
        """Callback für User-Status-Änderungen (Auto-Logout etc.)."""
        self.update_user_interface()
        if new_status == "Operator":
            self.app.ui.show_status("Automatischer Logout - Operator-Modus", "warning")
    
    def _create_modbus_section(self, layout):
        """WAGO Modbus Status-Sektion erstellen - OHNE Reset/Reconnect Buttons."""
        modbus_group = QGroupBox("WAGO Modbus")
        modbus_layout = QVBoxLayout(modbus_group)
        modbus_layout.setSpacing(5)
        
        # Verbindungsstatus
        connection_layout = QHBoxLayout()
        connection_layout.addWidget(QLabel("Status:"))
        self.modbus_status = QLabel("Getrennt")
        self.modbus_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.modbus_status.setStyleSheet("""
            background-color: #e74c3c;
            color: white;
            padding: 3px;
            border-radius: 3px;
            font-weight: bold;
            font-size: 11px;
        """)
        connection_layout.addWidget(self.modbus_status, 1)
        modbus_layout.addLayout(connection_layout)
        
        # IP-Adresse
        ip_layout = QHBoxLayout()
        ip_layout.addWidget(QLabel("IP:"))
        self.modbus_ip = QLabel("192.168.1.100")
        self.modbus_ip.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.modbus_ip.setStyleSheet("""
            background-color: #34495e;
            padding: 3px;
            border-radius: 3px;
            font-size: 11px;
        """)
        ip_layout.addWidget(self.modbus_ip, 1)
        modbus_layout.addLayout(ip_layout)
        
        # Coil-Status (kompakt)
        coils_layout = QHBoxLayout()
        coils_layout.addWidget(QLabel("Coils:"))
        
        # Reject Coil (Ausschuss)
        self.reject_coil_indicator = QLabel("R")
        self.reject_coil_indicator.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.reject_coil_indicator.setFixedSize(20, 20)
        self.reject_coil_indicator.setStyleSheet("""
            background-color: #7f8c8d;
            color: white;
            border-radius: 10px;
            font-weight: bold;
            font-size: 9px;
        """)
        self.reject_coil_indicator.setToolTip("Reject/Ausschuss Coil")
        coils_layout.addWidget(self.reject_coil_indicator)
        
        # Detection Active Coil
        self.detection_coil_indicator = QLabel("D")
        self.detection_coil_indicator.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.detection_coil_indicator.setFixedSize(20, 20)
        self.detection_coil_indicator.setStyleSheet("""
            background-color: #7f8c8d;
            color: white;
            border-radius: 10px;
            font-weight: bold;
            font-size: 9px;
        """)
        self.detection_coil_indicator.setToolTip("Detection Active Coil")
        coils_layout.addWidget(self.detection_coil_indicator)
        
        modbus_layout.addLayout(coils_layout)
        
        layout.addWidget(modbus_group)
    
    def _create_sensors_section(self, layout):
        """Workflow-Status mit Motion und Helligkeit."""
        workflow_group = QGroupBox("Status & Sensoren")
        workflow_layout = QVBoxLayout(workflow_group)
        workflow_layout.setSpacing(5)
        
        # Workflow-Status
        workflow_info_layout = QHBoxLayout()
        workflow_info_layout.addWidget(QLabel("Workflow:"))
        self.workflow_info = QLabel("READY")
        self.workflow_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.workflow_info.setStyleSheet("""
            background-color: #34495e;
            color: white;
            padding: 5px;
            border-radius: 4px;
            font-weight: bold;
        """)
        workflow_info_layout.addWidget(self.workflow_info, 1)
        workflow_layout.addLayout(workflow_info_layout)
        
        # Motion-Wert Anzeige
        motion_layout = QHBoxLayout()
        motion_layout.addWidget(QLabel("Motion:"))
        self.motion_info = QLabel("--")
        self.motion_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.motion_info.setStyleSheet("""
            background-color: #34495e;
            padding: 5px;
            border-radius: 4px;
            font-weight: bold;
            min-width: 60px;
        """)
        motion_layout.addWidget(self.motion_info)
        workflow_layout.addLayout(motion_layout)
        
        # Helligkeitsanzeige
        brightness_layout = QHBoxLayout()
        brightness_layout.addWidget(QLabel("Helligkeit:"))
        self.brightness_info = QLabel("--")
        self.brightness_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.brightness_info.setStyleSheet("""
            background-color: #34495e;
            padding: 5px;
            border-radius: 4px;
            font-weight: bold;
            min-width: 60px;
        """)
        brightness_layout.addWidget(self.brightness_info)
        workflow_layout.addLayout(brightness_layout)
        
        # Helligkeitswarnung
        self.brightness_warning = QLabel("Beleuchtung prüfen!")
        self.brightness_warning.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.brightness_warning.setStyleSheet("""
            background-color: #e74c3c;
            color: white;
            padding: 5px;
            border-radius: 4px;
            font-weight: bold;
            font-size: 11px;
        """)
        self.brightness_warning.setVisible(False)
        workflow_layout.addWidget(self.brightness_warning)
        
        layout.addWidget(workflow_group)
    
    def _create_model_section(self, layout):
        """Modell-Sektion erstellen."""
        model_group = QGroupBox("KI-Modell")
        model_layout = QVBoxLayout(model_group)
        model_layout.setSpacing(5)
        
        self.model_info = QLabel("Kein Modell geladen")
        self.model_info.setWordWrap(True)
        self.model_info.setStyleSheet("color: #bdc3c7; font-style: italic; font-size: 11px;")
        model_layout.addWidget(self.model_info)
        
        self.model_btn = QPushButton("Modell laden")
        model_layout.addWidget(self.model_btn)
        
        layout.addWidget(model_group)
    
    def _create_camera_section(self, layout):
        """Kamera-Sektion erstellen."""
        camera_group = QGroupBox("Kamera/Video")
        camera_layout = QVBoxLayout(camera_group)
        camera_layout.setSpacing(5)
        
        self.camera_info = QLabel("Keine Quelle ausgewählt")
        self.camera_info.setWordWrap(True)
        self.camera_info.setStyleSheet("color: #bdc3c7; font-style: italic; font-size: 11px;")
        camera_layout.addWidget(self.camera_info)
        
        self.camera_btn = QPushButton("Quelle wählen")
        camera_layout.addWidget(self.camera_btn)
        
        layout.addWidget(camera_group)
    
    def _create_stats_section(self, layout):
        """Statistiken-Sektion erstellen - ERWEITERT: 5 Spalten mit Durchschnitt."""
        stats_group = QGroupBox("Letzte Erkennung")
        stats_layout = QVBoxLayout(stats_group)
        stats_layout.setSpacing(5)
        
        # ERWEITERTE Tabelle für LETZTEN Zyklus - 5 Spalten
        self.last_cycle_table = QTableWidget(0, 5)  # 5 Spalten: Klasse, Img, Min, Max, Anz
        self.last_cycle_table.setHorizontalHeaderLabels(["Klasse", "Img", "Min", "Max", "Anz"])
        self.last_cycle_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.last_cycle_table.verticalHeader().hide()
        self.last_cycle_table.setMaximumHeight(150)  # Kompakter
        self.last_cycle_table.setStyleSheet("""
            QTableWidget {
                background: rgba(255, 255, 255, 0.05);
                color: #e2e8f0;
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 8px;
                font-size: 10px;
                gridline-color: rgba(255, 255, 255, 0.1);
            }
            QHeaderView::section {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                        stop: 0 #4a5568, stop: 1 #2d3748);
                color: white;
                border: none;
                padding: 4px;
                font-size: 10px;
                font-weight: 600;
                text-transform: uppercase;
            }
            QTableWidget::item {
                padding: 2px 4px;
                border: none;
            }
            QTableWidget::item:selected {
                background: rgba(255, 255, 255, 0.1);
            }
        """)
        stats_layout.addWidget(self.last_cycle_table)
        
        layout.addWidget(stats_group)
    
    def _create_actions_section(self, layout):
        """Aktionen-Sektion erstellen (OHNE Einstellungen-Button)."""
        actions_group = QGroupBox("Aktionen")
        actions_layout = QVBoxLayout(actions_group)
        actions_layout.setSpacing(5)
        
        self.start_btn = QPushButton("Starten")
        self.start_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                font-size: 14px;
                min-height: 35px;
            }
            QPushButton:hover {
                background-color: #2ecc71;
            }
        """)
        actions_layout.addWidget(self.start_btn)
        
        self.snapshot_btn = QPushButton("Schnappschuss")
        actions_layout.addWidget(self.snapshot_btn)
        
        # KEIN Einstellungen-Button mehr hier - wird in Header verschoben
        
        layout.addWidget(actions_group)
    
    def _create_quit_section(self, layout):
        """BEENDEN-Sektion erstellen."""
        quit_group = QGroupBox("Anwendung")
        quit_layout = QVBoxLayout(quit_group)
        quit_layout.setSpacing(5)
        
        # ESC-Hinweis
        esc_hint = QLabel("ESC = Schnelles Beenden")
        esc_hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        esc_hint.setStyleSheet("""
            color: #bdc3c7; 
            font-style: italic; 
            font-size: 10px;
            background-color: #34495e;
            padding: 3px;
            border-radius: 3px;
        """)
        quit_layout.addWidget(esc_hint)
        
        # BEENDEN Button
        self.quit_btn = QPushButton("BEENDEN")
        self.quit_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                font-size: 14px;
                font-weight: bold;
                min-height: 35px;
                border: 2px solid #c0392b;
            }
            QPushButton:hover {
                background-color: #c0392b;
                border: 2px solid #a93226;
            }
            QPushButton:pressed {
                background-color: #a93226;
            }
        """)
        self.quit_btn.setToolTip("Anwendung sofort beenden (ESC)")
        quit_layout.addWidget(self.quit_btn)
        
        layout.addWidget(quit_group)
    
    def create_main_area(self):
        """Hauptbereich mit optimiertem Header-Layout erstellen."""
        main_area = QFrame()
        main_area.setStyleSheet("""
            QFrame {
                background-color: #ecf0f1;
                border-radius: 8px;
            }
        """)
        
        layout = QVBoxLayout(main_area)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Header mit: [Menü-Button] [⚙️ Einstellungen] [Status] [Counter]
        header_layout = QHBoxLayout()
        header_layout.setSpacing(20)
        
        # 1. Sidebar Toggle Button (links)
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
                min-width: 40px;
                min-height: 40px;
            }
            QToolButton:hover {
                background-color: #2980b9;
            }
        """)
        header_layout.addWidget(self.sidebar_toggle_btn, 0, Qt.AlignmentFlag.AlignLeft)
        
        # 2. NEU: EINSTELLUNGEN-BUTTON mit Zahnrad (neben Menü)
        self.settings_btn = QPushButton("⚙️")
        self.settings_btn.setStyleSheet("""
            QPushButton {
                background-color: #8e44ad;
                color: white;
                border: none;
                font-size: 20px;
                padding: 8px;
                border-radius: 4px;
                min-width: 40px;
                min-height: 40px;
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
        header_layout.addWidget(self.status_label, 1)  # Stretch factor 1 für die Mitte
        
        # 4. KOMPAKTER COUNTER (rechts oben) - ÜBERARBEITET
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
        self.video_label.setText("Kein Stream verfügbar")
        layout.addWidget(self.video_label, 1)
        
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

        # Hauptlayout ohne Ränder, Platz zwischen Sektionen
        counter_layout = QHBoxLayout(self.counter_frame)
        counter_layout.setContentsMargins(0, 0, 0, 0)
        counter_layout.setSpacing(30)

        # Monospace-Font für Zahlen
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

            # Widgets hinzufügen mit minimalem Abstand
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

        # Reset-Button nur für Admin
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
        """Counter mit Formatierung für große Zahlen aktualisieren."""
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
    
    # MODBUS UI-Update-Methoden
    def update_modbus_status(self, connected, ip_address):
        """WAGO Modbus Status aktualisieren."""
        if connected:
            self.modbus_status.setText("Verbunden")
            self.modbus_status.setStyleSheet("""
                background-color: #27ae60;
                color: white;
                padding: 3px;
                border-radius: 3px;
                font-weight: bold;
                font-size: 11px;
            """)
        else:
            self.modbus_status.setText("Getrennt")
            self.modbus_status.setStyleSheet("""
                background-color: #e74c3c;
                color: white;
                padding: 3px;
                border-radius: 3px;
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
                border-radius: 10px;
                font-weight: bold;
                font-size: 9px;
            """)
        else:
            self.reject_coil_indicator.setStyleSheet("""
                background-color: #7f8c8d;
                color: white;
                border-radius: 10px;
                font-weight: bold;
                font-size: 9px;
            """)
        
        # Detection Active Coil
        if detection_active:
            self.detection_coil_indicator.setStyleSheet("""
                background-color: #27ae60;
                color: white;
                border-radius: 10px;
                font-weight: bold;
                font-size: 9px;
            """)
        else:
            self.detection_coil_indicator.setStyleSheet("""
                background-color: #7f8c8d;
                color: white;
                border-radius: 10px;
                font-weight: bold;
                font-size: 9px;
            """)
    
    # Standard UI-Update-Methoden
    def reset_session_counter(self):
        """Session-Counter zurücksetzen - NEU: NUR FÜR ADMIN."""
        # Prüfe Admin-Rechte
        if not self.app.user_manager.can_reset_counter():
            self.show_status("Admin-Rechte erforderlich für Counter-Reset", "error")
            return
        
        # Bestätigung anfordern
        reply = QMessageBox.question(
            self,
            "Counter zurücksetzen",
            "Session-Counter auf Null zurücksetzen?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.session_good_parts = 0
            self.session_bad_parts = 0
            self.session_total_cycles = 0
            self.update_counter_display()
            self.show_status("Session-Counter zurückgesetzt", "info")
            logging.info("Session-Counter von Admin zurückgesetzt")
    
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
            # Update Coil-Status für visuelles Feedback
            self.update_coil_status(reject_active=True, detection_active=True)
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
            # Admin-Style: Grün
            self.login_status_btn.setStyleSheet("""
                QPushButton {
                    background-color: #27ae60;
                    color: white;
                    border: 2px solid #229954;
                    padding: 12px;
                    border-radius: 8px;
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
            self.login_status_btn.setToolTip("Admin eingeloggt - Klicken für Logout")
        else:
            # Operator-Style: Grau
            self.login_status_btn.setStyleSheet("""
                QPushButton {
                    background-color: #34495e;
                    color: white;
                    border: 2px solid #5d6d7e;
                    padding: 12px;
                    border-radius: 8px;
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
            self.login_status_btn.setToolTip("Operator-Modus - Klicken für Admin-Login")
        
        # Buttons aktivieren/deaktivieren
        can_admin = self.app.user_manager.is_admin()
        self.model_btn.setEnabled(can_admin)
        self.camera_btn.setEnabled(can_admin)
        self.settings_btn.setEnabled(can_admin)  # NEU: Einstellungen-Button im Header
        
        # Reset-Button für Counter - NEU: NUR FÜR ADMIN
        self.reset_counter_btn.setEnabled(can_admin)
    
    def update_workflow_status(self, status):
        """Workflow-Status aktualisieren."""
        self.workflow_info.setText(status)
        
        # Farbe je nach Status
        colors = {
            'READY': "#757575",      # Grau
            'MOTION': '#757575',     # Grau  
            'SETTLING': "#757575",   # Grau
            'CAPTURING': "#23aeff",  # Blau
            'BLOWING': '#e74c3c'     # Rot
        }
        
        color = colors.get(status, '#34495e')
        self.workflow_info.setStyleSheet(f"""
            background-color: {color};
            color: white;
            padding: 5px;
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
            'ready': "#18929b",     # Türkis
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
        
        # Farbe je nach Motion-Level  
        if motion_value < 50:
            color = "#27ae60"  # Grün (ruhig)
        elif motion_value < 150:
            color = "#f39c12"  # Orange (moderate Bewegung)
        else:
            color = "#e74c3c"  # Rot (starke Bewegung)
        
        self.motion_info.setStyleSheet(f"""
            background-color: {color};
            color: white;
            padding: 5px;
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
            padding: 5px;
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
        # Detaillierte Tabelle für LETZTEN Zyklus aktualisieren - ERWEITERT
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
            
            # Skalieren für Video-Label
            scaled_pixmap = pixmap.scaled(
                self.video_label.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            
            self.video_label.setPixmap(scaled_pixmap)
            
        except Exception as e:
            print(f"Fehler beim Video-Update: {e}")
    
    # Dialog-Handler
    def select_model_file(self):
        """Modell-Datei auswählen Dialog."""
        from PyQt6.QtWidgets import QFileDialog
        
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "KI-Modell auswählen",
            "",
            "PyTorch Modelle (*.pt);;Alle Dateien (*)"
        )
        
        if file_path:
            self.model_info.setText(f"Modell: {os.path.basename(file_path)}")
            self.model_info.setStyleSheet("color: #27ae60; font-weight: bold; font-size: 11px;")
            
        return file_path
    
    def select_camera_source(self):
        """Kamera/Video-Quelle auswählen Dialog."""
        dialog = CameraSelectionDialog(self.app.camera_manager, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            source = dialog.get_selected_source()
            if source:
                # Info aktualisieren
                if isinstance(source, int):
                    self.camera_info.setText(f"Webcam: {source}")
                elif isinstance(source, str):
                    self.camera_info.setText(f"Video: {os.path.basename(source)}")
                elif isinstance(source, tuple):
                    self.camera_info.setText(f"IDS Kamera: {source[1]}")
                
                self.camera_info.setStyleSheet("color: #27ae60; font-weight: bold; font-size: 11px;")
                return source
        
        return None
    
    def open_settings_dialog(self, settings):
        """Einstellungen-Dialog öffnen - ANGEPASST: Mit class_names."""
        # Hole die aktuellen Klassennamen vom detection_engine
        class_names = {}
        if hasattr(self.app, 'detection_engine') and hasattr(self.app.detection_engine, 'class_names'):
            class_names = self.app.detection_engine.class_names
        
        dialog = SettingsDialog(settings, class_names, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Warnung wenn Erkennung läuft
            if self.app.running:
                QMessageBox.information(
                    self,
                    "Einstellungen geändert",
                    "Einstellungen wurden gespeichert.\n\nBitte stoppen Sie die Erkennung und starten Sie sie neu, damit die Änderungen wirksam werden."
                )