"""
Einstellungs-Manager - einfach und zuverlässig
Verwaltet alle Anwendungseinstellungen für industriellen Workflow mit Auto-Loading
"""

import json
import logging
from pathlib import Path

class Settings:
    """Einfache Einstellungsverwaltung für industriellen Workflow mit Auto-Loading."""
    
    def __init__(self, filename="settings.json"):
        self.filename = Path(filename)
        self.data = {}
        self.load()
    
    def load(self):
        """Einstellungen aus Datei laden."""
        try:
            if self.filename.exists():
                with open(self.filename, 'r', encoding='utf-8') as f:
                    self.data = json.load(f)
                logging.info(f"Einstellungen geladen: {len(self.data)} Einträge")
            else:
                logging.info("Keine Einstellungsdatei gefunden, verwende Standardwerte")
                self.data = self.get_defaults()
        except Exception as e:
            logging.error(f"Fehler beim Laden der Einstellungen: {e}")
            self.data = self.get_defaults()
    
    def save(self):
        """Einstellungen in Datei speichern."""
        try:
            with open(self.filename, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
            logging.info("Einstellungen gespeichert")
        except Exception as e:
            logging.error(f"Fehler beim Speichern der Einstellungen: {e}")
    
    def get(self, key, default=None):
        """Einstellungswert abrufen.
        
        Args:
            key (str): Schlüssel
            default: Standardwert falls nicht vorhanden
            
        Returns:
            Wert oder Standardwert
        """
        return self.data.get(key, default)
    
    def set(self, key, value):
        """Einstellungswert setzen.
        
        Args:
            key (str): Schlüssel
            value: Wert
        """
        self.data[key] = value
        logging.debug(f"Einstellung gesetzt: {key} = {value}")
    
    def get_defaults(self):
        """Standardeinstellungen für industriellen Workflow mit Auto-Loading.
        
        Returns:
            dict: Standardeinstellungen
        """
        return {
            # KI-Einstellungen
            'confidence_threshold': 0.5,
            'last_model': '',                    # Auto-Loading: Letztes Modell
            
            # Kamera-Einstellungen  
            'last_source': None,                 # Auto-Loading: Letzte Kamera/Video
            'last_mode_was_video': False,        # Auto-Loading: War es Video oder Kamera?
            'video_width': 1280,
            'video_height': 720,
            
            # Industrieller Workflow - Zeiteinstellungen
            'motion_threshold': 110,      # Schwellwert für Bewegungserkennung
            'settling_time': 1.0,         # Ausschwingzeit nach Bewegung (Sekunden)
            'capture_time': 3.0,          # Aufnahme-/Erkennungszeit (Sekunden)
            'blow_off_time': 5.0,         # Wartezeit nach Abblasen (Sekunden)
            
            # Schlecht-Teil Erkennung
            'bad_part_classes': [1],      # Klassen-IDs die als "schlecht" gelten
            'bad_part_min_confidence': 0.5, # Mindest-Konfidenz für Schlecht-Teile
            
            # Helligkeitsüberwachung
            'brightness_low_threshold': 30,      # Untere Helligkeitsschwelle
            'brightness_high_threshold': 220,    # Obere Helligkeitsschwelle
            'brightness_duration_threshold': 3.0, # Warndauer in Sekunden
            
            # UI-Einstellungen
            'sidebar_width': 350,
            'show_confidence': True,
            'show_class_names': True,
            
            # Sonstige
            'auto_save_snapshots': False,
            'log_level': 'INFO'
        }
    
    def update(self, new_settings):
        """Mehrere Einstellungen auf einmal aktualisieren.
        
        Args:
            new_settings (dict): Neue Einstellungen
        """
        self.data.update(new_settings)
        logging.info(f"{len(new_settings)} Einstellungen aktualisiert")
    
    def reset_to_defaults(self):
        """Alle Einstellungen auf Standardwerte zurücksetzen."""
        self.data = self.get_defaults()
        logging.info("Einstellungen auf Standardwerte zurückgesetzt")