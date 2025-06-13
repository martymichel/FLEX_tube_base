"""
Klassen-Konfiguration Dialog
KI-Modell Klassen-Zuordnungen, Farben und Schwellenwerte
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QTableWidget,
    QTableWidgetItem, QHeaderView, QPushButton, QComboBox,
    QSpinBox, QDoubleSpinBox, QColorDialog, QMessageBox,
    QLabel, QFormLayout, QCheckBox, QTabWidget
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QPixmap, QPainter

class ClassConfigurationTab(QWidget):
    """Tab für Klassen-Konfiguration."""
    
    def __init__(self, settings, class_names=None, parent=None):
        super().__init__(parent)
        self.settings = settings
        self.class_names = class_names or {}
        self.setup_ui()
    
    def setup_ui(self):
        """UI aufbauen."""
        layout = QVBoxLayout(self)
        
        # Tab Widget für Unterkategorien
        tab_widget = QTabWidget()
        layout.addWidget(tab_widget)
        
        # Klassen-Zuordnung Tab
        assignment_tab = self.create_assignment_tab()
        tab_widget.addTab(assignment_tab, "Zuordnungen")
        
        # Farben Tab
        colors_tab = self.create_colors_tab()
        tab_widget.addTab(colors_tab, "Farben")
        
        # Schwellenwerte Tab
        thresholds_tab = self.create_thresholds_tab()
        tab_widget.addTab(thresholds_tab, "Schwellenwerte")
        
        # Legacy Tab
        legacy_tab = self.create_legacy_tab()
        tab_widget.addTab(legacy_tab, "Legacy-Modus")
    
    def create_assignment_tab(self):
        """Klassen-Zuordnung Tab erstellen."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Info-Label
        info_label = QLabel("Klassen-Zuordnungen konfigurieren:")
        info_label.setStyleSheet("font-weight: bold; margin: 5px;")
        layout.addWidget(info_label)
        
        # Klassen-Tabelle
        self.class_table = QTableWidget()
        self.class_table.setColumnCount(5)
        self.class_table.setHorizontalHeaderLabels([
            "Klasse", "Zuordnung", "Erwartete Anzahl", "Min. Konfidenz", "Farbe"
        ])
        
        # Spaltenbreiten anpassen
        header = self.class_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        
        layout.addWidget(self.class_table)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.add_class_btn = QPushButton("➕ Klasse hinzufügen")
        self.add_class_btn.clicked.connect(self.add_class)
        button_layout.addWidget(self.add_class_btn)
        
        self.remove_class_btn = QPushButton("➖ Klasse entfernen")
        self.remove_class_btn.clicked.connect(self.remove_class)
        button_layout.addWidget(self.remove_class_btn)
        
        button_layout.addStretch()
        
        self.refresh_btn = QPushButton("🔄 Vom Modell laden")
        self.refresh_btn.clicked.connect(self.refresh_from_model)
        button_layout.addWidget(self.refresh_btn)
        
        layout.addLayout(button_layout)
        
        return widget
    
    def create_colors_tab(self):
        """Farben Tab erstellen."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Standard-Farben
        colors_group = QGroupBox("Standard-Farbschema")
        colors_layout = QVBoxLayout(colors_group)
        
        scheme_layout = QHBoxLayout()
        
        self.color_scheme_combo = QComboBox()
        self.color_scheme_combo.addItems([
            "Standard (Rot/Grün/Blau)",
            "Industrie (Orange/Blau)",
            "Hochkontrast (Schwarz/Weiß)",
            "Benutzerdefiniert"
        ])
        self.color_scheme_combo.currentTextChanged.connect(self.apply_color_scheme)
        scheme_layout.addWidget(QLabel("Farbschema:"))
        scheme_layout.addWidget(self.color_scheme_combo)
        scheme_layout.addStretch()
        
        colors_layout.addLayout(scheme_layout)
        
        # Farb-Vorschau
        self.color_preview = QLabel()
        self.color_preview.setMinimumHeight(50)
        self.color_preview.setStyleSheet("border: 1px solid gray; border-radius: 4px;")
        colors_layout.addWidget(self.color_preview)
        
        layout.addWidget(colors_group)
        
        # Individuelle Farbzuordnung
        individual_group = QGroupBox("Individuelle Farbzuordnung")
        individual_layout = QVBoxLayout(individual_group)
        
        self.color_table = QTableWidget()
        self.color_table.setColumnCount(3)
        self.color_table.setHorizontalHeaderLabels(["Klasse", "Aktuelle Farbe", "Aktion"])
        individual_layout.addWidget(self.color_table)
        
        layout.addWidget(individual_group)
        layout.addStretch()
        
        return widget
    
    def create_thresholds_tab(self):
        """Schwellenwerte Tab erstellen."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Globale Schwellenwerte
        global_group = QGroupBox("Globale Schwellenwerte")
        global_layout = QFormLayout(global_group)
        
        self.global_confidence = QDoubleSpinBox()
        self.global_confidence.setRange(0.0, 1.0)
        self.global_confidence.setSingleStep(0.05)
        self.global_confidence.setValue(0.5)
        global_layout.addRow("Standard-Konfidenz:", self.global_confidence)
        
        self.red_threshold = QSpinBox()
        self.red_threshold.setRange(0, 100)
        self.red_threshold.setValue(1)
        global_layout.addRow("Roter Rahmen ab:", self.red_threshold)
        
        self.green_threshold = QSpinBox()
        self.green_threshold.setRange(0, 100)
        self.green_threshold.setValue(4)
        global_layout.addRow("Grüner Rahmen ab:", self.green_threshold)
        
        layout.addWidget(global_group)
        
        # Klassen-spezifische Schwellenwerte
        specific_group = QGroupBox("Klassen-spezifische Schwellenwerte")
        specific_layout = QVBoxLayout(specific_group)
        
        self.threshold_table = QTableWidget()
        self.threshold_table.setColumnCount(4)
        self.threshold_table.setHorizontalHeaderLabels([
            "Klasse", "Min. Konfidenz", "Erwartete Anzahl", "Toleranz"
        ])
        specific_layout.addWidget(self.threshold_table)
        
        layout.addWidget(specific_group)
        layout.addStretch()
        
        return widget
    
    def create_legacy_tab(self):
        """Legacy-Modus Tab erstellen."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Legacy-Info
        info_group = QGroupBox("Legacy-Modus")
        info_layout = QVBoxLayout(info_group)
        
        info_label = QLabel("""
        <b>Legacy-Modus:</b> Kompatibilität mit älteren Konfigurationen
        
        Wenn aktiviert, werden die alten Einstellungen verwendet:
        • bad_part_classes: Klassen-IDs für schlechte Teile
        • good_part_classes: Klassen-IDs für gute Teile
        • class_colors: Einfache Farbzuordnung
        
        <i>Empfehlung: Migrieren Sie zur neuen Klassen-Konfiguration für erweiterte Funktionen.</i>
        """)
        info_label.setWordWrap(True)
        info_layout.addWidget(info_label)
        
        layout.addWidget(info_group)
        
        # Legacy-Einstellungen
        legacy_group = QGroupBox("Legacy-Einstellungen")
        legacy_layout = QFormLayout(legacy_group)
        
        self.use_legacy = QCheckBox("Legacy-Modus verwenden")
        self.use_legacy.toggled.connect(self.on_legacy_toggled)
        legacy_layout.addRow(self.use_legacy)
        
        self.legacy_bad_classes = QLineEdit()
        self.legacy_bad_classes.setPlaceholderText("z.B. 1,2,3")
        legacy_layout.addRow("Schlechte Klassen:", self.legacy_bad_classes)
        
        self.legacy_good_classes = QLineEdit()
        self.legacy_good_classes.setPlaceholderText("z.B. 0,4,5")
        legacy_layout.addRow("Gute Klassen:", self.legacy_good_classes)
        
        self.legacy_confidence = QDoubleSpinBox()
        self.legacy_confidence.setRange(0.0, 1.0)
        self.legacy_confidence.setSingleStep(0.05)
        legacy_layout.addRow("Mindest-Konfidenz:", self.legacy_confidence)
        
        # Migration-Button
        self.migrate_btn = QPushButton("🔄 Zu neuer Konfiguration migrieren")
        self.migrate_btn.clicked.connect(self.migrate_to_new_config)
        legacy_layout.addRow(self.migrate_btn)
        
        layout.addWidget(legacy_group)
        layout.addStretch()
        
        return widget
    
    def add_class(self):
        """Neue Klasse hinzufügen."""
        row = self.class_table.rowCount()
        self.class_table.insertRow(row)
        
        # Standard-Werte setzen
        class_id_item = QTableWidgetItem(str(row))
        self.class_table.setItem(row, 0, class_id_item)
        
        # Zuordnung ComboBox
        assignment_combo = QComboBox()
        assignment_combo.addItems(["good", "bad", "ignore"])
        self.class_table.setCellWidget(row, 1, assignment_combo)
        
        # Erwartete Anzahl
        count_spin = QSpinBox()
        count_spin.setRange(-1, 1000)
        count_spin.setValue(-1)  # -1 = beliebige Anzahl
        self.class_table.setCellWidget(row, 2, count_spin)
        
        # Min. Konfidenz
        conf_spin = QDoubleSpinBox()
        conf_spin.setRange(0.0, 1.0)
        conf_spin.setSingleStep(0.05)
        conf_spin.setValue(0.5)
        self.class_table.setCellWidget(row, 3, conf_spin)
        
        # Farb-Button
        color_btn = QPushButton("Farbe wählen")
        color_btn.clicked.connect(lambda: self.choose_color(row))
        self.class_table.setCellWidget(row, 4, color_btn)
    
    def remove_class(self):
        """Ausgewählte Klasse entfernen."""
        current_row = self.class_table.currentRow()
        if current_row >= 0:
            self.class_table.removeRow(current_row)
    
    def choose_color(self, row):
        """Farbe für Klasse wählen."""
        color = QColorDialog.getColor(QColor("#FF0000"), self, "Farbe wählen")
        if color.isValid():
            button = self.class_table.cellWidget(row, 4)
            if button:
                # Button-Farbe ändern
                button.setStyleSheet(f"background-color: {color.name()}; color: white;")
                button.setText(color.name())
    
    def apply_color_scheme(self, scheme_name):
        """Farbschema anwenden."""
        schemes = {
            "Standard (Rot/Grün/Blau)": ["#FF0000", "#00FF00", "#0000FF", "#FFFF00", "#FF00FF"],
            "Industrie (Orange/Blau)": ["#FF8C00", "#1E90FF", "#FF4500", "#00BFFF", "#FFA500"],
            "Hochkontrast (Schwarz/Weiß)": ["#000000", "#FFFFFF", "#808080", "#C0C0C0", "#404040"],
        }
        
        if scheme_name in schemes:
            colors = schemes[scheme_name]
            # Hier würden die Farben auf die Klassen angewendet
            self.update_color_preview(colors)
    
    def update_color_preview(self, colors):
        """Farb-Vorschau aktualisieren."""
        pixmap = QPixmap(300, 40)
        painter = QPainter(pixmap)
        
        width_per_color = 300 // len(colors)
        for i, color in enumerate(colors):
            painter.fillRect(i * width_per_color, 0, width_per_color, 40, QColor(color))
        
        painter.end()
        self.color_preview.setPixmap(pixmap)
    
    def refresh_from_model(self):
        """Klassen vom geladenen Modell aktualisieren."""
        if self.class_names:
            # Tabelle leeren
            self.class_table.setRowCount(0)
            
            # Klassen aus Modell hinzufügen
            for class_id, class_name in self.class_names.items():
                row = self.class_table.rowCount()
                self.class_table.insertRow(row)
                
                # Klassen-Name
                name_item = QTableWidgetItem(f"{class_id}: {class_name}")
                self.class_table.setItem(row, 0, name_item)
                
                # Standard-Zuordnung
                assignment_combo = QComboBox()
                assignment_combo.addItems(["good", "bad", "ignore"])
                self.class_table.setCellWidget(row, 1, assignment_combo)
                
                # Standard-Werte
                count_spin = QSpinBox()
                count_spin.setRange(-1, 1000)
                count_spin.setValue(-1)
                self.class_table.setCellWidget(row, 2, count_spin)
                
                conf_spin = QDoubleSpinBox()
                conf_spin.setRange(0.0, 1.0)
                conf_spin.setSingleStep(0.05)
                conf_spin.setValue(0.5)
                self.class_table.setCellWidget(row, 3, conf_spin)
                
                color_btn = QPushButton("Farbe wählen")
                color_btn.clicked.connect(lambda checked, r=row: self.choose_color(r))
                self.class_table.setCellWidget(row, 4, color_btn)
        else:
            QMessageBox.information(self, "Info", "Keine Klassen vom Modell verfügbar.\nBitte laden Sie zuerst ein KI-Modell.")
    
    def on_legacy_toggled(self, enabled):
        """Legacy-Modus umschalten."""
        # Legacy-Felder aktivieren/deaktivieren
        self.legacy_bad_classes.setEnabled(enabled)
        self.legacy_good_classes.setEnabled(enabled)
        self.legacy_confidence.setEnabled(enabled)
        
        # Neue Konfiguration deaktivieren wenn Legacy aktiv
        if hasattr(self, 'class_table'):
            self.class_table.setEnabled(not enabled)
    
    def migrate_to_new_config(self):
        """Von Legacy zu neuer Konfiguration migrieren."""
        reply = QMessageBox.question(
            self,
            "Migration",
            "Legacy-Einstellungen zur neuen Konfiguration migrieren?\n\n"
            "Dies wird die aktuellen Klassen-Zuordnungen überschreiben.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # Migration durchführen
            self.settings.migrate_legacy_settings()
            self.load_settings()
            QMessageBox.information(self, "Migration", "Migration erfolgreich abgeschlossen!")
    
    def load_settings(self):
        """Einstellungen laden."""
        # Legacy-Einstellungen
        bad_classes = self.settings.get('bad_part_classes', [])
        good_classes = self.settings.get('good_part_classes', [])
        
        self.legacy_bad_classes.setText(','.join(map(str, bad_classes)))
        self.legacy_good_classes.setText(','.join(map(str, good_classes)))
        self.legacy_confidence.setValue(self.settings.get('bad_part_min_confidence', 0.5))
        
        # Globale Schwellenwerte
        self.global_confidence.setValue(self.settings.get('confidence_threshold', 0.5))
        self.red_threshold.setValue(self.settings.get('red_threshold', 1))
        self.green_threshold.setValue(self.settings.get('green_threshold', 4))
        
        # Neue Klassen-Konfiguration laden
        class_assignments = self.settings.get('class_assignments', {})
        self.load_class_assignments(class_assignments)
    
    def load_class_assignments(self, assignments):
        """Klassen-Zuordnungen in Tabelle laden."""
        self.class_table.setRowCount(0)
        
        for class_id, config in assignments.items():
            row = self.class_table.rowCount()
            self.class_table.insertRow(row)
            
            # Klasse
            class_name = self.class_names.get(int(class_id), f"Klasse {class_id}")
            name_item = QTableWidgetItem(f"{class_id}: {class_name}")
            self.class_table.setItem(row, 0, name_item)
            
            # Zuordnung
            assignment_combo = QComboBox()
            assignment_combo.addItems(["good", "bad", "ignore"])
            assignment_combo.setCurrentText(config.get('assignment', 'good'))
            self.class_table.setCellWidget(row, 1, assignment_combo)
            
            # Erwartete Anzahl
            count_spin = QSpinBox()
            count_spin.setRange(-1, 1000)
            count_spin.setValue(config.get('expected_count', -1))
            self.class_table.setCellWidget(row, 2, count_spin)
            
            # Min. Konfidenz
            conf_spin = QDoubleSpinBox()
            conf_spin.setRange(0.0, 1.0)
            conf_spin.setSingleStep(0.05)
            conf_spin.setValue(config.get('min_confidence', 0.5))
            self.class_table.setCellWidget(row, 3, conf_spin)
            
            # Farbe
            color = config.get('color', '#FF0000')
            color_btn = QPushButton(color)
            color_btn.setStyleSheet(f"background-color: {color}; color: white;")
            color_btn.clicked.connect(lambda checked, r=row: self.choose_color(r))
            self.class_table.setCellWidget(row, 4, color_btn)
    
    def save_settings(self):
        """Einstellungen speichern."""
        # Legacy-Einstellungen
        try:
            bad_classes = [int(x.strip()) for x in self.legacy_bad_classes.text().split(',') if x.strip()]
            good_classes = [int(x.strip()) for x in self.legacy_good_classes.text().split(',') if x.strip()]
        except ValueError:
            bad_classes = []
            good_classes = []
        
        self.settings.set('bad_part_classes', bad_classes)
        self.settings.set('good_part_classes', good_classes)
        self.settings.set('bad_part_min_confidence', self.legacy_confidence.value())
        
        # Globale Schwellenwerte
        self.settings.set('confidence_threshold', self.global_confidence.value())
        self.settings.set('red_threshold', self.red_threshold.value())
        self.settings.set('green_threshold', self.green_threshold.value())
        
        # Neue Klassen-Konfiguration
        class_assignments = {}
        for row in range(self.class_table.rowCount()):
            class_item = self.class_table.item(row, 0)
            if class_item:
                class_text = class_item.text()
                class_id = class_text.split(':')[0]
                
                assignment_combo = self.class_table.cellWidget(row, 1)
                count_spin = self.class_table.cellWidget(row, 2)
                conf_spin = self.class_table.cellWidget(row, 3)
                color_btn = self.class_table.cellWidget(row, 4)
                
                if all([assignment_combo, count_spin, conf_spin, color_btn]):
                    class_assignments[class_id] = {
                        'assignment': assignment_combo.currentText(),
                        'expected_count': count_spin.value(),
                        'min_confidence': conf_spin.value(),
                        'color': color_btn.text() if color_btn.text().startswith('#') else '#FF0000'
                    }
        
        self.settings.set('class_assignments', class_assignments)