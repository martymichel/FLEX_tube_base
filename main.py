#!/usr/bin/env python3
"""
Einfache KI-Objekterkennungs-Anwendung
Neuaufbau mit sauberer Architektur und Grundfunktionen
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
    """Hauptanwendung für KI-Objekterkennung - einfach und sauber."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("KI-Objekterkennung - Einfach")
        self.setWindowState(Qt.WindowState.WindowFullScreen)
        
        # Komponenten initialisieren
        self.settings = Settings()
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
        
        # Timer für Frame-Updates
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.process_frame)
        
        logging.info("DetectionApp gestartet")
    
    def setup_connections(self):
        """Signale und Slots verbinden."""
        self.ui.start_btn.clicked.connect(self.toggle_detection)
        self.ui.model_btn.clicked.connect(self.load_model)
        self.ui.camera_btn.clicked.connect(self.select_camera)
        self.ui.settings_btn.clicked.connect(self.open_settings)
        self.ui.snapshot_btn.clicked.connect(self.take_snapshot)
    
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
                self.update_timer.start(30)  # ~30 FPS
                self.ui.start_btn.setText("⏹ Stoppen")
                self.ui.show_status("Erkennung läuft...", "success")
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
        logging.info("Erkennung gestoppt")
    
    def process_frame(self):
        """Aktuelles Frame verarbeiten."""
        try:
            frame = self.camera_manager.get_frame()
            if frame is None:
                return
                
            # KI-Erkennung durchführen
            detections = self.detection_engine.detect(frame)
            
            # Frame mit Erkennungen zeichnen
            annotated_frame = self.detection_engine.draw_detections(frame, detections)
            
            # UI aktualisieren
            self.ui.update_video(annotated_frame)
            self.ui.update_stats(detections)
            
            # Frame-Zähler
            self.frame_count += 1
            if self.frame_count % 30 == 0:  # Alle 30 Frames
                self.ui.update_frame_count(self.frame_count)
                
        except Exception as e:
            logging.error(f"Fehler bei Frame-Verarbeitung: {e}")
    
    def load_model(self):
        """KI-Modell laden."""
        model_path = self.ui.select_model_file()
        if model_path:
            if self.detection_engine.load_model(model_path):
                self.ui.show_status(f"Modell geladen: {os.path.basename(model_path)}", "success")
                self.settings.set('last_model', model_path)
            else:
                self.ui.show_status("Fehler beim Laden des Modells", "error")
    
    def select_camera(self):
        """Kamera/Video auswählen."""
        source = self.ui.select_camera_source()
        if source:
            if self.camera_manager.set_source(source):
                self.ui.show_status(f"Quelle ausgewählt: {source}", "success")
                self.settings.set('last_source', source)
            else:
                self.ui.show_status("Fehler bei Quellenauswahl", "error")
    
    def open_settings(self):
        """Einstellungen öffnen."""
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