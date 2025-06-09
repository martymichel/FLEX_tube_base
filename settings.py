"""
Einstellungs-Manager - einfach und zuverlässig Verwaltet alle Anwendungseinstellungen für industrllen Workflow mit Auto-Loading, Modbus und Bilderspeicherung
"""

import json
import logging
from pathlib import Path

class Settings:
    """
    Einfache Einstellungsverwaltung für Workflow mit Auto-Loading, Modbus und Bilderspeicherung.
    """

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

    def load_quietly(self):
        """Einstellungen aus Datei laden OHNE Logging (für regelmäßige Checks)."""
        try:
            if self.filename.exists():
                with open(self.filename, 'r', encoding='utf-8') as f:
                    self.data = json.load(f)
            else:
                self.data = self.get_defaults()
        except Exception as e:
            # Nur bei echten Fehlern loggen
            logging.error(f"Fehler beim stillen Laden der Einstellungen: {e}")
            self.data = self.get_defaults()

    def save(self):
        """Einstellungen in Datei speichern."""
        try:
            with open(self.filename, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
            logging.info("Einstellungen gespeichert settings.py -> def save(self)")
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
        """Standardeinstellungen für Workflow mit Auto-Loading, Modbus und Bilderspeicherung.
        
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
            'camera_config_path': '',            # Pfad zur IDS Peak Kamera-Konfigurationsdatei
            
            # Workflow - Zeiteinstellungen
            'motion_threshold': 110,      # Schwellwert für Bewegungserkennung
            'motion_decay_factor': 0.1,  # Abklingfaktor für Motion-Anzeige (0.1-0.99)
            'settling_time': 1.0,         # Ausschwingzeit nach Bewegung (Sekunden)
            'capture_time': 3.0,          # Aufnahme-/Erkennungszeit (Sekunden)
            'blow_off_time': 5.0,         # Wartezeit nach Abblasen (Sekunden)
            
            # Schlecht-Teil Erkennung
            'bad_part_classes': [1],      # Klassen-IDs die als "schlecht" gelten
            'bad_part_min_confidence': 0.5, # Mindest-Konfidenz für Schlecht-Teile
            
            # Gut-Teil Erkennung
            'good_part_classes': [0],     # Klassen-IDs die als "gut" gelten
            
            # Rahmen-Schwellenwerte
            'red_threshold': 1,           # Mindestanzahl für roten Rahmen (schlechte Teile)
            'green_threshold': 4,         # Mindestanzahl für grünen Rahmen (gute Teile)
            
            # Helligkeitsüberwachung
            'brightness_low_threshold': 30,      # Untere Helligkeitsschwelle
            'brightness_high_threshold': 220,    # Obere Helligkeitsschwelle
            'brightness_duration_threshold': 3.0, # Warndauer in Sekunden
            
            # MODBUS-Einstellungen (WAGO)
            'modbus_enabled': True,                       # Modbus aktiviert
            'modbus_ip': '192.168.1.100',                 # WAGO IP-Adresse
            'modbus_port': 502,                           # Modbus-TCP Port
            'watchdog_timeout_seconds': 5,                # Watchdog-Timeout in Sekunden
            'watchdog_interval_seconds': 2,               # Watchdog-Trigger-Intervall
            'reject_coil_address': 0,                     # Coil-Adresse für Ausschuss-Signal
            'detection_active_coil_address': 1,           # Coil-Adresse für Detection-Active
            'reject_coil_duration_seconds': 1.0,          # Dauer des Ausschuss-Signals
            
            # BILDERSPEICHERUNG-Einstellungen
            'save_bad_images': False,                     # Schlechtbilder speichern
            'save_good_images': False,                    # Gutbilder speichern
            'bad_images_directory': 'bad_images',         # Verzeichnis für Schlechtbilder
            'good_images_directory': 'good_images',       # Verzeichnis für Gutbilder
            'max_image_files': 100000,                    # Maximale Dateien pro Verzeichnis
            
            # PARQUET-LOGGING-Einstellungen
            'parquet_log_enabled': True,                  # Parquet-Logging aktiviert
            'parquet_log_directory': 'logs/detection_events',  # Verzeichnis für Parquet-Logs
            'parquet_log_max_files': 1000000,               # Maximale Anzahl Log-Dateien
            
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