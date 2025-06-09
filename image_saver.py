"""
Bild-Speicher-Manager - einfach und zuverlaessig
Speichert Gut- und Schlechtbilder mit Zeitstempel und Dateilimit
"""

import os
import cv2
import logging
from datetime import datetime
from pathlib import Path

class ImageSaver:
    """Einfacher Image-Saver fuer Gut- und Schlechtbilder."""
    
    def __init__(self, settings):
        self.settings = settings
        
        # Verzeichnisse aus Settings
        self.bad_images_dir = self.settings.get('bad_images_directory', 'bad_images')
        self.good_images_dir = self.settings.get('good_images_directory', 'good_images')
        
        # Speicher-Optionen
        self.save_bad_images = self.settings.get('save_bad_images', False)
        self.save_good_images = self.settings.get('save_good_images', False)
        self.max_images_per_dir = self.settings.get('max_image_files', 100000)
        
        # Verzeichnisse erstellen
        self._ensure_directories()
        
        logging.info(f"ImageSaver initialisiert - Bad: {self.save_bad_images}, Good: {self.save_good_images}")
    
    def _ensure_directories(self):
        """Stelle sicher, dass die Verzeichnisse existieren."""
        try:
            if self.save_bad_images and self.bad_images_dir:
                Path(self.bad_images_dir).mkdir(parents=True, exist_ok=True)
                logging.info(f"Schlechtbild-Verzeichnis: {self.bad_images_dir}")
            
            if self.save_good_images and self.good_images_dir:
                Path(self.good_images_dir).mkdir(parents=True, exist_ok=True)
                logging.info(f"Gutbild-Verzeichnis: {self.good_images_dir}")
                
        except Exception as e:
            logging.error(f"Fehler beim Erstellen der Verzeichnisse: {e}")
    
    def _count_images_in_directory(self, directory):
        """Zaehle Bilder in Verzeichnis."""
        try:
            if not os.path.exists(directory):
                return 0
            
            # Zaehle nur Bilddateien
            image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff'}
            count = 0
            
            for file in os.listdir(directory):
                if any(file.lower().endswith(ext) for ext in image_extensions):
                    count += 1
            
            return count
            
        except Exception as e:
            logging.error(f"Fehler beim Zaehlen der Bilder in {directory}: {e}")
            return 0
    
    def _generate_timestamp_filename(self, prefix, extension='.jpg'):
        """Erzeuge Dateiname mit Zeitstempel."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]  # Millisekunden
        return f"{prefix}_{timestamp}{extension}"
    
    def save_bad_image(self, frame, detection_summary=None):
        """Speichere Schlechtbild (ohne Bounding Boxes)."""
        if not self.save_bad_images or not self.bad_images_dir or frame is None:
            return None
        
        try:
            # Pruefe Dateilimit
            current_count = self._count_images_in_directory(self.bad_images_dir)
            if current_count >= self.max_images_per_dir:
                logging.warning(f"Schlechtbild-Verzeichnis voll ({current_count} Dateien) - speichere nicht")
                return "DIRECTORY_FULL"
            
            # Dateiname mit Zeitstempel generieren
            filename = self._generate_timestamp_filename("bad_part")
            filepath = os.path.join(self.bad_images_dir, filename)
            
            # Bild speichern (ohne Bounding Boxes)
            success = cv2.imwrite(filepath, frame)
            
            if success:
                logging.info(f"Schlechtbild gespeichert: {filename}")
                return filepath
            else:
                logging.error(f"Fehler beim Speichern des Schlechtbilds: {filename}")
                return None
                
        except Exception as e:
            logging.error(f"Fehler beim Speichern des Schlechtbilds: {e}")
            return None
    
    def save_good_image(self, frame, detection_summary=None):
        """Speichere Gutbild (ohne Bounding Boxes)."""
        if not self.save_good_images or not self.good_images_dir or frame is None:
            return None
        
        try:
            # Pruefe Dateilimit
            current_count = self._count_images_in_directory(self.good_images_dir)
            if current_count >= self.max_images_per_dir:
                logging.warning(f"Gutbild-Verzeichnis voll ({current_count} Dateien) - speichere nicht")
                return "DIRECTORY_FULL"
            
            # Dateiname mit Zeitstempel generieren
            filename = self._generate_timestamp_filename("good_part")
            filepath = os.path.join(self.good_images_dir, filename)
            
            # Bild speichern (ohne Bounding Boxes)
            success = cv2.imwrite(filepath, frame)
            
            if success:
                logging.info(f"Gutbild gespeichert: {filename}")
                return filepath
            else:
                logging.error(f"Fehler beim Speichern des Gutbilds: {filename}")
                return None
                
        except Exception as e:
            logging.error(f"Fehler beim Speichern des Gutbilds: {e}")
            return None
    
    def update_settings(self, new_settings):
        """Einstellungen aktualisieren."""
        old_bad_dir = self.bad_images_dir
        old_good_dir = self.good_images_dir
        
        # Neue Einstellungen laden
        self.bad_images_dir = new_settings.get('bad_images_directory', self.bad_images_dir)
        self.good_images_dir = new_settings.get('good_images_directory', self.good_images_dir)
        self.save_bad_images = new_settings.get('save_bad_images', self.save_bad_images)
        self.save_good_images = new_settings.get('save_good_images', self.save_good_images)
        self.max_images_per_dir = new_settings.get('max_image_files', self.max_images_per_dir)
        
        # Verzeichnisse neu erstellen wenn geaendert
        if (old_bad_dir != self.bad_images_dir or old_good_dir != self.good_images_dir):
            self._ensure_directories()
            logging.info("Bild-Verzeichnisse aktualisiert")
    
    def get_directory_stats(self):
        """Statistiken der Verzeichnisse."""
        stats = {}
        
        if self.save_bad_images and self.bad_images_dir:
            stats['bad_images'] = {
                'directory': self.bad_images_dir,
                'count': self._count_images_in_directory(self.bad_images_dir),
                'max': self.max_images_per_dir,
                'enabled': self.save_bad_images
            }
        
        if self.save_good_images and self.good_images_dir:
            stats['good_images'] = {
                'directory': self.good_images_dir,
                'count': self._count_images_in_directory(self.good_images_dir),
                'max': self.max_images_per_dir,
                'enabled': self.save_good_images
            }
        
        return stats