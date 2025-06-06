"""
Hauptbenutzeroberfläche - kompakt und fokussiert mit Counter, Motion-Anzeige und WAGO Modbus-Status
Status zwischen Menü und Counter, Motion-Wert-Anzeige wie Helligkeit
"""

import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
    QSplitter, QFrame, QTableWidget, QTableWidgetItem, QHeaderView, 
    QToolButton, QGroupBox, QScrollArea, QMessageBox, QDialog
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap, QFont
import cv2
import numpy as np

from .dialogs import CameraSelectionDialog, SettingsDialog

class MainUI(QWidget):
    """Hauptbenutzeroberfläche mit kompakter Sidebar, Counter und WAGO Modbus-Status."""
    
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
        
        # Titel und Benutzerstatus
        self._create_title_section(layout)
        
        # WAGO Modbus Status
        self._create_modbus_section(layout)
        
        # Workflow-Status mit Motion und Helligkeit
        self._create_sensors_section(layout)
        
        # Modell-Sektion
        self._create_model_section(layout)
        
        # Kamera-Sektion
        self._create_camera_section(layout)
        
        # Letzte Erkennung
        self._create_stats_section(layout)
        
        # Aktionen
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
    
    def _create_title_section(self, layout):
        """Titel und Benutzerstatus erstellen."""
        # Titel
        title = QLabel("KI-Objekterkennung")
        title.setFont(QFont("", 16, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Benutzerstatus
        user_group = QGroupBox("Benutzer")
        user_layout = QVBoxLayout(user_group)
        user_layout.setSpacing(5)
        
        user_info_layout = QHBoxLayout()
        self.user_label = QLabel("Benutzer: Gast")
        self.user_label.setStyleSheet("color: #ecf0f1; background-color: #34495e; padding: 3px; border-radius: 3px; font-size: 11px;")
        user_info_layout.addWidget(self.user_label, 1)
        
        self.login_btn = QPushButton("Login")
        self.login_btn.setMaximumWidth(50)
        self.login_btn.setToolTip("Admin Login")
        user_info_layout.addWidget(self.login_btn)
        
        user_layout.addLayout(user_info_layout)
        layout.addWidget(user_group)
    
    def _create_modbus_section(self, layout):
        """WAGO Modbus Status-Sektion erstellen."""
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
        
        # Erweiterte Modbus-Aktionen (nur für Admin)
        actions_layout = QHBoxLayout()
        
        # Reset Button
        self.modbus_reset_btn = QPushButton("Reset")
        self.modbus_reset_btn.setStyleSheet("""
            QPushButton {
                background-color: #e67e22;
                font-size: 11px;
                min-height: 25px;
            }
            QPushButton:hover {
                background-color: #d35400;
            }
        """)
        self.modbus_reset_btn.setToolTip("WAGO Controller zurücksetzen")
        self.modbus_reset_btn.clicked.connect(self.reset_modbus_controller)
        actions_layout.addWidget(self.modbus_reset_btn)
        
        # Reconnect Button
        self.modbus_reconnect_btn = QPushButton("Neuverbindung")
        self.modbus_reconnect_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                font-size: 11px;
                min-height: 25px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        self.modbus_reconnect_btn.setToolTip("Modbus neu verbinden")
        self.modbus_reconnect_btn.clicked.connect(self.reconnect_modbus)
        actions_layout.addWidget(self.modbus_reconnect_btn)
        
        modbus_layout.addLayout(actions_layout)
        
        layout.addWidget(modbus_group)
    
    def reset_modbus_controller(self):
        """WAGO Controller zurücksetzen."""
        if not self.app.user_manager.is_admin():
            self.show_status("Admin-Rechte erforderlich für Controller-Reset", "error")
            return
        
        reply = QMessageBox.question(
            self,
            "Controller Reset",
            "WAGO Controller zurücksetzen?\n\nDies kann Verbindungsprobleme beheben.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.show_status("Führe Controller-Reset durch...", "warning")
            
            if self.app.modbus_manager.restart_controller():
                self.show_status("Controller-Reset erfolgreich", "success")
                QMessageBox.information(
                    self,
                    "Reset erfolgreich",
                    "WAGO Controller wurde zurückgesetzt.\nVerbindung wird neu aufgebaut..."
                )
                # Neuverbindung nach Reset
                self.reconnect_modbus()
            else:
                self.show_status("Controller-Reset fehlgeschlagen", "error")
                QMessageBox.critical(
                    self,
                    "Reset fehlgeschlagen",
                    "Controller-Reset konnte nicht durchgeführt werden.\nPrüfen Sie die Verbindung."
                )
    
    def reconnect_modbus(self):
        """Modbus neu verbinden."""
        if not self.app.user_manager.is_admin():
            self.show_status("Admin-Rechte erforderlich für Neuverbindung", "error")
            return
        
        self.show_status("Verbinde Modbus neu...", "warning")
        
        if self.app.modbus_manager.force_reconnect():
            # Watchdog und Coil-Refresh neu starten
            if self.app.modbus_manager.start_watchdog():
                logging.info("Watchdog nach Neuverbindung gestartet")
            
            if self.app.modbus_manager.start_coil_refresh():
                logging.info("Coil-Refresh nach Neuverbindung gestartet")
            
            self.update_modbus_status(True, self.app.modbus_manager.ip_address)
            self.show_status("Modbus erfolgreich neu verbunden", "success")
        else:
            self.update_modbus_status(False, self.app.modbus_manager.ip_address)
            self.show_status("Modbus-Neuverbindung fehlgeschlagen", "error")
    
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
        """Statistiken-Sektion erstellen."""
        stats_group = QGroupBox("Letzte Erkennung")
        stats_layout = QVBoxLayout(stats_group)
        stats_layout.setSpacing(5)
        
        # Aktuelle Frame-Erkennungen
        self.current_frame_label = QLabel("Aktuell: 0")
        self.current_frame_label.setStyleSheet("color: #f39c12; background-color: #34495e; padding: 3px; border-radius: 3px; font-size: 11px;")
        stats_layout.addWidget(self.current_frame_label)
        
        # Detaillierte Tabelle für LETZTEN Zyklus
        self.last_cycle_table = QTableWidget(0, 3)
        self.last_cycle_table.setHorizontalHeaderLabels(["Klasse", "Anz", "Max"])
        self.last_cycle_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.last_cycle_table.verticalHeader().hide()
        self.last_cycle_table.setMaximumHeight(150)
        self.last_cycle_table.setStyleSheet("""
            QTableWidget {
                background-color: #34495e;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 11px;
            }
            QHeaderView::section {
                background-color: #2c3e50;
                color: white;
                border: none;
                padding: 3px;
                font-size: 11px;
            }
        """)
        stats_layout.addWidget(self.last_cycle_table)
        
        layout.addWidget(stats_group)
    
    def _create_actions_section(self, layout):
        """Aktionen-Sektion erstellen."""
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
        
        self.settings_btn = QPushButton("Einstellungen")
        actions_layout.addWidget(self.settings_btn)
        
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
        
        # Header mit: [Menü-Button] [Status] [Counter]
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
        
        # 2. STATUS IN DER MITTE
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
        header_layout.addWidget(self.status_label, 1)
        
        # 3. COUNTER (rechts oben)
        self._create_counter_section(header_layout)
        
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
        self.video_label.setText("Kein Video")
        layout.addWidget(self.video_label, 1)
        
        return main_area
    
    def _create_counter_section(self, header_layout):
        """Counter-Sektion im Header erstellen."""
        self.counter_frame = QFrame()
        self.counter_frame.setStyleSheet("""
            QFrame {
                background-color: #34495e;
                border-radius: 8px;
                padding: 10px;
            }
            QLabel {
                color: white;
                font-weight: bold;
            }
        """)
        
        counter_layout = QVBoxLayout(self.counter_frame)
        counter_layout.setSpacing(5)
        counter_layout.setContentsMargins(15, 10, 15, 10)
        
        # Session-Statistiken
        session_title = QLabel("Session")
        session_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        session_title.setFont(QFont("", 12, QFont.Weight.Bold))
        counter_layout.addWidget(session_title)
        
        # Good Parts
        good_layout = QHBoxLayout()
        good_layout.addWidget(QLabel("OK:"))
        self.good_parts_counter = QLabel("0")
        self.good_parts_counter.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.good_parts_counter.setStyleSheet("color: #27ae60; font-size: 14px;")
        good_layout.addWidget(self.good_parts_counter)
        counter_layout.addLayout(good_layout)
        
        # Bad Parts
        bad_layout = QHBoxLayout()
        bad_layout.addWidget(QLabel("Nicht OK:"))
        self.bad_parts_counter = QLabel("0")
        self.bad_parts_counter.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.bad_parts_counter.setStyleSheet("color: #e74c3c; font-size: 14px;")
        bad_layout.addWidget(self.bad_parts_counter)
        counter_layout.addLayout(bad_layout)
        
        # Total Cycles
        total_layout = QHBoxLayout()
        total_layout.addWidget(QLabel("Zyklen:"))
        self.total_cycles_counter = QLabel("0")
        self.total_cycles_counter.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.total_cycles_counter.setStyleSheet("color: #3498db; font-size: 14px;")
        total_layout.addWidget(self.total_cycles_counter)
        counter_layout.addLayout(total_layout)
        
        # Reset Button
        reset_counter_btn = QPushButton("Reset")
        reset_counter_btn.setStyleSheet("""
            QPushButton {
                background-color: #7f8c8d;
                color: white;
                border: none;
                padding: 5px;
                border-radius: 3px;
                font-size: 10px;
            }
            QPushButton:hover {
                background-color: #95a5a6;
            }
        """)
        reset_counter_btn.clicked.connect(self.reset_session_counter)
        counter_layout.addWidget(reset_counter_btn)
        
        header_layout.addWidget(self.counter_frame, 0, Qt.AlignmentFlag.AlignRight)
    
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
        
        # Admin-Buttons je nach Verbindungsstatus aktivieren/deaktivieren
        self.modbus_reset_btn.setEnabled(connected and self.app.user_manager.is_admin())
        self.modbus_reconnect_btn.setEnabled(self.app.user_manager.is_admin())
    
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
        """Session-Counter zurücksetzen."""
        self.session_good_parts = 0
        self.session_bad_parts = 0
        self.session_total_cycles = 0
        self.update_counter_display()
    
    def update_counter_display(self):
        """Counter-Anzeige aktualisieren."""
        self.good_parts_counter.setText(str(self.session_good_parts))
        self.bad_parts_counter.setText(str(self.session_bad_parts))
        self.total_cycles_counter.setText(str(self.session_total_cycles))
    
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
        self.user_label.setText(f"Benutzer: {user_level}")
        
        # Button-Text ändern
        if self.app.user_manager.is_admin():
            self.login_btn.setText("Logout")
            self.login_btn.setToolTip("Admin Logout")
            self.user_label.setStyleSheet("color: #ecf0f1; background-color: #27ae60; padding: 3px; border-radius: 3px; font-size: 11px;")
        else:
            self.login_btn.setText("Login")
            self.login_btn.setToolTip("Admin Login")
            self.user_label.setStyleSheet("color: #ecf0f1; background-color: #34495e; padding: 3px; border-radius: 3px; font-size: 11px;")
        
        # Buttons aktivieren/deaktivieren
        can_admin = self.app.user_manager.is_admin()
        self.model_btn.setEnabled(can_admin)
        self.camera_btn.setEnabled(can_admin)
        self.settings_btn.setEnabled(can_admin)
        
        # Modbus-Buttons für Admin
        self.modbus_reset_btn.setEnabled(can_admin and self.app.modbus_manager.connected)
        self.modbus_reconnect_btn.setEnabled(can_admin)
    
    def update_workflow_status(self, status):
        """Workflow-Status aktualisieren."""
        self.workflow_info.setText(status)
        
        # Farbe je nach Status
        colors = {
            'READY': '#95a5a6',      # Grau
            'MOTION': '#f39c12',     # Orange  
            'SETTLING': '#e67e22',   # Dunkelorange
            'CAPTURING': '#27ae60',  # Grün
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
            'info': '#3498db',      # Blau
            'success': '#27ae60',   # Grün
            'error': '#e74c3c',     # Rot
            'ready': '#95a5a6',     # Grau
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
        
        # Farbe je nach Helligkeit
        if brightness < 50:
            color = "#e74c3c"  # Rot (zu dunkel)
        elif brightness > 200:
            color = "#e74c3c"  # Rot (zu hell)
        else:
            color = "#27ae60"  # Grün (gut)
        
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
    
    def update_last_cycle_stats(self, last_cycle_stats, current_frame_detections):
        """Letzte Erkennungen aktualisieren."""
        # Aktuelle Frame-Erkennungen
        current_count = len(current_frame_detections)
        self.current_frame_label.setText(f"Aktuell: {current_count}")
        
        # Detaillierte Tabelle für LETZTEN Zyklus aktualisieren
        self.last_cycle_table.setRowCount(len(last_cycle_stats))
        
        for row, (class_name, stats) in enumerate(last_cycle_stats.items()):
            # Klasse
            self.last_cycle_table.setItem(row, 0, QTableWidgetItem(class_name))
            
            # Anzahl im letzten Zyklus
            count_item = QTableWidgetItem(str(stats['count']))
            count_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.last_cycle_table.setItem(row, 1, count_item)
            
            # Max Konfidenz im letzten Zyklus
            max_conf_item = QTableWidgetItem(f"{stats['max_confidence']:.2f}")
            max_conf_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.last_cycle_table.setItem(row, 2, max_conf_item)
    
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
        """Einstellungen-Dialog öffnen."""
        dialog = SettingsDialog(settings, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Warnung wenn Erkennung läuft
            if self.app.running:
                QMessageBox.information(
                    self,
                    "Einstellungen geändert",
                    "Einstellungen wurden gespeichert.\n\nBitte stoppen Sie die Erkennung und starten Sie sie neu, damit die Änderungen wirksam werden."
                )