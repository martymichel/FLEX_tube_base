#!/usr/bin/env python3
"""
Einfache KI-Objekterkennungs-Anwendung - Erweitert
Neuaufbau mit sauberer Architektur und erweiterten Grundfunktionen
"""

import sys
import os
import logging
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont

# Eigene Module
from detection_engine import DetectionEngine
from camera_manager import CameraManager  
from settings import Settings
from ui_components import MainUI
from user_manager import UserManager

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
    """Hauptanwendung für KI-Objekterkennung - einfach aber vollständig."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("KI-Objekterkennung - Erweitert")
        self.setWindowState(Qt.WindowState.WindowFullScreen)
        
        # Komponenten initialisieren
        self.settings = Settings()
        self.user_manager = UserManager()
        self.camera_manager = CameraManager()
        self.detection_engine = DetectionEngine()
        
        # UI aufbauen
        self.ui = MainUI(self)
        self.setCentralWidget(self.ui)
        
        # Verbindungen herstellen
        self.setup_connections()
        
        # Status
        self.running = False
        self.frame_count = 0
        self.motion_detected = False
        self.settling_start_time = None
        self.capture_start_time = None
        self.clearing_start_time = None
        self.detection_state = "idle"  # idle, settling, capturing, clearing
        
        # Timer für Frame-Updates
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.process_frame)
        
        # Timer für Zustandsübergänge
        self.state_timer = QTimer()
        self.state_timer.timeout.connect(self.check_state_transitions)
        self.state_timer.start(100)  # Alle 100ms prüfen
        
        # Bewegungserkennung
        self.bg_subtractor = None
        self.last_frame = None
        
        # Helligkeitsüberwachung
        self.brightness_values = []
        self.low_brightness_start = None
        
        # Einstellungen überwachen
        self.last_settings_update = 0
        self.settings_timer = QTimer()
        self.settings_timer.timeout.connect(self.check_settings_changes)
        self.settings_timer.start(2000)  # Alle 2 Sekunden prüfen
        
        logging.info("DetectionApp gestartet - Erweiterte Version")
    
    def setup_connections(self):
        """Signale und Slots verbinden."""
        self.ui.start_btn.clicked.connect(self.toggle_detection)
        self.ui.model_btn.clicked.connect(self.load_model)
        self.ui.camera_btn.clicked.connect(self.select_camera)
        self.ui.settings_btn.clicked.connect(self.open_settings)
        self.ui.snapshot_btn.clicked.connect(self.take_snapshot)
        self.ui.login_btn.clicked.connect(self.toggle_login)
        self.ui.sidebar_toggle_btn.clicked.connect(self.toggle_sidebar)
    
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
                    self.settings.load()
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
                self.detection_state = "idle"
                
                # Bewegungserkennung initialisieren
                import cv2
                self.bg_subtractor = cv2.createBackgroundSubtractorMOG2(
                    detectShadows=False,
                    varThreshold=self.settings.get('motion_threshold', 110)
                )
                
                self.update_timer.start(30)  # ~30 FPS
                self.ui.start_btn.setText("⏹ Stoppen")
                self.ui.show_status("Erkennung läuft - Warte auf Bewegung...", "success")
                logging.info("Erkennung gestartet")
            else:
                self.ui.show_status("Fehler beim Starten der Kamera", "error")
                
        except Exception as e:
            logging.error(f"Fehler beim Starten: {e}")
            self.ui.show_status(f"Fehler: {e}", "error")
    
    def stop_detection(self):
        """Erkennung stoppen."""
        self.running = False
        self.update_timer.stop()
        self.camera_manager.stop()
        self.ui.start_btn.setText("▶ Starten")
        self.ui.show_status("Bereit", "ready")
        self.detection_state = "idle"
        self.bg_subtractor = None
        logging.info("Erkennung gestoppt")
    
    def process_frame(self):
        """Aktuelles Frame verarbeiten."""
        try:
            frame = self.camera_manager.get_frame()
            if frame is None:
                return
            
            # Helligkeitsüberwachung
            self.check_brightness(frame)
            
            # Bewegungserkennung
            motion_detected = self.detect_motion(frame)
            
            # Zustandsmaschine für Bewegungserkennung
            current_time = self.camera_manager.get_current_time()
            
            if self.detection_state == "idle" and motion_detected:
                # Bewegung erkannt - Ausschwingzeit starten
                self.detection_state = "settling"
                self.settling_start_time = current_time
                self.ui.show_status("Bewegung erkannt - Ausschwingzeit...", "warning")
            
            # KI-Erkennung nur während Capture-Phase
            detections = []
            if self.detection_state == "capturing":
                detections = self.detection_engine.detect(frame)
            
            # Frame mit Erkennungen zeichnen
            annotated_frame = self.detection_engine.draw_detections(frame, detections)
            
            # Zustandsinfo auf Frame zeichnen
            self.draw_state_info(annotated_frame)
            
            # UI aktualisieren
            self.ui.update_video(annotated_frame)
            self.ui.update_stats(detections)
            
            # Frame-Zähler
            self.frame_count += 1
            if self.frame_count % 30 == 0:  # Alle 30 Frames
                self.ui.update_frame_count(self.frame_count)
                
        except Exception as e:
            logging.error(f"Fehler bei Frame-Verarbeitung: {e}")
    
    def detect_motion(self, frame):
        """Bewegungserkennung durchführen."""
        if self.bg_subtractor is None:
            return False
        
        import cv2
        import numpy as np
        
        # Grayscale für Bewegungserkennung
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Background Subtraction
        fg_mask = self.bg_subtractor.apply(gray)
        
        # Rauschen reduzieren
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_OPEN, kernel)
        
        # Bewegung detektieren
        motion_pixels = cv2.countNonZero(fg_mask)
        motion_threshold = self.settings.get('motion_threshold', 110) * 100  # Schwellwert anpassen
        
        return motion_pixels > motion_threshold
    
    def check_state_transitions(self):
        """Prüfe Zustandsübergänge der Bewegungserkennung."""
        if not self.running:
            return
            
        current_time = self.camera_manager.get_current_time()
        settling_time = self.settings.get('settling_time', 1.0)
        capture_time = self.settings.get('capture_time', 3.0)
        clearing_time = self.settings.get('clearing_time', 3.0)
        
        if self.detection_state == "settling" and self.settling_start_time:
            if current_time - self.settling_start_time >= settling_time:
                # Ausschwingzeit vorbei - Aufnahme starten
                self.detection_state = "capturing"
                self.capture_start_time = current_time
                self.ui.show_status("Aufnahme läuft - KI-Erkennung aktiv", "success")
        
        elif self.detection_state == "capturing" and self.capture_start_time:
            if current_time - self.capture_start_time >= capture_time:
                # Aufnahme beendet - Clearing starten
                self.detection_state = "clearing"
                self.clearing_start_time = current_time
                self.ui.show_status("Auswertung beendet - Wartezeit...", "info")
        
        elif self.detection_state == "clearing" and self.clearing_start_time:
            if current_time - self.clearing_start_time >= clearing_time:
                # Clearing beendet - zurück zu idle
                self.detection_state = "idle"
                self.ui.show_status("Bereit für nächste Bewegung", "ready")
    
    def check_brightness(self, frame):
        """Helligkeitsüberwachung."""
        import cv2
        import numpy as np
        
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
        
        current_time = self.camera_manager.get_current_time()
        
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
    
    def draw_state_info(self, frame):
        """Zustandsinfo auf Frame zeichnen."""
        import cv2
        
        state_text = f"Status: {self.detection_state.upper()}"
        cv2.putText(frame, state_text, (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
    
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
                self.settings.set('last_source', source)
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
        """Anwendung schließen."""
        self.stop_detection()
        self.settings.save()
        event.accept()

def main():
    """Hauptfunktion."""
    app = QApplication(sys.argv)
    app.setApplicationName("KI-Objekterkennung")
    
    # Moderne Schriftart
    app.setFont(QFont("Segoe UI", 10))
    
    # Hauptfenster erstellen und anzeigen
    window = DetectionApp()
    window.show()
    
    # Event-Loop starten
    sys.exit(app.exec())

if __name__ == "__main__":
    main()