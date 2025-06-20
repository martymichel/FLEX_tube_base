""" 
Detection Event Logger - Tagebasierte Parquet-Dateien Speichert alle Ereignisse eines Tages in einer gemeinsamen Parquet-Datei Neue Datei wird automatisch um Mitternacht erstellt
"""

import os
import logging
from datetime import datetime, date
from pathlib import Path
import pandas as pd
import threading
from typing import Dict, Any, Optional

try:
    import pyarrow as pa
    import pyarrow.parquet as pq
    PYARROW_AVAILABLE = True
except ImportError:
    PYARROW_AVAILABLE = False
    logging.warning("pyarrow nicht verfügbar - Parquet-Logging deaktiviert")

class DetectionLogger:
    """
    Tagebasierter Detection Event Logger.

    Speichert alle Events eines Tages in einer gemeinsamen Parquet-Datei.
    Format: detection_events_YYYY-MM-DD.parquet
    """

    def __init__(self, settings):
        self.settings = settings
        self.enabled = settings.get('parquet_log_enabled', True) and PYARROW_AVAILABLE
        
        if not self.enabled:
            logging.info("Parquet-Logging deaktiviert")
            return
        
        # Konfiguration
        self.log_directory = settings.get('parquet_log_directory', 'logs/detection_events')
        self.max_files = settings.get('parquet_log_max_files', 1000000)
        
        # Thread-Sicherheit
        self._lock = threading.Lock()
        
        # Aktueller Tag und Datei-Status
        self.current_date = None
        self.current_file_path = None
        self.events_buffer = []
        
        # Verzeichnis erstellen
        self._ensure_log_directory()
        
        # Schema für Parquet-Dateien definieren
        self._define_schema()
        
        logging.info(f"DetectionLogger initialisiert - Verzeichnis: {self.log_directory}")

    def _ensure_log_directory(self):
        """Log-Verzeichnis erstellen falls nicht vorhanden."""
        try:
            Path(self.log_directory).mkdir(parents=True, exist_ok=True)
        except Exception as e:
            logging.error(f"Fehler beim Erstellen des Log-Verzeichnisses: {e}")
            self.enabled = False

    def _define_schema(self):
        """Parquet-Schema für Event-Daten definieren."""
        # KORRIGIERT: Verwende 'ns' statt 'ms' für pandas-Kompatibilität
        self.schema = pa.schema([
            ('timestamp', pa.timestamp('ns')),  # Geändert von 'ms' zu 'ns'
            ('event_type', pa.string()),
            ('sub_type', pa.string()),
            ('status', pa.string()),
            ('message', pa.string()),
            ('details_json', pa.string()),  # JSON-String für komplexe Details
        ])

    def _get_current_file_path(self):
        """Aktuellen Dateipfad für heutiges Datum ermitteln."""
        today = date.today()
        filename = f"detection_events_{today.strftime('%Y-%m-%d')}.parquet"
        return os.path.join(self.log_directory, filename)

    def _check_day_change(self):
        """Prüfen ob ein neuer Tag begonnen hat."""
        today = date.today()
        if self.current_date != today:
            # Neuer Tag - alte Events noch schreiben falls vorhanden
            if self.events_buffer:
                self._flush_events()
            
            # Neue Datei für heute
            self.current_date = today
            self.current_file_path = self._get_current_file_path()
            self.events_buffer = []
            
            logging.info(f"Neuer Tag erkannt - Log-Datei: {os.path.basename(self.current_file_path)}")

    def _create_event_record(self, event_type: str, sub_type: str, status: str, 
                        message: str, details: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Event-Record für Parquet erstellen."""
        import json
        
        return {
            'timestamp': datetime.now(),
            'event_type': event_type,
            'sub_type': sub_type,
            'status': status,
            'message': message,
            'details_json': json.dumps(details) if details else '{}'
        }

    def _append_to_file(self, events_data):
        """Events zu Parquet-Datei hinzufügen."""
        try:
            # DataFrame aus Events erstellen
            df = pd.DataFrame(events_data)
            
            # KORRIGIERT: Explizite Timestamp-Konvertierung zu pandas-Standard
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            
            # VERBESSERT: Schema automatisch aus DataFrame ableiten anstatt erzwingen
            # Das verhindert Casting-Probleme zwischen ns und ms
            table = pa.Table.from_pandas(df, preserve_index=False)
            
            # An bestehende Datei anhängen oder neue erstellen
            if os.path.exists(self.current_file_path):
                # Bestehende Datei lesen
                existing_table = pq.read_table(self.current_file_path)
                # Neue Daten anhängen
                combined_table = pa.concat_tables([existing_table, table])
                # Zurückschreiben mit Snappy-Kompression
                pq.write_table(combined_table, self.current_file_path, compression='snappy')
            else:
                # Neue Datei erstellen mit Snappy-Kompression
                pq.write_table(table, self.current_file_path, compression='snappy')
            
            logging.debug(f"Events in Parquet-Datei gespeichert: {len(events_data)} Events")
            
        except Exception as e:
            logging.error(f"Fehler beim Schreiben der Parquet-Datei: {e}")

    def _flush_events(self):
        """Gepufferte Events in Datei schreiben."""
        if not self.events_buffer or not self.enabled:
            return
        
        try:
            self._append_to_file(self.events_buffer)
            self.events_buffer = []
        except Exception as e:
            logging.error(f"Fehler beim Flushen der Events: {e}")

    def _log_event(self, event_type: str, sub_type: str, status: str, 
                message: str, details: Optional[Dict[str, Any]] = None):
        """Basis-Methode für Event-Logging."""
        if not self.enabled:
            return
        
        with self._lock:
            try:
                # Tag-Wechsel prüfen
                self._check_day_change()
                
                # Event-Record erstellen
                event_record = self._create_event_record(event_type, sub_type, status, message, details)
                
                # Zu Buffer hinzufügen
                self.events_buffer.append(event_record)
                
                # Sofort schreiben (für Echtzeit-Verfügbarkeit)
                self._flush_events()
                
            except Exception as e:
                logging.error(f"Fehler beim Event-Logging: {e}")

    # Spezifische Logging-Methoden

    def log_detection_cycle(self, bad_parts_detected: bool, cycle_detections: Dict[str, Any], 
                        cycle_stats: Optional[Dict[str, Any]] = None):
        """Detection-Zyklus-Ergebnis loggen."""
        status = 'ERROR' if bad_parts_detected else 'SUCCESS'
        message = 'Schlechte Teile erkannt' if bad_parts_detected else 'Keine schlechten Teile'
        
        # Erkannte Klassen extrahieren
        detected_classes = list(cycle_detections.keys()) if cycle_detections else []
        total_detections = sum(stats.get('total_detections', 0) for stats in cycle_detections.values())
        
        details = {
            'bad_parts_detected': bad_parts_detected,
            'cycle_detections': cycle_detections,
            'detected_classes': detected_classes,
            'total_detections': total_detections
        }
        
        if cycle_stats:
            details.update(cycle_stats)
        
        self._log_event('DETECTION', 'CYCLE_RESULT', status, message, details)

    def log_modbus_event(self, sub_type: str, status: str, message: str, 
                        details: Optional[Dict[str, Any]] = None):
        """Modbus-Event loggen."""
        self._log_event('MODBUS', sub_type, status, message, details)

    def log_brightness_event(self, auto_stop_triggered: bool, brightness_value: float,
                        threshold_info: Optional[Dict[str, Any]] = None):
        """Helligkeits-Event loggen."""
        sub_type = 'AUTO_STOP' if auto_stop_triggered else 'MONITORING'
        status = 'ERROR' if auto_stop_triggered else 'INFO'
        message = f"Helligkeits-Auto-Stopp: {brightness_value:.1f}" if auto_stop_triggered else f"Helligkeit: {brightness_value:.1f}"
        
        details = {
            'auto_stop_triggered': auto_stop_triggered,
            'brightness_value': brightness_value
        }
        
        if threshold_info:
            details.update(threshold_info)
        
        self._log_event('BRIGHTNESS', sub_type, status, message, details)

    def log_system_event(self, sub_type: str, status: str, message: str, 
                        details: Optional[Dict[str, Any]] = None):
        """System-Event loggen."""
        self._log_event('SYSTEM', sub_type, status, message, details)

    def log_motion_event(self, motion_detected: bool, motion_value: float,
                        workflow_status: str, details: Optional[Dict[str, Any]] = None):
        """Bewegungs-Event loggen."""
        sub_type = 'DETECTED' if motion_detected else 'CLEARED'
        status = 'INFO'
        message = f"Bewegung {'erkannt' if motion_detected else 'gestoppt'}: {motion_value:.1f}"
        
        event_details = {
            'motion_detected': motion_detected,
            'motion_value': motion_value,
            'workflow_status': workflow_status
        }
        
        if details:
            event_details.update(details)
        
        self._log_event('MOTION', sub_type, status, message, event_details)

    def get_current_file_info(self):
        """Info über aktuelle Log-Datei."""
        if not self.enabled:
            return {'enabled': False}
        
        file_info = {
            'enabled': True,
            'current_file': self.current_file_path,
            'current_date': str(self.current_date),
            'buffered_events': len(self.events_buffer)
        }
        
        if self.current_file_path and os.path.exists(self.current_file_path):
            try:
                stat = os.stat(self.current_file_path)
                file_info['file_size_mb'] = stat.st_size / (1024 * 1024)
                file_info['last_modified'] = datetime.fromtimestamp(stat.st_mtime).isoformat()
            except Exception:
                pass
        
        return file_info

    def get_available_log_files(self):
        """Liste verfügbarer Log-Dateien."""
        if not self.enabled:
            return []
        
        try:
            log_files = []
            log_dir = Path(self.log_directory)
            
            for file_path in log_dir.glob('detection_events_*.parquet'):
                try:
                    stat = file_path.stat()
                    log_files.append({
                        'filename': file_path.name,
                        'path': str(file_path),
                        'size_mb': stat.st_size / (1024 * 1024),
                        'modified': datetime.fromtimestamp(stat.st_mtime).isoformat()
                    })
                except Exception:
                    continue
            
            # Nach Datum sortieren (neueste zuerst)
            log_files.sort(key=lambda x: x['modified'], reverse=True)
            return log_files
            
        except Exception as e:
            logging.error(f"Fehler beim Auflisten der Log-Dateien: {e}")
            return []

    def cleanup_old_files(self):
        """Alte Log-Dateien aufräumen wenn Limit erreicht."""
        try:
            log_files = self.get_available_log_files()
            
            if len(log_files) > self.max_files:
                # Älteste Dateien löschen
                files_to_delete = log_files[self.max_files:]
                deleted_count = 0
                
                for file_info in files_to_delete:
                    try:
                        os.remove(file_info['path'])
                        deleted_count += 1
                    except Exception as e:
                        logging.warning(f"Fehler beim Löschen der Log-Datei {file_info['filename']}: {e}")
                
                if deleted_count > 0:
                    logging.info(f"Log-Cleanup: {deleted_count} alte Dateien gelöscht")
            
        except Exception as e:
            logging.error(f"Fehler beim Log-Cleanup: {e}")

    def close(self):
        """Logger schliessen und letzte Events schreiben."""
        if not self.enabled:
            return
        
        with self._lock:
            try:
                # Letzte Events flushen
                if self.events_buffer:
                    self._flush_events()
                
                # Cleanup durchführen
                self.cleanup_old_files()
                
                logging.info("DetectionLogger geschlossen")
                
            except Exception as e:
                logging.error(f"Fehler beim Schliessen des DetectionLoggers: {e}")