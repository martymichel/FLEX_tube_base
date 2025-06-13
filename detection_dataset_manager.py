"""
Detection-Datensatz Manager
Verwaltet komplette Einstellungssätze für verschiedene Produkte
Jeder Datensatz enthält ALLE Einstellungen: Modell, Kamera, Klassen, Workflow, etc.
"""

import json
import os
import logging
from datetime import datetime
from pathlib import Path
import shutil

class DetectionDatasetManager:
    """Manager für Detection-Datensätze (Produktkonfigurationen)."""
    
    def __init__(self, datasets_directory="detection_datasets"):
        self.datasets_directory = Path(datasets_directory)
        self.datasets_directory.mkdir(exist_ok=True)
        
        # Aktueller Datensatz
        self.current_dataset = None
        self.current_dataset_name = None
        
        # Backup-Verzeichnis
        self.backup_directory = self.datasets_directory / "backups"
        self.backup_directory.mkdir(exist_ok=True)
        
        logging.info(f"DetectionDatasetManager initialisiert - Verzeichnis: {self.datasets_directory}")
    
    def get_available_datasets(self):
        """Verfügbare Datensätze auflisten.
        
        Returns:
            list: Liste von Datensatz-Informationen [{'name': str, 'file': str, 'created': str, 'description': str}, ...]
        """
        datasets = []
        
        try:
            for file_path in self.datasets_directory.glob("*.json"):
                if file_path.name.startswith("backup_"):
                    continue  # Backup-Dateien überspringen
                    
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        dataset = json.load(f)
                    
                    # Datensatz-Info extrahieren
                    dataset_info = {
                        'name': dataset.get('dataset_info', {}).get('name', file_path.stem),
                        'file': file_path.name,
                        'created': dataset.get('dataset_info', {}).get('created', 'Unbekannt'),
                        'description': dataset.get('dataset_info', {}).get('description', ''),
                        'model_path': dataset.get('detection_settings', {}).get('model_path', ''),
                        'camera_source': dataset.get('detection_settings', {}).get('camera_source', ''),
                        'camera_type': dataset.get('detection_settings', {}).get('camera_type', '')
                    }
                    
                    datasets.append(dataset_info)
                    
                except Exception as e:
                    logging.error(f"Fehler beim Laden von Datensatz {file_path}: {e}")
                    
        except Exception as e:
            logging.error(f"Fehler beim Auflisten der Datensätze: {e}")
        
        # Nach Name sortieren
        datasets.sort(key=lambda x: x['name'])
        return datasets
    
    def create_dataset(self, name, description, current_settings, model_path, camera_source, camera_type):
        """Neuen Datensatz erstellen.
        
        Args:
            name (str): Name des Datensatzes
            description (str): Beschreibung
            current_settings (dict): Aktuelle Anwendungseinstellungen
            model_path (str): Pfad zum KI-Modell
            camera_source: Kamera-Quelle (int, str, oder tuple)
            camera_type (str): Typ der Kamera ('webcam', 'video', 'ids')
            
        Returns:
            bool: True wenn erfolgreich erstellt
        """
        try:
            # Dateiname generieren (sicher für Dateisystem)
            safe_name = self._make_safe_filename(name)
            file_path = self.datasets_directory / f"{safe_name}.json"
            
            # Prüfen ob Datei bereits existiert
            if file_path.exists():
                logging.error(f"Datensatz '{name}' existiert bereits")
                return False
            
            # Datensatz-Struktur erstellen
            dataset = {
                'dataset_info': {
                    'name': name,
                    'description': description,
                    'created': datetime.now().isoformat(),
                    'modified': datetime.now().isoformat(),
                    'version': '1.0'
                },
                'detection_settings': {
                    'model_path': model_path,
                    'camera_source': camera_source,
                    'camera_type': camera_type
                },
                'application_settings': current_settings.copy()
            }
            
            # Datensatz speichern
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(dataset, f, indent=2, ensure_ascii=False)
            
            logging.info(f"Datensatz '{name}' erfolgreich erstellt: {file_path}")
            return True
            
        except Exception as e:
            logging.error(f"Fehler beim Erstellen des Datensatzes '{name}': {e}")
            return False
    
    def load_dataset(self, dataset_name_or_file):
        """Datensatz laden.
        
        Args:
            dataset_name_or_file (str): Name des Datensatzes oder Dateiname
            
        Returns:
            dict oder None: Geladener Datensatz oder None bei Fehler
        """
        try:
            # Pfad bestimmen
            if dataset_name_or_file.endswith('.json'):
                file_path = self.datasets_directory / dataset_name_or_file
            else:
                safe_name = self._make_safe_filename(dataset_name_or_file)
                file_path = self.datasets_directory / f"{safe_name}.json"
            
            if not file_path.exists():
                logging.error(f"Datensatz-Datei nicht gefunden: {file_path}")
                return None
            
            # Datensatz laden
            with open(file_path, 'r', encoding='utf-8') as f:
                dataset = json.load(f)
            
            # Validierung
            if not self._validate_dataset(dataset):
                logging.error(f"Ungültiger Datensatz: {file_path}")
                return None
            
            self.current_dataset = dataset
            self.current_dataset_name = dataset['dataset_info']['name']
            
            logging.info(f"Datensatz '{self.current_dataset_name}' erfolgreich geladen")
            return dataset
            
        except Exception as e:
            logging.error(f"Fehler beim Laden des Datensatzes '{dataset_name_or_file}': {e}")
            return None
    
    def save_dataset(self, name, description, current_settings, model_path, camera_source, camera_type):
        """Bestehenden Datensatz aktualisieren oder neuen erstellen.
        
        Args:
            name (str): Name des Datensatzes
            description (str): Beschreibung
            current_settings (dict): Aktuelle Anwendungseinstellungen
            model_path (str): Pfad zum KI-Modell
            camera_source: Kamera-Quelle
            camera_type (str): Typ der Kamera
            
        Returns:
            bool: True wenn erfolgreich gespeichert
        """
        try:
            safe_name = self._make_safe_filename(name)
            file_path = self.datasets_directory / f"{safe_name}.json"
            
            # Backup erstellen wenn Datei existiert
            if file_path.exists():
                self._create_backup(file_path)
            
            # Datensatz erstellen/aktualisieren
            if file_path.exists():
                # Bestehenden Datensatz laden für created-Datum
                with open(file_path, 'r', encoding='utf-8') as f:
                    existing = json.load(f)
                created_date = existing.get('dataset_info', {}).get('created', datetime.now().isoformat())
            else:
                created_date = datetime.now().isoformat()
            
            dataset = {
                'dataset_info': {
                    'name': name,
                    'description': description,
                    'created': created_date,
                    'modified': datetime.now().isoformat(),
                    'version': '1.0'
                },
                'detection_settings': {
                    'model_path': model_path,
                    'camera_source': camera_source,
                    'camera_type': camera_type
                },
                'application_settings': current_settings.copy()
            }
            
            # Datensatz speichern
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(dataset, f, indent=2, ensure_ascii=False)
            
            self.current_dataset = dataset
            self.current_dataset_name = name
            
            logging.info(f"Datensatz '{name}' erfolgreich gespeichert")
            return True
            
        except Exception as e:
            logging.error(f"Fehler beim Speichern des Datensatzes '{name}': {e}")
            return False
    
    def delete_dataset(self, dataset_name_or_file):
        """Datensatz löschen.
        
        Args:
            dataset_name_or_file (str): Name des Datensatzes oder Dateiname
            
        Returns:
            bool: True wenn erfolgreich gelöscht
        """
        try:
            # Pfad bestimmen
            if dataset_name_or_file.endswith('.json'):
                file_path = self.datasets_directory / dataset_name_or_file
            else:
                safe_name = self._make_safe_filename(dataset_name_or_file)
                file_path = self.datasets_directory / f"{safe_name}.json"
            
            if not file_path.exists():
                logging.warning(f"Datensatz-Datei zum Löschen nicht gefunden: {file_path}")
                return False
            
            # Backup vor Löschung erstellen
            self._create_backup(file_path, prefix="deleted_")
            
            # Datei löschen
            file_path.unlink()
            
            # Aktuellen Datensatz zurücksetzen wenn gelöscht
            if self.current_dataset_name == dataset_name_or_file:
                self.current_dataset = None
                self.current_dataset_name = None
            
            logging.info(f"Datensatz '{dataset_name_or_file}' erfolgreich gelöscht")
            return True
            
        except Exception as e:
            logging.error(f"Fehler beim Löschen des Datensatzes '{dataset_name_or_file}': {e}")
            return False
    
    def duplicate_dataset(self, source_name, new_name, new_description):
        """Datensatz duplizieren.
        
        Args:
            source_name (str): Name des Quell-Datensatzes
            new_name (str): Name des neuen Datensatzes
            new_description (str): Beschreibung des neuen Datensatzes
            
        Returns:
            bool: True wenn erfolgreich dupliziert
        """
        try:
            # Quell-Datensatz laden
            source_dataset = self.load_dataset(source_name)
            if not source_dataset:
                return False
            
            # Neuen Datensatz erstellen
            return self.create_dataset(
                new_name,
                new_description,
                source_dataset['application_settings'],
                source_dataset['detection_settings']['model_path'],
                source_dataset['detection_settings']['camera_source'],
                source_dataset['detection_settings']['camera_type']
            )
            
        except Exception as e:
            logging.error(f"Fehler beim Duplizieren des Datensatzes: {e}")
            return False
    
    def export_dataset(self, dataset_name, export_path):
        """Datensatz exportieren.
        
        Args:
            dataset_name (str): Name des zu exportierenden Datensatzes
            export_path (str): Pfad für den Export
            
        Returns:
            bool: True wenn erfolgreich exportiert
        """
        try:
            dataset = self.load_dataset(dataset_name)
            if not dataset:
                return False
            
            export_file = Path(export_path)
            with open(export_file, 'w', encoding='utf-8') as f:
                json.dump(dataset, f, indent=2, ensure_ascii=False)
            
            logging.info(f"Datensatz '{dataset_name}' erfolgreich exportiert nach: {export_path}")
            return True
            
        except Exception as e:
            logging.error(f"Fehler beim Exportieren des Datensatzes: {e}")
            return False
    
    def import_dataset(self, import_path, new_name=None):
        """Datensatz importieren.
        
        Args:
            import_path (str): Pfad der zu importierenden Datei
            new_name (str, optional): Neuer Name für den Datensatz
            
        Returns:
            bool: True wenn erfolgreich importiert
        """
        try:
            import_file = Path(import_path)
            if not import_file.exists():
                logging.error(f"Import-Datei nicht gefunden: {import_path}")
                return False
            
            # Datensatz laden und validieren
            with open(import_file, 'r', encoding='utf-8') as f:
                dataset = json.load(f)
            
            if not self._validate_dataset(dataset):
                logging.error(f"Ungültiger Datensatz in Import-Datei: {import_path}")
                return False
            
            # Namen anpassen wenn gewünscht
            if new_name:
                dataset['dataset_info']['name'] = new_name
            
            name = dataset['dataset_info']['name']
            
            # Datensatz erstellen
            return self.create_dataset(
                name,
                dataset['dataset_info']['description'],
                dataset['application_settings'],
                dataset['detection_settings']['model_path'],
                dataset['detection_settings']['camera_source'],
                dataset['detection_settings']['camera_type']
            )
            
        except Exception as e:
            logging.error(f"Fehler beim Importieren des Datensatzes: {e}")
            return False
    
    def get_current_dataset_info(self):
        """Informationen über den aktuell geladenen Datensatz.
        
        Returns:
            dict: Datensatz-Informationen oder None wenn kein Datensatz geladen
        """
        if not self.current_dataset:
            return None
        
        return {
            'name': self.current_dataset_name,
            'description': self.current_dataset['dataset_info']['description'],
            'created': self.current_dataset['dataset_info']['created'],
            'modified': self.current_dataset['dataset_info']['modified'],
            'model_path': self.current_dataset['detection_settings']['model_path'],
            'camera_source': self.current_dataset['detection_settings']['camera_source'],
            'camera_type': self.current_dataset['detection_settings']['camera_type']
        }
    
    def _make_safe_filename(self, name):
        """Sicheren Dateinamen erstellen.
        
        Args:
            name (str): Originalname
            
        Returns:
            str: Sicherer Dateiname
        """
        # Ungültige Zeichen entfernen/ersetzen
        safe_chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-"
        safe_name = ''.join(c if c in safe_chars else '_' for c in name)
        
        # Mehrfache Unterstriche reduzieren
        while '__' in safe_name:
            safe_name = safe_name.replace('__', '_')
        
        # Unterstriche am Anfang/Ende entfernen
        safe_name = safe_name.strip('_')
        
        # Fallback falls Name komplett leer
        if not safe_name:
            safe_name = "unnamed_dataset"
        
        return safe_name
    
    def _validate_dataset(self, dataset):
        """Datensatz validieren.
        
        Args:
            dataset (dict): Zu validierender Datensatz
            
        Returns:
            bool: True wenn gültig
        """
        try:
            # Struktur prüfen
            required_sections = ['dataset_info', 'detection_settings', 'application_settings']
            for section in required_sections:
                if section not in dataset:
                    return False
            
            # Dataset-Info prüfen
            dataset_info = dataset['dataset_info']
            required_info = ['name', 'description', 'created']
            for field in required_info:
                if field not in dataset_info:
                    return False
            
            # Detection-Settings prüfen
            detection_settings = dataset['detection_settings']
            required_detection = ['model_path', 'camera_source', 'camera_type']
            for field in required_detection:
                if field not in detection_settings:
                    return False
            
            return True
            
        except Exception:
            return False
    
    def _create_backup(self, file_path, prefix="backup_"):
        """Backup einer Datei erstellen.
        
        Args:
            file_path (Path): Pfad der zu sichernden Datei
            prefix (str): Prefix für Backup-Datei
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"{prefix}{file_path.stem}_{timestamp}.json"
            backup_path = self.backup_directory / backup_name
            
            shutil.copy2(file_path, backup_path)
            logging.debug(f"Backup erstellt: {backup_path}")
            
        except Exception as e:
            logging.warning(f"Fehler beim Erstellen des Backups: {e}")
    
    def cleanup_old_backups(self, max_backups=50):
        """Alte Backup-Dateien aufräumen.
        
        Args:
            max_backups (int): Maximale Anzahl Backup-Dateien
        """
        try:
            backup_files = list(self.backup_directory.glob("*.json"))
            
            if len(backup_files) > max_backups:
                # Nach Änderungsdatum sortieren (älteste zuerst)
                backup_files.sort(key=lambda x: x.stat().st_mtime)
                
                # Älteste Dateien löschen
                files_to_delete = backup_files[:-max_backups]
                deleted_count = 0
                
                for file_path in files_to_delete:
                    try:
                        file_path.unlink()
                        deleted_count += 1
                    except Exception as e:
                        logging.warning(f"Fehler beim Löschen der Backup-Datei {file_path}: {e}")
                
                if deleted_count > 0:
                    logging.info(f"Backup-Cleanup: {deleted_count} alte Dateien gelöscht")
            
        except Exception as e:
            logging.error(f"Fehler beim Backup-Cleanup: {e}")