#!/usr/bin/env python3
"""
Einfache KI-Objekterkennungs-Anwendung - Industrieller Workflow
Mit Counter, Motion-Anzeige, WAGO Modbus-Schnittstelle und optimiertem Layout
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
from settings import Settings
from ui.main_ui import MainUI  # Direkter Import aus main_ui
from user_manager import UserManager
from modbus_manager import ModbusManager

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
    """Hauptanwendung für industrielle KI-Objekterkennung mit Counter, Motion-Anzeige und WAGO Modbus."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("KI-Objekterkennung - Industriell mit WAGO Modbus")
        self.setWindowState(Qt.WindowState.WindowFullScreen)
        
        # Komponenten initialisieren
        self.settings = Settings()
        self.user_manager = UserManager()
        self.camera_manager = CameraManager()
        self.detection_engine = DetectionEngine()
        
        # MODBUS-Manager initialisieren
        self.modbus_manager = ModbusManager(self.settings)
        
        # UI aufbauen
        self.ui = MainUI(self)
        self.setCentralWidget(self.ui)
        
        # Verbindungen herstellen
        self.setup_connections()
        
        # ESC-Taste für schnelles Beenden
        self.setup_exit_shortcuts()
        
        # Status
        self.running = False
        
        # Industrieller Workflow-Status
        self.motion_detected = False
        self.motion_cleared = False
        self.detection_running = False
        self.blow_off_active = False
        
        # Timing-Variablen
        self.motion_clear_time = None
        self.detection_start_time = None
        self.blow_off_start_time = None
        
        # Erkennungsstatistiken - NUR für letzten Zyklus (nicht Session-Summen)
        self.last_cycle_detections = {}  # Erkennungen des letzten Capture-Zyklus
        self.current_frame_detections = []  # Aktuelle Frame-Erkennungen
        
        # Timer für Frame-Updates
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.process_frame)
        
        # Robuste Bewegungserkennung (wie komplexe App, aber Threshold einstellbar)
        self.bg_subtractor = None
        self.last_frame = None
        self.motion_history = []  # Rolling window für stabilere Erkennung
        self.motion_stable_count = 0  # Zähler für stabile Motion-States
        self.no_motion_stable_count = 0  # Zähler für stabile No-Motion-States
        
        # Motion-Wert Tracking (für Anzeige)
        self.motion_values = []  # Rolling window für geglättete Motion-Anzeige
        self.current_motion_value = 0.0  # Aktueller, geglätteter Motion-Wert
        
        # Helligkeitsüberwachung
        self.brightness_values = []
        self.low_brightness_start = None
        
        # Einstellungen überwachen
        self.last_settings_update = 0
        self.settings_timer = QTimer()
        self.settings_timer.timeout.connect(self.check_settings_changes)
        self.settings_timer.start(2000)  # Alle 2 Sekunden prüfen
        
        # MODBUS initialisieren
        self.initialize_modbus()
        
        # Auto-Loading beim Start
        self.auto_load_on_startup()
        
        logging.info("DetectionApp gestartet - Industrieller Workflow mit WAGO Modbus")
    
    def initialize_modbus(self):
        """WAGO Modbus initialisieren."""
        if not self.settings.get('modbus_enabled', True):
            logging.info("Modbus deaktiviert in den Einstellungen")
            return
        
        try:
            logging.info("Initialisiere WAGO Modbus-Verbindung...")
            
            # Verbindung herstellen
            if self.modbus_manager.connect():
                # Watchdog starten
                if self.modbus_manager.start_watchdog():
                    logging.info("WAGO Watchdog erfolgreich gestartet")
                else:
                    logging.warning("WAGO Watchdog konnte nicht gestartet werden")
                
                # Coil-Refresh starten
                if self.modbus_manager.start_coil_refresh():
                    logging.info("WAGO Coil-Refresh erfolgreich gestartet")
                else:
                    logging.warning("WAGO Coil-Refresh konnte nicht gestartet werden")
                
                # UI Status aktualisieren
                self.ui.update_modbus_status(True, self.modbus_manager.ip_address)
                
            else:
                logging.error("WAGO Modbus-Verbindung fehlgeschlagen")
                self.ui.update_modbus_status(False, self.modbus_manager.ip_address)
                
        except Exception as e:
            logging.error(f"Fehler bei WAGO Modbus-Initialisierung: {e}")
            self.ui.update_modbus_status(False, self.modbus_manager.ip_address)
    
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
        """Automatisches Laden von Modell und Kamera beim Start."""
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
                self.ui.show_status("Bereit - Alle Komponenten geladen", "ready")
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
        self.ui.login_btn.clicked.connect(self.toggle_login)
        self.ui.sidebar_toggle_btn.clicked.connect(self.toggle_sidebar)
        
        # BEENDEN Button verbinden
        self.ui.quit_btn.clicked.connect(self.quit_application)
    
    def toggle_login(self):
        """Login/Logout umschalten."""
        if self.user_manager.is_admin():
            # Logout
            self.user_manager.logout()
            self.ui.update_user_interface()
            self.ui.show_status("Abgemeldet - Gastmodus", "info")
        else:
            # Login versuchen
            if self.user_manager.login():
                self.ui.update_user_interface()
                self.ui.show_status("Angemeldet als Administrator", "success")
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
                    
                    # Prüfe ob Modbus-Einstellungen geändert wurden
                    modbus_changed = self.modbus_manager.update_settings(self.settings.data)
                    if modbus_changed:
                        logging.info("Modbus-Einstellungen geändert - Neuverbindung...")
                        self.initialize_modbus()
                    
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
                
                # Erkennungsstatistiken zurücksetzen (nur letzter Zyklus)
                self.last_cycle_detections = {}
                self.current_frame_detections = []
                
                # Robuste Bewegungserkennung initialisieren
                self.init_robust_motion_detection()
                
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
    
    def init_robust_motion_detection(self):
        """Robuste Bewegungserkennung initialisieren (Threshold weiterhin einstellbar)."""
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
        
        # Motion-Wert Tracking zurücksetzen
        self.motion_values = []
        self.current_motion_value = 0.0
        
        logging.info("Robuste Motion-Detection initialisiert - Threshold bleibt einstellbar")
    
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
        self.ui.show_status("Bereit", "ready")
        self.ui.update_workflow_status("READY")
        
        # 6. Workflow-Status zurücksetzen
        self.reset_workflow()
        self.bg_subtractor = None
        
        logging.info("Erkennung gestoppt")
    
    def process_frame(self):
        """Aktuelles Frame verarbeiten."""
        try:
            # Schneller Exit-Check
            if not self.running:
                return
                
            frame = self.camera_manager.get_frame()
            if frame is None:
                return
            
            # Helligkeitsüberwachung
            self.check_brightness(frame)
            
            # Motion-Wert berechnen und anzeigen (auch wenn kein Workflow läuft)
            self.update_motion_display(frame)
            
            # Industrieller Workflow verarbeiten
            self.process_industrial_workflow(frame)
            
            # KI-Erkennung nur während Aufnahme-Phase
            detections = []
            if self.detection_running and self.running:  # Doppel-Check für schnelles Beenden
                detections = self.detection_engine.detect(frame)
                self.current_frame_detections = detections
                
                # Erkennungen für aktuellen Zyklus sammeln
                self.update_cycle_statistics(detections)
            
            # Frame mit Erkennungen zeichnen
            annotated_frame = self.detection_engine.draw_detections(frame, detections)
            
            # UI aktualisieren (nur wenn noch running)
            if self.running:
                self.ui.update_video(annotated_frame)
                self.ui.update_last_cycle_stats(self.last_cycle_detections, self.current_frame_detections)
                
        except Exception as e:
            logging.error(f"Fehler bei Frame-Verarbeitung: {e}")
    
    def update_motion_display(self, frame):
        """Motion-Wert für Anzeige berechnen und UI aktualisieren."""
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
        # Basierend auf typischen Werten für 1280x720
        motion_value = min(255, motion_pixels / 100)  # Grober Normalisierungsansatz
        
        # Glättung über mehrere Frames für Anzeige
        self.motion_values.append(motion_value)
        if len(self.motion_values) > 10:  # Letzte 10 Frames
            self.motion_values.pop(0)
        
        # Geglätteter Motion-Wert für Anzeige
        self.current_motion_value = np.mean(self.motion_values)
        
        # UI aktualisieren
        self.ui.update_motion(self.current_motion_value)
    
    def process_industrial_workflow(self, frame):
        """Industrieller Workflow mit robuster Motion-Detection und MODBUS-Integration."""
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
    
    def update_cycle_statistics(self, detections):
        """Erkennungen für aktuellen Zyklus sammeln (NICHT Session-Summen!)."""
        for detection in detections:
            _, _, _, _, confidence, class_id = detection
            class_name = self.detection_engine.class_names.get(class_id, f"Class {class_id}")
            
            # Nur für aktuellen Zyklus (nicht Session-Gesamtstatistik)
            if class_name not in self.last_cycle_detections:
                self.last_cycle_detections[class_name] = {
                    'count': 0,
                    'max_confidence': 0.0,
                    'avg_confidence': 0.0,
                    'confidences': [],
                    'class_id': class_id
                }
            
            self.last_cycle_detections[class_name]['count'] += 1
            self.last_cycle_detections[class_name]['confidences'].append(confidence)
            self.last_cycle_detections[class_name]['max_confidence'] = max(
                self.last_cycle_detections[class_name]['max_confidence'], confidence
            )
            
            # Durchschnitt berechnen
            confidences = self.last_cycle_detections[class_name]['confidences']
            self.last_cycle_detections[class_name]['avg_confidence'] = sum(confidences) / len(confidences)
    
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
            count = stats.get('count', 0)
            
            # Prüfe: Klasse in bad_part_classes UND Anzahl >= red_threshold UND Konfidenz >= min_confidence
            if (class_id in bad_part_classes and 
                count >= red_threshold and 
                max_conf >= min_confidence):
                logging.info(f"Schlechtes Teil erkannt: {class_name} (Anzahl: {count}, Konfidenz: {max_conf:.2f})")
                return True
        
        # 2. PRIORITÄT: Prüfe auf gute Teile (Grüne Rahmen) - nur wenn keine schlechten Teile
        for class_name, stats in self.last_cycle_detections.items():
            class_id = stats.get('class_id', 0)
            count = stats.get('count', 0)
            
            # Prüfe: Klasse in good_part_classes UND Anzahl >= green_threshold
            if (class_id in good_part_classes and 
                count >= green_threshold):
                logging.info(f"Gutes Teil erkannt: {class_name} (Anzahl: {count})")
                return False  # Kein Abblasen erforderlich
        
        # 3. STANDARD: Weder schlechte noch gute Teile erfüllen Kriterien
        logging.info("Keine eindeutige Klassifizierung - Standard: Kein Abblasen")
        return False
    
    def check_brightness(self, frame):
        """Helligkeitsüberwachung."""
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
        
        if avg_brightness < low_threshold:
            if self.low_brightness_start is None:
                self.low_brightness_start = current_time
            elif current_time - self.low_brightness_start >= duration_threshold:
                self.ui.show_brightness_warning(f"Zu dunkel: {avg_brightness:.1f}")
        elif avg_brightness > high_threshold:
            self.ui.show_brightness_warning(f"Zu hell: {avg_brightness:.1f}")
        else:
            self.low_brightness_start = None
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