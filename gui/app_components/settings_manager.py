"""Einstellungsmanager-Modul für die Anwendung - KORRIGIERT für stabilere Speicherung."""

import json
import logging
import os
import traceback
from pathlib import Path
import threading
import shutil
import time
import uuid  # Für eindeutige temporäre Dateinamen

# Bedingter Import für PyQt-Klassen
try:
    from PyQt6.QtCore import QObject, pyqtSignal
    PYQT_AVAILABLE = True
except ImportError:
    PYQT_AVAILABLE = False
    QObject = type('QObject', (), {})  # Dummy-Klasse, wenn PyQt nicht verfügbar ist

class SettingsManager:
    """
    Verwaltet Anwendungseinstellungen mit verbesserter Persistierung.
    KORRIGIERT: Robustere und fehlertolerante Speicherung aller Einstellungen.
    """
    
    def __init__(self, settings_file="detection_settings.json"):
        """Initialisieren des Settings Managers."""
        self.settings_file = settings_file
        self.settings = {}
        
        # Thread-Lock für sichere Zugriffe
        self._lock = threading.Lock()
        
        # Zeitstempel der letzten Änderung
        self._last_modified_time = 0
        
        # Thread für zyklisches Laden
        self._reload_thread = None
        self._reload_running = False
        
        # Callback für Einstellungsänderungen
        self._settings_changed_callback = None
        
        # Lade Einstellungen beim Start
        self._load_settings_internal()
        
        # Logging für Initialisierung
        logging.info(f"SettingsManager initialized with file: {self.settings_file}")
        logging.info(f"Loaded {len(self.settings)} settings")
        
        # Erstelle Backup-Verzeichnis
        self._ensure_backup_directory()
        
    def _ensure_backup_directory(self):
        """Stelle sicher, dass das Backup-Verzeichnis existiert."""
        try:
            backup_dir = os.path.join(os.path.dirname(os.path.abspath(self.settings_file)), "settings_backup")
            if not os.path.exists(backup_dir):
                os.makedirs(backup_dir, exist_ok=True)
                logging.info(f"Created backup directory: {backup_dir}")
        except Exception as e:
            logging.warning(f"Could not create backup directory: {e}")
    
    def _load_settings_internal(self):
        """
        Interne Methode zum Laden der Einstellungen aus JSON-Datei.
        
        Returns:
            dict: Die geladenen Einstellungen oder ein leeres Dictionary bei Fehler
        """
        try:
            if os.path.exists(self.settings_file):
                # Aktuellen Zeitstempel speichern
                self._last_modified_time = os.path.getmtime(self.settings_file)
                logging.debug(f"Datei-Zeitstempel: {self._last_modified_time}")
                
                # Verbesserte Fehlerbehandlung beim Datei-Lesen
                try:
                    with open(self.settings_file, 'r', encoding='utf-8') as f:
                        file_content = f.read().strip()
                        
                    # Prüfe, ob die Datei leer ist
                    if not file_content:
                        logging.warning(f"Settings file {self.settings_file} is empty, using default settings")
                        self.settings = self._get_default_settings()
                        return
                        
                    # Versuche die JSON-Daten zu laden
                    data = json.loads(file_content)
                    
                    # Handle if settings are wrapped in an array
                    if isinstance(data, list) and len(data) > 0:
                        self.settings = data[0]
                    else:
                        self.settings = data
                    
                    logging.info(f"Successfully loaded {len(self.settings)} settings from {self.settings_file}")
                    
                    # Validiere geladene Einstellungen
                    self._validate_loaded_settings()
                    
                except json.JSONDecodeError as json_err:
                    logging.error(f"JSON parse error in settings file: {json_err}")
                    logging.error(f"File content start: {file_content[:100]}...")
                    
                    # Versuche Backup zu laden
                    if self._try_load_backup():
                        logging.info("Successfully loaded settings from backup after JSON error")
                    else:
                        logging.warning("Using default settings due to JSON parse failure")
                        self.settings = self._get_default_settings()
                    
            else:
                logging.info(f"Settings file {self.settings_file} does not exist, starting with default settings")
                self.settings = self._get_default_settings()
                
        except Exception as e:
            logging.error(f"Failed to load settings from {self.settings_file}: {e}")
            logging.error(traceback.format_exc())
            
            # Versuche Backup zu laden
            if self._try_load_backup():
                logging.info("Successfully loaded settings from backup")
            else:
                logging.warning("Using default settings due to load failure")
                self.settings = self._get_default_settings()
    
    def _validate_loaded_settings(self):
        """Validiere die geladenen Einstellungen und setze fehlende Defaults."""
        defaults = self._get_default_settings()
        
        # Füge fehlende Einstellungen hinzu
        for key, default_value in defaults.items():
            if key not in self.settings:
                self.settings[key] = default_value
                logging.info(f"Added missing setting: {key} = {default_value}")
    
    def _get_default_settings(self):
        """Gibt Standard-Einstellungen zurück."""
        return {
            # Motion settings
            'motion_threshold': 110,
            'settling_time': 1.0,
            'capture_time': 3.0,
            'frame_duration': 1.0,
            'clearing_time': 3.0,
            'iou_threshold': 0.45,
            
            # Visual settings
            'font_size': 0.7,
            'line_thickness': 2,
            'text_thickness': 1,
            'show_labels': True,
            
            # Session settings
            'session_timeout_minutes': 3,
            'default_model_directory': '',
            
            # File settings
            'save_bad_images': False,
            'save_good_images': False,
            'bad_images_directory': '',
            'parquet_directory': '',
            'max_image_files': 10000,
            
            # Brightness settings
            'brightness_low_threshold': 30,
            'brightness_high_threshold': 220,
            'brightness_duration_threshold': 3.0,
            
            # Class settings
            'green_threshold': 4,
            'red_threshold': 1,
            'class_thresholds': {},
            'frame_assignments': {},
            'class_colors': {},
            
            # Other settings
            'overlay_duration': 5.0,
            'camera_config_path': '',
            'manual_stop': False,
            'last_video_path': '',
            'last_camera_id': 0,
            'last_mode_was_video': False
        }
    
    def _try_load_backup(self):
        """Versuche ein Backup zu laden."""
        try:
            backup_dir = os.path.join(os.path.dirname(os.path.abspath(self.settings_file)), "settings_backup")
            if not os.path.exists(backup_dir):
                return False
            
            # Finde das neueste Backup
            backup_files = [f for f in os.listdir(backup_dir) if f.startswith('settings_') and f.endswith('.json')]
            if not backup_files:
                return False
            
            backup_files.sort(reverse=True)  # Neuestes zuerst
            backup_path = os.path.join(backup_dir, backup_files[0])
            
            # Verbesserte Fehlerbehandlung beim Backup-Lesen
            try:
                with open(backup_path, 'r', encoding='utf-8') as f:
                    file_content = f.read().strip()
                    
                # Prüfe, ob die Datei leer ist
                if not file_content:
                    logging.warning(f"Backup file {backup_path} is empty")
                    return False
                    
                # Versuche die JSON-Daten zu laden
                data = json.loads(file_content)
                
                if isinstance(data, list) and len(data) > 0:
                    self.settings = data[0]
                else:
                    self.settings = data
                    
                logging.info(f"Loaded settings from backup: {backup_path}")
                return True
                
            except json.JSONDecodeError as json_err:
                logging.error(f"JSON parse error in backup file: {json_err}")
                return False
                
        except Exception as e:
            logging.error(f"Failed to load backup: {e}")
            return False
    
    def load_settings(self):
        """
        Öffentliche Methode zum Laden der Einstellungen.
        
        Returns:
            dict: Die geladenen Einstellungen
        """
        with self._lock:
            self._load_settings_internal()
            return self.settings.copy()
    
    def save_settings(self, force_backup=True):
        """
        Speichere Einstellungen in JSON-Datei mit verbesserter Fehlerbehandlung.
        
        Args:
            force_backup (bool): Erstelle automatisch ein Backup
        """
        with self._lock:
            try:
                logging.info("Starting save_settings() method")
                
                # TEMPORÄRE ÄNDERUNG FÜR TESTING: Deaktiviere _sanitize_settings
                # Um zu testen, ob die _sanitize_settings-Methode den Absturz verursacht
                logging.info("TESTING MODE: Skipping _sanitize_settings method")
                
                # Direkte Verwendung der Einstellungen ohne Sanitization
                settings_to_save = self.settings
                logging.info(f"Settings to save type: {type(settings_to_save)}")
                logging.info(f"Settings to save count: {len(settings_to_save)}")
                
                # ORIGINAL CODE (kommentiert für Testing):
                # # Sanitize settings to ensure they're serializable
                # sanitized_settings = self._sanitize_settings(self.settings)
                # settings_to_save = sanitized_settings
                
                # Erstelle Backup der aktuellen Datei, falls sie existiert
                if force_backup and os.path.exists(self.settings_file):
                    logging.info("Creating backup before save")
                    self._create_backup()
                
                # Verzeichnis erstellen, falls es nicht existiert
                settings_dir = os.path.dirname(os.path.abspath(self.settings_file))
                if settings_dir and not os.path.exists(settings_dir):
                    os.makedirs(settings_dir, exist_ok=True)
                    logging.info(f"Created settings directory: {settings_dir}")
                
                # Erstelle eine eindeutige temporäre Datei mit UUID
                unique_id = uuid.uuid4().hex
                temp_file = f"{self.settings_file}.{unique_id}.tmp"
                logging.info(f"Using temporary file: {temp_file}")
                
                # Sichere die Einstellungen zuerst in einer temporären Datei
                logging.info("Writing to temporary file")
                with open(temp_file, 'w', encoding='utf-8') as f:
                    json.dump(settings_to_save, f, indent=4, ensure_ascii=False)
                logging.info("Successfully wrote to temporary file")
                
                # Verifiziere die temporäre Datei
                logging.info("Verifying temporary file")
                try:
                    with open(temp_file, 'r', encoding='utf-8') as f:
                        file_content = f.read().strip()
                        
                    # Prüfe ob die Datei leer ist
                    if not file_content:
                        raise ValueError("Temporary file is empty")
                        
                    # Versuche die JSON-Daten zu laden
                    verification_data = json.loads(file_content)
                    
                    # Überprüfe ob die Daten überhaupt geladen werden konnten
                    if not verification_data:
                        raise ValueError("Verification returned empty data")
                        
                except json.JSONDecodeError as json_err:
                    raise ValueError(f"JSON error in temporary file: {json_err}")
                    
                except Exception as verify_error:
                    raise ValueError(f"Failed to verify temporary file: {verify_error}")
                
                logging.info("Temporary file verification successful")
                
                # Verwende os.replace für atomares Ersetzen der Datei
                # Diese Operation ist atomar und vermeidet das Zeitfenster-Problem
                logging.info("Replacing original file with temporary file")
                os.replace(temp_file, self.settings_file)
                
                logging.info(f"Successfully saved {len(settings_to_save)} settings to {self.settings_file} using atomic replace")
                
                # Verifiziere, dass die Datei tatsächlich geschrieben wurde
                if not os.path.exists(self.settings_file):
                    raise FileNotFoundError("Settings file doesn't exist after saving")
                
                file_size = os.path.getsize(self.settings_file)
                if file_size < 10:  # Eine Minimalgröße überprüfen
                    raise ValueError(f"Settings file too small after save: {file_size} bytes")
                
                # Aktualisiere den Zeitstempel nach erfolgreicher Speicherung
                self._last_modified_time = os.path.getmtime(self.settings_file)
                
                logging.info("save_settings() completed successfully")
                
            except Exception as e:
                logging.error(f"Failed to save settings to {self.settings_file}: {e}")
                logging.error(traceback.format_exc())
                
                # Bereinige temporäre Dateien
                try:
                    # Lösche alle potentiellen temporären Dateien
                    settings_dir = os.path.dirname(os.path.abspath(self.settings_file))
                    for temp_file in [f for f in os.listdir(settings_dir) if f.startswith(os.path.basename(self.settings_file)) and f.endswith('.tmp')]:
                        os.remove(os.path.join(settings_dir, temp_file))
                except Exception:
                    pass
                
                # Propagiere den Fehler nach oben, damit der Aufrufer weiß, dass etwas schiefgegangen ist
                raise
    
    def _sanitize_settings(self, settings_dict):
        """
        Sanitize settings to ensure they're JSON-serializable.
        
        Args:
            settings_dict (dict): Original settings dictionary
            
        Returns:
            dict: Sanitized settings dictionary
        """
        if settings_dict is None:
            logging.warning("Received None settings in _sanitize_settings, returning empty dict")
            return {}
            
        sanitized = {}
        
        # Process each setting to ensure JSON serialization compatibility
        for key, value in settings_dict.items():
            try:
                # Handle dictionaries recursively
                if isinstance(value, dict):
                    sanitized[key] = self._sanitize_settings(value)
                # Handle None values explicitly
                elif value is None:
                    sanitized[key] = None
                # Handle simple JSON-serializable types directly
                elif isinstance(value, (int, float, bool, str)):
                    sanitized[key] = value
                # Safely handle PyQt objects
                elif PYQT_AVAILABLE and isinstance(value, QObject):
                    # Convert QObject to a safe string representation
                    class_name = value.__class__.__name__
                    sanitized[key] = f"<PyQtObject:{class_name}>"
                    logging.warning(f"Found QObject in settings ({key}): {class_name} - converting to string")
                # Handle lists recursively
                elif isinstance(value, (list, tuple)):
                    sanitized_list = []
                    for item in value:
                        if isinstance(item, dict):
                            sanitized_list.append(self._sanitize_settings(item))
                        elif isinstance(item, (int, float, bool, str, type(None))):
                            sanitized_list.append(item)
                        elif PYQT_AVAILABLE and isinstance(item, QObject):
                            # Handle PyQt objects in lists
                            class_name = item.__class__.__name__
                            sanitized_list.append(f"<PyQtObject:{class_name}>")
                        else:
                            # Try simple string conversion for other types
                            try:
                                sanitized_list.append(str(item))
                            except Exception:
                                sanitized_list.append("<non-serializable-value>")
                    
                    sanitized[key] = sanitized_list
                else:
                    # For all other types, try string conversion
                    try:
                        sanitized[key] = str(value)
                    except Exception as str_error:
                        logging.warning(f"Cannot convert setting {key} to string: {str_error}")
                        sanitized[key] = "<non-serializable-value>"
            except Exception as e:
                # Catch any other exceptions during processing of this key
                logging.warning(f"Error processing setting {key}: {e}")
                sanitized[key] = "<error-during-processing>"
        
        return sanitized
    
    def _create_backup(self):
        """Erstelle ein Backup der aktuellen Einstellungsdatei."""
        try:
            import datetime
            backup_dir = os.path.join(os.path.dirname(os.path.abspath(self.settings_file)), "settings_backup")
            if not os.path.exists(backup_dir):
                os.makedirs(backup_dir, exist_ok=True)
            
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = os.path.join(backup_dir, f"settings_{timestamp}.json")
            
            # Verwende explizite Kopie statt Umbenennung
            shutil.copy2(self.settings_file, backup_file)
            logging.debug(f"Created settings backup: {backup_file}")
            
            # Bereinige alte Backups (behalte nur die letzten 10)
            self._cleanup_old_backups(backup_dir)
            
        except Exception as e:
            logging.warning(f"Could not create settings backup: {e}")
    
    def _cleanup_old_backups(self, backup_dir, keep_count=10):
        """Bereinige alte Backup-Dateien."""
        try:
            backup_files = [f for f in os.listdir(backup_dir) if f.startswith('settings_') and f.endswith('.json')]
            if len(backup_files) > keep_count:
                backup_files.sort()  # Älteste zuerst
                files_to_remove = backup_files[:-keep_count]
                
                for file_to_remove in files_to_remove:
                    file_path = os.path.join(backup_dir, file_to_remove)
                    os.remove(file_path)
                    logging.debug(f"Removed old backup: {file_to_remove}")
                    
        except Exception as e:
            logging.warning(f"Could not cleanup old backups: {e}")
    
    def update(self, new_settings):
        """
        Aktualisiere Einstellungen mit neuen Werten und speichere sofort.
        
        Args:
            new_settings (dict): Neue Einstellungswerte
        """
        if new_settings is None:
            logging.error("Attempted to update settings with None value")
            return
            
        if not isinstance(new_settings, dict):
            logging.error(f"update() called with non-dict: {type(new_settings)}")
            raise ValueError("new_settings must be a dictionary")
        
        with self._lock:
            try:
                logging.info(f"Starting update() with {len(new_settings)} new settings")
                
                # Log welche Einstellungen geändert werden
                changes = []
                for key, new_value in new_settings.items():
                    old_value = self.settings.get(key, "NOT_SET")
                    if old_value != new_value:
                        changes.append(f"{key}: {old_value} -> {new_value}")
                
                if changes:
                    logging.info(f"Updating {len(changes)} settings:")
                    for i, change in enumerate(changes):
                        if i < 10:  # Log first 10 changes to avoid spam
                            logging.debug(f"  {change}")
                    if len(changes) > 10:
                        logging.debug(f"  ... and {len(changes) - 10} more changes")
                
                # Update settings - Store backup first
                old_settings = self.settings.copy()
                logging.info("Stored backup of old settings")
                
                self.settings.update(new_settings)
                logging.info("Updated settings dictionary")
                
                # Sofort speichern nach Update
                try:
                    logging.info("Starting save_settings() call")
                    self.save_settings()
                    logging.info("Settings updated and saved successfully")
                except Exception as e:
                    # Rollback bei Speicherfehler
                    logging.error(f"Settings save failed, rolling back: {e}")
                    self.settings = old_settings
                    logging.error("Rollback completed")
                    raise
                    
            except Exception as e:
                logging.error(f"Error in update() method: {e}")
                logging.error(traceback.format_exc())
                raise
    
    def get(self, key, default=None):
        """
        Hole einen Einstellungswert.
        
        Args:
            key (str): Schlüssel der Einstellung
            default: Standardwert, falls Schlüssel nicht existiert
            
        Returns:
            Der Wert der Einstellung oder der Standardwert
        """
        with self._lock:
            return self.settings.get(key, default)
    
    def set(self, key, value):
        """
        Setze einen Einstellungswert ohne sofortiges Speichern.
        
        Args:
            key (str): Schlüssel der Einstellung
            value: Neuer Wert für die Einstellung
        """
        with self._lock:
            old_value = self.settings.get(key, "NOT_SET")
            self.settings[key] = value
            logging.debug(f"set({key}): {old_value} -> {value}")
    
    def set_and_save(self, key, value):
        """
        Setze einen Einstellungswert und speichere sofort.
        
        Args:
            key (str): Schlüssel der Einstellung
            value: Neuer Wert für die Einstellung
        """
        with self._lock:
            old_value = self.settings.get(key, "NOT_SET")
            self.settings[key] = value
            logging.debug(f"set_and_save({key}): {old_value} -> {value}")
            
            try:
                self.save_settings()
            except Exception as e:
                # Rollback bei Fehler
                if old_value != "NOT_SET":
                    self.settings[key] = old_value
                else:
                    del self.settings[key]
                raise
    
    def get_default_model_directory(self):
        """
        Hole den Pfad zum Standard-Modellverzeichnis.
        
        Returns:
            str: Pfad zum Standard-Modellverzeichnis oder leerer String
        """
        return self.get('default_model_directory', '')
    
    def get_default_model(self):
        """
        Hole die erste .pt-Datei aus dem Standard-Modellverzeichnis.
        
        Returns:
            str: Vollständiger Pfad zur gefundenen Modelldatei oder None
        """
        default_dir = self.get_default_model_directory()
        if not default_dir or not os.path.exists(default_dir):
            return None
            
        # Suche nach .pt-Dateien im Verzeichnis
        for file in os.listdir(default_dir):
            if file.endswith('.pt'):
                model_path = os.path.join(default_dir, file)
                if os.path.exists(model_path) and os.path.isfile(model_path):
                    return model_path
        return None
        
    # ----- Neue Methoden für zyklisches Auslesen -----
    
    def register_settings_changed_callback(self, callback_func):
        """
        Registriere eine Callback-Funktion, die aufgerufen wird, 
        wenn sich Einstellungen geändert haben.
        
        Args:
            callback_func (callable): Funktion, die aufgerufen wird, wenn sich 
                                     Einstellungen ändern. Die Funktion erhält 
                                     die aktuellen Einstellungen als Parameter.
        """
        self._settings_changed_callback = callback_func
        logging.info(f"Settings change callback registered: {callback_func.__qualname__ if hasattr(callback_func, '__qualname__') else callback_func}")
    
    def start_cyclic_reload(self, interval_seconds=5):
        """
        Starte zyklisches Auslesen der Einstellungsdatei.
        
        Args:
            interval_seconds (int): Intervall in Sekunden für die Überprüfung auf Änderungen
        """
        with self._lock:
            if self._reload_thread and self._reload_thread.is_alive():
                logging.info("Cyclic reload already running")
                return
                
            self._reload_running = True
            self._reload_thread = threading.Thread(
                target=self._reload_thread_func,
                args=(interval_seconds,),
                daemon=True,
                name="SettingsReloadThread"
            )
            self._reload_thread.start()
            logging.info(f"Started cyclic settings reload every {interval_seconds} seconds")
    
    def stop_cyclic_reload(self):
        """
        Stoppe das zyklische Auslesen der Einstellungsdatei.
        """
        with self._lock:
            self._reload_running = False
            if self._reload_thread and self._reload_thread.is_alive():
                logging.info("Stopping cyclic settings reload thread")
                # Thread wird durch Flag _reload_running beendet
                self._reload_thread.join(timeout=2.0)
                if self._reload_thread.is_alive():
                    logging.warning("Settings reload thread did not terminate cleanly")
                else:
                    logging.info("Settings reload thread terminated")
            self._reload_thread = None
    
    def _reload_thread_func(self, interval_seconds):
        """
        Thread-Funktion für zyklisches Auslesen.
        
        Args:
            interval_seconds (int): Intervall in Sekunden
        """
        try:
            logging.info(f"Settings reload thread started with {interval_seconds}s interval")
            
            while self._reload_running:
                try:
                    self._check_for_changes_and_reload()
                except Exception as e:
                    logging.error(f"Error in settings reload cycle: {e}")
                
                # Warte auf nächsten Zyklus oder Beendigung
                for _ in range(int(interval_seconds * 10)):  # 10 checks per second for responsive shutdown
                    if not self._reload_running:
                        break
                    time.sleep(0.1)
                    
        except Exception as e:
            logging.error(f"Unexpected error in settings reload thread: {e}")
            logging.error(traceback.format_exc())
        finally:
            logging.info("Settings reload thread exiting")
    
    def _check_for_changes_and_reload(self):
        """
        Überprüfe ob die Einstellungsdatei geändert wurde und lade sie bei Bedarf neu.
        """
        try:
            if not os.path.exists(self.settings_file):
                return
                
            # Aktuelle Änderungszeit der Datei holen
            current_mtime = os.path.getmtime(self.settings_file)
            
            # Wenn die Datei geändert wurde und nicht gerade gespeichert wird
            if current_mtime > self._last_modified_time:
                logging.info(f"Settings file changed: {self.settings_file}")
                logging.info(f"Last known mtime: {self._last_modified_time}, Current mtime: {current_mtime}")
                
                # Warte kurz um sicherzustellen, dass Schreibvorgänge abgeschlossen sind
                time.sleep(0.5)
                
                # Prüfe, ob die Datei noch existiert (könnte zwischenzeitlich gelöscht worden sein)
                if not os.path.exists(self.settings_file):
                    logging.warning("Settings file no longer exists after change detection")
                    return
                
                # Prüfe, ob die Datei fertig geschrieben wurde (kein weiterer Zugriff)
                try:
                    # Versuche die Datei im schreibgeschützten Modus zu öffnen
                    with open(self.settings_file, 'r', encoding='utf-8'):
                        pass
                except IOError:
                    logging.warning("Settings file still being written, skipping this reload cycle")
                    return
                
                with self._lock:
                    # Speichere eine Kopie der alten Einstellungen für Vergleich
                    old_settings = self.settings.copy() if self.settings else {}
                    
                    # Lade neue Einstellungen
                    self._load_settings_internal()
                    
                    # Update Zeitstempel
                    self._last_modified_time = current_mtime
                
                # Vergleiche alte und neue Einstellungen
                has_changes = False
                if len(old_settings) != len(self.settings):
                    has_changes = True
                else:
                    # Vergleiche Werte
                    for key, value in self.settings.items():
                        if key not in old_settings or old_settings[key] != value:
                            has_changes = True
                            break
                
                # Wenn sich etwas geändert hat, benachrichtige
                if has_changes:
                    self._notify_settings_changed()
                else:
                    logging.info("Settings file changed but no actual setting values changed")
                
        except Exception as e:
            logging.error(f"Error checking for settings changes: {e}")
            logging.error(traceback.format_exc())
    
    def _notify_settings_changed(self):
        """
        Benachrichtige über geänderte Einstellungen via Callback-Funktion.
        """
        if self._settings_changed_callback is not None:
            try:
                # Erstelle eine Kopie der Einstellungen für den Callback
                settings_copy = self.settings.copy()
                logging.info(f"Notifying settings changed: {len(settings_copy)} settings")
                self._settings_changed_callback(settings_copy)
            except Exception as e:
                logging.error(f"Error in settings changed callback: {e}")
                logging.error(traceback.format_exc())
        else:
            logging.debug("Settings changed but no callback registered")