"""
Einstellungs-Manager - einfach und zuverlässig
Verwaltet alle Anwendungseinstellungen
"""

import json
import logging
from pathlib import Path

class Settings:
    """Einfache Einstellungsverwaltung."""
    
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
        """Standardeinstellungen zurückgeben.
        
        Returns:
            dict: Standardeinstellungen
        """
        return {
            # KI-Einstellungen
            'confidence_threshold': 0.5,
            'last_model': '',
            
            # Kamera-Einstellungen  
            'last_source': 0,
            'video_width': 1280,
            'video_height': 720,
            
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