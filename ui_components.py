"""
UI-Komponenten - kompakt und fokussiert mit Counter und Motion-Anzeige
Status zwischen Menü und Counter, Motion-Wert-Anzeige wie Helligkeit
"""

import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
    QSplitter, QFrame, QFileDialog, QDialog, QSpinBox,
    QDoubleSpinBox, QCheckBox, QFormLayout, QMessageBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QToolButton, QListWidget,
    QGroupBox, QScrollArea, QProgressBar
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QPixmap, QFont, QColor
import cv2
import numpy as np

class MainUI(QWidget):
    """Hauptbenutzeroberfläche mit kompakter Sidebar und Counter."""
    
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
        
        # Titel und Benutzerstatus (kompakt)
        title = QLabel("KI-Objekterkennung")
        title.setFont(QFont("", 16, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Benutzerstatus (kompakt)
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
        
        # Workflow-Status mit Motion und Helligkeit
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
        
        # Motion-Wert Anzeige (wie Helligkeit)
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
        
        # Helligkeitsanzeige (kompakt)
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
        
        # Modell-Sektion (kompakt)
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
        
        # Kamera-Sektion (kompakt)
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
        
        # Letzte Erkennung (NICHT Session-Summen)
        stats_group = QGroupBox("Letzte Erkennung")
        stats_layout = QVBoxLayout(stats_group)
        stats_layout.setSpacing(5)
        
        # Aktuelle Frame-Erkennungen (kompakt)
        self.current_frame_label = QLabel("Aktuell: 0")
        self.current_frame_label.setStyleSheet("color: #f39c12; background-color: #34495e; padding: 3px; border-radius: 3px; font-size: 11px;")
        stats_layout.addWidget(self.current_frame_label)
        
        # Detaillierte Tabelle für LETZTEN Zyklus (kompakter)
        self.last_cycle_table = QTableWidget(0, 3)  # 3 Spalten
        self.last_cycle_table.setHorizontalHeaderLabels(["Klasse", "Anz", "Max"])
        self.last_cycle_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.last_cycle_table.verticalHeader().hide()
        self.last_cycle_table.setMaximumHeight(150)  # Kompakter
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
        
        # Aktionen (kompakt)
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
        
        # Stretch am Ende
        layout.addStretch()
        
        # Sidebar-Content zu Scroll hinzufügen
        scroll.setWidget(sidebar_content)
        
        # Scroll zu Sidebar hinzufügen
        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.addWidget(scroll)
        
        return self.sidebar
    
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
        
        # 2. STATUS IN DER MITTE (zwischen Menü und Counter)
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
        
        # 3. COUNTER (rechts oben, minimalistisch aber funktional)
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
        
        # Reset Button (minimalistisch)
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
        
        layout.addLayout(header_layout)
        
        # Video-Bereich (ohne separaten Status, da Status jetzt im Header ist)
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
        layout.addWidget(self.video_label, 1)  # Stretch factor 1
        
        return main_area
    
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
        """Status im Header anzeigen (zwischen Menü und Counter)."""
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
        """Motion-Wert aktualisieren (wie Helligkeit)."""
        self.motion_info.setText(f"{motion_value:.0f}")
        
        # Farbe je nach Motion-Level  
        # Niedrige Werte = ruhig (grün), hohe Werte = Bewegung (orange/rot)
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
            color = "#f39c12"  # Orange (zu hell)
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
        """Letzte Erkennungen aktualisieren (NICHT Session-Summen!)."""
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
    
    def select_model_file(self):
        """Modell-Datei auswählen Dialog."""
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
    """Erweiterte Einstellungen-Dialog für Workflow ohne Helligkeits-Limits."""
    
    def __init__(self, settings, parent=None):
        super().__init__(parent)
        self.settings = settings
        self.setWindowTitle("Workflow-Einstellungen")
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
        ki_label = QLabel("KI-Einstellungen")
        ki_label.setFont(QFont("", 12, QFont.Weight.Bold))
        form_layout.addRow(ki_label)
        
        self.confidence_spin = QDoubleSpinBox()
        self.confidence_spin.setRange(0.1, 1.0)
        self.confidence_spin.setSingleStep(0.1)
        self.confidence_spin.setDecimals(2)
        form_layout.addRow("Konfidenz-Schwellwert:", self.confidence_spin)
        
        # Workflow
        workflow_label = QLabel("Workflow")
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
        
        # Schlecht-Teil Konfiguration
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
        
        # Helligkeitsüberwachung (OHNE Limits, nur Low < High)
        brightness_label = QLabel("Helligkeitsüberwachung")
        brightness_label.setFont(QFont("", 12, QFont.Weight.Bold))
        form_layout.addRow(brightness_label)
        
        self.brightness_low_spin = QSpinBox()
        self.brightness_low_spin.setRange(0, 254)  # Kann bis 254 gehen
        self.brightness_low_spin.valueChanged.connect(self.validate_brightness_ranges)
        form_layout.addRow("Untere Schwelle:", self.brightness_low_spin)
        
        self.brightness_high_spin = QSpinBox()
        self.brightness_high_spin.setRange(1, 255)  # Kann ab 1 starten
        self.brightness_high_spin.valueChanged.connect(self.validate_brightness_ranges)
        form_layout.addRow("Obere Schwelle:", self.brightness_high_spin)
        
        self.brightness_duration_spin = QDoubleSpinBox()
        self.brightness_duration_spin.setRange(1.0, 30.0)
        self.brightness_duration_spin.setSingleStep(0.5)
        form_layout.addRow("Warndauer (Sekunden):", self.brightness_duration_spin)
        
        # Video-Einstellungen
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
        
        # Anzeige-Optionen
        display_label = QLabel("Anzeige-Optionen")
        display_label.setFont(QFont("", 12, QFont.Weight.Bold))
        form_layout.addRow(display_label)
        
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