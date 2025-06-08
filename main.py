#!/usr/bin/env python3
"""
Einfache KI-Objekterkennungs-Anwendung - Industrieller Workflow
Mit Counter, Motion-Anzeige, WAGO Modbus-Schnittstelle, Bilderspeicherung und Helligkeits-basiertem Stopp
OPTIMIERT: Intelligente Modbus-Initialisierung ohne redundante Aktionen
"""

import sys
import os
import logging
import time
import cv2
import numpy as np
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout
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
    """Hauptanwendung für industrielle KI-Objekterkennung mit OPTIMIERTER Modbus-Initialisierung."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("KI-Objekterkennung - Industriell mit WAGO Modbus")
        self.setWindowState(Qt.WindowState.WindowFullScreen)
        
        # Komponenten initialisieren
        self.settings = Settings()
        self.user_manager = UserManager()
        
        # Kamera-Konfigurationsmanager für IDS Peak
        self.camera_config_manager = CameraConfigManager()
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
        self.modbus_critical_failure = False  # Flag für kritische Modbus-Ausfälle
        
        # Industrieller Workflow-Status
        self.motion_detected = False
        self.motion_cleared = False
        self.detection_running = False
        self.blow_off_active = False
        
        # Timing-Variablen
        self.motion_clear_time = None
        self.detection_start_time = None
        self.blow_off_start_time = None
        
        # Erkennungsstatistiken - Erweitert für neue Tabelle
        self.last_cycle_detections = {}  # Erkennungen des letzten Capture-Zyklus
        self.current_frame_detections = []  # Aktuelle Frame-Erkennungen
        self.cycle_image_count = 0  # Anzahl Bilder im aktuellen Zyklus
        
        # Timer für Frame-Updates
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.process_frame)
        
        # Robuste Bewegungserkennung mit schnellerem Motion-Drop
        self.bg_subtractor = None
        self.last_frame = None
        self.motion_history = []  # Rolling window für stabilere Erkennung
        self.motion_stable_count = 0  # Zähler für stabile Motion-States
        self.no_motion_stable_count = 0  # Zähler für stabile No-Motion-States
        
        # Motion-Wert Tracking (für Anzeige) - OPTIMIERT für schnelleren Drop
        self.motion_values = []  # Rolling window für geglättete Motion-Anzeige
        self.current_motion_value = 0.0  # Aktueller, geglätteter Motion-Wert
        self.motion_decay_factor = 0.85  # Schnellerer Abfall (vorher implizit langsamer)
        
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
        
        # OPTIMIERTE MODBUS-Initialisierung
        self.initialize_smart_modbus()
        
        # Auto-Loading beim Start
        self.auto_load_on_startup()
        
        logging.info("DetectionApp gestartet - Optimierte Modbus-Initialisierung")
    
    def initialize_smart_modbus(self):
        """INTELLIGENTE Modbus-Initialisierung - vermeidet redundante Aktionen."""
        if not self.settings.get('modbus_enabled', True):
            logging.info("Modbus deaktiviert in den Einstellungen")
            return
        
        try:
            logging.info("Starte intelligente WAGO Modbus-Initialisierung...")
            
            # SCHRITT 1: Versuche zuerst normale Verbindung (ohne Reset)
            if self.modbus_manager.connect():
                logging.info("WAGO Modbus-Direktverbindung erfolgreich - kein Reset erforderlich")
                
                # Direkt zu Watchdog und Services
                self._start_modbus_services()
                return
            
            # SCHRITT 2: Normale Verbindung fehlgeschlagen -> Controller-Reset versuchen
            logging.warning("Normale WAGO-Verbindung fehlgeschlagen - versuche Controller-Reset...")
            
            if self.modbus_manager.restart_controller():
                logging.info("Controller-Reset erfolgreich - warte auf Neustart...")
                time.sleep(3)  # Warten nach Reset
                
                # SCHRITT 3: Nach Reset erneut verbinden
                if self.modbus_manager.connect():
                    logging.info("WAGO Verbindung nach Reset erfolgreich")
                    self._start_modbus_services()
                    return
                else:
                    logging.error("WAGO Verbindung auch nach Reset fehlgeschlagen")
            else:
                logging.warning("Controller-Reset fehlgeschlagen")
                
                # SCHRITT 4: Letzter Versuch ohne Reset
                logging.info("Letzter Verbindungsversuch ohne Reset...")
                if self.modbus_manager.connect():
                    logging.info("WAGO Verbindung im letzten Versuch erfolgreich")
                    self._start_modbus_services()
                    return
            
            # SCHRITT 5: Alle Versuche fehlgeschlagen
            logging.error("ALLE WAGO Modbus-Verbindungsversuche fehlgeschlagen")
            self.modbus_critical_failure = True
            self.ui.update_modbus_status(False, self.modbus_manager.ip_address)
            self.lock_app_due_to_modbus_failure()
                
        except Exception as e:
            logging.error(f"Kritischer Fehler bei WAGO Modbus-Initialisierung: {e}")
            self.modbus_critical_failure = True
            self.ui.update_modbus_status(False, self.modbus_manager.ip_address)
            self.lock_app_due_to_modbus_failure()
    
    def _start_modbus_services(self):
        """Starte Modbus-Services nach erfolgreicher Verbindung."""
        try:
            # UI Status sofort aktualisieren
            self.ui.update_modbus_status(True, self.modbus_manager.ip_address)
            
            # Watchdog starten (mit Verzögerung für ersten Trigger)
            if self.modbus_manager.start_watchdog():
                logging.info("WAGO Watchdog erfolgreich gestartet")
                
                # Kurz warten vor erstem Trigger-Versuch
                time.sleep(1)
            else:
                logging.warning("WAGO Watchdog konnte nicht gestartet werden")
            
            # Coil-Refresh starten (SIMPLE Version)
            if self.modbus_manager.start_coil_refresh():
                logging.info("WAGO Coil-Refresh erfolgreich gestartet")
            else:
                logging.warning("WAGO Coil-Refresh konnte nicht gestartet werden")
            
            logging.info("WAGO Modbus vollständig initialisiert")
            
        except Exception as e:
            logging.error(f"Fehler beim Starten der Modbus-Services: {e}")
    
    def lock_app_due_to_modbus_failure(self):
        """Sperre App bei kritischem Modbus-Ausfall."""
        self.modbus_critical_failure = True
        
        # UI-Elemente deaktivieren
        if hasattr(self.ui, 'start_btn'):
            self.ui.start_btn.setEnabled(False)
        
        self.ui.show_status("MODBUS-FEHLER: Anwendung gesperrt", "error")
        logging.critical("Anwendung gesperrt aufgrund kritischen Modbus-Ausfalls")
    
    def unlock_app_after_modbus_recovery(self):
        """Entsperre App nach Modbus-Wiederherstellung."""
        self.modbus_critical_failure = False
        
        # UI-Elemente wieder aktivieren
        if hasattr(self.ui, 'start_btn'):
            self.ui.start_btn.setEnabled(True)
        
        self.ui.show_status("Modbus wiederhergestellt - Anwendung entsperrt", "success")
        logging.info("Anwendung entsperrt nach Modbus-Wiederherstellung")
    
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
            # Letztes Modell laden
            last_model = self.settings.get('last_model', '')
            if last_model and os.path.exists(last_model):
                if self.detection_engine.load_model(last_model):
                    self.ui.model_info.setText(f"Modell: {os.path.basename(last_model)}")
                    self.ui.model_info.setStyleSheet("color: #27ae60; font-weight: bold;")
                    logging.info(f"Auto-loaded model: {last_model}")
                else:
                    logging.warning(f"Failed to auto-load model: {last_model}")
            
            # Kamera-Konfiguration laden
            camera_config_path = self.settings.get('camera_config_path', '')
            if camera_config_path and os.path.exists(camera_config_path):
                if self.camera_config_manager.load_config(camera_config_path):
                    logging.info(f"Auto-loaded camera config: {camera_config_path}")
                else:
                    logging.warning(f"Failed to auto-load camera config: {camera_config_path}")
            
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
                    self.ui.show_status("Modell/Kamera bereit - Modbus-Problem", "warning")
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
        self.ui.login_status_btn.clicked.connect(self.toggle_login)  # GEÄNDERT: Neuer Button
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
                    
                    # Update Kamera-Konfiguration
                    camera_config_path = self.settings.get('camera_config_path', '')
                    if camera_config_path and os.path.exists(camera_config_path):
                        self.camera_config_manager.load_config(camera_config_path)
                    
                    # Prüfe ob Modbus-Einstellungen geändert wurden
                    modbus_changed = self.modbus_manager.update_settings(self.settings.data)
                    if modbus_changed:
                        logging.info("Modbus-Einstellungen geändert - Neuverbindung...")
                        self.initialize_smart_modbus()
                    
                    self.ui.show_status("Einstellungen aktualisiert", "info")
        except:
            pass  # Datei existiert möglicherweise nicht
    
    def toggle_detection(self):
        """Erkennung starten/stoppen."""
        # Prüfe auf kritischen Modbus-Ausfall
        if self.modbus_critical_failure and not self.running:
            from PyQt6.QtWidgets import QMessageBox, QPushButton
            
            msg = QMessageBox(self)
            msg.setWindowTitle("Modbus-Verbindungsfehler")
            msg.setText("Die Objekterkennung kann nicht gestartet werden:")
            msg.setInformativeText(
                "Alle Modbus-Verbindungsversuche zur WAGO-Steuerung sind fehlgeschlagen.\n\n"
                "Mögliche Ursachen:\n"
                "• Netzwerkverbindung unterbrochen\n"
                "• WAGO-Controller nicht erreichbar\n"
                "• Falsche IP-Adresse konfiguriert\n\n"
                "Verwenden Sie die Buttons unten, um das Problem zu beheben:"
            )
            msg.setIcon(QMessageBox.Icon.Critical)
            
            # Custom Buttons
            reset_btn = msg.addButton("Controller Reset", QMessageBox.ButtonRole.ActionRole)
            reconnect_btn = msg.addButton("Neuverbindung", QMessageBox.ButtonRole.ActionRole)
            cancel_btn = msg.addButton("Abbrechen", QMessageBox.ButtonRole.RejectRole)
            
            msg.exec()
            
            if msg.clickedButton() == reset_btn:
                # Controller Reset versuchen
                self.ui.show_status("Führe Controller-Reset durch...", "warning")
                if self.modbus_manager.restart_controller():
                    time.sleep(3)
                    if self.modbus_manager.connect():
                        self._start_modbus_services()
                        self.unlock_app_after_modbus_recovery()
                    else:
                        self.ui.show_status("Reset erfolgreich, Verbindung fehlgeschlagen", "error")
                else:
                    self.ui.show_status("Controller-Reset fehlgeschlagen", "error")
                    
            elif msg.clickedButton() == reconnect_btn:
                # Neuverbindung versuchen
                self.ui.show_status("Versuche Neuverbindung...", "warning")
                if self.modbus_manager.connect():
                    self._start_modbus_services()
                    self.unlock_app_after_modbus_recovery()
                else:
                    self.ui.show_status("Neuverbindung fehlgeschlagen", "error")
            
            return
        
        if not self.running:
            self.start_detection()
        else:
            self.stop_detection()
    
    def start_detection(self):
        """Erkennung starten."""
        try:
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
                
                # Erkennungsstatistiken zurücksetzen
                self.last_cycle_detections = {}
                self.current_frame_detections = []
                self.cycle_image_count = 0
                
                # Robuste Bewegungserkennung initialisieren
                self.init_robust_motion_detection()
                
                # Helligkeits-Auto-Stopp zurücksetzen
                self.brightness_auto_stop_active = False
                self.low_brightness_start = None
                self.high_brightness_start = None
                
                # MODBUS: Detection-Active-Signal setzen (wenn verfügbar)
                if self.modbus_manager.connected:
                    self.modbus_manager.set_detection_active_coil(True)
                    self.ui.update_coil_status(detection_active=True)
                
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
    
    def init_robust_motion_detection(self):
        """Robuste Bewegungserkennung initialisieren mit optimiertem Motion-Drop."""
        # Background Subtractor mit festen Parametern (außer Threshold)
        self.bg_subtractor = cv2.createBackgroundSubtractorMOG2(
            detectShadows=False,
            varThreshold=16,  # Fester Wert für Stabilität
            history=500
        )
        
        # Motion-Tracking zurücksetzen
        self.motion_history = []
        self.motion_stable_count = 0
        self.no_motion_stable_count = 0
        self.last_frame = None
        
        # Motion-Wert Tracking zurücksetzen mit Decay-Faktor
        self.motion_values = []
        self.current_motion_value = 0.0
        
        logging.info("Robuste Motion-Detection mit schnellerem Drop initialisiert")
    
    def stop_detection(self):
        """Erkennung stoppen - SCHNELL und thread-safe."""
        logging.info("Stoppe Detection schnell und sauber...")
        
        # 1. Sofort Running-Flag setzen
        self.running = False
        
        # 2. Timer sofort stoppen
        if hasattr(self, 'update_timer'):
            self.update_timer.stop()
        
        # 3. MODBUS: Detection-Active-Signal ausschalten (wenn verfügbar)
        if self.modbus_manager.connected:
            self.modbus_manager.set_detection_active_coil(False)
            self.ui.update_coil_status(detection_active=False)
        
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
            self.ui.show_status("Bereit - Modbus-Problem", "warning")
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
        from PyQt6.QtWidgets import QMessageBox
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
            
            # Motion-Wert berechnen und anzeigen (OPTIMIERT für schnelleren Drop)
            self.update_motion_display_with_decay(frame)
            
            # Industrieller Workflow verarbeiten
            self.process_industrial_workflow(frame)
            
            # KI-Erkennung nur während Aufnahme-Phase
            detections = []
            if self.detection_running and self.running:  # Doppel-Check für schnelles Beenden
                detections = self.detection_engine.detect(frame)
                self.current_frame_detections = detections
                
                # Erkennungen für aktuellen Zyklus sammeln (ERWEITERT)
                self.update_cycle_statistics_extended(detections)
                self.cycle_image_count += 1  # Frame-Zähler erhöhen
            
            # Frame mit Erkennungen zeichnen
            annotated_frame = self.detection_engine.draw_detections(frame, detections)
            
            # UI aktualisieren (nur wenn noch running)
            if self.running:
                self.ui.update_video(annotated_frame)
                self.ui.update_last_cycle_stats(self.last_cycle_detections)  # GEÄNDERT: Weniger Parameter
                
        except Exception as e:
            logging.error(f"Fehler bei Frame-Verarbeitung: {e}")
    
    def update_motion_display_with_decay(self, frame):
        """Motion-Wert für Anzeige berechnen mit Decay-Faktor für schnelleren Drop."""
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
        current_motion = min(255, motion_pixels / 100)  # Grober Normalisierungsansatz
        
        # OPTIMIERT: Decay-Anwendung für schnelleren Drop bei wenig Bewegung
        if current_motion < self.current_motion_value:
            # Bewegung nimmt ab -> Decay anwenden für schnelleren Drop
            self.current_motion_value = self.current_motion_value * self.motion_decay_factor
            # Aber nicht unter aktuellen Wert
            self.current_motion_value = max(self.current_motion_value, current_motion)
        else:
            # Bewegung nimmt zu -> Direkter Wert
            self.current_motion_value = current_motion
        
        # UI aktualisieren
        self.ui.update_motion(self.current_motion_value)
    
    def process_industrial_workflow(self, frame):
        """Industrieller Workflow mit robuster Motion-Detection, MODBUS-Integration und Bilderspeicherung."""
        current_time = time.time()
        
        # Einstellungen (Threshold weiterhin einstellbar!)
        settling_time = self.settings.get('settling_time', 1.0)
        capture_time = self.settings.get('capture_time', 3.0)
        blow_off_time = self.settings.get('blow_off_time', 5.0)
        
        # 1. Robuste Bewegungserkennung (nur wenn nicht in spezieller Phase)
        if not self.motion_detected and not self.blow_off_active:
            motion_now = self.detect_robust_motion(frame)
            
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
            motion_now = self.detect_robust_motion(frame)
            
            if not motion_now:
                # Stabile No-Motion Zeit akkumulieren
                self.no_motion_stable_count += 1
                
                # Ausschwingzeit startet erst nach stabiler No-Motion Phase
                if self.no_motion_stable_count >= 10:  # ~300ms stabile No-Motion
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
                        self.last_cycle_detections = {}  # Reset für neue Aufnahme-Session
                        self.cycle_image_count = 0  # Reset Frame-Counter
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
                    
                    # MODBUS: Ausschuss-Signal aktivieren (wenn verfügbar)
                    if self.modbus_manager.connected:
                        self.modbus_manager.set_reject_coil()
                        self.ui.update_coil_status(reject_active=True, detection_active=True)
                    
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
                
                # MODBUS: Coil-Status zurücksetzen
                if self.modbus_manager.connected:
                    self.ui.update_coil_status(reject_active=False, detection_active=True)
                
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
    
    def detect_robust_motion(self, frame):
        """Robuste Bewegungserkennung (Threshold weiterhin einstellbar!)."""
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
        
        # Rolling Window für Stabilität (wie komplexe App)
        self.motion_history.append(has_motion)
        if len(self.motion_history) > 5:  # Letzte 5 Frames
            self.motion_history.pop(0)
        
        # Motion nur wenn mindestens 3 von 5 Frames Motion haben
        stable_motion = sum(self.motion_history) >= 3
        
        # Zusätzliche Stabilität: Motion muss mindestens 3 Frames bestehen
        if stable_motion:
            self.motion_stable_count += 1
        else:
            self.motion_stable_count = 0
        
        # Endgültige Motion-Entscheidung
        final_motion = self.motion_stable_count >= 3
        
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
    
    def update_cycle_statistics_extended(self, detections):
        """Erkennungen für aktuellen Zyklus sammeln - ERWEITERT für neue Tabelle."""
        for detection in detections:
            _, _, _, _, confidence, class_id = detection
            class_name = self.detection_engine.class_names.get(class_id, f"Class {class_id}")
            
            # Nur für aktuellen Zyklus (nicht Session-Gesamtstatistik)
            if class_name not in self.last_cycle_detections:
                self.last_cycle_detections[class_name] = {
                    'count': 0,
                    'max_confidence': 0.0,
                    'min_confidence': 1.0,  # NEU für MIN-Spalte
                    'avg_confidence': 0.0,
                    'confidences': [],
                    'class_id': class_id,
                    'total_detections': 0  # NEU für Durchschnittsberechnung
                }
            
            stats = self.last_cycle_detections[class_name]
            stats['count'] += 1
            stats['total_detections'] += 1  # Gesamtzahl für Durchschnitt
            stats['confidences'].append(confidence)
            stats['max_confidence'] = max(stats['max_confidence'], confidence)
            stats['min_confidence'] = min(stats['min_confidence'], confidence)  # NEU
            
            # Durchschnitt berechnen
            confidences = stats['confidences']
            stats['avg_confidence'] = sum(confidences) / len(confidences)
    
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
        
        # Normale Helligkeit - kein Auto-Stopp erforderlich
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