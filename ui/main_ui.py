"""
Hauptbenutzeroberflaeche - REFACTORED Version mit Referenzlinien-Overlay
Übersichtlicher Code durch Auslagerung der Style-Definitionen
ERWEITERT: Referenzlinien-Overlay über Video-Stream und 50% höhere Sidebar-Tabelle
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
from .styles import UIStyles
from .reference_line_overlay import ReferenceLineOverlay
from .camera_overlay_button import CameraOverlayButton

class MainUI(QWidget):
    """Hauptbenutzeroberflaeche mit externen Stylesheets und Referenzlinien-Overlay."""
    
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

        # Platzhalter fuer spaeter erzeugte Widgets
        self.motion_info = QLabel("--")
        self.motion_status = QLabel("Unkalibriert")
        
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
        """Kompakte Sidebar erstellen."""
        self.sidebar = QFrame()
        self.sidebar.setStyleSheet(UIStyles.get_sidebar_base_style())
        self.sidebar.setMinimumWidth(300)
        self.sidebar.setMaximumWidth(380)
        
        # KOMPAKTES Layout
        sidebar_content = QWidget()
        layout = QVBoxLayout(sidebar_content)
        layout.setSpacing(15)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Benutzer-Status
        self._create_login_status_section(layout)
        
        # Aktionen
        self._create_actions_section(layout)
        
        # KI-Modell
        self._create_model_status_section(layout)
        
        # Kamera-Video
        self._create_camera_status_section(layout)
        
        # Letzte Erkennung - ERWEITERT: 50% höher
        self._create_stats_section(layout)
        
        # Status Grenzwerte + WAGO Modbus
        self._create_united_status_section(layout)
                
        # ESC Hinweis + Footer
        self._create_esc_hint(layout)
        
        # Content zu Sidebar hinzufügen
        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.addWidget(sidebar_content)
            
        return self.sidebar
    
    def _create_login_status_section(self, layout):
        """Logo und Login-Status-Button erstellen."""
        # Logo hinzufügen
        self._create_logo_section(layout)
        
        # Login-Status-Button
        self.login_status_btn = QPushButton("Benutzerstatus: Operator")
        self.login_status_btn.setStyleSheet(UIStyles.get_login_button_operator_style())
        self.login_status_btn.setToolTip("Klicken für Admin-Login/Logout")
        layout.addWidget(self.login_status_btn)

    def _create_logo_section(self, layout):
        """Logo-Sektion erstellen."""
        import os
        from PyQt6.QtGui import QPixmap
        from PyQt6.QtCore import Qt
        
        # Logo-Container erstellen
        logo_container = QWidget()
        logo_layout = QVBoxLayout(logo_container)
        logo_layout.setContentsMargins(10, 15, 10, 10)
        logo_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Logo-Label erstellen
        self.logo_label = QLabel()
        self.logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Logo laden
        logo_path = os.path.join("img", "LOGO.png")
        if os.path.exists(logo_path):
            try:
                pixmap = QPixmap(logo_path)
                if not pixmap.isNull():
                    # Logo auf Sidebar-Breite skalieren (max 320px für etwas Padding)
                    scaled_pixmap = pixmap.scaled(
                        320, 92,  # Maximale Breite und Höhe
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation
                    )
                    self.logo_label.setPixmap(scaled_pixmap)
                    self.logo_label.setStyleSheet("""
                        QLabel {
                            background-color: transparent;
                            padding: 5px;
                            border-radius: 8px;
                        }
                    """)
                    logging.info(f"Logo erfolgreich geladen: {logo_path}")
                else:
                    self._create_fallback_logo()
                    logging.warning(f"Logo konnte nicht geladen werden: {logo_path}")
            except Exception as e:
                self._create_fallback_logo()
                logging.error(f"Fehler beim Laden des Logos: {e}")
        else:
            self._create_fallback_logo()
            logging.warning(f"Logo-Datei nicht gefunden: {logo_path}")
        
        logo_layout.addWidget(self.logo_label)
        layout.addWidget(logo_container)

    def _create_fallback_logo(self):
        """Fallback-Logo erstellen wenn Datei nicht gefunden."""
        self.logo_label.setText("INSPECTUBE\nKI-OBJEKTERKENNUNG")
        self.logo_label.setStyleSheet("""
            QLabel {
                background-color: rgba(52, 73, 94, 0.8);
                color: white;
                font-size: 16px;
                font-weight: bold;
                text-align: center;
                padding: 20px 10px;
                border-radius: 8px;
                border: 2px solid rgba(255, 255, 255, 0.1);
            }
        """)

    def _create_model_status_section(self, layout):
        """Konfigurations-Button erstellen (ersetzt Modell- und Moduswahl)."""
        self.config_btn = QPushButton("Konfiguration laden")
        self.config_btn.setStyleSheet(UIStyles.get_model_button_inactive_style())
        self.config_btn.setToolTip("Produktkonfiguration laden oder erstellen")
        layout.addWidget(self.config_btn)

    def _create_camera_status_section(self, layout):
        """Platzhalter fuer alte Kamera-Sektion (entfernt)."""
        pass

    def _create_actions_section(self, layout):
        """Aktionen erstellen."""
        actions_layout = QVBoxLayout()
        actions_layout.setSpacing(8)

        self.start_btn = QPushButton("▶ Live Detection STARTEN")
        self.start_btn.setStyleSheet(UIStyles.get_start_button_style())
        actions_layout.addWidget(self.start_btn)
        
        # ENTFERNT: Snapshot-Button
        # self.snapshot_btn = QPushButton("Schnappschuss")
        # self.snapshot_btn.setStyleSheet(UIStyles.get_snapshot_button_style())
        # actions_layout.addWidget(self.snapshot_btn)
        
        layout.addLayout(actions_layout)

    def _create_stats_section(self, layout):
        """Statistiken erstellen - ERWEITERT: 50% höher."""
        self.last_cycle_table = QTableWidget(0, 5)
        self.last_cycle_table.setHorizontalHeaderLabels(["Klasse", "Img", "Min", "Max", "Anz"])
        self.last_cycle_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.last_cycle_table.verticalHeader().hide()
        
        self.last_cycle_table.setMaximumHeight(240) 
        self.last_cycle_table.setMinimumHeight(180)
        
        self.last_cycle_table.setStyleSheet(UIStyles.get_stats_table_style())
        layout.addWidget(self.last_cycle_table)

    def _create_united_status_section(self, layout):
        """VEREINT: Status Grenzwerte + WAGO Modbus erstellen."""
        status_layout = QVBoxLayout()
        status_layout.setSpacing(6)  # Einheitlicher Abstand zwischen Zeilen
        status_layout.setContentsMargins(0, 0, 0, 0)  # Keine äusseren Abstände
        
        # Kompakte Hilfsfunktion für Status-Zeilen mit einheitlicher Breite
        def _add_compact_status_row(label_text, value_widget, tooltip_text="", extra_widget=None):
            row_layout = QHBoxLayout()
            row_layout.setSpacing(8)
            row_layout.setContentsMargins(0, 2, 0, 2)  # Einheitliche Abstände
            
            label = QLabel(label_text)
            label.setStyleSheet(UIStyles.get_compact_status_label_style())
            label.setFixedWidth(90)  # Breiter für "Ausgänge:" und "Helligkeit:"
            label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            if tooltip_text:
                label.setToolTip(tooltip_text)
            
            # Value-Widget einheitliche Eigenschaften geben
            value_widget.setMinimumWidth(120)  # Etwas breiter für bessere Proportionen
            value_widget.setMaximumWidth(120)  # Feste Breite
            value_widget.setFixedHeight(32)    # Feste Höhe
            
            row_layout.addWidget(label)
            row_layout.addWidget(value_widget)
            
            # Extra-Widget hinzufügen falls vorhanden
            if extra_widget:
                extra_widget.setMinimumWidth(120)
                extra_widget.setMaximumWidth(120)
                extra_widget.setFixedHeight(32)
                row_layout.addWidget(extra_widget)
            else:
                # Spacer hinzufügen wenn kein extra_widget, damit Zeilen gleich aussehen
                row_layout.addStretch()
            
            status_layout.addLayout(row_layout)

        # Workflow-Status
        self.workflow_info = QLabel("BEREIT")
        self.workflow_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.workflow_info.setStyleSheet(UIStyles.get_unified_status_widget_style("#34495e"))
        _add_compact_status_row("Workflow:", self.workflow_info)
        
        # Motion-Wert mit Status
        self.motion_info = QLabel("--")
        self.motion_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.motion_info.setStyleSheet(UIStyles.get_unified_status_widget_style("#878787"))
        self.motion_info.setToolTip("Aktueller Motion-Wert")

        self.motion_status = QLabel("Kalibriert OK")
        self.motion_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.motion_status.setStyleSheet(UIStyles.get_unified_status_widget_style("#27ae60"))
        self.motion_status.setToolTip("Motion-Kalibrierungsstatus")

        _add_compact_status_row("Bewegung:", self.motion_info, extra_widget=self.motion_status)

        # Helligkeit mit Warnung (immer angezeigt, aber Inhalt ändert sich)
        self.brightness_info = QLabel("--")
        self.brightness_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.brightness_info.setStyleSheet(UIStyles.get_unified_status_widget_style("#878787"))
        self.brightness_info.setToolTip("Aktuelle Helligkeit")

        self.brightness_warning = QLabel("OK")  # Standardtext statt versteckt
        self.brightness_warning.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.brightness_warning.setStyleSheet(UIStyles.get_unified_status_widget_style("#27ae60"))
        self.brightness_warning.setToolTip("Helligkeitsstatus")

        _add_compact_status_row("Helligkeit:", self.brightness_info, extra_widget=self.brightness_warning)
        
        # WAGO Status mit IP
        self.modbus_status = QLabel("Getrennt")
        self.modbus_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.modbus_status.setStyleSheet(UIStyles.get_unified_status_widget_style("#e74c3c"))
        self.modbus_status.setToolTip("WAGO Modbus Status")

        self.modbus_ip = QLabel("Keine Verbindung")
        self.modbus_ip.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.modbus_ip.setStyleSheet(UIStyles.get_unified_status_widget_style("#7f8c8d"))
        self.modbus_ip.setToolTip("WAGO Modbus IP-Adresse")

        _add_compact_status_row("WAGO:", self.modbus_status, extra_widget=self.modbus_ip)
                
        # Ausgänge - WAGO Modbus-Ausgänge
        self.reject_coil_indicator = QLabel("Ausschuss")
        self.reject_coil_indicator.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.reject_coil_indicator.setStyleSheet(UIStyles.get_unified_status_widget_style("#7f8c8d"))
        self.reject_coil_indicator.setToolTip("Ausschuss Modbus Ausgang")

        self.detection_coil_indicator = QLabel("SEPRO Ablage")
        self.detection_coil_indicator.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.detection_coil_indicator.setStyleSheet(UIStyles.get_unified_status_widget_style("#7f8c8d"))
        self.detection_coil_indicator.setToolTip("SEPRO Ablage Modbus Ausgang")

        _add_compact_status_row("Ausgänge:", self.reject_coil_indicator, extra_widget=self.detection_coil_indicator)
        
        layout.addLayout(status_layout)

    def _create_esc_hint(self, layout):    
        # BEENDEN Button mit Bestätigungsdialog
        self.quit_btn = QPushButton("SOFTWARE BEENDEN")
        self.quit_btn.setStyleSheet(UIStyles.get_quit_button_style())
        self.quit_btn.setToolTip("Anwendung beenden (ESC druecken)")
        layout.addWidget(self.quit_btn)

        # ESC-Hinweis
        esc_hint = QLabel("ESC = Applikation Beenden")
        esc_hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        esc_hint.setStyleSheet(UIStyles.get_esc_hint_style())
        layout.addWidget(esc_hint)
        
        # INSPECTUBE Footer
        self.footer_label = QPushButton("INSPECTUBE by Michel Marty")
        self.footer_label.setStyleSheet(UIStyles.get_footer_button_style())
        self.footer_label.clicked.connect(self._show_smiley)
        layout.addWidget(self.footer_label)

    def _confirm_quit(self):
        """Bestätigungsdialog vor dem Beenden der Anwendung."""
        reply = QMessageBox.question(
            self,
            "Anwendung beenden",
            "Möchten Sie die Anwendung wirklich beenden?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No  # Standard: Nein
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.app.quit_application()

    def _show_smiley(self):
        """Zeigt einen kleinen Smiley wenn auf den Footer geklickt wird."""
        original_text = self.footer_label.text()
        self.footer_label.setText("INSPECTUBE by Michel Marty 😊")
        QTimer.singleShot(2000, lambda: self.footer_label.setText(original_text))
    
    def on_user_status_changed(self, new_status):
        """Callback fuer User-Status-Änderungen."""
        self.update_user_interface()
        if new_status == "Operator":
            self.app.ui.show_status("Automatischer Logout - Operator-Modus", "warning")
    
    def create_main_area(self):
        """Hauptbereich erstellen."""
        main_area = QFrame()
        main_area.setStyleSheet(UIStyles.get_main_area_base_style())
        
        layout = QVBoxLayout(main_area)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Header mit: [Menue-Button] [⚙️ Einstellungen] [Status] [Counter]
        header_layout = QHBoxLayout()
        header_layout.setSpacing(20)
        
        # 1. Sidebar Toggle Button
        self.sidebar_toggle_btn = QToolButton()
        self.sidebar_toggle_btn.setText("≡")
        self.sidebar_toggle_btn.setStyleSheet(UIStyles.get_sidebar_toggle_button_style())
        header_layout.addWidget(self.sidebar_toggle_btn, 0, Qt.AlignmentFlag.AlignLeft)
        
        # 2. Einstellungen-Button
        self.settings_btn = QPushButton("⚙️")
        self.settings_btn.setStyleSheet(UIStyles.get_settings_button_style())
        self.settings_btn.setToolTip("Einstellungen (Admin-Rechte erforderlich)")
        header_layout.addWidget(self.settings_btn, 0, Qt.AlignmentFlag.AlignLeft)
        
        # 3. STATUS IN DER MITTE
        self.status_label = QLabel("Bereit")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setFont(QFont("", 16, QFont.Weight.Bold))
        self.status_label.setStyleSheet(UIStyles.get_status_label_style("#95a5a6"))
        header_layout.addWidget(self.status_label, 1)
        
        # 4. KOMPAKTER COUNTER
        self._create_compact_counter_section(header_layout)
        
        layout.addLayout(header_layout)
        
        # Video-Bereich mit Referenzlinien-Overlay
        self._create_video_area(layout)
        
        # Referenz fuer das Main Area Frame speichern (fuer Blinken)
        self.main_area_frame = main_area
        
        return main_area
    
    def _create_video_area(self, layout):
        """Video-Bereich mit Referenzlinien-Overlay und Kamera-Button erstellen."""
        # Container für Video + Overlays
        self.video_container = QWidget()
        self.video_container.setMinimumSize(640, 480)
        
        # Video-Label
        self.video_label = QLabel(self.video_container)
        self.video_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.video_label.setMinimumSize(640, 480)
        self.video_label.setStyleSheet(UIStyles.get_video_label_base_style())
        self.video_label.setText("Kein Stream verfuegbar")
        
        # Referenzlinien-Overlay
        self.reference_overlay = ReferenceLineOverlay(self.video_container)
        
        # NEUER KAMERA-OVERLAY-BUTTON
        self.camera_overlay_btn = CameraOverlayButton(self.video_container)
        self.camera_overlay_btn.snapshot_requested.connect(self.app.take_snapshot)
        
        # Layout für Video-Container
        video_layout = QVBoxLayout(self.video_container)
        video_layout.setContentsMargins(0, 0, 0, 0)
        video_layout.addWidget(self.video_label)
        
        # Overlays über Video legen
        self.video_label.resizeEvent = self._on_video_resize
        
        layout.addWidget(self.video_container, 1)
    
    def _on_video_resize(self, event):
        """Video-Label wurde resized - Overlays anpassen."""
        # Overlay exakt über Video-Label positionieren
        self.reference_overlay.setGeometry(self.video_label.geometry())
        
        # Kamera-Button in oberer linker Ecke positionieren (mit 10px Abstand)
        video_rect = self.video_label.geometry()
        self.camera_overlay_btn.move(video_rect.x() + 10, video_rect.y() + 10)
        
        # Original resizeEvent aufrufen
        QLabel.resizeEvent(self.video_label, event)
    
    def _create_compact_counter_section(self, header_layout):
        """KOMPAKTER Counter-Sektion im Header erstellen"""
        from PyQt6.QtWidgets import QGraphicsDropShadowEffect, QWidget, QFrame, QHBoxLayout, QVBoxLayout, QLabel, QPushButton
        from PyQt6.QtCore import Qt
        from PyQt6.QtGui import QColor, QFont

        # Frame mit Schatten und Hintergrund
        self.counter_frame = QFrame()
        self.counter_frame.setStyleSheet(UIStyles.get_counter_frame_style())
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
            vbox.setSpacing(2)
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
        self.reset_counter_btn.setStyleSheet(UIStyles.get_reset_counter_button_style())
        self.reset_counter_btn.clicked.connect(self.reset_session_counter)
        self.reset_counter_btn.setToolTip("Counter zuruecksetzen (Admin-Rechte erforderlich)")
        counter_layout.addWidget(self.reset_counter_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        # Hohe begrenzen
        self.counter_frame.setMaximumHeight(140)
        header_layout.addWidget(self.counter_frame, 0, Qt.AlignmentFlag.AlignRight)

    # =============================================================================
    # REFERENZLINIEN-MANAGEMENT
    # =============================================================================
    
    def update_reference_lines(self):
        """Referenzlinien aus Settings aktualisieren."""
        try:
            if hasattr(self, 'reference_overlay'):
                reference_lines = self.app.settings.get('reference_lines', [])
                self.reference_overlay.update_reference_lines(reference_lines)
                logging.debug(f"Referenzlinien aktualisiert: {len(reference_lines)} Linien")
        except Exception as e:
            logging.error(f"Fehler beim Aktualisieren der Referenzlinien: {e}")

    # =============================================================================
    # FLASH ANIMATION METHODEN
    # =============================================================================
    
    def flash_red_on_bad_part_detection(self):
        """Startet rotes Blinken bei Schlecht-Teil-Erkennung."""
        if self.is_flashing:
            return
        
        logging.info("Starte rotes Blinken bei Schlecht-Teil-Erkennung")
        self.is_flashing = True
        self.flash_count = 0
        self.flash_timer.start(150)  # 150ms Interval
    
    def _flash_step(self):
        """Ein Schritt des Blinkens (wird alle 100ms aufgerufen)."""
        if self.flash_count >= 4:
            self.flash_timer.stop()
            self.is_flashing = False
            self.flash_count = 0
            self._reset_flash_colors()
            return
        
        # Blinken zwischen rot und normal
        if self.flash_count % 2 == 0:
            self._set_flash_red()
        else:
            self._reset_flash_colors()
        
        self.flash_count += 1
        
    def _set_flash_red(self):
        """Setze rote Blink-Farben - GLEICHE MARGINS/PADDINGS."""
        # Main Area rot
        self.main_area_frame.setStyleSheet(UIStyles.get_main_area_flash_style())
        
        # Video-Label auch rot
        self.video_label.setStyleSheet(UIStyles.get_video_label_flash_style())
        
        # Sidebar komplett rot
        self.sidebar.setStyleSheet(UIStyles.get_sidebar_flash_style())

        # Logo-Hintergrund auch rot machen (falls vorhanden)
        if hasattr(self, 'logo_label') and self.logo_label.pixmap() is None:
            # Nur bei Text-Fallback-Logo
            self.logo_label.setStyleSheet("""
                QLabel {
                    background-color: rgba(231, 76, 60, 0.9) !important;
                    color: white;
                    font-size: 16px;
                    font-weight: bold;
                    text-align: center;
                    padding: 20px 10px;
                    border-radius: 8px;
                    border: 2px solid rgba(255, 255, 255, 0.3);
                }
            """)

    def _reset_flash_colors(self):
        """Setze normale Farben zurueck - GLEICHE MARGINS/PADDINGS."""
        # Main Area normal
        self.main_area_frame.setStyleSheet(UIStyles.get_main_area_base_style())
        
        # Video-Label normal
        self.video_label.setStyleSheet(UIStyles.get_video_label_base_style())
        
        # Sidebar normal
        self.sidebar.setStyleSheet(UIStyles.get_sidebar_base_style())

        # Logo-Hintergrund zurücksetzen (falls vorhanden)
        if hasattr(self, 'logo_label') and self.logo_label.pixmap() is None:
            # Nur bei Text-Fallback-Logo
            self._create_fallback_logo()        

    # =============================================================================
    # MODBUS UI-UPDATE-METHODEN
    # =============================================================================
    
    def update_modbus_status(self, connected, ip_address):
        """WAGO Modbus Status aktualisieren."""
        if connected:
            self.modbus_status.setText("Verbunden")
            self.modbus_status.setStyleSheet(UIStyles.get_modbus_status_connected_style())
        else:
            self.modbus_status.setText("Getrennt")
            self.modbus_status.setStyleSheet(UIStyles.get_modbus_status_disconnected_style())
        
        self.modbus_ip.setText(ip_address)
    
    def update_coil_status(self, reject_active=False, detection_active=False):
        """Ausgänge-Status aktualisieren."""
        # Ausschuss-Ausgang
        if reject_active:
            self.reject_coil_indicator.setStyleSheet(UIStyles.get_unified_status_widget_style("#e74c3c"))
        else:
            self.reject_coil_indicator.setStyleSheet(UIStyles.get_unified_status_widget_style("#7f8c8d"))
        
        # SEPRO Ablage-Ausgang  
        if detection_active:
            self.detection_coil_indicator.setStyleSheet(UIStyles.get_unified_status_widget_style("#27ae60"))
        else:
            self.detection_coil_indicator.setStyleSheet(UIStyles.get_unified_status_widget_style("#7f8c8d"))
            
        # =============================================================================
    # COUNTER & STATUS UPDATE-METHODEN
    # =============================================================================
    
    def reset_session_counter(self):
        """Session-Counter zuruecksetzen - NUR FÜR ADMIN."""
        if not self.app.user_manager.can_reset_counter():
            self.show_status("Admin-Rechte erforderlich fuer Counter-Reset", "error")
            return
        
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
        """Counter-Anzeige aktualisieren."""
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
            self.update_coil_status(reject_active=True, detection_active=True)
            self.flash_red_on_bad_part_detection()
        else:
            self.session_good_parts += 1
        
        self.update_counter_display()
    
    def toggle_sidebar(self):
        """Sidebar ein-/ausblenden."""
        if self.sidebar_visible:
            self.splitter.setSizes([0, 1000])
            self.sidebar_visible = False
            self.sidebar_toggle_btn.setText("≡")
        else:
            self.splitter.setSizes([350, 1000])
            self.sidebar_visible = True
            self.sidebar_toggle_btn.setText("‹")
    
    def update_user_interface(self):
        """UI basierend auf Benutzerlevel aktualisieren."""
        user_level = self.app.user_manager.get_user_level_text()
        
        # Login-Status-Button aktualisieren
        self.login_status_btn.setText(user_level)
        
        if self.app.user_manager.is_admin():
            self.login_status_btn.setStyleSheet(UIStyles.get_login_button_admin_style())
            self.login_status_btn.setToolTip("Admin eingeloggt - Klicken fuer Logout")
        else:
            self.login_status_btn.setStyleSheet(UIStyles.get_login_button_operator_style())
            self.login_status_btn.setToolTip("Operator-Modus - Klicken fuer Admin-Login")
        
        # Buttons aktivieren/deaktivieren
        can_admin = self.app.user_manager.is_admin()
        self.config_btn.setEnabled(can_admin)
        self.settings_btn.setEnabled(can_admin)
        self.reset_counter_btn.setEnabled(can_admin)
    
    def update_workflow_status(self, status):
        """Workflow-Status aktualisieren."""
        self.workflow_info.setText(status)
        
        # Farbe je nach Status
        colors = {
            'BEREIT': "#757575",
            'BANDTAKT': '#757575', 
            'AUSSCHWINGEN': "#757575",
            'DETEKTION': "#23aeff",
            'ABBLASEN': '#e74c3c'
        }
        
        color = colors.get(status, '#34495e')
        self.workflow_info.setStyleSheet(UIStyles.get_unified_status_widget_style(color))
    
    def show_status(self, message, status_type="info"):
        """Status im Header anzeigen."""
        self.status_label.setText(message)
        
        colors = {
            'info': "#757575",
            'success': "#757575",
            'error': '#e74c3c',
            'ready': "#757575",
            'warning': '#f39c12'
        }
        
        color = colors.get(status_type, '#95a5a6')
        self.status_label.setStyleSheet(UIStyles.get_status_label_style(color))
    
    def update_motion(self, motion_value):
        """Motion-Wert aktualisieren."""
        self.motion_info.setText(f"{motion_value:.0f}")
        # Farbe bleibt konstant
        self.motion_info.setStyleSheet(UIStyles.get_motion_brightness_style("#878787"))

    def update_motion_status(self, status):
        """Kalibrierungsstatus anzeigen."""
        self.motion_status.setText(status)
        colors = {
            'Unkalibriert': '#e67e22',
            'Lernt...': '#f39c12',
            'Kalibriert OK': '#27ae60',
        }
        color = colors.get(status, '#7f8c8d')
        self.motion_status.setStyleSheet(UIStyles.get_motion_status_style(color))

    def update_brightness(self, brightness):
        """Helligkeitsanzeige aktualisieren."""
        self.brightness_info.setText(f"{brightness:.0f}")
        # Farbe bleibt konstant
        self.brightness_info.setStyleSheet(UIStyles.get_unified_status_widget_style("#878787"))

    def show_brightness_warning(self, message):
        """Helligkeitswarnung anzeigen."""
        self.brightness_warning.setText("WARNUNG")
        self.brightness_warning.setStyleSheet(UIStyles.get_unified_status_widget_style("#e74c3c"))

    def hide_brightness_warning(self):
        """Helligkeitswarnung ausblenden."""
        self.brightness_warning.setText("OK")
        self.brightness_warning.setStyleSheet(UIStyles.get_unified_status_widget_style("#27ae60"))
        
    def update_last_cycle_stats(self, last_cycle_stats):
        """Letzte Erkennungen aktualisieren."""
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
            if min_conf == 1.0:
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
                avg_rounded = round(avg_detections_per_image)
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

            # Bereich des angezeigten Frames bestimmen
            scaled_w = scaled_pixmap.width()
            scaled_h = scaled_pixmap.height()
            off_x = int((self.video_label.width() - scaled_w) / 2)
            off_y = int((self.video_label.height() - scaled_h) / 2)

            # Overlay an Video-Label-Grösse anpassen
            self.reference_overlay.setGeometry(self.video_label.geometry())
            self.reference_overlay.set_display_area(scaled_w, scaled_h, off_x, off_y)
            
        except Exception as e:
            print(f"Fehler beim Video-Update: {e}")

    def clear_video(self):
        """Video-Anzeige leeren."""
        self.video_label.clear()
        self.video_label.setText("Kein Stream verfuegbar")            
    
    # =============================================================================
    # STATUS-BUTTON UPDATE-METHODEN
    # =============================================================================
    
    def update_model_status(self, model_path):
        """Rueckwaerts-Kompatibilitaet: aktualisiert Config-Button."""
        if model_path and os.path.exists(model_path):
            model_name = os.path.basename(model_path)
            self.config_btn.setText(f"Konfiguration: {model_name}")
            self.config_btn.setStyleSheet(UIStyles.get_model_button_active_style())
        else:
            self.config_btn.setText("Konfiguration laden")
            self.config_btn.setStyleSheet(UIStyles.get_model_button_inactive_style())
    
    def update_camera_status(self, source_info, source_type):
        """Rueckwaerts-Kompatibilitaet: ignoriert."""
        pass
    
    # =============================================================================
    # DIALOG-HANDLER
    # =============================================================================
    
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
        """Einstellungen-Dialog oeffnen - ERWEITERT: Mit Referenzlinien-Update."""
        # Hole die aktuellen Klassennamen vom detection_engine
        class_names = {}
        if hasattr(self.app, 'detection_engine') and hasattr(self.app.detection_engine, 'class_names'):
            class_names = self.app.detection_engine.class_names
        
        dialog = SettingsDialog(settings, class_names, self)
        
        # Modbus-Verbindungsstatus vor Dialog-Öffnung aktualisieren
        if hasattr(self.app, 'modbus_manager'):
            is_connected = self.app.modbus_manager.is_connected()
            dialog.update_modbus_connection_status(is_connected)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Referenzlinien nach Settings-Änderung aktualisieren
            self.update_reference_lines()
            
            # Warnung wenn Erkennung laeuft
            if self.app.running:
                QMessageBox.information(
                    self,
                    "Einstellungen geaendert",
                    "Einstellungen wurden gespeichert.\n\nBitte stoppen Sie die Erkennung und starten Sie sie neu, damit die Änderungen wirksam werden."
                )