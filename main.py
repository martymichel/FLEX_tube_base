#!/usr/bin/env python3
"""
Einfache KI-Objekterkennungs-Anwendung
Mit Counter, Motion-Anzeige, WAGO Modbus-Schnittstelle, Bilderspeicherung und Helligkeits-basiertem Stopp
ERWEITERT: Modbus-Fehler-Dialog-System mit App-Sperrung
"""

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
from ui.main_ui import MainUI  # Direkter Import aus main_ui
from user_manager import UserManager
from modbus_manager import ModbusManager
from image_saver import ImageSaver

# Logging konfigurieren - OHNE Unicode-Emojis für Windows-Kompatibilität
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('detection_app.log')
    ]
)

class DetectionApp(QMainWindow):
    """Hauptanwendung für KI-Objekterkennung mit Modbus-Fehler-Behandlung."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("INSPECTUBE - Defect Detection App")
        # Kombiniert Frameless + Maximized = Kiosk-Stil
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint, True)
        self.showMaximized()

        # Komponenten initialisieren
        self.settings = Settings()
        self.user_manager = UserManager()
        
        # Kamera-Konfigurationsmanager initialisieren
        self.camera_config_manager = CameraConfigManager()
        
        # Kamera-Manager mit Konfigurationsmanager initialisieren
        self.camera_manager = CameraManager(self.camera_config_manager)
        
        self.detection_engine = DetectionEngine()
        
        # MODBUS-Manager initialisieren
        self.modbus_manager = ModbusManager(self.settings)
        
        # IMAGE-SAVER initialisieren
        self.image_saver = ImageSaver(self.settings)
        
        # UI aufbauen
        self.ui = MainUI(self)
        self.setCentralWidget(self.ui)
        
        # Verbindungen herstellen
        self.setup_connections()
        
        # ESC-Taste für schnelles Beenden
        self.setup_exit_shortcuts()
        
        # Status
        self.running = False
        
        # MODBUS-FEHLER-BEHANDLUNG: App-Sperrung bei kritischen Fehlern
        self.modbus_critical_failure = False
        self.modbus_failure_dialog_shown = False
        
        # Workflow-Status
        self.motion_detected = False
        self.motion_cleared = False
        self.detection_running = False
        self.blow_off_active = False
        
        # Timing-Variablen
        self.motion_clear_time = None
        self.detection_start_time = None
        self.blow_off_start_time = None
        
        # ERWEITERTE Erkennungsstatistiken für bessere Durchschnittsberechnung
        self.last_cycle_detections = {}  # Erkennungen des letzten Capture-Zyklus
        self.current_frame_detections = []  # Aktuelle Frame-Erkennungen
        self.cycle_image_count = 0  # Anzahl verarbeiteter Bilder im aktuellen Zyklus
        self.cycle_class_image_counts = {}  # Pro Klasse: Anzahl Bilder mit dieser Klasse
        
        # Timer für Frame-Updates
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.process_frame)
        
        # BESCHLEUNIGTE Bewegungserkennung (Motion-Drop schneller)
        self.bg_subtractor = None
        self.last_frame = None
        self.motion_history = []  # VERKÜRZT: Rolling window für schnellere Motion-Erkennung
        self.motion_stable_count = 0  # Zähler für stabile Motion-States
        self.no_motion_stable_count = 0  # Zähler für stabile No-Motion-States
        
        # Motion-Wert Tracking (für Anzeige) - BESCHLEUNIGT
        self.motion_values = []  # VERKÜRZT: Rolling window für schnellere Motion-Anzeige
        self.current_motion_value = 0.0  # Aktueller, geglätteter Motion-Wert
        
        # Helligkeitsüberwachung mit Auto-Stopp
        self.brightness_values = []
        self.low_brightness_start = None
        self.high_brightness_start = None
        self.brightness_auto_stop_active = False
        
        # Einstellungen überwachen
        self.last_settings_update = 0
        self.settings_timer = QTimer()
        self.settings_timer.timeout.connect(self.check_settings_changes)
        self.settings_timer.start(2000)  # Alle 2 Sekunden prüfen
        
        # MODBUS mit automatischer Neuverbindung initialisieren
        self.initialize_modbus_with_startup_reconnect()
        
        # Auto-Loading beim Start
        self.auto_load_on_startup()
        
        logging.info("DetectionApp gestartet - Workflow mit WAGO Modbus und Bilderspeicherung")
    
    def initialize_modbus_with_startup_reconnect(self):
        """WAGO Modbus mit automatischer Neuverbindung bei Start initialisieren."""
        modbus_enabled = self.settings.get('modbus_enabled', True)
        if not modbus_enabled:
            logging.info("Modbus deaktiviert in den Einstellungen")
            return
        
        try:
            logging.info("Initialisiere WAGO Modbus mit automatischer Neuverbindung...")
            
            # IMMER eine Neuverbindung bei App-Start durchführen
            if self.modbus_manager.startup_reconnect():
                
                # Watchdog starten
                if self.modbus_manager.start_watchdog():
                    logging.info("WAGO Watchdog erfolgreich gestartet")
                else:
                    logging.warning("WAGO Watchdog konnte nicht gestartet werden")
                
                # Coil-Refresh starten (SIMPLE Version)
                if self.modbus_manager.start_coil_refresh():
                    logging.info("WAGO Coil-Refresh erfolgreich gestartet")
                else:
                    logging.warning("WAGO Coil-Refresh konnte nicht gestartet werden")
                
                # UI Status aktualisieren
                self.ui.update_modbus_status(True, self.modbus_manager.ip_address)
                logging.info("WAGO Modbus vollständig initialisiert")
                
                # Modbus erfolgreich - kritischer Fehler-Status zurücksetzen
                self.modbus_critical_failure = False
                
            else:
                logging.error("WAGO Modbus-Neuverbindung bei Start fehlgeschlagen")
                self.ui.update_modbus_status(False, self.modbus_manager.ip_address)
                
                # KRITISCHER MODBUS-FEHLER: App sperren
                self.handle_critical_modbus_failure()
                
        except Exception as e:
            logging.error(f"Fehler bei WAGO Modbus-Initialisierung: {e}")
            self.ui.update_modbus_status(False, self.modbus_manager.ip_address)
            
            # KRITISCHER MODBUS-FEHLER: App sperren
            self.handle_critical_modbus_failure()
    
    def handle_critical_modbus_failure(self):
        """Behandlung kritischer Modbus-Fehler - App sperren."""
        self.modbus_critical_failure = True
        
        # Start-Button deaktivieren
        self.ui.start_btn.setEnabled(False)
        self.ui.start_btn.setStyleSheet("""
            QPushButton {
                background-color: #7f8c8d;
                color: #bdc3c7;
                font-size: 14px;
                min-height: 35px;
            }
        """)
        self.ui.start_btn.setToolTip("Start gesperrt - Modbus-Verbindung erforderlich")
        
        # Status-Meldung
        self.ui.show_status("MODBUS-FEHLER: Start gesperrt", "error")
        
        logging.critical("Kritischer Modbus-Fehler - Anwendung gesperrt")
        
        # Dialog nach kurzer Verzögerung anzeigen (damit UI initialisiert ist)
        QTimer.singleShot(1000, self.show_modbus_failure_dialog)
    
    def show_modbus_failure_dialog(self):
        """Dialog für Modbus-Verbindungsfehler anzeigen."""
        if self.modbus_failure_dialog_shown:
            return  # Dialog bereits angezeigt
        
        self.modbus_failure_dialog_shown = True
        
        # Erstelle Fehler-Dialog
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("🔌 WAGO Modbus-Verbindungsfehler")
        msg_box.setIcon(QMessageBox.Icon.Critical)
        
        msg_box.setText(
            "Die WAGO Modbus-Verbindung konnte nicht hergestellt werden!\n\n"
            "Die Objekterkennung ist gesperrt, bis die Verbindung wiederhergestellt ist."
        )
        
        msg_box.setDetailedText(
            f"IP-Adresse: {self.modbus_manager.ip_address}\n"
            f"Port: {self.modbus_manager.port}\n\n"
            "Mögliche Ursachen:\n"
            "• WAGO-Controller ist nicht erreichbar\n"
            "• Falsche IP-Adresse oder Port\n"
            "• Netzwerkverbindung unterbrochen\n"
            "• Controller-Fehler oder Neustart erforderlich"
        )
        
        # Buttons hinzufügen
        reset_btn = msg_box.addButton("🔄 Controller Reset", QMessageBox.ButtonRole.ActionRole)
        reconnect_btn = msg_box.addButton("🔌 Neuverbindung", QMessageBox.ButtonRole.ActionRole)
        ignore_btn = msg_box.addButton("⚠️ Ignorieren", QMessageBox.ButtonRole.RejectRole)
        
        # Styling für bessere Sichtbarkeit
        msg_box.setStyleSheet("""
            QMessageBox {
                font-size: 14px;
            }
            QPushButton {
                min-width: 120px;
                min-height: 35px;
                font-size: 12px;
                padding: 8px;
            }
        """)
        
        # Dialog anzeigen und Aktion basierend auf Button behandeln
        msg_box.exec()
        clicked_button = msg_box.clickedButton()
        
        if clicked_button == reset_btn:
            self.handle_modbus_reset_from_dialog()
        elif clicked_button == reconnect_btn:
            self.handle_modbus_reconnect_from_dialog()
        elif clicked_button == ignore_btn:
            self.handle_modbus_ignore_from_dialog()
        
        # Dialog kann wieder angezeigt werden
        self.modbus_failure_dialog_shown = False
    
    def handle_modbus_reset_from_dialog(self):
        """Controller-Reset aus Fehler-Dialog."""
        logging.info("Controller-Reset aus Fehler-Dialog initiiert")
        self.ui.show_status("Führe Controller-Reset durch...", "warning")
        
        try:
            if self.modbus_manager.restart_controller():
                self.ui.show_status("Controller-Reset erfolgreich - Verbinde neu...", "info")
                QTimer.singleShot(3000, self.handle_modbus_reconnect_from_dialog)  # 3 Sekunden warten
            else:
                self.ui.show_status("Controller-Reset fehlgeschlagen", "error")
                QTimer.singleShot(2000, self.show_modbus_failure_dialog)  # Dialog erneut anzeigen
        except Exception as e:
            logging.error(f"Fehler beim Controller-Reset: {e}")
            self.ui.show_status("Controller-Reset-Fehler", "error")
            QTimer.singleShot(2000, self.show_modbus_failure_dialog)
    
    def handle_modbus_reconnect_from_dialog(self):
        """Neuverbindung aus Fehler-Dialog."""
        logging.info("Neuverbindung aus Fehler-Dialog initiiert")
        self.ui.show_status("Verbinde Modbus neu...", "warning")
        
        try:
            if self.modbus_manager.force_reconnect():
                # Watchdog und Services neu starten
                self.modbus_manager.start_watchdog()
                self.modbus_manager.start_coil_refresh()
                
                # UI Status aktualisieren
                self.ui.update_modbus_status(True, self.modbus_manager.ip_address)
                self.ui.show_status("Modbus erfolgreich verbunden", "success")
                
                # App entsperren
                self.unlock_app_after_modbus_recovery()
                
            else:
                self.ui.update_modbus_status(False, self.modbus_manager.ip_address)
                self.ui.show_status("Neuverbindung fehlgeschlagen", "error")
                QTimer.singleShot(2000, self.show_modbus_failure_dialog)  # Dialog erneut anzeigen
                
        except Exception as e:
            logging.error(f"Fehler bei Neuverbindung: {e}")
            self.ui.show_status("Neuverbindungs-Fehler", "error")
            QTimer.singleShot(2000, self.show_modbus_failure_dialog)
    
    def handle_modbus_ignore_from_dialog(self):
        """Modbus-Fehler ignorieren (für Testing/Debug)."""
        logging.warning("Modbus-Fehler vom Benutzer ignoriert - App entsperrt")
        
        # Warnung anzeigen
        QMessageBox.warning(
            self,
            "⚠️ Modbus ignoriert",
            "Die Anwendung läuft OHNE Modbus-Verbindung!\n\n"
            "WARNUNG:\n"
            "• Keine Ausschuss-Signale an die WAGO\n"
            "• Kein Watchdog-System\n"
            "• Workflow eingeschränkt\n\n"
            "Nur für Test- und Debug-Zwecke verwenden!"
        )
        
        # App entsperren aber Modbus als kritisch markiert lassen
        self.unlock_app_after_modbus_recovery(force_unlock=True)
        self.ui.show_status("Modbus IGNORIERT - Testmodus aktiv", "warning")
    
    def unlock_app_after_modbus_recovery(self, force_unlock=False):
        """App nach Modbus-Wiederherstellung entsperren."""
        if force_unlock or self.modbus_manager.connected:
            self.modbus_critical_failure = False
            
            # Start-Button wieder aktivieren
            self.ui.start_btn.setEnabled(True)
            self.ui.start_btn.setStyleSheet("""
                QPushButton {
                    background-color: #27ae60;
                    font-size: 14px;
                    min-height: 35px;
                }
                QPushButton:hover {
                    background-color: #2ecc71;
                }
            """)
            self.ui.start_btn.setToolTip("")
            
            logging.info("Anwendung nach Modbus-Wiederherstellung entsperrt")
    
    def setup_exit_shortcuts(self):
        """ESC-Taste und andere Exit-Shortcuts einrichten."""
        # ESC-Taste für schnelles Beenden
        self.esc_shortcut = QShortcut(QKeySequence(Qt.Key.Key_Escape), self)
        self.esc_shortcut.activated.connect(self.quit_application)
        
        # Ctrl+Q als alternative (Standard unter Linux/Windows)
        self.quit_shortcut = QShortcut(QKeySequence("Ctrl+Q"), self)
        self.quit_shortcut.activated.connect(self.quit_application)
        
        logging.info("Exit shortcuts eingerichtet: ESC und Ctrl+Q")
    
    def quit_application(self):
        """Anwendung schnell und sauber beenden."""
        logging.info("Schnelles Beenden der Anwendung eingeleitet...")
        
        try:
            # 1. Sofort alle Timer stoppen
            if hasattr(self, 'update_timer'):
                self.update_timer.stop()
            if hasattr(self, 'settings_timer'):
                self.settings_timer.stop()
            
            # 2. Detection sofort stoppen (wichtig für Thread-Safety)
            if self.running:
                self.stop_detection()
            
            # 3. MODBUS sauber trennen
            try:
                self.modbus_manager.disconnect()
                logging.info("WAGO Modbus-Verbindung getrennt")
            except Exception as e:
                logging.warning(f"Fehler beim Trennen der Modbus-Verbindung: {e}")
            
            # 4. UI Status aktualisieren
            if hasattr(self, 'ui'):
                self.ui.show_status("Beende Anwendung...", "warning")
                QApplication.processEvents()  # UI aktualisieren
            
            # 5. Einstellungen speichern (schnell)
            try:
                self.settings.save()
                logging.info("Einstellungen gespeichert")
            except Exception as e:
                logging.warning(f"Einstellungen konnten nicht gespeichert werden: {e}")
            
            # 6. Anwendung beenden
            logging.info("Anwendung wird beendet")
            QApplication.quit()
            
        except Exception as e:
            logging.error(f"Fehler beim Beenden der Anwendung: {e}")
            # Notfall-Exit
            sys.exit(0)
    
    def auto_load_on_startup(self):
        """Automatisches Laden von Modell, Kamera und Konfiguration beim Start."""
        try:
            # Kamera-Konfiguration laden
            camera_config_path = self.settings.get('camera_config_path', '')
            if camera_config_path and os.path.exists(camera_config_path):
                if self.camera_config_manager.load_config(camera_config_path):
                    logging.info(f"Auto-loaded camera config: {camera_config_path}")
                else:
                    logging.warning(f"Failed to auto-load camera config: {camera_config_path}")
            
            # Letztes Modell laden
            last_model = self.settings.get('last_model', '')
            if last_model and os.path.exists(last_model):
                if self.detection_engine.load_model(last_model):
                    self.ui.model_info.setText(f"Modell: {os.path.basename(last_model)}")
                    self.ui.model_info.setStyleSheet("color: #27ae60; font-weight: bold;")
                    logging.info(f"Auto-loaded model: {last_model}")
                else:
                    logging.warning(f"Failed to auto-load model: {last_model}")
            
            # Letzte Kamera/Video-Quelle laden
            last_source = self.settings.get('last_source')
            last_mode_was_video = self.settings.get('last_mode_was_video', False)
            
            if last_source is not None:
                if last_mode_was_video and isinstance(last_source, str):
                    # Video-Datei
                    if os.path.exists(last_source):
                        if self.camera_manager.set_source(last_source):
                            self.ui.camera_info.setText(f"Video: {os.path.basename(last_source)}")
                            self.ui.camera_info.setStyleSheet("color: #27ae60; font-weight: bold;")
                            logging.info(f"Auto-loaded video: {last_source}")
                        else:
                            logging.warning(f"Failed to auto-load video: {last_source}")
                elif not last_mode_was_video and isinstance(last_source, int):
                    # Webcam
                    if self.camera_manager.set_source(last_source):
                        self.ui.camera_info.setText(f"Webcam: {last_source}")
                        self.ui.camera_info.setStyleSheet("color: #27ae60; font-weight: bold;")
                        logging.info(f"Auto-loaded webcam: {last_source}")
                    else:
                        logging.warning(f"Failed to auto-load webcam: {last_source}")
            
            # Status aktualisieren
            if self.detection_engine.model_loaded and self.camera_manager.camera_ready:
                if not self.modbus_critical_failure:
                    self.ui.show_status("Bereit - Alle Komponenten geladen", "ready")
                else:
                    self.ui.show_status("MODBUS-FEHLER: Start gesperrt", "error")
            elif self.detection_engine.model_loaded:
                self.ui.show_status("Modell geladen - Kamera/Video auswählen", "warning")
            elif self.camera_manager.camera_ready:
                self.ui.show_status("Kamera bereit - Modell laden", "warning")
            else:
                self.ui.show_status("Modell und Kamera/Video auswählen", "warning")
                
        except Exception as e:
            logging.error(f"Fehler beim Auto-Loading: {e}")
    
    def setup_connections(self):
        """Signale und Slots verbinden."""
        self.ui.start_btn.clicked.connect(self.toggle_detection)
        self.ui.model_btn.clicked.connect(self.load_model)
        self.ui.camera_btn.clicked.connect(self.select_camera)
        self.ui.settings_btn.clicked.connect(self.open_settings)
        self.ui.snapshot_btn.clicked.connect(self.take_snapshot)
        self.ui.login_status_btn.clicked.connect(self.toggle_login)  # GEÄNDERT: neuer Button
        self.ui.sidebar_toggle_btn.clicked.connect(self.toggle_sidebar)
        
        # BEENDEN Button verbinden
        self.ui.quit_btn.clicked.connect(self.quit_application)
    
    def toggle_login(self):
        """Login/Logout umschalten."""
        if self.user_manager.is_admin():
            # Logout
            self.user_manager.logout()
            self.ui.update_user_interface()
            self.ui.show_status("Abgemeldet - Operator-Modus", "info")
        else:
            # Login versuchen
            if self.user_manager.login():
                self.ui.update_user_interface()
                self.ui.show_status("Angemeldet als Admin / Dev", "success")
            else:
                self.ui.show_status("Falsches Passwort", "error")
    
    def toggle_sidebar(self):
        """Sidebar ein-/ausblenden."""
        self.ui.toggle_sidebar()
    
    def check_settings_changes(self):
        """Prüfe ob sich Einstellungen geändert haben."""
        try:
            current_time = os.path.getmtime(self.settings.filename)
            if current_time > self.last_settings_update:
                self.last_settings_update = current_time
                if self.running:
                    # Einstellungen während Laufzeit geändert
                    self.ui.show_status("Einstellungen geändert - Bitte Erkennung neu starten", "warning")
                else:
                    # Einstellungen neu laden
                    old_settings = self.settings.data.copy()
                    self.settings.load()
                    
                    # Update Image Saver mit neuen Einstellungen
                    self.image_saver.update_settings(self.settings.data)
                    
                    # Update Camera Config Manager falls Pfad geändert
                    new_camera_config_path = self.settings.get('camera_config_path', '')
                    if new_camera_config_path != old_settings.get('camera_config_path', ''):
                        if new_camera_config_path and os.path.exists(new_camera_config_path):
                            if self.camera_config_manager.load_config(new_camera_config_path):
                                logging.info(f"Kamera-Konfiguration neu geladen: {new_camera_config_path}")
                        else:
                            self.camera_config_manager.clear_config()
                            logging.info("Kamera-Konfiguration geleert")
                    
                    # Prüfe ob Modbus-Einstellungen geändert wurden
                    modbus_changed = self.modbus_manager.update_settings(self.settings.data)
                    if modbus_changed:
                        logging.info("Modbus-Einstellungen geändert - Neuverbindung...")
                        self.initialize_modbus_with_startup_reconnect()
                    
                    self.ui.show_status("Einstellungen aktualisiert", "info")
        except:
            pass  # Datei existiert möglicherweise nicht
    
    def toggle_detection(self):
        """Erkennung starten/stoppen."""
        if not self.running:
            self.start_detection()
        else:
            self.stop_detection()
    
    def start_detection(self):
        """Erkennung starten."""
        try:
            # KRITISCHER MODBUS-CHECK: Start-Sperre bei Modbus-Fehlern
            if self.modbus_critical_failure:
                self.ui.show_status("Start gesperrt - Modbus-Verbindung erforderlich", "error")
                QTimer.singleShot(500, self.show_modbus_failure_dialog)  # Dialog anzeigen
                return
            
            # Prüfe ob alles bereit ist
            if not self.detection_engine.model_loaded:
                self.ui.show_status("Bitte zuerst ein Modell laden", "error")
                return
                
            if not self.camera_manager.camera_ready:
                self.ui.show_status("Bitte zuerst Kamera/Video auswählen", "error")
                return
            
            # Kamera starten
            if self.camera_manager.start():
                self.running = True
                
                # Workflow-Status zurücksetzen
                self.reset_workflow()
                
                # ERWEITERTE Statistiken für neuen Zyklus zurücksetzen
                self.last_cycle_detections = {}
                self.current_frame_detections = []
                self.cycle_image_count = 0
                self.cycle_class_image_counts = {}
                
                # BESCHLEUNIGTE Bewegungserkennung initialisieren
                self.init_accelerated_motion_detection()
                
                # Helligkeits-Auto-Stopp zurücksetzen
                self.brightness_auto_stop_active = False
                self.low_brightness_start = None
                self.high_brightness_start = None
                
                # MODBUS: Detection-Active-Signal setzen
                if self.modbus_manager.connected:
                    self.modbus_manager.set_detection_active_coil(True)
                
                self.update_timer.start(30)  # ~30 FPS
                self.ui.start_btn.setText("Stoppen")
                self.ui.show_status("Bereit - Warte auf Förderband-Bewegung", "success")
                self.ui.update_workflow_status("READY")
                logging.info("Erkennung gestartet - Warte auf Bewegung")
            else:
                self.ui.show_status("Fehler beim Starten der Kamera", "error")
                
        except Exception as e:
            logging.error(f"Fehler beim Starten: {e}")
            self.ui.show_status(f"Fehler: {e}", "error")
    
    def init_accelerated_motion_detection(self):
        """BESCHLEUNIGTE Bewegungserkennung initialisieren (Motion-Drop schneller)."""
        # Background Subtractor mit optimierten Parametern für schnelleren Drop
        self.bg_subtractor = cv2.createBackgroundSubtractorMOG2(
            detectShadows=False,
            varThreshold=16,  # Fester Wert für Stabilität
            history=200  # REDUZIERT: Kürzere History für schnelleren Drop (vorher 500)
        )
        
        # Motion-Tracking zurücksetzen - VERKÜRZT für schnelleren Drop
        self.motion_history = []
        self.motion_stable_count = 0
        self.no_motion_stable_count = 0
        self.last_frame = None
        
        # Motion-Wert Tracking zurücksetzen - VERKÜRZT für schnellere Anzeige
        self.motion_values = []
        self.current_motion_value = 0.0
        
        logging.info("BESCHLEUNIGTE Motion-Detection initialisiert - Schnellerer Motion-Drop")
    
    def stop_detection(self):
        """Erkennung stoppen - SCHNELL und thread-safe."""
        logging.info("Stoppe Detection schnell und sauber...")
        
        # 1. Sofort Running-Flag setzen
        self.running = False
        
        # 2. Timer sofort stoppen
        if hasattr(self, 'update_timer'):
            self.update_timer.stop()
        
        # 3. MODBUS: Detection-Active-Signal ausschalten
        if self.modbus_manager.connected:
            self.modbus_manager.set_detection_active_coil(False)
        
        # 4. Kamera stoppen (kann etwas dauern)
        try:
            self.camera_manager.stop()
        except Exception as e:
            logging.warning(f"Fehler beim Stoppen der Kamera: {e}")
        
        # 5. UI sofort aktualisieren
        self.ui.start_btn.setText("Starten")
        if not self.modbus_critical_failure:
            self.ui.show_status("Bereit", "ready")
        else:
            self.ui.show_status("MODBUS-FEHLER: Start gesperrt", "error")
        self.ui.update_workflow_status("READY")
        
        # 6. Workflow-Status zurücksetzen
        self.reset_workflow()
        self.bg_subtractor = None
        
        # 7. Helligkeits-Auto-Stopp zurücksetzen
        self.brightness_auto_stop_active = False
        
        logging.info("Erkennung gestoppt")
    
    def stop_detection_due_to_brightness(self, reason):
        """Erkennung aufgrund Helligkeitsproblem stoppen."""
        if not self.running:
            return
            
        logging.warning(f"Stoppe Erkennung aufgrund Helligkeit: {reason}")
        
        # Detection stoppen
        self.stop_detection()
        
        # Flag setzen um wiederholte Stops zu verhindern
        self.brightness_auto_stop_active = True
        
        # UI Meldung
        self.ui.show_status(f"Erkennung gestoppt: {reason}", "error")
        
        # Optional: Benutzer benachrichtigen
        QMessageBox.warning(
            self,
            "Erkennung gestoppt",
            f"Die Objekterkennung wurde automatisch gestoppt:\n\n{reason}\n\n"
            f"Bitte die Beleuchtung prüfen und die Erkennung manuell neu starten."
        )
    
    def process_frame(self):
        """Aktuelles Frame verarbeiten."""
        try:
            # Schneller Exit-Check
            if not self.running:
                return
                
            frame = self.camera_manager.get_frame()
            if frame is None:
                return
            
            # Helligkeitsüberwachung mit Auto-Stopp
            self.check_brightness_with_auto_stop(frame)
            
            # Wenn brightness_auto_stop_active, nicht weiter verarbeiten
            if self.brightness_auto_stop_active:
                return
            
            # BESCHLEUNIGTES Motion-Wert berechnen und anzeigen
            self.update_accelerated_motion_display(frame)
            
            # Workflow verarbeiten
            self.process_industrial_workflow(frame)
            
            # KI-Erkennung nur während Aufnahme-Phase
            detections = []
            if self.detection_running and self.running:  # Doppel-Check für schnelles Beenden
                detections = self.detection_engine.detect(frame)
                self.current_frame_detections = detections
                
                # ERWEITERTE Erkennungen für aktuellen Zyklus sammeln
                self.update_enhanced_cycle_statistics(detections)
            
            # Frame mit Erkennungen zeichnen
            annotated_frame = self.detection_engine.draw_detections(frame, detections)
            
            # UI aktualisieren (nur wenn noch running)
            if self.running:
                self.ui.update_video(annotated_frame)
                self.ui.update_last_cycle_stats(self.last_cycle_detections)
                
        except Exception as e:
            logging.error(f"Fehler bei Frame-Verarbeitung: {e}")
    
    def update_accelerated_motion_display(self, frame):
        """BESCHLEUNIGTES Motion-Wert für Anzeige berechnen (schnellerer Drop)."""
        if self.bg_subtractor is None:
            return
        
        # Grayscale für bessere Performance
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Gaussian Blur für Rauschreduktion
        gray = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # Background Subtraction
        fg_mask = self.bg_subtractor.apply(gray)
        
        # Morphologische Operationen für Rauschreduktion
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_OPEN, kernel)
        fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_CLOSE, kernel)
        
        # Motion Pixels zählen (roher Wert)
        motion_pixels = cv2.countNonZero(fg_mask)
        
        # Normalisiere auf sinnvollen Bereich (0-255)
        motion_value = min(255, motion_pixels / 100)
        
        # VERKÜRZTE Glättung über weniger Frames für schnelleren Drop
        self.motion_values.append(motion_value)
        if len(self.motion_values) > 5:  # REDUZIERT: Nur 5 Frames statt 10
            self.motion_values.pop(0)
        
        # Geglätteter Motion-Wert für Anzeige
        self.current_motion_value = np.mean(self.motion_values)
        
        # UI aktualisieren
        self.ui.update_motion(self.current_motion_value)
    
    def process_industrial_workflow(self, frame):
        """ Workflow mit robuster Motion-Detection, MODBUS-Integration und Bilderspeicherung."""
        current_time = time.time()
        
        # Einstellungen (Threshold weiterhin einstellbar!)
        settling_time = self.settings.get('settling_time', 1.0)
        capture_time = self.settings.get('capture_time', 3.0)
        blow_off_time = self.settings.get('blow_off_time', 5.0)
        
        # 1. BESCHLEUNIGTE Bewegungserkennung (nur wenn nicht in spezieller Phase)
        if not self.motion_detected and not self.blow_off_active:
            motion_now = self.detect_accelerated_motion(frame)
            
            if motion_now and not self.motion_detected:
                # Bewegung erkannt - Förderband taktet
                self.motion_detected = True
                self.motion_cleared = False
                self.motion_clear_time = None
                self.no_motion_stable_count = 0  # Reset
                self.ui.show_status("Förderband taktet - Warte auf Stillstand", "warning")
                self.ui.update_workflow_status("MOTION")
                logging.info("Bewegung erkannt - Förderband startet")
        
        # 2. Stabiles Ausschwingen nach Bewegung
        if self.motion_detected and not self.motion_cleared:
            motion_now = self.detect_accelerated_motion(frame)
            
            if not motion_now:
                # Stabile No-Motion Zeit akkumulieren
                self.no_motion_stable_count += 1
                
                # REDUZIERTE Ausschwingzeit - schnellere Stabilisierung
                if self.no_motion_stable_count >= 5:  # REDUZIERT: 5 statt 10 Frames (~150ms)
                    if self.motion_clear_time is None:
                        self.motion_clear_time = current_time
                        self.ui.show_status("Ausschwingzeit läuft...", "warning")
                        self.ui.update_workflow_status("SETTLING")
                        logging.info("Stabile No-Motion erreicht - Ausschwingzeit startet")
                    
                    # Prüfe ob Ausschwingzeit abgelaufen
                    elif current_time - self.motion_clear_time >= settling_time:
                        # Ausschwingzeit beendet - Aufnahme startet
                        self.motion_cleared = True
                        self.detection_running = True
                        self.detection_start_time = current_time
                        
                        # ERWEITERTE Statistiken für neuen Zyklus zurücksetzen
                        self.last_cycle_detections = {}
                        self.cycle_image_count = 0
                        self.cycle_class_image_counts = {}
                        
                        self.ui.show_status("Aufnahme läuft - KI-Erkennung aktiv", "success")
                        self.ui.update_workflow_status("CAPTURING")
                        logging.info("Ausschwingzeit beendet - KI-Erkennung startet")
            else:
                # Wieder Bewegung - alles zurücksetzen
                self.motion_clear_time = None
                self.no_motion_stable_count = 0
                logging.debug("Motion detected during settling - resetting")
        
        # 3. Aufnahme-/Erkennungsphase
        if self.detection_running:
            if current_time - self.detection_start_time >= capture_time:
                # Aufnahme beendet - Prüfe Ergebnis
                self.detection_running = False
                bad_parts_detected = self.evaluate_detection_results()
                
                # BILDERSPEICHERUNG: Speichere Frame (OHNE Bounding Boxes)
                self.save_detection_result_image(frame, bad_parts_detected)
                
                # Counter aktualisieren
                self.ui.increment_session_counters(bad_parts_detected)
                
                if bad_parts_detected:
                    # Schlechte Teile erkannt - Abblasen erforderlich
                    self.blow_off_active = True
                    self.blow_off_start_time = current_time
                    
                    # MODBUS: Ausschuss-Signal aktivieren
                    if self.modbus_manager.connected:
                        self.modbus_manager.set_reject_coil()
                    
                    self.ui.show_status("Schlechte Teile erkannt - Abblasen aktiv", "error")
                    self.ui.update_workflow_status("BLOWING")
                    logging.info(f"Schlechte Teile erkannt - Abblas-Wartezeit: {blow_off_time}s")
                else:
                    # Alles gut - zurück zum Anfang
                    self.reset_workflow()
                    self.ui.show_status("Prüfung abgeschlossen - Bereit für nächsten Zyklus", "ready")
                    self.ui.update_workflow_status("READY")
                    logging.info("Keine schlechten Teile - Zyklus beendet")
        
        # 4. Abblas-Wartezeit
        if self.blow_off_active:
            if current_time - self.blow_off_start_time >= blow_off_time:
                # Abblas-Wartezeit beendet
                self.blow_off_active = False
                self.reset_workflow()
                self.ui.show_status("Abblasen beendet - Bereit für nächsten Zyklus", "ready")
                self.ui.update_workflow_status("READY")
                logging.info("Abblas-Wartezeit beendet - Zyklus beendet")
    
    def save_detection_result_image(self, frame, bad_parts_detected):
        """Speichere Bild basierend auf Erkennungsergebnis."""
        try:
            if bad_parts_detected:
                # Schlechtbild speichern
                result = self.image_saver.save_bad_image(frame, self.last_cycle_detections)
                if result == "DIRECTORY_FULL":
                    self.ui.show_status("Schlechtbild-Verzeichnis voll (100000 Dateien)", "warning")
                elif result:
                    logging.debug("Schlechtbild gespeichert")
            else:
                # Gutbild speichern
                result = self.image_saver.save_good_image(frame, self.last_cycle_detections)
                if result == "DIRECTORY_FULL":
                    self.ui.show_status("Gutbild-Verzeichnis voll (100000 Dateien)", "warning")
                elif result:
                    logging.debug("Gutbild gespeichert")
                    
        except Exception as e:
            logging.error(f"Fehler beim Speichern des Ergebnisbilds: {e}")
    
    def detect_accelerated_motion(self, frame):
        """BESCHLEUNIGTE Bewegungserkennung (Motion-Drop schneller)."""
        if self.bg_subtractor is None:
            return False
        
        # Grayscale für bessere Performance
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Gaussian Blur für Rauschreduktion
        gray = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # Background Subtraction
        fg_mask = self.bg_subtractor.apply(gray)
        
        # Morphologische Operationen für Rauschreduktion
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_OPEN, kernel)
        fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_CLOSE, kernel)
        
        # Motion Pixels zählen
        motion_pixels = cv2.countNonZero(fg_mask)
        
        # EINSTELLBARER Threshold (das war das Missverständnis - bleibt einstellbar!)
        motion_threshold = self.settings.get('motion_threshold', 110) * 100
        has_motion = motion_pixels > motion_threshold
        
        # VERKÜRZTE Rolling Window für schnellere Stabilität
        self.motion_history.append(has_motion)
        if len(self.motion_history) > 3:  # REDUZIERT: 3 statt 5 Frames
            self.motion_history.pop(0)
        
        # Motion nur wenn mindestens 2 von 3 Frames Motion haben
        stable_motion = sum(self.motion_history) >= 2  # REDUZIERT: 2 statt 3
        
        # REDUZIERTE Stabilität: Motion muss nur 2 Frames bestehen
        if stable_motion:
            self.motion_stable_count += 1
        else:
            self.motion_stable_count = 0
        
        # Endgültige Motion-Entscheidung - SCHNELLER
        final_motion = self.motion_stable_count >= 2  # REDUZIERT: 2 statt 3 Frames
        
        return final_motion
    
    def reset_workflow(self):
        """Workflow für nächsten Zyklus zurücksetzen."""
        self.motion_detected = False
        self.motion_cleared = False
        self.detection_running = False
        self.blow_off_active = False
        self.motion_clear_time = None
        self.detection_start_time = None
        self.blow_off_start_time = None
        self.motion_stable_count = 0
        self.no_motion_stable_count = 0
    
    def update_enhanced_cycle_statistics(self, detections):
        """ERWEITERTE Erkennungen für aktuellen Zyklus sammeln mit Bildanzahl-Tracking."""
        # Bildanzahl für aktuellen Zyklus erhöhen
        self.cycle_image_count += 1
        
        # Klassen in diesem Frame sammeln
        classes_in_this_frame = set()
        
        for detection in detections:
            _, _, _, _, confidence, class_id = detection
            class_name = self.detection_engine.class_names.get(class_id, f"Class {class_id}")
            
            classes_in_this_frame.add(class_name)
            
            # Nur für aktuellen Zyklus (nicht Session-Gesamtstatistik)
            if class_name not in self.last_cycle_detections:
                self.last_cycle_detections[class_name] = {
                    'total_detections': 0,  # Gesamtanzahl aller Erkennungen dieser Klasse
                    'max_confidence': 0.0,
                    'min_confidence': 1.0,
                    'confidences': [],
                    'class_id': class_id
                }
                self.cycle_class_image_counts[class_name] = 0
            
            self.last_cycle_detections[class_name]['total_detections'] += 1
            self.last_cycle_detections[class_name]['confidences'].append(confidence)
            self.last_cycle_detections[class_name]['max_confidence'] = max(
                self.last_cycle_detections[class_name]['max_confidence'], confidence
            )
            self.last_cycle_detections[class_name]['min_confidence'] = min(
                self.last_cycle_detections[class_name]['min_confidence'], confidence
            )
        
        # Für jede Klasse in diesem Frame: Bildanzahl erhöhen
        for class_name in classes_in_this_frame:
            if class_name in self.cycle_class_image_counts:
                self.cycle_class_image_counts[class_name] += 1
    
    def evaluate_detection_results(self):
        """Erkennungsergebnisse auswerten mit Priorisierung: Schlecht > Gut > Standard."""
        # Hole alle relevanten Einstellungen
        bad_part_classes = self.settings.get('bad_part_classes', [])
        good_part_classes = self.settings.get('good_part_classes', [])
        red_threshold = self.settings.get('red_threshold', 1)
        green_threshold = self.settings.get('green_threshold', 4)
        min_confidence = self.settings.get('bad_part_min_confidence', 0.5)
        
        # 1. PRIORITÄT: Prüfe auf schlechte Teile (Rote Rahmen)
        for class_name, stats in self.last_cycle_detections.items():
            class_id = stats.get('class_id', 0)
            max_conf = stats.get('max_confidence', 0.0)
            
            # Verwende total_detections statt count
            total_detections = stats.get('total_detections', 0)
            
            # Prüfe: Klasse in bad_part_classes UND Anzahl >= red_threshold UND Konfidenz >= min_confidence
            if (class_id in bad_part_classes and 
                total_detections >= red_threshold and 
                max_conf >= min_confidence):
                logging.info(f"Schlechtes Teil erkannt: {class_name} (Anzahl: {total_detections}, Konfidenz: {max_conf:.2f})")
                return True
        
        # 2. PRIORITÄT: Prüfe auf gute Teile (Grüne Rahmen) - nur wenn keine schlechten Teile
        for class_name, stats in self.last_cycle_detections.items():
            class_id = stats.get('class_id', 0)
            
            # Verwende total_detections statt count
            total_detections = stats.get('total_detections', 0)
            
            # Prüfe: Klasse in good_part_classes UND Anzahl >= green_threshold
            if (class_id in good_part_classes and 
                total_detections >= green_threshold):
                logging.info(f"Gutes Teil erkannt: {class_name} (Anzahl: {total_detections})")
                return False  # Kein Abblasen erforderlich
        
        # 3. STANDARD: Weder schlechte noch gute Teile erfüllen Kriterien
        logging.info("Keine eindeutige Klassifizierung - Standard: Kein Abblasen")
        return False
    
    def check_brightness_with_auto_stop(self, frame):
        """Helligkeitsüberwachung mit automatischem Stopp der Erkennung."""
        # Durchschnittshelligkeit berechnen
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        brightness = np.mean(gray)
        
        # Glättung über mehrere Frames
        self.brightness_values.append(brightness)
        if len(self.brightness_values) > 30:  # Letzte 30 Frames
            self.brightness_values.pop(0)
        
        avg_brightness = np.mean(self.brightness_values)
        
        # Schwellwerte prüfen
        low_threshold = self.settings.get('brightness_low_threshold', 30)
        high_threshold = self.settings.get('brightness_high_threshold', 220)
        duration_threshold = self.settings.get('brightness_duration_threshold', 3.0)
        
        current_time = time.time()
        
        # Zu dunkle Helligkeit prüfen
        if avg_brightness < low_threshold:
            if self.low_brightness_start is None:
                self.low_brightness_start = current_time
            elif current_time - self.low_brightness_start >= duration_threshold:
                # AUTO-STOPP: Zu dunkel für zu lange
                if not self.brightness_auto_stop_active:
                    self.stop_detection_due_to_brightness(f"Zu dunkel: {avg_brightness:.1f} < {low_threshold}")
                return
        else:
            self.low_brightness_start = None
        
        # Zu helle Helligkeit prüfen
        if avg_brightness > high_threshold:
            if self.high_brightness_start is None:
                self.high_brightness_start = current_time
            elif current_time - self.high_brightness_start >= duration_threshold:
                # AUTO-STOPP: Zu hell für zu lange
                if not self.brightness_auto_stop_active:
                    self.stop_detection_due_to_brightness(f"Zu hell: {avg_brightness:.1f} > {high_threshold}")
                return
        else:
            self.high_brightness_start = None
        
        #  Normale Helligkeit - kein Auto-Stopp erforderlich
        self.ui.hide_brightness_warning()
        
        # Helligkeit in UI anzeigen
        self.ui.update_brightness(avg_brightness)
    
    def load_model(self):
        """KI-Modell laden."""
        if not self.user_manager.can_change_model():
            self.ui.show_status("Keine Berechtigung - Admin-Login erforderlich", "error")
            return
            
        model_path = self.ui.select_model_file()
        if model_path:
            if self.detection_engine.load_model(model_path):
                self.ui.show_status(f"Modell geladen: {os.path.basename(model_path)}", "success")
                self.settings.set('last_model', model_path)
                self.settings.save()
            else:
                self.ui.show_status("Fehler beim Laden des Modells", "error")
    
    def select_camera(self):
        """Kamera/Video auswählen."""
        if not self.user_manager.can_change_camera():
            self.ui.show_status("Keine Berechtigung - Admin-Login erforderlich", "error")
            return
            
        source = self.ui.select_camera_source()
        if source:
            if self.camera_manager.set_source(source):
                self.ui.show_status(f"Quelle ausgewählt: {source}", "success")
                
                # Speichere Quelle und Modus
                self.settings.set('last_source', source)
                self.settings.set('last_mode_was_video', isinstance(source, str))
                self.settings.save()
            else:
                self.ui.show_status("Fehler bei Quellenauswahl", "error")
    
    def open_settings(self):
        """Einstellungen öffnen."""
        if not self.user_manager.can_access_settings():
            self.ui.show_status("Keine Berechtigung - Admin-Login erforderlich", "error")
            return
            
        self.ui.open_settings_dialog(self.settings)
    
    def take_snapshot(self):
        """Schnappschuss machen."""
        frame = self.camera_manager.get_frame()
        if frame is not None:
            filename = self.camera_manager.save_snapshot(frame)
            if filename:
                self.ui.show_status(f"Schnappschuss gespeichert: {filename}", "success")
            else:
                self.ui.show_status("Fehler beim Speichern", "error")
    
    def closeEvent(self, event):
        """Sauberes Herunterfahren der Anwendung."""
        logging.info("Application closing - performing cleanup")
        try:
            # Verwende die robuste quit_application Methode
            self.quit_application()
        except Exception as e:
            logging.error(f"Error during application shutdown: {e}")
        finally:
            event.accept()

def main():
    """Hauptfunktion."""
    app = QApplication(sys.argv)
    app.setApplicationName("KI-Objekterkennung mit WAGO Modbus")
    
    # Moderne Schriftart
    app.setFont(QFont("Segoe UI", 10))
    
    # Hauptfenster erstellen und anzeigen
    window = DetectionApp()
    window.show()
    
    # Event-Loop starten
    sys.exit(app.exec())

if __name__ == "__main__":
    main()