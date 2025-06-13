#!/usr/bin/env python3
""" Einfache KI-Objekterkennungs-Anwendung - VEREINFACHT MODBUS: Einfache, robuste Lösung ohne komplexe Threading-Probleme FIXED: Modbus-Bedingungen implementiert ERWEITERT: Parquet-basiertes Event-Logging mit Countdown in Statusleiste """

import sys
import os
import logging
import time
import cv2
import numpy as np
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QMessageBox
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QKeySequence, QShortcut

# Eigene Module
from detection_engine import DetectionEngine
from camera_manager import CameraManager

from camera_config_manager import CameraConfigManager
from settings import Settings
from ui.main_ui import MainUI
from user_manager import UserManager
from modbus_manager import ModbusManager
from image_saver import ImageSaver
from detection_logger import DetectionLogger

# Logging konfigurieren
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('detection_app.log')
    ]
)

class DetectionApp(QMainWindow):
    """
    Hauptanwendung - VEREINFACHT ohne komplexe Threading-Probleme.
    ERWEITERT: Countdown in Statusleiste während der Aufnahmezeit
    """

    def __init__(self):
        super().__init__()
        self.setWindowTitle("KI-Objekterkennung - VEREINFACHT")
        self.setWindowState(Qt.WindowState.WindowFullScreen)
        
        # Komponenten initialisieren
        self.settings = Settings()
        self.user_manager = UserManager()
        
        # Kamera und KI
        self.camera_config_manager = CameraConfigManager()
        self.camera_manager = CameraManager(self.camera_config_manager)
        self.detection_engine = DetectionEngine()
        
        # EINFACHER MODBUS-Manager
        self.modbus_manager = ModbusManager(self.settings)
        
        # Image-Saver
        self.image_saver = ImageSaver(self.settings)
        
        # NEUER Parquet Detection Logger
        self.detection_logger = DetectionLogger(self.settings)
        
        # UI aufbauen
        self.ui = MainUI(self)
        self.setCentralWidget(self.ui)
        
        # Verbindungen herstellen
        self.setup_connections()
        
        # ESC-Taste für schnelles Beenden
        self.setup_exit_shortcuts()
        self._shutdown_confirmed = False
        
        # Status
        self.running = False
        self.blink_timer = None  # Für rotes Blinken
        
        # Workflow-Status
        self.motion_detected = False
        self.motion_cleared = False
        self.detection_running = False
        self.blow_off_active = False
        
        # Timing-Variablen
        self.motion_clear_time = None
        self.detection_start_time = None
        self.blow_off_start_time = None
        
        # COUNTDOWN-TIMER für Statusleiste
        self.countdown_timer = QTimer()
        self.countdown_timer.timeout.connect(self.update_status_countdown)
        
        # Statistiken
        self.last_cycle_detections = {}
        self.current_frame_detections = []
        self.cycle_image_count = 0
        
        # Timer für Frame-Updates
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.process_frame)
        
        # Motion Detection
        self.bg_subtractor = None
        self.motion_history = []
        self.motion_stable_count = 0
        self.no_motion_stable_count = 0
        self.motion_values = []
        self.current_motion_value = 0.0
        self.motion_decay_factor = self.settings.get('motion_decay_factor', 0.1)        

        # Helligkeitsüberwachung
        self.brightness_values = []
        self.low_brightness_start = None
        self.high_brightness_start = None
        self.brightness_auto_stop_active = False
        
        # Einstellungen überwachen
        self.settings_timer = QTimer()
        self.settings_timer.timeout.connect(self.check_settings_changes)
        self.settings_timer.start(2000)
        
        # EINFACHER Modbus-Status-Check
        self.modbus_check_timer = QTimer()
        self.modbus_check_timer.timeout.connect(self.check_modbus_status)
        self.modbus_check_timer.start(5000)  # Alle 5 Sekunden
        
        # INTELLIGENTE MODBUS-Initialisierung mit Reset-Fallback
        self.intelligent_modbus_init()
        
        # Auto-Loading beim Start
        self.auto_load_on_startup()
        
        # Log Application Start
        self.detection_logger.log_system_event('START', 'INFO', 'DetectionApp erfolgreich gestartet', {
            'model_loaded': self.detection_engine.model_loaded,
            'camera_ready': self.camera_manager.camera_ready,
            'modbus_connected': self.modbus_manager.connected
        })
        
        logging.info("DetectionApp erfolgreich gestartet")

    def intelligent_modbus_init(self):
        """INTELLIGENTE Modbus-Initialisierung: Erst direkt versuchen, dann Reset-Fallback."""
        try:
            # Callback für sofortigen Verbindungsverlust setzen
            self.modbus_manager.set_connection_lost_callback(self.on_modbus_connection_lost)
            
            if self.modbus_manager.startup_connect_with_reset_fallback():
                self.modbus_manager.start_watchdog()
                self.ui.update_modbus_status(True, self.modbus_manager.ip_address)
                
                # Log Modbus Connection Success
                self.detection_logger.log_modbus_event('CONNECTION_ESTABLISHED', 'SUCCESS', 
                    'WAGO Modbus erfolgreich initialisiert', {
                        'ip_address': self.modbus_manager.ip_address,
                        'port': self.modbus_manager.port
                    })
                
                logging.info("WAGO Modbus erfolgreich initialisiert")
            else:
                self.ui.update_modbus_status(False, self.modbus_manager.ip_address)
                
                # Log Modbus Connection Failure
                self.detection_logger.log_modbus_event('CONNECTION_FAILED', 'ERROR', 
                    'WAGO Modbus Verbindung endgültig fehlgeschlagen', {
                        'ip_address': self.modbus_manager.ip_address,
                        'port': self.modbus_manager.port
                    })
                
                logging.warning("WAGO Modbus Verbindung endgültig fehlgeschlagen")
        except Exception as e:
            logging.error(f"Modbus-Initialisierung fehlgeschlagen: {e}")
            self.ui.update_modbus_status(False, self.modbus_manager.ip_address)
            
            # Log Modbus Initialization Error
            self.detection_logger.log_modbus_event('INITIALIZATION_ERROR', 'ERROR', 
                f'Modbus-Initialisierung fehlgeschlagen: {e}', {
                    'ip_address': self.modbus_manager.ip_address,
                    'error': str(e)
                })

    def on_modbus_connection_lost(self, reason):
        """SOFORTIGER Callback bei Modbus-Verbindungsverlust."""
        logging.error(f"MODBUS VERBINDUNG VERLOREN: {reason}")
        
        # Log Modbus Connection Lost
        self.detection_logger.log_modbus_event('CONNECTION_LOST', 'ERROR', 
            f'MODBUS VERBINDUNG VERLOREN: {reason}', {
                'reason': reason,
                'detection_was_running': self.running
            })
        
        # Detection SOFORT stoppen falls läuft
        if self.running:
            self.stop_detection()
            self.ui.show_status("MODBUS GETRENNT - Detection gestoppt", "error")
            logging.warning("Detection SOFORT gestoppt aufgrund Modbus-Verlust")
        
        # UI sofort aktualisieren
        self.ui.update_modbus_status(False, self.modbus_manager.ip_address)
        self.ui.update_coil_status(reject_active=False, detection_active=False)

    def check_modbus_status(self):
        """VERBESSERTE Modbus-Status-Überprüfung mit sofortigem Detection-Stopp."""
        try:
            # Prüfe Verbindung
            was_connected = self.modbus_manager.connected
            is_connected = self.modbus_manager.is_connected()
            
            if was_connected and not is_connected:
                # Verbindung verloren - SOFORTIGER STOPP DER DETECTION
                logging.error("Modbus-Verbindung verloren - stoppe Detection SOFORT")
                self.modbus_manager.connected = False
                
                # Log Modbus Connection Lost in Status Check
                self.detection_logger.log_modbus_event('CONNECTION_LOST_STATUS_CHECK', 'ERROR', 
                    'Modbus-Verbindung im Status-Check verloren', {
                        'detection_was_running': self.running
                    })
                
                # Detection sofort stoppen falls läuft
                if self.running:
                    self.stop_detection()
                    self.ui.show_status("MODBUS GETRENNT - Detection gestoppt", "error")
                    logging.warning("Detection aufgrund Modbus-Verlust gestoppt")
                
                # UI aktualisieren
                self.ui.update_modbus_status(False, self.modbus_manager.ip_address)
                self.ui.update_coil_status(reject_active=False, detection_active=False)
                
            elif not was_connected and is_connected:
                # Verbindung wiederhergestellt
                logging.info("Modbus-Verbindung wiederhergestellt")
                self.modbus_manager.connected = True
                self.ui.update_modbus_status(True, self.modbus_manager.ip_address)
                self.ui.show_status("Modbus wiederhergestellt", "success")
                
                # Log Modbus Connection Restored
                self.detection_logger.log_modbus_event('CONNECTION_RESTORED', 'SUCCESS', 
                    'Modbus-Verbindung wiederhergestellt', {
                        'ip_address': self.modbus_manager.ip_address
                    })
                
            # Update UI Status
            self.ui.update_modbus_status(is_connected, self.modbus_manager.ip_address)
            
        except Exception as e:
            logging.error(f"Fehler bei Modbus-Status-Check: {e}")
            # Bei kritischen Fehlern im Status-Check auch Detection stoppen
            if self.running and ("Connection" in str(e) or "timed out" in str(e).lower()):
                logging.error("Kritischer Modbus-Fehler - stoppe Detection")
                
                # Log Critical Modbus Error
                self.detection_logger.log_modbus_event('CRITICAL_ERROR', 'ERROR', 
                    f'Kritischer Modbus-Fehler: {e}', {
                        'error': str(e),
                        'detection_stopped': True
                    })
                
                self.stop_detection()
                self.ui.show_status("Modbus-Fehler - Detection gestoppt", "error")

    def setup_exit_shortcuts(self):
        """ESC-Taste für schnelles Beenden."""
        self.esc_shortcut = QShortcut(QKeySequence(Qt.Key.Key_Escape), self)
        self.esc_shortcut.activated.connect(self.confirm_quit_application)
        
        self.quit_shortcut = QShortcut(QKeySequence("Ctrl+Q"), self)
        self.quit_shortcut.activated.connect(self.confirm_quit_application)
        
        logging.info("Exit shortcuts eingerichtet: ESC und Ctrl+Q")

    def confirm_quit_application(self):
        """Bestätigungsabfrage vor dem Beenden der Anwendung."""
        reply = QMessageBox.question(
            self,
            "Anwendung beenden",
            "Möchten Sie die Anwendung wirklich beenden?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No  # Standard: Nein
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.quit_application()

    def quit_application(self):
        """Anwendung schnell beenden."""
        logging.info("Schnelles Beenden eingeleitet...")
        
        try:
            # Timer stoppen
            if hasattr(self, 'update_timer'):
                self.update_timer.stop()
            if hasattr(self, 'settings_timer'):
                self.settings_timer.stop()
            if hasattr(self, 'modbus_check_timer'):
                self.modbus_check_timer.stop()
            if hasattr(self, 'countdown_timer'):
                self.countdown_timer.stop()
            
            # Detection stoppen
            if self.running:
                self.stop_detection()

            # Kamerastream stoppen
            if hasattr(self.camera_manager, 'stop'):
                self.camera_manager.stop()
            
            # Modbus trennen
            self.modbus_manager.disconnect()
            
            # UI Status
            self.ui.show_status("Beende Anwendung...", "warning")
            QApplication.processEvents()
            
            # Einstellungen speichern
            self.settings.save()
            
            # Detection Logger schließen
            if hasattr(self, 'detection_logger'):
                self.detection_logger.close()
            
            logging.info("Anwendung wird beendet")
            QApplication.quit()
            
        except Exception as e:
            logging.error(f"Fehler beim Beenden: {e}")
            sys.exit(0)

    def convert_class_assignments_to_colors(self, class_assignments):
        """Konvertiert class_assignments zu class_colors Format für DetectionEngine."""
        class_colors = {}
        for class_id, assignment in class_assignments.items():
            if 'color' in assignment:
                class_colors[int(class_id)] = assignment['color']
        return class_colors

    def apply_class_settings_to_engine(self):
        """Wendet alle Klassen-Einstellungen auf die DetectionEngine an."""
        class_assignments = self.settings.get('class_assignments', {})
        
        if class_assignments:
            # Neue Struktur: Farben extrahieren und übertragen
            class_colors = self.convert_class_assignments_to_colors(class_assignments)
            if class_colors:
                self.detection_engine.set_class_colors_quietly(class_colors)
                logging.info(f"Klassen-Farben übernommen: {len(class_colors)} Klassen")
        else:
            # Fallback auf alte Struktur
            class_colors = self.settings.get('class_colors', {})
            if class_colors:
                self.detection_engine.set_class_colors_quietly(class_colors)

    def auto_load_on_startup(self):
        """Auto-Loading beim Start."""
        try:
            # Letztes Modell laden
            last_model = self.settings.get('last_model', '')
            if last_model and os.path.exists(last_model):
                if self.detection_engine.load_model(last_model):
                    # NEUE STRUKTUR: class_assignments verwenden
                    self.apply_class_settings_to_engine()
                    
                    self.ui.update_model_status(last_model)
                    
                    # Log Model Auto-Loading
                    self.detection_logger.log_system_event('MODEL_AUTO_LOADED', 'SUCCESS', 
                        f'Modell automatisch geladen: {os.path.basename(last_model)}', {
                            'model_path': last_model,
                            'class_names': list(self.detection_engine.class_names.values())
                        })
                    
                    logging.info(f"Auto-loaded model: {last_model}")
            
            # Kamera-Konfiguration laden
            camera_config_path = self.settings.get('camera_config_path', '')
            if camera_config_path and os.path.exists(camera_config_path):
                self.camera_config_manager.load_config(camera_config_path)
            
            # Letzte Quelle laden
            last_source = self.settings.get('last_source')
            last_mode_was_video = self.settings.get('last_mode_was_video', False)
            
            if last_source is not None:
                if last_mode_was_video and isinstance(last_source, str):
                    if os.path.exists(last_source):
                        if self.camera_manager.set_source(last_source):
                            self.ui.update_camera_status(last_source, 'video')
                elif not last_mode_was_video and isinstance(last_source, int):
                    if self.camera_manager.set_source(last_source):
                        self.ui.update_camera_status(last_source, 'webcam')
            
            # Status setzen basierend auf Modbus-Verbindung
            if self.detection_engine.model_loaded and self.camera_manager.camera_ready:
                if self.modbus_manager.connected:
                    self.ui.show_status("Bereit - Alle Komponenten geladen", "ready")
                else:
                    self.ui.show_status("Warte auf Modbus-Verbindung", "warning")
            else:
                self.ui.show_status("Modell und Kamera auswählen", "warning")
                
        except Exception as e:
            logging.error(f"Fehler beim Auto-Loading: {e}")

    def setup_connections(self):
        """Signale verbinden."""
        self.ui.start_btn.clicked.connect(self.toggle_detection)
        self.ui.model_btn.clicked.connect(self.load_model)
        self.ui.camera_btn.clicked.connect(self.select_camera)
        self.ui.settings_btn.clicked.connect(self.open_settings)
        self.ui.snapshot_btn.clicked.connect(self.take_snapshot)
        self.ui.login_status_btn.clicked.connect(self.toggle_login)
        self.ui.sidebar_toggle_btn.clicked.connect(self.toggle_sidebar)
        # GEÄNDERT: quit_btn mit Bestätigung
        self.ui.quit_btn.clicked.connect(self.confirm_quit_application)

    def check_settings_changes(self):
        """Einstellungsänderungen prüfen - OPTIMIERT: Weniger Logging."""
        try:
            # Einfache Datei-Änderungsprüfung
            if os.path.exists(self.settings.filename):
                old_settings = self.settings.data.copy()
                self.settings.load_quietly()  # Verwende quiet loading
                
                # Update Image Saver nur bei Änderungen
                if old_settings != self.settings.data:
                    self.image_saver.update_settings(self.settings.data)
                    
                    # Update Kamera-Konfiguration nur bei Pfad-Änderung
                    old_camera_config = old_settings.get('camera_config_path', '')
                    new_camera_config = self.settings.get('camera_config_path', '')
                    if old_camera_config != new_camera_config and new_camera_config and os.path.exists(new_camera_config):
                        self.camera_config_manager.load_config(new_camera_config)
                    
                    # NEUE: class_assignments Überwachung
                    old_class_assignments = old_settings.get('class_assignments', {})
                    new_class_assignments = self.settings.get('class_assignments', {})
                    
                    if old_class_assignments != new_class_assignments:
                        # Klassen-Einstellungen komplett anwenden
                        if self.detection_engine.model_loaded:
                            self.apply_class_settings_to_engine()
                            logging.info("Klassen-Einstellungen nach Änderung aktualisiert")

                    # Motion Decay Factor bei Änderung aktualisieren
                    old_decay = old_settings.get('motion_decay_factor', 0.1)
                    new_decay = self.settings.get('motion_decay_factor', 0.1)
                    if old_decay != new_decay:
                        self.motion_decay_factor = new_decay
                        logging.info(f"Motion Decay Factor aktualisiert: {new_decay}")

                    # NEUE: Referenzlinien-Update
                    old_reference_lines = old_settings.get('reference_lines', [])
                    new_reference_lines = self.settings.get('reference_lines', [])
                    if old_reference_lines != new_reference_lines:
                        self.ui.update_reference_lines()
                        
        except:
            pass

    def toggle_login(self):
        """Login/Logout umschalten - MIT SCHÖNEM PIN-DIALOG."""
        if self.user_manager.is_admin():
            self.user_manager.logout()
            self.ui.update_user_interface()
            self.ui.show_status("Abgemeldet - Operator-Modus", "info")
        else:
            if self.user_manager.login():  # PIN-Dialog
                self.ui.update_user_interface()
                self.ui.show_status("Angemeldet als Admin", "success")
            else:
                self.ui.show_status("Ungültige PIN", "error")

    def toggle_sidebar(self):
        """Sidebar umschalten."""
        self.ui.toggle_sidebar()

    def toggle_detection(self):
        """Detection starten/stoppen."""
        if not self.running:
            self.start_detection()
        else:
            self.stop_detection()

    def start_detection(self):
        """Detection starten - NUR WENN MODBUS VERBUNDEN."""
        try:
            if not self.detection_engine.model_loaded:
                self.ui.show_status("Bitte zuerst ein Modell laden", "error")
                return
                
            if not self.camera_manager.camera_ready:
                self.ui.show_status("Bitte zuerst Kamera/Video auswählen", "error")
                return
            
            # NEUE BEDINGUNG: Prüfe Modbus-Verbindung
            if not self.modbus_manager.is_connected():
                self.ui.show_status("Modbus-Verbindung erforderlich für Detection", "error")
                logging.warning("Detection-Start verweigert - Modbus nicht verbunden")
                
                # Log Detection Start Denied
                self.detection_logger.log_system_event('DETECTION_START_DENIED', 'WARNING', 
                    'Detection-Start verweigert - Modbus nicht verbunden', {
                        'modbus_connected': False,
                        'model_loaded': self.detection_engine.model_loaded,
                        'camera_ready': self.camera_manager.camera_ready
                    })
                return
            
            if self.camera_manager.start():
                self.running = True
                self.reset_workflow()
                self.init_robust_motion_detection()
                
                # Modbus: Detection-Active setzen
                if self.modbus_manager.connected:
                    self.modbus_manager.set_detection_active_coil(True)
                    self.ui.update_coil_status(detection_active=True)
                
                self.update_timer.start(30)
                
                # Button zu Stoppen mit Gradient und Stop-Symbol
                self.ui.start_btn.setText("⏹ STOPPEN")
                self.ui.start_btn.setStyleSheet("""
                    QPushButton {
                        background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0,
                                                stop: 0 #3498db, stop: 1 #2980b9);
                        font-size: 18px;
                        font-weight: bold;
                        min-height: 45px;
                        padding: 15px 25px;
                        border-radius: 4px;
                        color: white;
                    }
                    QPushButton:hover {
                        background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0,
                                                stop: 0 #5dade2, stop: 1 #3498db);
                    }
                """)
                
                self.ui.show_status("Detection läuft", "success")
                self.ui.update_workflow_status("BEREIT")
                
                # Log Detection Started
                self.detection_logger.log_system_event('DETECTION_STARTED', 'SUCCESS', 
                    'Detection erfolgreich gestartet', {
                        'modbus_connected': self.modbus_manager.connected,
                        'camera_source': self.camera_manager.source_info,
                        'camera_type': self.camera_manager.source_type
                    })
                
                logging.info("Detection gestartet")
            else:
                self.ui.show_status("Fehler beim Starten der Kamera", "error")
                
                # Log Camera Start Error
                self.detection_logger.log_system_event('CAMERA_START_ERROR', 'ERROR', 
                    'Fehler beim Starten der Kamera', {
                        'camera_source': self.camera_manager.source_info,
                        'camera_type': self.camera_manager.source_type
                    })
                
        except Exception as e:
            logging.error(f"Fehler beim Starten: {e}")
            self.ui.show_status(f"Fehler: {e}", "error")
            
            # Log Detection Start Error
            self.detection_logger.log_system_event('DETECTION_START_ERROR', 'ERROR', 
                f'Fehler beim Starten der Detection: {e}', {
                    'error': str(e)
                })

    def stop_detection(self):
        """Detection stoppen."""
        self.running = False
        
        if hasattr(self, 'update_timer'):
            self.update_timer.stop()
        
        # COUNTDOWN-TIMER stoppen
        if hasattr(self, 'countdown_timer'):
            self.countdown_timer.stop()
        
        # Modbus: Detection-Active ausschalten
        if self.modbus_manager.connected:
            self.modbus_manager.set_detection_active_coil(False)
            self.ui.update_coil_status(detection_active=False)
        
        try:
            self.camera_manager.stop()
        except:
            pass
        
        # Button zurück zu Starten mit Play-Symbol
        self.ui.start_btn.setText("▶ Live Detection STARTEN")
        self.ui.start_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                font-size: 16px;
                font-weight: bold;
                min-height: 45px;
                padding: 15px 25px;
                border-radius: 4px;
                color: white;
            }
            QPushButton:hover {
                background-color: #2ecc71;
            }
        """)
        
        self.ui.show_status("Bereit", "ready")
        self.ui.update_workflow_status("BEREIT")
        self.reset_workflow()
        
        # Log Detection Stopped
        self.detection_logger.log_system_event('DETECTION_STOPPED', 'INFO', 
            'Detection gestoppt', {
                'modbus_connected': self.modbus_manager.connected
            })
        
        logging.info("Detection gestoppt")

    def init_robust_motion_detection(self):
        """Motion Detection initialisieren."""
        self.bg_subtractor = cv2.createBackgroundSubtractorMOG2(
            detectShadows=False, # Deaktiviert für bessere Performance
            varThreshold=32, # Varianz-Schwelle für bessere Erkennung
            history=200 # History für stabilere Bewegungserkennung
        )
        
        self.motion_history = []
        self.motion_stable_count = 0
        self.no_motion_stable_count = 0
        self.motion_values = []
        self.current_motion_value = 0.0
        
        # Erkennungsstatistiken zurücksetzen
        self.last_cycle_detections = {}
        self.current_frame_detections = []
        self.cycle_image_count = 0
        
        # Helligkeits-Auto-Stopp zurücksetzen
        self.brightness_auto_stop_active = False
        self.low_brightness_start = None
        self.high_brightness_start = None
        
        logging.info("Motion Detection initialisiert")

    def reset_workflow(self):
        """Workflow zurücksetzen."""
        self.motion_detected = False
        self.motion_cleared = False
        self.detection_running = False
        self.blow_off_active = False
        self.motion_clear_time = None
        self.detection_start_time = None
        self.blow_off_start_time = None
        self.motion_stable_count = 0
        self.no_motion_stable_count = 0

    def process_frame(self):
        """Frame verarbeiten."""
        try:
            if not self.running:
                return
                
            frame = self.camera_manager.get_frame()
            if frame is None:
                return
            
            # Helligkeitsüberwachung
            self.check_brightness_with_auto_stop(frame)
            
            if self.brightness_auto_stop_active:
                return
            
            # Motion-Wert berechnen
            self.update_motion_display_with_decay(frame)
            
            # Workflow verarbeiten
            self.process_industrial_workflow(frame)
            
            # KI-Erkennung
            detections = []
            if self.detection_running and self.running:
                detections = self.detection_engine.detect(frame)
                self.current_frame_detections = detections
                self.update_cycle_statistics_extended(detections)
                self.cycle_image_count += 1
            
            # Frame zeichnen
            annotated_frame = self.detection_engine.draw_detections(frame, detections)
            
            # UI aktualisieren
            if self.running:
                self.ui.update_video(annotated_frame)
                self.ui.update_last_cycle_stats(self.last_cycle_detections)
                
        except Exception as e:
            logging.error(f"Fehler bei Frame-Verarbeitung: {e}")

    def update_motion_display_with_decay(self, frame):
        """Motion-Wert berechnen mit drastischem Abfall nach Stillstand."""
        if self.bg_subtractor is None:
            return

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (5, 5), 0)
        fg_mask = self.bg_subtractor.apply(gray)

        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_OPEN, kernel)
        fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_CLOSE, kernel)

        # Motion-Berechnung mit Downsampling-Kompensation
        motion_pixels = cv2.countNonZero(fg_mask) * 16  # Kompensiert 4x4 Downsampling
        current_motion = min(255, motion_pixels / 100)
        
        # ELEGANTE DECAY-MATHEMATIK: Ein-Schritt Division
        if current_motion < self.current_motion_value:
            decay_power = 1.0 / max(0.001, self.motion_decay_factor)
            self.current_motion_value = max(self.current_motion_value, current_motion) / decay_power
            
            # Intelligenter Threshold für sofortigen Reset
            if self.current_motion_value < 1.0:
                self.current_motion_value = 0.0
        else:
            # Sofortige Aktualisierung bei steigenden Werten
            self.current_motion_value = current_motion
        
        # UI aktualisieren
        self.ui.update_motion(self.current_motion_value)

    def process_industrial_workflow(self, frame):
        """Industrieller Workflow mit COUNTDOWN in Statusleiste."""
        current_time = time.time()
        
        settling_time = self.settings.get('settling_time', 1.0)
        capture_time = self.settings.get('capture_time', 3.0)
        blow_off_time = self.settings.get('blow_off_time', 5.0)
        
        # 1. Bewegungserkennung
        if not self.motion_detected and not self.blow_off_active:
            motion_now = self.detect_robust_motion(frame)
            
            if motion_now and not self.motion_detected:
                self.motion_detected = True
                self.motion_cleared = False
                self.motion_clear_time = None
                self.no_motion_stable_count = 0
                self.ui.show_status("Förderband taktet", "warning")
                self.ui.update_workflow_status("BEWEGUNG")
                logging.info("Bewegung erkannt")
        
        # 2. Ausschwingen
        if self.motion_detected and not self.motion_cleared:
            motion_now = self.detect_robust_motion(frame)
            
            if not motion_now:
                self.no_motion_stable_count += 1
                
                if self.no_motion_stable_count >= 10:
                    if self.motion_clear_time is None:
                        self.motion_clear_time = current_time
                        self.ui.show_status("Ausschwingzeit läuft...", "warning")
                        self.ui.update_workflow_status("AUSSCHWINGEN")
                        logging.info("Ausschwingzeit startet")
                    
                    elif current_time - self.motion_clear_time >= settling_time:
                        self.motion_cleared = True
                        self.detection_running = True
                        self.detection_start_time = current_time
                        self.last_cycle_detections = {}
                        self.cycle_image_count = 0
                        
                        # COUNTDOWN STARTEN für Erkennungsphase
                        self.countdown_timer.start(100)  # Alle 100ms aktualisieren
                        
                        self.ui.show_status("Objekterkennung aktiv", "success")
                        self.ui.update_workflow_status("OBJEKTERKENNUNG")
                        logging.info("Objekterkennung startet")
            else:
                self.motion_clear_time = None
                self.no_motion_stable_count = 0
        
        # 3. Erkennungsphase
        if self.detection_running:
            if current_time - self.detection_start_time >= capture_time:
                self.detection_running = False
                
                # COUNTDOWN STOPPEN
                self.countdown_timer.stop()
                
                bad_parts_detected = self.evaluate_detection_results()
                
                # Bilderspeicherung
                self.save_detection_result_image(frame, bad_parts_detected)
                
                # Counter aktualisieren
                self.ui.increment_session_counters(bad_parts_detected)
                
                if bad_parts_detected:
                    # Rotes Blinken starten
                    self.start_red_blink()
                    
                    self.blow_off_active = True
                    self.blow_off_start_time = current_time
                    
                    if self.modbus_manager.connected:
                        self.modbus_manager.set_reject_coil()
                        self.ui.update_coil_status(reject_active=True, detection_active=True)
                    
                    self.ui.show_status("Schlechte Teile - Abblasen aktiv", "error")
                    self.ui.update_workflow_status("ABBLASEN")
                    logging.info("Schlechte Teile erkannt")
                else:
                    self.reset_workflow()
                    self.ui.show_status("Prüfung abgeschlossen", "ready")
                    self.ui.update_workflow_status("BEREIT")
                    logging.info("Keine schlechten Teile")
        
        # 4. Abblas-Wartezeit
        if self.blow_off_active:
            if current_time - self.blow_off_start_time >= blow_off_time:
                self.blow_off_active = False
                
                if self.modbus_manager.connected:
                    self.ui.update_coil_status(reject_active=False, detection_active=True)
                
                self.reset_workflow()
                self.ui.show_status("Abblasen beendet", "ready")
                self.ui.update_workflow_status("BEREIT")
                logging.info("Abblas-Wartezeit beendet")

    def update_status_countdown(self):
        """COUNTDOWN in Statusleiste während der Erkennungsphase aktualisieren."""
        if not self.detection_running or not self.detection_start_time:
            self.countdown_timer.stop()
            return
        
        current_time = time.time()
        capture_time = self.settings.get('capture_time', 3.0)
        elapsed = current_time - self.detection_start_time
        remaining = max(0, capture_time - elapsed)
        
        # Status mit Countdown aktualisieren
        countdown_text = f"KI-Erkennung aktiv ({remaining:.2f} sec)"
        self.ui.show_status(countdown_text, "success")
        
        # Stoppen wenn Zeit abgelaufen
        if remaining <= 0:
            self.countdown_timer.stop()

    def start_red_blink(self):
        """Rotes Blinken für 1 Sekunde starten - DELEGIERT AN UI."""
        try:
            # DELEGIERE AN UI-KLASSE statt eigene Implementierung
            self.ui.flash_red_on_bad_part_detection()
            
        except Exception as e:
            logging.error(f"Fehler beim roten Blinken: {e}")

    def detect_robust_motion(self, frame):
        """Robuste Bewegungserkennung."""
        if self.bg_subtractor is None:
            return False
        
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (5, 5), 0)
        fg_mask = self.bg_subtractor.apply(gray)
        
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_OPEN, kernel)
        fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_CLOSE, kernel)
        
        motion_pixels = cv2.countNonZero(fg_mask)
        motion_threshold = self.settings.get('motion_threshold', 110) * 100
        has_motion = motion_pixels > motion_threshold
        
        self.motion_history.append(has_motion)
        if len(self.motion_history) > 5:
            self.motion_history.pop(0)
        
        stable_motion = sum(self.motion_history) >= 3
        
        if stable_motion:
            self.motion_stable_count += 1
        else:
            self.motion_stable_count = 0
        
        return self.motion_stable_count >= 3

    def update_cycle_statistics_extended(self, detections):
        """Statistiken für aktuellen Zyklus."""
        for detection in detections:
            _, _, _, _, confidence, class_id = detection
            class_name = self.detection_engine.class_names.get(class_id, f"Class {class_id}")
            
            if class_name not in self.last_cycle_detections:
                self.last_cycle_detections[class_name] = {
                    'count': 0,
                    'max_confidence': 0.0,
                    'min_confidence': 1.0,
                    'avg_confidence': 0.0,
                    'confidences': [],
                    'class_id': class_id,
                    'total_detections': 0
                }
            
            stats = self.last_cycle_detections[class_name]
            stats['count'] += 1
            stats['total_detections'] += 1
            stats['confidences'].append(confidence)
            stats['max_confidence'] = max(stats['max_confidence'], confidence)
            stats['min_confidence'] = min(stats['min_confidence'], confidence)
            
            confidences = stats['confidences']
            stats['avg_confidence'] = sum(confidences) / len(confidences)

    def evaluate_detection_results(self):
        """KORRIGIERT: Erkennungsergebnisse auswerten mit durchschnittlicher Anzahl pro Bild."""
        class_assignments = self.settings.get('class_assignments', {})
        bad_parts_found = False
        
        # NEUE STRUKTUR verwenden wenn verfügbar
        if class_assignments:
            for class_name, stats in self.last_cycle_detections.items():
                class_id = stats.get('class_id', 0)
                max_conf = stats.get('max_confidence', 0.0)
                total_detections = stats.get('total_detections', 0)
                
                # KORRIGIERT: Durchschnittliche Anzahl pro Bild berechnen (wie in Sidebar "ANZ")
                if self.cycle_image_count > 0:
                    avg_detections_per_image = total_detections / self.cycle_image_count
                    avg_count = round(avg_detections_per_image)
                else:
                    avg_count = 0
                
                assignment = class_assignments.get(str(class_id), {})
                assignment_type = assignment.get('assignment', 'ignore')
                expected_count = assignment.get('expected_count', -1)
                min_confidence = assignment.get('min_confidence', 0.5)
                
                if assignment_type == 'bad' and max_conf >= min_confidence:
                    # Schlecht-Teil erkannt mit ausreichender Konfidenz
                    logging.info(f"Schlecht-Teil erkannt: {class_name} (Konfidenz: {max_conf:.2f})")
                    bad_parts_found = True
                    
                elif assignment_type == 'good' and expected_count != -1:
                    # Gut-Teil mit erwarteter Anzahl prüfen
                    if avg_count != expected_count and max_conf >= min_confidence:
                        logging.info(f"Gut-Teil Anzahl-Fehler: {class_name} - erwartet: {expected_count}, gefunden: {avg_count}")
                        bad_parts_found = True
        else:
            # FALLBACK auf alte Struktur
            bad_part_classes = self.settings.get('bad_part_classes', [])
            red_threshold = self.settings.get('red_threshold', 1)
            min_confidence = self.settings.get('bad_part_min_confidence', 0.5)
            
            for class_name, stats in self.last_cycle_detections.items():
                class_id = stats.get('class_id', 0)
                max_conf = stats.get('max_confidence', 0.0)
                total_detections = stats.get('total_detections', 0)
                
                if (class_id in bad_part_classes and 
                    total_detections >= red_threshold and 
                    max_conf >= min_confidence):
                    logging.info(f"Schlechtes Teil (alte Struktur): {class_name}")
                    bad_parts_found = True
        
        # Log Detection Cycle Result
        self.detection_logger.log_detection_cycle(
            bad_parts_detected=bad_parts_found,
            cycle_detections=self.last_cycle_detections,
            cycle_stats={
                'cycle_image_count': self.cycle_image_count,
                'evaluation_method': 'class_assignments' if class_assignments else 'legacy'
            }
        )
        
        return bad_parts_found

    def save_detection_result_image(self, frame, bad_parts_detected):
        """Bild speichern."""
        try:
            if bad_parts_detected:
                self.image_saver.save_bad_image(frame, self.last_cycle_detections)
            else:
                self.image_saver.save_good_image(frame, self.last_cycle_detections)
        except Exception as e:
            logging.error(f"Fehler beim Speichern: {e}")

    def check_brightness_with_auto_stop(self, frame):
        """Helligkeitsüberwachung."""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        brightness = np.mean(gray)
        
        self.brightness_values.append(brightness)
        if len(self.brightness_values) > 30:
            self.brightness_values.pop(0)
        
        avg_brightness = np.mean(self.brightness_values)
        
        low_threshold = self.settings.get('brightness_low_threshold', 30)
        high_threshold = self.settings.get('brightness_high_threshold', 220)
        duration_threshold = self.settings.get('brightness_duration_threshold', 3.0)
        
        current_time = time.time()
        
        if avg_brightness < low_threshold:
            if self.low_brightness_start is None:
                self.low_brightness_start = current_time
            elif current_time - self.low_brightness_start >= duration_threshold:
                if not self.brightness_auto_stop_active:
                    self.stop_detection()
                    self.brightness_auto_stop_active = True
                    self.ui.show_status(f"Zu dunkel: {avg_brightness:.1f}", "error")
                    
                    # Log Brightness Auto-Stop (Low)
                    self.detection_logger.log_brightness_event(
                        auto_stop_triggered=True,
                        brightness_value=avg_brightness,
                        threshold_info={
                            'reason': 'too_low',
                            'threshold': low_threshold,
                            'duration_threshold': duration_threshold
                        }
                    )
                return
        else:
            self.low_brightness_start = None
        
        if avg_brightness > high_threshold:
            if self.high_brightness_start is None:
                self.high_brightness_start = current_time
            elif current_time - self.high_brightness_start >= duration_threshold:
                if not self.brightness_auto_stop_active:
                    self.stop_detection()
                    self.brightness_auto_stop_active = True
                    self.ui.show_status(f"Zu hell: {avg_brightness:.1f}", "error")
                    
                    # Log Brightness Auto-Stop (High)
                    self.detection_logger.log_brightness_event(
                        auto_stop_triggered=True,
                        brightness_value=avg_brightness,
                        threshold_info={
                            'reason': 'too_high',
                            'threshold': high_threshold,
                            'duration_threshold': duration_threshold
                        }
                    )
                return
        else:
            self.high_brightness_start = None
        
        self.ui.hide_brightness_warning()
        self.ui.update_brightness(avg_brightness)

    def load_model(self):
        """Modell laden."""
        if not self.user_manager.can_change_model():
            self.ui.show_status("Admin-Login erforderlich", "error")
            return
            
        model_path = self.ui.select_model_file()
        if model_path:
            if self.detection_engine.load_model(model_path):
                # NEUE STRUKTUR: class_assignments verwenden
                self.apply_class_settings_to_engine()
                
                self.ui.show_status(f"Modell geladen", "success")
                self.ui.update_model_status(model_path)
                self.settings.set('last_model', model_path)
                self.settings.save()
                
                # Log Model Loaded
                self.detection_logger.log_system_event('MODEL_LOADED', 'SUCCESS', 
                    f'Modell manuell geladen: {os.path.basename(model_path)}', {
                        'model_path': model_path,
                        'class_names': list(self.detection_engine.class_names.values())
                    })
            else:
                self.ui.show_status("Fehler beim Laden", "error")
                
                # Log Model Load Error
                self.detection_logger.log_system_event('MODEL_LOAD_ERROR', 'ERROR', 
                    f'Fehler beim Laden des Modells: {model_path}', {
                        'model_path': model_path
                    })

    def select_camera(self):
        """Kamera auswählen."""
        if not self.user_manager.can_change_camera():
            self.ui.show_status("Admin-Login erforderlich", "error")
            return
            
        source = self.ui.select_camera_source()
        if source:
            if self.camera_manager.set_source(source):
                self.ui.show_status("Quelle ausgewählt", "success")
                
                if isinstance(source, int):
                    self.ui.update_camera_status(source, 'webcam')
                elif isinstance(source, str):
                    self.ui.update_camera_status(source, 'video')
                elif isinstance(source, tuple):
                    self.ui.update_camera_status(source[1], 'ids')
                
                self.settings.set('last_source', source)
                self.settings.set('last_mode_was_video', isinstance(source, str))
                self.settings.save()
            else:
                self.ui.show_status("Fehler bei Auswahl", "error")

    def open_settings(self):
        """Einstellungen öffnen."""
        if not self.user_manager.can_access_settings():
            self.ui.show_status("Admin-Login erforderlich", "error")
            return
            
        self.ui.open_settings_dialog(self.settings)

    def take_snapshot(self):
        """Schnappschuss."""
        frame = self.camera_manager.get_frame()
        if frame is not None:
            filename = self.camera_manager.save_snapshot(frame)
            if filename:
                self.ui.show_status("Schnappschuss gespeichert", "success")
            else:
                self.ui.show_status("Fehler beim Speichern", "error")

    def closeEvent(self, event):
        """Sauberes Herunterfahren mit Bestätigungsabfrage."""
        reply = QMessageBox.question(
            self,
            "Anwendung beenden",
            "Möchten Sie die Anwendung wirklich beenden?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No  # Standard: Nein
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.quit_application()
            event.accept()
        else:
            event.ignore()  # Schließvorgang abbrechen

def main():
    """Hauptfunktion."""
    app = QApplication(sys.argv)
    app.setApplicationName("KI-Objekterkennung VEREINFACHT")
    app.setFont(QFont("Segoe UI", 10))
    
    window = DetectionApp()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()