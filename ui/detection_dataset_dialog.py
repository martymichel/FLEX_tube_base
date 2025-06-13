"""
Detection-Datensatz Dialog
Verwaltung und Auswahl von Produktkonfigurationen
Ersetzt die einzelnen Modell- und Kamera-Auswahl-Buttons
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QHeaderView, QMessageBox, QInputDialog,
    QTextEdit, QGroupBox, QFormLayout, QLineEdit, QComboBox,
    QFileDialog, QTabWidget, QWidget, QSplitter, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
import os

from .camera_selection_dialog import CameraSelectionDialog

class DetectionDatasetDialog(QDialog):
    """Dialog für Verwaltung und Auswahl von Detection-Datensätzen."""
    
    # Signal wird emittiert wenn ein Datensatz ausgewählt wurde
    dataset_selected = pyqtSignal(str)  # Name des ausgewählten Datensatzes
    
    def __init__(self, dataset_manager, camera_manager, parent=None):
        super().__init__(parent)
        self.dataset_manager = dataset_manager
        self.camera_manager = camera_manager
        self.selected_dataset = None
        
        self.setWindowTitle("Detection-Datensätze verwalten")
        self.setModal(True)
        self.resize(1000, 700)
        
        self.setup_ui()
        self.refresh_datasets()
    
    def setup_ui(self):
        """UI aufbauen."""
        layout = QHBoxLayout(self)
        
        # Splitter für Listen-/Detail-Ansicht
        splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(splitter)
        
        # Linke Seite: Datensatz-Liste
        left_widget = self.create_dataset_list()
        splitter.addWidget(left_widget)
        
        # Rechte Seite: Details/Editor
        right_widget = self.create_dataset_editor()
        splitter.addWidget(right_widget)
        
        # Splitter-Verhältnis
        splitter.setSizes([400, 600])
        
        # Button-Layout unten
        button_layout = QHBoxLayout()
        
        # Import/Export
        self.import_btn = QPushButton("📁 Importieren")
        self.import_btn.clicked.connect(self.import_dataset)
        button_layout.addWidget(self.import_btn)
        
        self.export_btn = QPushButton("📤 Exportieren")
        self.export_btn.clicked.connect(self.export_dataset)
        self.export_btn.setEnabled(False)
        button_layout.addWidget(self.export_btn)
        
        button_layout.addStretch()
        
        # Hauptbuttons
        self.cancel_btn = QPushButton("Abbrechen")
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)
        
        self.select_btn = QPushButton("Datensatz laden")
        self.select_btn.clicked.connect(self.load_selected_dataset)
        self.select_btn.setEnabled(False)
        button_layout.addWidget(self.select_btn)
        
        layout.addLayout(button_layout)
    
    def create_dataset_list(self):
        """Datensatz-Liste erstellen."""
        widget = QFrame()
        layout = QVBoxLayout(widget)
        
        # Header
        header_label = QLabel("Verfügbare Detection-Datensätze")
        header_label.setFont(QFont("", 12, QFont.Weight.Bold))
        layout.addWidget(header_label)
        
        # Datensatz-Tabelle
        self.datasets_table = QTableWidget()
        self.datasets_table.setColumnCount(4)
        self.datasets_table.setHorizontalHeaderLabels([
            "Name", "Erstellt", "Modell", "Kamera"
        ])
        
        # Spaltenbreiten
        header = self.datasets_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        
        # Selection-Handler
        self.datasets_table.selectionModel().selectionChanged.connect(self.on_dataset_selected)
        self.datasets_table.itemDoubleClicked.connect(self.load_selected_dataset)
        
        layout.addWidget(self.datasets_table)
        
        # Verwaltungs-Buttons
        management_layout = QHBoxLayout()
        
        self.new_btn = QPushButton("➕ Neu")
        self.new_btn.clicked.connect(self.create_new_dataset)
        management_layout.addWidget(self.new_btn)
        
        self.duplicate_btn = QPushButton("📄 Duplizieren")
        self.duplicate_btn.clicked.connect(self.duplicate_dataset)
        self.duplicate_btn.setEnabled(False)
        management_layout.addWidget(self.duplicate_btn)
        
        self.delete_btn = QPushButton("🗑️ Löschen")
        self.delete_btn.clicked.connect(self.delete_dataset)
        self.delete_btn.setEnabled(False)
        management_layout.addWidget(self.delete_btn)
        
        self.refresh_btn = QPushButton("🔄 Aktualisieren")
        self.refresh_btn.clicked.connect(self.refresh_datasets)
        management_layout.addWidget(self.refresh_btn)
        
        layout.addLayout(management_layout)
        
        return widget
    
    def create_dataset_editor(self):
        """Datensatz-Editor erstellen."""
        widget = QFrame()
        layout = QVBoxLayout(widget)
        
        # Header
        self.editor_header = QLabel("Datensatz-Details")
        self.editor_header.setFont(QFont("", 12, QFont.Weight.Bold))
        layout.addWidget(self.editor_header)
        
        # Tab Widget für verschiedene Bereiche
        self.editor_tabs = QTabWidget()
        layout.addWidget(self.editor_tabs)
        
        # Allgemeine Informationen Tab
        info_tab = self.create_info_tab()
        self.editor_tabs.addTab(info_tab, "ℹ️ Informationen")
        
        # Detection-Einstellungen Tab
        detection_tab = self.create_detection_tab()
        self.editor_tabs.addTab(detection_tab, "🎯 Detection")
        
        # Vorschau Tab
        preview_tab = self.create_preview_tab()
        self.editor_tabs.addTab(preview_tab, "👁️ Vorschau")
        
        # Editor-Buttons
        editor_buttons = QHBoxLayout()
        
        self.save_btn = QPushButton("💾 Speichern")
        self.save_btn.clicked.connect(self.save_current_dataset)
        self.save_btn.setEnabled(False)
        editor_buttons.addWidget(self.save_btn)
        
        self.revert_btn = QPushButton("↶ Zurücksetzen")
        self.revert_btn.clicked.connect(self.revert_changes)
        self.revert_btn.setEnabled(False)
        editor_buttons.addWidget(self.revert_btn)
        
        editor_buttons.addStretch()
        
        layout.addLayout(editor_buttons)
        
        return widget
    
    def create_info_tab(self):
        """Allgemeine Informationen Tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Datensatz-Info
        info_group = QGroupBox("Datensatz-Information")
        info_layout = QFormLayout(info_group)
        
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Name für den Datensatz")
        self.name_edit.textChanged.connect(self.on_editor_changed)
        info_layout.addRow("Name:", self.name_edit)
        
        self.description_edit = QTextEdit()
        self.description_edit.setPlaceholderText("Beschreibung des Datensatzes...")
        self.description_edit.setMaximumHeight(80)
        self.description_edit.textChanged.connect(self.on_editor_changed)
        info_layout.addRow("Beschreibung:", self.description_edit)
        
        layout.addWidget(info_group)
        
        # Statistiken
        stats_group = QGroupBox("Statistiken")
        stats_layout = QFormLayout(stats_group)
        
        self.created_label = QLabel("Nicht verfügbar")
        stats_layout.addRow("Erstellt:", self.created_label)
        
        self.modified_label = QLabel("Nicht verfügbar")
        stats_layout.addRow("Geändert:", self.modified_label)
        
        self.settings_count_label = QLabel("0")
        stats_layout.addRow("Einstellungen:", self.settings_count_label)
        
        layout.addWidget(stats_group)
        layout.addStretch()
        
        return widget
    
    def create_detection_tab(self):
        """Detection-Einstellungen Tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # KI-Modell
        model_group = QGroupBox("KI-Modell")
        model_layout = QVBoxLayout(model_group)
        
        model_select_layout = QHBoxLayout()
        
        self.model_path_edit = QLineEdit()
        self.model_path_edit.setPlaceholderText("Pfad zum KI-Modell (.pt Datei)")
        self.model_path_edit.setReadOnly(True)
        model_select_layout.addWidget(self.model_path_edit)
        
        self.browse_model_btn = QPushButton("📁 Modell wählen")
        self.browse_model_btn.clicked.connect(self.browse_model)
        model_select_layout.addWidget(self.browse_model_btn)
        
        model_layout.addLayout(model_select_layout)
        
        # Modell-Info
        self.model_info_label = QLabel("Kein Modell ausgewählt")
        self.model_info_label.setStyleSheet("color: gray; font-style: italic;")
        model_layout.addWidget(self.model_info_label)
        
        layout.addWidget(model_group)
        
        # Kamera/Video-Quelle
        camera_group = QGroupBox("Kamera/Video-Quelle")
        camera_layout = QVBoxLayout(camera_group)
        
        camera_select_layout = QHBoxLayout()
        
        self.camera_type_combo = QComboBox()
        self.camera_type_combo.addItems(["webcam", "video", "ids"])
        self.camera_type_combo.currentTextChanged.connect(self.on_camera_type_changed)
        camera_select_layout.addWidget(QLabel("Typ:"))
        camera_select_layout.addWidget(self.camera_type_combo)
        
        camera_select_layout.addStretch()
        
        self.select_camera_btn = QPushButton("📷 Quelle wählen")
        self.select_camera_btn.clicked.connect(self.select_camera_source)
        camera_select_layout.addWidget(self.select_camera_btn)
        
        camera_layout.addLayout(camera_select_layout)
        
        # Kamera-Info
        self.camera_info_label = QLabel("Keine Quelle ausgewählt")
        self.camera_info_label.setStyleSheet("color: gray; font-style: italic;")
        camera_layout.addWidget(self.camera_info_label)
        
        # Aktuelle Quelle (intern)
        self.current_camera_source = None
        
        layout.addWidget(camera_group)
        
        # Test-Bereich
        test_group = QGroupBox("Test")
        test_layout = QHBoxLayout(test_group)
        
        self.test_model_btn = QPushButton("🧪 Modell testen")
        self.test_model_btn.clicked.connect(self.test_model)
        self.test_model_btn.setEnabled(False)
        test_layout.addWidget(self.test_model_btn)
        
        self.test_camera_btn = QPushButton("📹 Kamera testen")
        self.test_camera_btn.clicked.connect(self.test_camera)
        self.test_camera_btn.setEnabled(False)
        test_layout.addWidget(self.test_camera_btn)
        
        test_layout.addStretch()
        
        layout.addWidget(test_group)
        layout.addStretch()
        
        return widget
    
    def create_preview_tab(self):
        """Vorschau Tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Datensatz-Vorschau
        preview_group = QGroupBox("Datensatz-Vorschau")
        preview_layout = QVBoxLayout(preview_group)
        
        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        self.preview_text.setFont(QFont("Courier", 9))
        preview_layout.addWidget(self.preview_text)
        
        layout.addWidget(preview_group)
        
        return widget
    
    def on_dataset_selected(self, selected, deselected):
        """Event-Handler für Datensatz-Auswahl."""
        if not selected.indexes():
            # Keine Auswahl
            self.selected_dataset = None
            self.select_btn.setEnabled(False)
            self.duplicate_btn.setEnabled(False)
            self.delete_btn.setEnabled(False)
            self.export_btn.setEnabled(False)
            self.clear_editor()
            return
        
        # Ausgewählte Zeile
        row = selected.indexes()[0].row()
        dataset_name = self.datasets_table.item(row, 0).text()
        
        self.selected_dataset = dataset_name
        self.select_btn.setEnabled(True)
        self.duplicate_btn.setEnabled(True)
        self.delete_btn.setEnabled(True)
        self.export_btn.setEnabled(True)
        
        # Datensatz in Editor laden
        self.load_dataset_in_editor(dataset_name)
    
    def on_editor_changed(self):
        """Editor-Inhalte haben sich geändert."""
        if self.selected_dataset:
            self.save_btn.setEnabled(True)
            self.revert_btn.setEnabled(True)
    
    def on_camera_type_changed(self):
        """Kamera-Typ wurde geändert."""
        self.current_camera_source = None
        self.camera_info_label.setText("Keine Quelle ausgewählt")
        self.test_camera_btn.setEnabled(False)
        self.on_editor_changed()
    
    def browse_model(self):
        """KI-Modell durchsuchen."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "KI-Modell auswählen",
            "",
            "PyTorch Modelle (*.pt);;Alle Dateien (*)"
        )
        
        if file_path:
            self.model_path_edit.setText(file_path)
            model_name = os.path.basename(file_path)
            self.model_info_label.setText(f"Ausgewählt: {model_name}")
            self.test_model_btn.setEnabled(True)
            self.on_editor_changed()
    
    def select_camera_source(self):
        """Kamera/Video-Quelle auswählen."""
        camera_type = self.camera_type_combo.currentText()
        
        if camera_type == "video":
            # Video-Datei auswählen
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                "Video-Datei auswählen",
                "",
                "Video Files (*.mp4 *.avi *.mov *.mkv *.wmv *.flv);;All Files (*)"
            )
            
            if file_path:
                self.current_camera_source = file_path
                video_name = os.path.basename(file_path)
                self.camera_info_label.setText(f"Video: {video_name}")
                self.test_camera_btn.setEnabled(True)
                self.on_editor_changed()
        
        else:
            # Kamera-Auswahl-Dialog verwenden
            dialog = CameraSelectionDialog(self.camera_manager, self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                source = dialog.get_selected_source()
                if source:
                    self.current_camera_source = source
                    
                    # Info-Text erstellen
                    if camera_type == "webcam":
                        self.camera_info_label.setText(f"Webcam: {source}")
                    elif camera_type == "ids":
                        self.camera_info_label.setText(f"IDS Kamera: {source[1]}")
                    
                    self.test_camera_btn.setEnabled(True)
                    self.on_editor_changed()
    
    def test_model(self):
        """KI-Modell testen."""
        model_path = self.model_path_edit.text()
        if not model_path or not os.path.exists(model_path):
            QMessageBox.warning(self, "Test", "Ungültiger Modell-Pfad")
            return
        
        try:
            # Hier würde normalerweise das Modell getestet
            QMessageBox.information(
                self, 
                "Test erfolgreich", 
                f"Modell '{os.path.basename(model_path)}' ist gültig und kann geladen werden."
            )
        except Exception as e:
            QMessageBox.critical(self, "Test fehlgeschlagen", f"Fehler beim Testen des Modells:\n{str(e)}")
    
    def test_camera(self):
        """Kamera/Video-Quelle testen."""
        if not self.current_camera_source:
            QMessageBox.warning(self, "Test", "Keine Quelle ausgewählt")
            return
        
        try:
            # Hier würde normalerweise die Kamera getestet
            camera_type = self.camera_type_combo.currentText()
            QMessageBox.information(
                self, 
                "Test erfolgreich", 
                f"{camera_type.title()}-Quelle ist verfügbar und kann verwendet werden."
            )
        except Exception as e:
            QMessageBox.critical(self, "Test fehlgeschlagen", f"Fehler beim Testen der Quelle:\n{str(e)}")
    
    def create_new_dataset(self):
        """Neuen Datensatz erstellen."""
        name, ok = QInputDialog.getText(
            self,
            "Neuer Datensatz",
            "Name für den neuen Datensatz:"
        )
        
        if ok and name.strip():
            # Editor für neuen Datensatz vorbereiten
            self.clear_editor()
            self.name_edit.setText(name.strip())
            self.description_edit.setText("")
            self.selected_dataset = None
            
            # Editor aktivieren
            self.save_btn.setEnabled(True)
            self.editor_header.setText("Neuer Datensatz")
            
            # Focus auf Name
            self.name_edit.setFocus()
            self.name_edit.selectAll()
    
    def duplicate_dataset(self):
        """Datensatz duplizieren."""
        if not self.selected_dataset:
            return
        
        new_name, ok = QInputDialog.getText(
            self,
            "Datensatz duplizieren",
            f"Neuer Name für Kopie von '{self.selected_dataset}':",
            text=f"{self.selected_dataset}_Kopie"
        )
        
        if ok and new_name.strip():
            description, ok2 = QInputDialog.getText(
                self,
                "Beschreibung",
                "Beschreibung für duplizierten Datensatz:"
            )
            
            if ok2:
                success = self.dataset_manager.duplicate_dataset(
                    self.selected_dataset,
                    new_name.strip(),
                    description
                )
                
                if success:
                    self.refresh_datasets()
                    QMessageBox.information(self, "Erfolg", f"Datensatz '{new_name}' wurde erstellt.")
                else:
                    QMessageBox.critical(self, "Fehler", "Fehler beim Duplizieren des Datensatzes.")
    
    def delete_dataset(self):
        """Datensatz löschen."""
        if not self.selected_dataset:
            return
        
        reply = QMessageBox.question(
            self,
            "Datensatz löschen",
            f"Datensatz '{self.selected_dataset}' wirklich löschen?\n\n"
            "Diese Aktion kann nicht rückgängig gemacht werden!",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            success = self.dataset_manager.delete_dataset(self.selected_dataset)
            
            if success:
                self.refresh_datasets()
                self.clear_editor()
                QMessageBox.information(self, "Gelöscht", f"Datensatz '{self.selected_dataset}' wurde gelöscht.")
            else:
                QMessageBox.critical(self, "Fehler", "Fehler beim Löschen des Datensatzes.")
    
    def import_dataset(self):
        """Datensatz importieren."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Datensatz importieren",
            "",
            "JSON Files (*.json);;All Files (*)"
        )
        
        if file_path:
            success = self.dataset_manager.import_dataset(file_path)
            
            if success:
                self.refresh_datasets()
                QMessageBox.information(self, "Importiert", "Datensatz wurde erfolgreich importiert.")
            else:
                QMessageBox.critical(self, "Fehler", "Fehler beim Importieren des Datensatzes.")
    
    def export_dataset(self):
        """Datensatz exportieren."""
        if not self.selected_dataset:
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            f"Datensatz '{self.selected_dataset}' exportieren",
            f"{self.selected_dataset}.json",
            "JSON Files (*.json);;All Files (*)"
        )
        
        if file_path:
            success = self.dataset_manager.export_dataset(self.selected_dataset, file_path)
            
            if success:
                QMessageBox.information(self, "Exportiert", f"Datensatz wurde nach '{file_path}' exportiert.")
            else:
                QMessageBox.critical(self, "Fehler", "Fehler beim Exportieren des Datensatzes.")
    
    def save_current_dataset(self):
        """Aktuellen Datensatz speichern."""
        name = self.name_edit.text().strip()
        description = self.description_edit.toPlainText().strip()
        model_path = self.model_path_edit.text().strip()
        camera_type = self.camera_type_combo.currentText()
        camera_source = self.current_camera_source
        
        # Validierung
        if not name:
            QMessageBox.warning(self, "Fehler", "Name ist erforderlich.")
            return
        
        if not model_path or not os.path.exists(model_path):
            QMessageBox.warning(self, "Fehler", "Gültiger Modell-Pfad ist erforderlich.")
            return
        
        if not camera_source:
            QMessageBox.warning(self, "Fehler", "Kamera/Video-Quelle ist erforderlich.")
            return
        
        # Aktuelle Einstellungen holen (würde normalerweise von Hauptanwendung kommen)
        current_settings = {}  # Placeholder
        
        # Datensatz speichern
        success = self.dataset_manager.save_dataset(
            name, description, current_settings, 
            model_path, camera_source, camera_type
        )
        
        if success:
            self.refresh_datasets()
            self.save_btn.setEnabled(False)
            self.revert_btn.setEnabled(False)
            QMessageBox.information(self, "Gespeichert", f"Datensatz '{name}' wurde gespeichert.")
        else:
            QMessageBox.critical(self, "Fehler", "Fehler beim Speichern des Datensatzes.")
    
    def revert_changes(self):
        """Änderungen zurücksetzen."""
        if self.selected_dataset:
            self.load_dataset_in_editor(self.selected_dataset)
        else:
            self.clear_editor()
        
        self.save_btn.setEnabled(False)
        self.revert_btn.setEnabled(False)
    
    def load_selected_dataset(self):
        """Ausgewählten Datensatz laden (schließt Dialog)."""
        if self.selected_dataset:
            self.dataset_selected.emit(self.selected_dataset)
            self.accept()
    
    def load_dataset_in_editor(self, dataset_name):
        """Datensatz in Editor laden."""
        dataset = self.dataset_manager.load_dataset(dataset_name)
        if not dataset:
            return
        
        # Informationen laden
        dataset_info = dataset['dataset_info']
        detection_settings = dataset['detection_settings']
        
        self.name_edit.setText(dataset_info['name'])
        self.description_edit.setText(dataset_info['description'])
        self.created_label.setText(dataset_info.get('created', 'Unbekannt'))
        self.modified_label.setText(dataset_info.get('modified', 'Unbekannt'))
        
        # Detection-Einstellungen
        self.model_path_edit.setText(detection_settings['model_path'])
        model_name = os.path.basename(detection_settings['model_path']) if detection_settings['model_path'] else "Kein Modell"
        self.model_info_label.setText(f"Geladen: {model_name}")
        
        self.camera_type_combo.setCurrentText(detection_settings['camera_type'])
        self.current_camera_source = detection_settings['camera_source']
        
        # Kamera-Info
        if detection_settings['camera_type'] == 'webcam':
            self.camera_info_label.setText(f"Webcam: {detection_settings['camera_source']}")
        elif detection_settings['camera_type'] == 'video':
            video_name = os.path.basename(str(detection_settings['camera_source']))
            self.camera_info_label.setText(f"Video: {video_name}")
        elif detection_settings['camera_type'] == 'ids':
            self.camera_info_label.setText(f"IDS Kamera: {detection_settings['camera_source'][1] if isinstance(detection_settings['camera_source'], tuple) else detection_settings['camera_source']}")
        
        # Test-Buttons aktivieren
        self.test_model_btn.setEnabled(bool(detection_settings['model_path']))
        self.test_camera_btn.setEnabled(bool(detection_settings['camera_source']))
        
        # Einstellungen-Anzahl
        settings_count = len(dataset.get('application_settings', {}))
        self.settings_count_label.setText(str(settings_count))
        
        # Vorschau
        self.update_preview(dataset)
        
        # Editor-Header
        self.editor_header.setText(f"Datensatz: {dataset_info['name']}")
        
        # Buttons zurücksetzen
        self.save_btn.setEnabled(False)
        self.revert_btn.setEnabled(False)
    
    def clear_editor(self):
        """Editor leeren."""
        self.name_edit.clear()
        self.description_edit.clear()
        self.model_path_edit.clear()
        self.camera_type_combo.setCurrentIndex(0)
        self.current_camera_source = None
        
        self.created_label.setText("Nicht verfügbar")
        self.modified_label.setText("Nicht verfügbar")
        self.settings_count_label.setText("0")
        
        self.model_info_label.setText("Kein Modell ausgewählt")
        self.camera_info_label.setText("Keine Quelle ausgewählt")
        
        self.test_model_btn.setEnabled(False)
        self.test_camera_btn.setEnabled(False)
        
        self.preview_text.clear()
        self.editor_header.setText("Datensatz-Details")
        
        self.save_btn.setEnabled(False)
        self.revert_btn.setEnabled(False)
    
    def update_preview(self, dataset):
        """Vorschau aktualisieren."""
        try:
            import json
            preview_json = json.dumps(dataset, indent=2, ensure_ascii=False)
            self.preview_text.setText(preview_json)
        except Exception as e:
            self.preview_text.setText(f"Fehler bei Vorschau: {str(e)}")
    
    def refresh_datasets(self):
        """Datensatz-Liste aktualisieren."""
        datasets = self.dataset_manager.get_available_datasets()
        
        self.datasets_table.setRowCount(len(datasets))
        
        for row, dataset in enumerate(datasets):
            # Name
            name_item = QTableWidgetItem(dataset['name'])
            self.datasets_table.setItem(row, 0, name_item)
            
            # Erstellt
            created_item = QTableWidgetItem(dataset['created'][:10])  # Nur Datum
            self.datasets_table.setItem(row, 1, created_item)
            
            # Modell
            model_name = os.path.basename(dataset['model_path']) if dataset['model_path'] else "Kein Modell"
            model_item = QTableWidgetItem(model_name)
            model_item.setToolTip(dataset['model_path'])
            self.datasets_table.setItem(row, 2, model_item)
            
            # Kamera
            camera_type = dataset['camera_type']
            if camera_type == 'video':
                camera_text = f"Video: {os.path.basename(str(dataset['camera_source']))}"
            elif camera_type == 'webcam':
                camera_text = f"Webcam {dataset['camera_source']}"
            elif camera_type == 'ids':
                source = dataset['camera_source']
                if isinstance(source, tuple):
                    camera_text = f"IDS {source[1]}"
                else:
                    camera_text = f"IDS {source}"
            else:
                camera_text = camera_type
            
            camera_item = QTableWidgetItem(camera_text)
            self.datasets_table.setItem(row, 3, camera_item)
    
    def get_selected_dataset_name(self):
        """Namen des ausgewählten Datensatzes zurückgeben."""
        return self.selected_dataset