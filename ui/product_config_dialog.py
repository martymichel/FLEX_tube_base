from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QListWidget,
    QMessageBox, QInputDialog, QLabel, QWidget, QGroupBox
)
from PyQt6.QtCore import Qt
import logging

from product_dataset_manager import ProductDatasetManager

class ProductConfigDialog(QDialog):
    """Dialog zur Verwaltung von Produktkonfigurationen."""

    def __init__(self, dataset_manager: ProductDatasetManager, parent=None):
        super().__init__(parent)
        self.dataset_manager = dataset_manager
        self.parent_app = parent
        self.setWindowTitle("Konfiguration verwalten")
        self.resize(600, 400)
        self.setup_ui()
        self.load_datasets()

    # ------------------------------------------------------------------
    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Dataset Manager
        ds_group = QGroupBox("Datensatz-Manager")
        ds_layout = QVBoxLayout(ds_group)
        self.dataset_list = QListWidget()
        ds_layout.addWidget(self.dataset_list)

        btn_layout = QHBoxLayout()
        self.load_btn = QPushButton("Laden")
        self.save_btn = QPushButton("Speichern")
        self.rename_btn = QPushButton("Umbenennen")
        self.delete_btn = QPushButton("Löschen")
        btn_layout.addWidget(self.load_btn)
        btn_layout.addWidget(self.save_btn)
        btn_layout.addWidget(self.rename_btn)
        btn_layout.addWidget(self.delete_btn)
        ds_layout.addLayout(btn_layout)
        layout.addWidget(ds_group)

        # Neu Einrichten
        new_group = QGroupBox("Neu einrichten")
        ng_layout = QVBoxLayout(new_group)
        self.model_btn = QPushButton("Modell wählen")
        self.mode_btn = QPushButton("Modus wählen")
        ng_layout.addWidget(self.model_btn)
        ng_layout.addWidget(self.mode_btn)
        layout.addWidget(new_group)

        # Connections
        self.load_btn.clicked.connect(self.load_selected_dataset)
        self.save_btn.clicked.connect(self.save_dataset)
        self.rename_btn.clicked.connect(self.rename_dataset)
        self.delete_btn.clicked.connect(self.delete_dataset)
        self.model_btn.clicked.connect(self.choose_model)
        self.mode_btn.clicked.connect(self.choose_mode)

    # ------------------------------------------------------------------
    def load_datasets(self):
        self.dataset_list.clear()
        for name in self.dataset_manager.list_datasets():
            self.dataset_list.addItem(name)

    # Dataset Actions ---------------------------------------------------
    def current_dataset_name(self):
        item = self.dataset_list.currentItem()
        return item.text() if item else None

    def load_selected_dataset(self):
        name = self.current_dataset_name()
        if not name:
            return
        if self.dataset_manager.load_dataset(name):
            QMessageBox.information(self, "Erfolg", f"Datensatz {name} geladen")
            self.accept()
        else:
            QMessageBox.critical(self, "Fehler", f"Datensatz {name} konnte nicht geladen werden")

    def save_dataset(self):
        name, ok = QInputDialog.getText(self, "Speichern", "Name des Datensatzes:")
        if not ok or not name:
            return
        if self.dataset_manager.save_dataset(name):
            QMessageBox.information(self, "Gespeichert", f"Datensatz {name} gespeichert")
            self.load_datasets()
        else:
            QMessageBox.critical(self, "Fehler", "Speichern fehlgeschlagen")

    def rename_dataset(self):
        old = self.current_dataset_name()
        if not old:
            return
        new, ok = QInputDialog.getText(self, "Umbenennen", "Neuer Name:", text=old)
        if not ok or not new:
            return
        if self.dataset_manager.rename_dataset(old, new):
            self.load_datasets()
        else:
            QMessageBox.critical(self, "Fehler", "Umbenennen fehlgeschlagen")

    def delete_dataset(self):
        name = self.current_dataset_name()
        if not name:
            return
        if QMessageBox.question(self, "Löschen", f"Datensatz {name} wirklich löschen?") == QMessageBox.StandardButton.Yes:
            if self.dataset_manager.delete_dataset(name):
                self.load_datasets()
            else:
                QMessageBox.critical(self, "Fehler", "Löschen fehlgeschlagen")

    # Model/Mode --------------------------------------------------------
    def choose_model(self):
        if hasattr(self.parent_app, 'select_model_file'):
            model = self.parent_app.select_model_file()
            if model:
                logging.info(f"Neues Modell gewählt: {model}")

    def choose_mode(self):
        if hasattr(self.parent_app, 'select_camera_source'):
            source = self.parent_app.select_camera_source()
            if source is not None:
                logging.info(f"Neue Quelle gewählt: {source}")
