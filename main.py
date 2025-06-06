"""
Hauptbenutzeroberfläche - modern und elegant mit Counter, Motion-Anzeige und WAGO Modbus-Status
Status zwischen Menü und Counter, Motion-Wert-Anzeige wie Helligkeit
"""

import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
    QSplitter, QFrame, QTableWidget, QHeaderView, 
    QGroupBox, QScrollArea, QMessageBox, QDialog
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import  QFont
import cv2
import numpy as np
import logging

class MainUI(QWidget):
    """Hauptbenutzeroberfläche mit moderner Sidebar, Counter und WAGO Modbus-Status."""
    
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
        layout.setSpacing(0)
        
        # Splitter für Sidebar und Hauptbereich
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.setHandleWidth(2)
        self.splitter.setStyleSheet("""
            QSplitter::handle {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                    stop:0 #667eea, stop:1 #764ba2);
                border-radius: 1px;
            }
        """)
        layout.addWidget(self.splitter)
        
        # Sidebar erstellen
        sidebar = self.create_sidebar()
        
        # Hauptbereich erstellen
        main_area = self.create_main_area()
        
        # Zu Splitter hinzufügen
        self.splitter.addWidget(sidebar)
        self.splitter.addWidget(main_area)
        
        # Größenverhältnis setzen
        self.splitter.setSizes([380, 1200])
    
    def create_sidebar(self):
        """Moderne Sidebar mit Glasmorphism-Effekt erstellen."""
        self.sidebar = QFrame()
        self.sidebar.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(26, 35, 126, 0.95),
                    stop:0.5 rgba(49, 27, 146, 0.95),
                    stop:1 rgba(74, 20, 140, 0.95));
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 16px;
                backdrop-filter: blur(20px);
            }
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(102, 126, 234, 0.8),
                    stop:1 rgba(118, 75, 162, 0.8));
                color: white;
                border: 1px solid rgba(255, 255, 255, 0.2);
                padding: 12px 16px;
                border-radius: 12px;
                font-size: 13px;
                font-weight: 600;
                min-height: 20px;
                backdrop-filter: blur(10px);
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(102, 126, 234, 1.0),
                    stop:1 rgba(118, 75, 162, 1.0));
                border: 1px solid rgba(255, 255, 255, 0.3);
                transform: translateY(-2px);
                box-shadow: 0 8px 25px rgba(102, 126, 234, 0.3);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(82, 106, 214, 0.9),
                    stop:1 rgba(98, 55, 142, 0.9));
                transform: translateY(0px);
            }
            QPushButton:disabled {
                background: rgba(255, 255, 255, 0.1);
                color: rgba(255, 255, 255, 0.4);
                border: 1px solid rgba(255, 255, 255, 0.05);
            }
            QLabel {
                color: rgba(255, 255, 255, 0.9);
                font-size: 13px;
                font-weight: 500;
            }
            QGroupBox {
                font-weight: 600;
                border: 1px solid rgba(255, 255, 255, 0.15);
                border-radius: 12px;
                margin-top: 12px;
                padding-top: 16px;
                background: rgba(255, 255, 255, 0.05);
                backdrop-filter: blur(5px);
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top center;
                padding: 4px 12px;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(102, 126, 234, 0.9),
                    stop:1 rgba(118, 75, 162, 0.9));
                border-radius: 8px;
                font-size: 12px;
                font-weight: 700;
                color: white;
                border: 1px solid rgba(255, 255, 255, 0.2);
            }
        """)
        self.sidebar.setMinimumWidth(340)
        self.sidebar.setMaximumWidth(420)
        
        # Scrollbereich für Sidebar
        scroll = QScrollArea()
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background: transparent;
            }
            QScrollBar:vertical {
                background: rgba(255, 255, 255, 0.1);
                width: 8px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background: rgba(255, 255, 255, 0.3);
                border-radius: 4px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background: rgba(255, 255, 255, 0.5);
            }
        """)
        
        sidebar_content = QWidget()
        layout = QVBoxLayout(sidebar_content)
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)
        
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
        sidebar_layout.setContentsMargins(8, 8, 8, 8)
        sidebar_layout.addWidget(scroll)
        
        return self.sidebar
    
    def _create_title_section(self, layout):
        """Titel und Benutzerstatus erstellen."""
        # Titel mit modernem Gradient
        title = QLabel("KI-Objekterkennung")
        title.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("""
            QLabel {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #ff6b6b, stop:0.5 #ffd93d, stop:1 #6bcf7f);
                -webkit-background-clip: text;
                color: white;
                padding: 12px;
                border-radius: 12px;
                border: 1px solid rgba(255, 255, 255, 0.2);
                backdrop-filter: blur(10px);
            }
        """)
        layout.addWidget(title)
        
        # Benutzerstatus mit Card-Design
        user_group = QGroupBox("Benutzer")
        user_layout = QVBoxLayout(user_group)
        user_layout.setSpacing(8)
        
        user_info_layout = QHBoxLayout()
        self.user_label = QLabel("Benutzer: Gast")
        self.user_label.setStyleSheet("""
            color: rgba(255, 255, 255, 0.9); 
            background: rgba(255, 255, 255, 0.1); 
            padding: 8px 12px; 
            border-radius: 8px; 
            font-size: 12px;
            font-weight: 500;
            border: 1px solid rgba(255, 255, 255, 0.15);
        """)
        user_info_layout.addWidget(self.user_label, 1)
        
        self.login_btn = QPushButton("Login")
        self.login_btn.setMaximumWidth(60)
        self.login_btn.setToolTip("Admin Login")
        self.login_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #667eea, stop:1 #764ba2);
                font-size: 11px;
                padding: 8px 12px;
                min-height: 12px;
            }
        """)
        user_info_layout.addWidget(self.login_btn)
        
        user_layout.addLayout(user_info_layout)
        layout.addWidget(user_group)
    
    def _create_modbus_section(self, layout):
        """WAGO Modbus Status-Sektion mit modernem Design erstellen."""
        modbus_group = QGroupBox("WAGO Modbus")
        modbus_layout = QVBoxLayout(modbus_group)
        modbus_layout.setSpacing(8)
        
        # Verbindungsstatus mit Neon-Effekt
        connection_layout = QHBoxLayout()
        connection_layout.addWidget(QLabel("Status:"))
        self.modbus_status = QLabel("Getrennt")
        self.modbus_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.modbus_status.setStyleSheet("""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #ff416c, stop:1 #ff4757);
            color: white;
            padding: 8px;
            border-radius: 8px;
            font-weight: 700;
            font-size: 11px;
            border: 1px solid rgba(255, 255, 255, 0.2);
            box-shadow: 0 4px 15px rgba(255, 65, 108, 0.3);
        """)
        connection_layout.addWidget(self.modbus_status, 1)
        modbus_layout.addLayout(connection_layout)
        
        # IP-Adresse mit Glass-Card
        ip_layout = QHBoxLayout()
        ip_layout.addWidget(QLabel("IP:"))
        self.modbus_ip = QLabel("192.168.1.100")
        self.modbus_ip.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.modbus_ip.setStyleSheet("""
            background: rgba(255, 255, 255, 0.1);
            padding: 8px;
            border-radius: 8px;
            font-size: 11px;
            font-weight: 500;
            border: 1px solid rgba(255, 255, 255, 0.15);
            backdrop-filter: blur(5px);
        """)
        ip_layout.addWidget(self.modbus_ip, 1)
        modbus_layout.addLayout(ip_layout)
        
        # Coil-Status mit modernen Indikatoren
        coils_layout = QHBoxLayout()
        coils_layout.addWidget(QLabel("Coils:"))
        
        # Reject Coil mit Pulsing-Effekt
        self.reject_coil_indicator = QLabel("R")
        self.reject_coil_indicator.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.reject_coil_indicator.setFixedSize(24, 24)
        self.reject_coil_indicator.setStyleSheet("""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 rgba(108, 117, 125, 0.8),
                stop:1 rgba(134, 142, 150, 0.8));
            color: white;
            border-radius: 12px;
            font-weight: bold;
            font-size: 10px;
            border: 2px solid rgba(255, 255, 255, 0.2);
        """)
        self.reject_coil_indicator.setToolTip("Reject/Ausschuss Coil")
        coils_layout.addWidget(self.reject_coil_indicator)
        
        # Detection Active Coil
        self.detection_coil_indicator = QLabel("D")
        self.detection_coil_indicator.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.detection_coil_indicator.setFixedSize(24, 24)
        self.detection_coil_indicator.setStyleSheet("""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 rgba(108, 117, 125, 0.8),
                stop:1 rgba(134, 142, 150, 0.8));
            color: white;
            border-radius: 12px;
            font-weight: bold;
            font-size: 10px;
            border: 2px solid rgba(255, 255, 255, 0.2);
        """)
        self.detection_coil_indicator.setToolTip("Detection Active Coil")
        coils_layout.addWidget(self.detection_coil_indicator)
        
        modbus_layout.addLayout(coils_layout)
        
        # Erweiterte Modbus-Aktionen mit Premium-Buttons
        actions_layout = QHBoxLayout()
        
        # Reset Button
        self.modbus_reset_btn = QPushButton("Reset")
        self.modbus_reset_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #ff9a56, stop:1 #ff6b35);
                font-size: 11px;
                min-height: 28px;
                padding: 6px 12px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #ff8a46, stop:1 #ff5b25);
                box-shadow: 0 6px  20px rgba(255, 154, 86, 0.4);
            }
        """)
        self.modbus_reset_btn.setToolTip("WAGO Controller zurücksetzen")
        self.modbus_reset_btn.clicked.connect(self.reset_modbus_controller)
        actions_layout.addWidget(self.modbus_reset_btn)
        
        # Reconnect Button
        self.modbus_reconnect_btn = QPushButton("Neuverbindung")
        self.modbus_reconnect_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #667eea, stop:1 #764ba2);
                font-size: 11px;
                min-height: 28px;
                padding: 6px 12px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #5a72ea, stop:1 #6a3b92);
                box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
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
        """Workflow-Status mit Motion und Helligkeit in modernem Design."""
        workflow_group = QGroupBox("Status & Sensoren")
        workflow_layout = QVBoxLayout(workflow_group)
        workflow_layout.setSpacing(8)
        
        # Workflow-Status mit Gradient
        workflow_info_layout = QHBoxLayout()
        workflow_info_layout.addWidget(QLabel("Workflow:"))
        self.workflow_info = QLabel("READY")
        self.workflow_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.workflow_info.setStyleSheet("""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 rgba(255, 255, 255, 0.15),
                stop:1 rgba(255, 255, 255, 0.05));
            color: white;
            padding: 10px;
            border-radius: 10px;
            font-weight: 700;
            font-size: 12px;
            border: 1px solid rgba(255, 255, 255, 0.2);
            backdrop-filter: blur(10px);
        """)
        workflow_info_layout.addWidget(self.workflow_info, 1)
        workflow_layout.addLayout(workflow_info_layout)
        
        # Motion-Wert mit modernem Indikator
        motion_layout = QHBoxLayout()
        motion_layout.addWidget(QLabel("Motion:"))
        self.motion_info = QLabel("--")
        self.motion_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.motion_info.setStyleSheet("""
            background: rgba(255, 255, 255, 0.1);
            padding: 8px;
            border-radius: 8px;
            font-weight: 600;
            min-width: 60px;
            font-size: 12px;
            border: 1px solid rgba(255, 255, 255, 0.15);
        """)
        motion_layout.addWidget(self.motion_info)
        workflow_layout.addLayout(motion_layout)
        
        # Helligkeitsanzeige mit Glow-Effekt
        brightness_layout = QHBoxLayout()
        brightness_layout.addWidget(QLabel("Helligkeit:"))
        self.brightness_info = QLabel("--")
        self.brightness_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.brightness_info.setStyleSheet("""
            background: rgba(255, 255, 255, 0.1);
            padding: 8px;
            border-radius: 8px;
            font-weight: 600;
            min-width: 60px;
            font-size: 12px;
            border: 1px solid rgba(255, 255, 255, 0.15);
        """)
        brightness_layout.addWidget(self.brightness_info)
        workflow_layout.addLayout(brightness_layout)
        
        # Helligkeitswarnung mit Neon-Effekt
        self.brightness_warning = QLabel("Beleuchtung prüfen!")
        self.brightness_warning.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.brightness_warning.setStyleSheet("""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #ff416c, stop:1 #ff4757);
            color: white;
            padding: 8px;
            border-radius: 8px;
            font-weight: 700;
            font-size: 11px;
            border: 1px solid rgba(255, 255, 255, 0.3);
            box-shadow: 0 0 20px rgba(255, 65, 108, 0.5);
        """)
        self.brightness_warning.setVisible(False)
        workflow_layout.addWidget(self.brightness_warning)
        
        layout.addWidget(workflow_group)
    
    def _create_model_section(self, layout):
        """Modell-Sektion mit modernem Card-Design erstellen."""
        model_group = QGroupBox("KI-Modell")
        model_layout = QVBoxLayout(model_group)
        model_layout.setSpacing(8)
        
        self.model_info = QLabel("Kein Modell geladen")
        self.model_info.setWordWrap(True)
        self.model_info.setStyleSheet("""
            color: rgba(255, 255, 255, 0.7); 
            font-style: italic; 
            font-size: 11px;
            background: rgba(255, 255, 255, 0.05);
            padding: 8px;
            border-radius: 8px;
            border: 1px solid rgba(255, 255, 255, 0.1);
        """)
        model_layout.addWidget(self.model_info)
        
        self.model_btn = QPushButton("Modell laden")
        self.model_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #ff6b6b, stop:1 #ee5a52);
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #ff5b5b, stop:1 #de4a42);
                box-shadow: 0 8px 25px rgba(255, 107, 107, 0.4);
            }
        """)
        model_layout.addWidget(self.model_btn)
        
        layout.addWidget(model_group)
    
    def _create_camera_section(self, layout):
        """Kamera-Sektion mit modernem Design erstellen."""
        camera_group = QGroupBox("Kamera/Video")
        camera_layout = QVBoxLayout(camera_group)
        camera_layout.setSpacing(8)
        
        self.camera_info = QLabel("Keine Quelle ausgewählt")
        self.camera_info.setWordWrap(True)
        self.camera_info.setStyleSheet("""
            color: rgba(255, 255, 255, 0.7); 
            font-style: italic; 
            font-size: 11px;
            background: rgba(255, 255, 255, 0.05);
            padding: 8px;
            border-radius: 8px;
            border: 1px solid rgba(255, 255, 255, 0.1);
        """)
        camera_layout.addWidget(self.camera_info)
        
        self.camera_btn = QPushButton("Quelle wählen")
        self.camera_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #74b9ff, stop:1 #0984e3);
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #64a9ef, stop:1 #0974d3);
                box-shadow: 0 8px 25px rgba(116, 185, 255, 0.4);
            }
        """)
        camera_layout.addWidget(self.camera_btn)
        
        layout.addWidget(camera_group)
    
    def _create_stats_section(self, layout):
        """Statistiken-Sektion mit modernem Tabellen-Design erstellen."""
        stats_group = QGroupBox("Letzte Erkennung")
        stats_layout = QVBoxLayout(stats_group)
        stats_layout.setSpacing(8)
        
        # Aktuelle Frame-Erkennungen mit Highlight
        self.current_frame_label = QLabel("Aktuell: 0")
        self.current_frame_label.setStyleSheet("""
            color: white; 
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #ffd93d, stop:1 #ff6b35);
            padding: 8px; 
            border-radius: 8px; 
            font-size: 11px;
            font-weight: 600;
            border: 1px solid rgba(255, 255, 255, 0.2);
        """)
        stats_layout.addWidget(self.current_frame_label)
        
        # Detaillierte Tabelle mit modernem Design
        self.last_cycle_table = QTableWidget(0, 3)
        self.last_cycle_table.setHorizontalHeaderLabels(["Klasse", "Anz", "Max"])
        self.last_cycle_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.last_cycle_table.verticalHeader().hide()
        self.last_cycle_table.setMaximumHeight(150)
        self.last_cycle_table.setStyleSheet("""
            QTableWidget {
                background: rgba(255, 255, 255, 0.08);
                color: white;
                border: 1px solid rgba(255, 255, 255, 0.15);
                border-radius: 8px;
                font-size: 11px;
                font-weight: 500;
                gridline-color: rgba(255, 255, 255, 0.1);
            }
            QTableWidget::item {
                padding: 6px;
                border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            }
            QTableWidget::item:selected {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(102, 126, 234, 0.5),
                    stop:1 rgba(118, 75, 162, 0.5));
            }
            QHeaderView::section {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(26, 35, 126, 0.8),
                    stop:1 rgba(49, 27, 146, 0.8));
                color: white;
                border: 1px solid rgba(255, 255, 255, 0.2);
                padding: 8px;
                font-size: 11px;
                font-weight: 700;
                border-radius: 4px;
            }
        """)