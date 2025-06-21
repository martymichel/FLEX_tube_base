import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict

from settings import Settings

class ProductDatasetManager:
    """Manager fuer produktspezifische Konfigurationsdatensaetze."""

    def __init__(self, settings: Settings, datasets_dir: str = "datasets"):
        self.settings = settings
        self.datasets_dir = Path(datasets_dir)
        self.datasets_dir.mkdir(parents=True, exist_ok=True)

        # Globale Einstellungen die nicht im Datensatz gespeichert werden
        self.global_keys = {
            'modbus_enabled',
            'modbus_ip',
            'modbus_port',
            'watchdog_timeout_seconds',
            'watchdog_interval_seconds',
            'reject_coil_address',
            'detection_active_coil_address',
            'reject_coil_duration_seconds',
            'class_colors',
            # Quelle und Modus sind produktspezifisch und werden daher
            # nicht mehr als globale Einstellungen behandelt
            'last_dataset',
        }

    # ------------------------------------------------------------------
    # Hilfsfunktionen
    # ------------------------------------------------------------------
    def _dataset_path(self, name: str) -> Path:
        return self.datasets_dir / f"{name}.json"

    def list_datasets(self) -> List[str]:
        datasets = []
        for p in self.datasets_dir.glob("*.json"):
            if "_v1_" in p.stem:
                continue
            datasets.append(p.stem)
        return datasets

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------
    def validate_dataset(self, data: Dict):
        """Einfache Validierung der noetigen Einstellungen."""
        defaults = Settings().get_defaults()
        missing = []
        for key in defaults.keys():
            if key in self.global_keys:
                continue
            if key not in data:
                missing.append(key)
        if missing:
            raise ValueError(f"Fehlende Einstellungen: {', '.join(missing)}")

    # ------------------------------------------------------------------
    # Laden / Speichern
    # ------------------------------------------------------------------
    def load_dataset(self, name: str) -> bool:
        path = self._dataset_path(name)
        if not path.exists():
            logging.error(f"Datensatz nicht gefunden: {name}")
            return False
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self.validate_dataset(data)
            for k, v in data.items():
                if k not in self.global_keys:
                    self.settings.set(k, v)
            self.settings.set('last_dataset', name)
            self.settings.save()
            logging.info(f"Datensatz geladen: {name}")
            return True
        except Exception as exc:  # noqa: broad-except
            logging.error(f"Fehler beim Laden des Datensatzes {name}: {exc}")
            return False

    def save_dataset(self, name: str) -> bool:
        path = self._dataset_path(name)
        data = {
            k: v for k, v in self.settings.data.items() if k not in self.global_keys
        }
        try:
            self.validate_dataset(data)
        except Exception as exc:
            logging.error(f"Datensatz ungueltig: {exc}")
            return False

        if path.exists():
            ts = datetime.now().strftime('%Y%m%d_%H%M')
            archive = self.datasets_dir / f"{name}_v1_{ts}.json"
            try:
                path.replace(archive)
                logging.info(f"Vorherige Version archiviert: {archive}")
            except Exception as exc:  # noqa: broad-except
                logging.error(f"Fehler beim Archivieren der alten Version: {exc}")
        try:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            self.settings.set('last_dataset', name)
            self.settings.save()
            logging.info(f"Datensatz gespeichert: {name}")
            return True
        except Exception as exc:  # noqa: broad-except
            logging.error(f"Fehler beim Speichern des Datensatzes {name}: {exc}")
            return False

    def rename_dataset(self, old: str, new: str) -> bool:
        old_path = self._dataset_path(old)
        new_path = self._dataset_path(new)
        if not old_path.exists():
            logging.error(f"Datensatz nicht gefunden: {old}")
            return False
        try:
            old_path.rename(new_path)
            logging.info(f"Datensatz umbenannt: {old} -> {new}")
            if self.settings.get('last_dataset') == old:
                self.settings.set('last_dataset', new)
                self.settings.save()
            return True
        except Exception as exc:  # noqa: broad-except
            logging.error(f"Fehler beim Umbenennen des Datensatzes: {exc}")
            return False

    def delete_dataset(self, name: str) -> bool:
        path = self._dataset_path(name)
        if not path.exists():
            return False
        try:
            path.unlink()
            logging.info(f"Datensatz geloescht: {name}")
            if self.settings.get('last_dataset') == name:
                self.settings.set('last_dataset', '')
                self.settings.save()
            return True
        except Exception as exc:  # noqa: broad-except
            logging.error(f"Fehler beim Loeschen des Datensatzes {name}: {exc}")
            return False

    def migrate_from_settings(self):
        """Bestehende Einstellungen in einen ersten Datensatz ueberfuehren."""
        last_ds = self.settings.get('last_dataset', 'default') or 'default'
        path = self._dataset_path(last_ds)
        if path.exists():
            return
        logging.info(f"Migration: speichere aktuelle Einstellungen als Datensatz {last_ds}")
        self.save_dataset(last_ds)

    def load_dataset_with_backup(self, name: str) -> bool:
        """Versuche Datensatz zu laden, nutze Backup bei Fehlern."""
        if self.load_dataset(name):
            return True
        # Lade Backup wenn vorhanden
        backups = sorted(self.datasets_dir.glob(f"{name}_v1_*.json"), reverse=True)
        for backup in backups:
            try:
                with open(backup, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self.validate_dataset(data)
                for k, v in data.items():
                    if k not in self.global_keys:
                        self.settings.set(k, v)
                self.settings.set('last_dataset', name)
                self.settings.save()
                logging.warning(f"Backup-Datensatz geladen: {backup}")
                return True
            except Exception as exc:  # noqa: broad-except
                logging.error(f"Backup {backup} ungueltig: {exc}")
        return False

