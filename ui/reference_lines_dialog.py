"""
Referenzlinien-Einstellungen Dialog
Konfiguration von sichtbaren Referenzlinien im Video-Stream
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QTableWidget,
    QTableWidgetItem, QHeaderView, QPushButton, QComboBox,
    QSpinBox, QCheckBox, QMessageBox, QLabel, QFormLayout,
    QTabWidget, QTextEdit, QSlider
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor

class ReferenceLinesTab(QWidget):
    """Tab für Referenzlinien-Einstellungen."""
    
    def __init__(self, settings, parent=None):
        super().__init__(parent)
        self.settings = settings
        self.setup_ui()
    
    def setup_ui(self):
        """UI aufbauen."""
        layout = QVBoxLayout(self)
        
        # Tab Widget für Unterkategorien
        tab_widget = QTabWidget()
        layout.addWidget(tab_widget)
        
        # Linien-Konfiguration Tab
        lines_tab = self.create_lines_tab()
        tab_widget.addTab(lines_tab, "Linien")
        
        # Vorlagen Tab
        templates_tab = self.create_templates_tab()
        tab_widget.addTab(templates_tab, "Vorlagen")
        
        # Vorschau Tab
        preview_tab = self.create_preview_tab()
        tab_widget.addTab(preview_tab, "Vorschau")
    
    def create_lines_tab(self):
        """Linien-Konfiguration Tab erstellen."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Info-Label
        info_label = QLabel("Referenzlinien-Konfiguration:")
        info_label.setStyleSheet("font-weight: bold; margin: 5px;")
        layout.addWidget(info_label)
        
        # Linien-Tabelle
        self.lines_table = QTableWidget()
        self.lines_table.setColumnCount(6)
        self.lines_table.setHorizontalHeaderLabels([
            "Aktiviert", "Typ", "Position (%)", "Farbe", "Dicke", "Aktion"
        ])
        
        # Spaltenbreiten anpassen
        header = self.lines_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)
        
        layout.addWidget(self.lines_table)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.add_line_btn = QPushButton("➕ Linie hinzufügen")
        self.add_line_btn.clicked.connect(self.add_line)
        button_layout.addWidget(self.add_line_btn)
        
        self.remove_line_btn = QPushButton("➖ Linie entfernen")
        self.remove_line_btn.clicked.connect(self.remove_line)
        button_layout.addWidget(self.remove_line_btn)
        
        button_layout.addStretch()
        
        self.clear_all_btn = QPushButton("🗑️ Alle löschen")
        self.clear_all_btn.clicked.connect(self.clear_all_lines)
        button_layout.addWidget(self.clear_all_btn)
        
        layout.addLayout(button_layout)
        
        return widget
    
    def create_templates_tab(self):
        """Vorlagen Tab erstellen."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Standard-Vorlagen
        templates_group = QGroupBox("Standard-Vorlagen")
        templates_layout = QVBoxLayout(templates_group)
        
        # Vorlage-Buttons
        template_buttons = [
            ("🎯 Zentrierte Kreuzlinien", self.apply_cross_template),
            ("📐 Drittel-Regel", self.apply_thirds_template),
            ("🔲 Rahmen-Linien", self.apply_frame_template),
            ("⚖️ Symmetrie-Linien", self.apply_symmetry_template),
            ("📏 Mess-Linien", self.apply_measurement_template),
        ]
        
        for text, callback in template_buttons:
            btn = QPushButton(text)
            btn.clicked.connect(callback)
            templates_layout.addWidget(btn)
        
        layout.addWidget(templates_group)
        
        # Benutzerdefinierte Vorlagen
        custom_group = QGroupBox("Benutzerdefinierte Vorlagen")
        custom_layout = QVBoxLayout(custom_group)
        
        custom_buttons_layout = QHBoxLayout()
        
        self.save_template_btn = QPushButton("💾 Als Vorlage speichern")
        self.save_template_btn.clicked.connect(self.save_custom_template)
        custom_buttons_layout.addWidget(self.save_template_btn)
        
        self.load_template_btn = QPushButton("📁 Vorlage laden")
        self.load_template_btn.clicked.connect(self.load_custom_template)
        custom_buttons_layout.addWidget(self.load_template_btn)
        
        custom_layout.addLayout(custom_buttons_layout)
        
        # Template-Liste
        self.template_list = QTableWidget()
        self.template_list.setColumnCount(3)
        self.template_list.setHorizontalHeaderLabels(["Name", "Linien", "Aktion"])
        custom_layout.addWidget(self.template_list)
        
        layout.addWidget(custom_group)
        layout.addStretch()
        
        return widget
    
    def create_preview_tab(self):
        """Vorschau Tab erstellen."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Vorschau-Einstellungen
        preview_group = QGroupBox("Vorschau-Einstellungen")
        preview_layout = QFormLayout(preview_group)
        
        self.preview_enabled = QCheckBox("Live-Vorschau aktivieren")
        preview_layout.addRow(self.preview_enabled)
        
        self.preview_opacity = QSlider(Qt.Orientation.Horizontal)
        self.preview_opacity.setRange(0, 100)
        self.preview_opacity.setValue(80)
        preview_layout.addRow("Transparenz:", self.preview_opacity)
        
        layout.addWidget(preview_group)
        
        # Koordinaten-Info
        coords_group = QGroupBox("Koordinaten-Information")
        coords_layout = QVBoxLayout(coords_group)
        
        coords_text = QTextEdit()
        coords_text.setReadOnly(True)
        coords_text.setMaximumHeight(150)
        coords_text.setText("""
        Koordinaten-System:

        • Position: 0-100% der Bildbreite/höhe
        • Horizontal: 0% = oben, 100% = unten
        • Vertikal: 0% = links, 100% = rechts

        Beispiele:
        • Mittellinien: 50%
        • Drittel-Regel: 33% und 67%
        • Rand-Linien: 10% und 90%
        """)
        coords_layout.addWidget(coords_text)
        
        layout.addWidget(coords_group)
        
        # Farb-Information
        colors_group = QGroupBox("Verfügbare Farben")
        colors_layout = QVBoxLayout(colors_group)
        
        color_info = QTextEdit()
        color_info.setReadOnly(True)
        color_info.setMaximumHeight(100)
        color_info.setText("""
        Verfügbare Laser-Farben:
        red, green, blue, yellow, cyan, magenta, white, orange

        Alle Farben werden mit Glow-Effekt für bessere Sichtbarkeit dargestellt.
        """)
        colors_layout.addWidget(color_info)
        
        layout.addWidget(colors_group)
        layout.addStretch()
        
        return widget
    
    def add_line(self):
        """Neue Referenzlinie hinzufügen."""
        row = self.lines_table.rowCount()
        self.lines_table.insertRow(row)
        
        # Aktiviert-Checkbox
        enabled_check = QCheckBox()
        enabled_check.setChecked(True)
        self.lines_table.setCellWidget(row, 0, enabled_check)
        
        # Typ ComboBox
        type_combo = QComboBox()
        type_combo.addItems(["horizontal", "vertical"])
        self.lines_table.setCellWidget(row, 1, type_combo)
        
        # Position SpinBox
        position_spin = QSpinBox()
        position_spin.setRange(0, 100)
        position_spin.setValue(50)
        position_spin.setSuffix("%")
        self.lines_table.setCellWidget(row, 2, position_spin)
        
        # Farbe ComboBox
        color_combo = QComboBox()
        color_combo.addItems([
            "red", "green", "blue", "yellow", 
            "cyan", "magenta", "white", "orange"
        ])
        color_combo.setCurrentText("red")
        self.lines_table.setCellWidget(row, 3, color_combo)
        
        # Dicke SpinBox
        thickness_spin = QSpinBox()
        thickness_spin.setRange(1, 10)
        thickness_spin.setValue(2)
        thickness_spin.setSuffix("px")
        self.lines_table.setCellWidget(row, 4, thickness_spin)
        
        # Aktion Button
        action_btn = QPushButton("🗑️ Löschen")
        action_btn.clicked.connect(lambda: self.remove_line_by_button(row))
        self.lines_table.setCellWidget(row, 5, action_btn)
    
    def remove_line(self):
        """Ausgewählte Linie entfernen."""
        current_row = self.lines_table.currentRow()
        if current_row >= 0:
            self.lines_table.removeRow(current_row)
    
    def remove_line_by_button(self, row):
        """Linie über Button entfernen."""
        if 0 <= row < self.lines_table.rowCount():
            self.lines_table.removeRow(row)
            # Buttons neu verknüpfen
            self.refresh_action_buttons()
    
    def refresh_action_buttons(self):
        """Action-Buttons nach Zeilen-Änderung neu verknüpfen."""
        for row in range(self.lines_table.rowCount()):
            action_btn = self.lines_table.cellWidget(row, 5)
            if action_btn:
                # Alte Verbindung trennen und neue erstellen
                action_btn.clicked.disconnect()
                action_btn.clicked.connect(lambda checked, r=row: self.remove_line_by_button(r))
    
    def clear_all_lines(self):
        """Alle Linien löschen."""
        reply = QMessageBox.question(
            self,
            "Alle Linien löschen",
            "Alle Referenzlinien löschen?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.lines_table.setRowCount(0)
    
    def apply_cross_template(self):
        """Zentrierte Kreuzlinien-Vorlage anwenden."""
        self.lines_table.setRowCount(0)
        
        # Horizontale Mittellinie
        self.add_line()
        self.set_line_config(0, True, "horizontal", 50, "green", 2)
        
        # Vertikale Mittellinie
        self.add_line()
        self.set_line_config(1, True, "vertical", 50, "green", 2)
    
    def apply_thirds_template(self):
        """Drittel-Regel-Vorlage anwenden."""
        self.lines_table.setRowCount(0)
        
        # Horizontale Drittel-Linien
        self.add_line()
        self.set_line_config(0, True, "horizontal", 33, "blue", 1)
        
        self.add_line()
        self.set_line_config(1, True, "horizontal", 67, "blue", 1)
        
        # Vertikale Drittel-Linien
        self.add_line()
        self.set_line_config(2, True, "vertical", 33, "blue", 1)
        
        self.add_line()
        self.set_line_config(3, True, "vertical", 67, "blue", 1)
    
    def apply_frame_template(self):
        """Rahmen-Linien-Vorlage anwenden."""
        self.lines_table.setRowCount(0)
        
        # Rahmen-Linien
        positions = [10, 90]
        for pos in positions:
            # Horizontal
            self.add_line()
            self.set_line_config(len(positions) * 2 - 2 + positions.index(pos), True, "horizontal", pos, "yellow", 1)
            
            # Vertikal
            self.add_line()
            self.set_line_config(len(positions) * 2 - 1 + positions.index(pos), True, "vertical", pos, "yellow", 1)
    
    def apply_symmetry_template(self):
        """Symmetrie-Linien-Vorlage anwenden."""
        self.lines_table.setRowCount(0)
        
        # Symmetrie-Linien (25%, 50%, 75%)
        positions = [25, 50, 75]
        colors = ["cyan", "white", "cyan"]
        
        for i, (pos, color) in enumerate(zip(positions, colors)):
            # Horizontal
            self.add_line()
            self.set_line_config(i * 2, True, "horizontal", pos, color, 1)
            
            # Vertikal
            self.add_line()
            self.set_line_config(i * 2 + 1, True, "vertical", pos, color, 1)
    
    def apply_measurement_template(self):
        """Mess-Linien-Vorlage anwenden."""
        self.lines_table.setRowCount(0)
        
        # Mess-Linien mit verschiedenen Abständen
        h_positions = [20, 40, 60, 80]
        v_positions = [15, 30, 70, 85]
        
        for pos in h_positions:
            self.add_line()
            row = self.lines_table.rowCount() - 1
            self.set_line_config(row, True, "horizontal", pos, "orange", 1)
        
        for pos in v_positions:
            self.add_line()
            row = self.lines_table.rowCount() - 1
            self.set_line_config(row, True, "vertical", pos, "orange", 1)
    
    def set_line_config(self, row, enabled, line_type, position, color, thickness):
        """Linien-Konfiguration für bestimmte Zeile setzen."""
        if row < self.lines_table.rowCount():
            # Enabled
            enabled_widget = self.lines_table.cellWidget(row, 0)
            if enabled_widget:
                enabled_widget.setChecked(enabled)
            
            # Type
            type_widget = self.lines_table.cellWidget(row, 1)
            if type_widget:
                type_widget.setCurrentText(line_type)
            
            # Position
            pos_widget = self.lines_table.cellWidget(row, 2)
            if pos_widget:
                pos_widget.setValue(position)
            
            # Color
            color_widget = self.lines_table.cellWidget(row, 3)
            if color_widget:
                color_widget.setCurrentText(color)
            
            # Thickness
            thick_widget = self.lines_table.cellWidget(row, 4)
            if thick_widget:
                thick_widget.setValue(thickness)
    
    def save_custom_template(self):
        """Aktuelle Konfiguration als Vorlage speichern."""
        # Implementierung für benutzerdefinierte Vorlagen
        QMessageBox.information(self, "Vorlage", "Funktion wird in zukünftiger Version implementiert.")
    
    def load_custom_template(self):
        """Benutzerdefinierte Vorlage laden."""
        # Implementierung für benutzerdefinierte Vorlagen
        QMessageBox.information(self, "Vorlage", "Funktion wird in zukünftiger Version implementiert.")
    
    def load_settings(self):
        """Einstellungen laden."""
        reference_lines = self.settings.get('reference_lines', [])
        
        # Tabelle leeren
        self.lines_table.setRowCount(0)
        
        # Linien aus Einstellungen laden
        for line_config in reference_lines:
            self.add_line()
            row = self.lines_table.rowCount() - 1
            
            enabled = line_config.get('enabled', False)
            line_type = line_config.get('type', 'horizontal')
            position = line_config.get('position', 50)
            color = line_config.get('color', 'red')
            thickness = line_config.get('thickness', 2)
            
            self.set_line_config(row, enabled, line_type, position, color, thickness)
    
    def save_settings(self):
        """Einstellungen speichern."""
        reference_lines = []
        
        for row in range(self.lines_table.rowCount()):
            enabled_widget = self.lines_table.cellWidget(row, 0)
            type_widget = self.lines_table.cellWidget(row, 1)
            pos_widget = self.lines_table.cellWidget(row, 2)
            color_widget = self.lines_table.cellWidget(row, 3)
            thick_widget = self.lines_table.cellWidget(row, 4)
            
            if all([enabled_widget, type_widget, pos_widget, color_widget, thick_widget]):
                line_config = {
                    'enabled': enabled_widget.isChecked(),
                    'type': type_widget.currentText(),
                    'position': pos_widget.value(),
                    'color': color_widget.currentText(),
                    'thickness': thick_widget.value()
                }
                reference_lines.append(line_config)
        
        self.settings.set('reference_lines', reference_lines)