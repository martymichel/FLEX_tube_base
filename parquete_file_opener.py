""" Standalone Parquet Viewer - Zum Anzeigen der Detection Event Logs Kann während der Anwendung läuft die Parquet-Dateien öffnen und anzeigen """
import sys
import pandas as pd
import json
from datetime import datetime
from PyQt6.QtWidgets import (QApplication, QMainWindow, QTableView, QVBoxLayout, QHBoxLayout,
QWidget, QPushButton, QLineEdit, QLabel, QComboBox, QStatusBar,
QHeaderView, QFileDialog, QMessageBox, QTextEdit, QSplitter,
QListWidget, QGroupBox, QFormLayout)
from PyQt6.QtCore import Qt, QSortFilterProxyModel, pyqtSignal
from PyQt6.QtGui import QStandardItemModel, QStandardItem, QFont

class DetailViewWidget(QWidget):
    """Widget zur Anzeige der Event-Details als formatierter JSON."""

    def __init__(self):
        super().__init__()
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Header
        header_label = QLabel("Event Details")
        header_label.setFont(QFont("", 12, QFont.Weight.Bold))
        layout.addWidget(header_label)
        
        # Text-Bereich für JSON-Details
        self.details_text = QTextEdit()
        self.details_text.setReadOnly(True)
        self.details_text.setFont(QFont("Consolas", 10))
        layout.addWidget(self.details_text)

    def update_details(self, details_json_str):
        """Details aus JSON-String anzeigen."""
        try:
            if details_json_str and details_json_str != '{}':
                details = json.loads(details_json_str)
                formatted_json = json.dumps(details, indent=2, ensure_ascii=False)
                self.details_text.setPlainText(formatted_json)
            else:
                self.details_text.setPlainText("Keine Details verfügbar")
        except json.JSONDecodeError:
            self.details_text.setPlainText(f"Ungültiges JSON:\n{details_json_str}")

class CustomProxyModel(QSortFilterProxyModel):
    """Erweiterte Proxy-Model für kombinierte Filter."""
    
    def __init__(self):
        super().__init__()
        self.event_type_filter = ""
        self.status_filter = ""
        self.search_filter = ""
        
    def setEventTypeFilter(self, text):
        self.event_type_filter = text
        self.invalidateFilter()
        
    def setStatusFilter(self, text):
        self.status_filter = text
        self.invalidateFilter()
        
    def setSearchFilter(self, text):
        self.search_filter = text
        self.invalidateFilter()
        
    def filterAcceptsRow(self, source_row, source_parent):
        model = self.sourceModel()
        
        # Event-Type Filter (Spalte 1)
        if self.event_type_filter and self.event_type_filter != "Alle":
            event_type_index = model.index(source_row, 1, source_parent)
            event_type_value = model.data(event_type_index, Qt.ItemDataRole.DisplayRole)
            if event_type_value != self.event_type_filter:
                return False
        
        # Status Filter (Spalte 3)
        if self.status_filter and self.status_filter != "Alle":
            status_index = model.index(source_row, 3, source_parent)
            status_value = model.data(status_index, Qt.ItemDataRole.DisplayRole)
            if status_value != self.status_filter:
                return False
        
        # Text-Suche in Nachrichten (Spalte 4)
        if self.search_filter:
            message_index = model.index(source_row, 4, source_parent)
            message_value = model.data(message_index, Qt.ItemDataRole.DisplayRole)
            if message_value and self.search_filter.lower() not in message_value.lower():
                return False
        
        return True
            
class ParquetViewer(QMainWindow):
    """Hauptfenster für Parquet Event Log Viewer."""

    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("Detection Event Log Viewer")
        # Fenster maximiert öffnen
        self.showMaximized()
        
        self.df = None
        self.model = QStandardItemModel()
        self.proxy_model = CustomProxyModel()
        self.proxy_model.setSourceModel(self.model)
        
        self.init_ui()
        
    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Hauptlayout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(5, 5, 5, 5)
        
        # Toolbar oben (maximal 40px hoch)
        toolbar_widget = self.create_toolbar()
        toolbar_widget.setMaximumHeight(40)
        main_layout.addWidget(toolbar_widget)
        
        # Horizontaler Splitter für Tabelle und Details (nimmt den Rest der Höhe)
        content_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Linke Seite: Filter + Tabelle
        left_widget = self.create_left_panel()
        content_splitter.addWidget(left_widget)
        
        # Rechte Seite: Detail-View (gesamte Höhe)
        self.detail_view = DetailViewWidget()
        content_splitter.addWidget(self.detail_view)
        
        # Splitter-Verhältnis setzen (70% links, 30% rechts)
        content_splitter.setSizes([1000, 400])
        
        main_layout.addWidget(content_splitter)
        
        # Status-Bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

    def create_toolbar(self):
        """Kompakte Toolbar mit nur Buttons und Dateiname (max 40px hoch)."""
        toolbar_widget = QWidget()
        toolbar_layout = QHBoxLayout(toolbar_widget)
        toolbar_layout.setContentsMargins(0, 0, 0, 0)
        
        self.open_button = QPushButton("📁 Datei öffnen")
        self.open_button.setFixedHeight(30)
        self.open_button.clicked.connect(self.open_file)
        toolbar_layout.addWidget(self.open_button)
        
        self.refresh_button = QPushButton("🔄 Aktualisieren")
        self.refresh_button.setFixedHeight(30)
        self.refresh_button.clicked.connect(self.refresh_current_file)
        toolbar_layout.addWidget(self.refresh_button)
        
        toolbar_layout.addStretch()
        
        # Info-Label für aktuelle Datei
        self.file_info_label = QLabel("Keine Datei geladen")
        self.file_info_label.setStyleSheet("color: #7f8c8d; font-style: italic;")
        toolbar_layout.addWidget(self.file_info_label)
        
        return toolbar_widget

    def create_left_panel(self):
        """Linkes Panel mit Filtern und Tabelle."""
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        # Filter-Zeile
        filter_layout = QHBoxLayout()
        
        filter_layout.addWidget(QLabel("Event-Typ:"))
        self.event_type_combo = QComboBox()
        self.event_type_combo.setMinimumWidth(200)
        self.event_type_combo.addItem("Alle")
        self.event_type_combo.currentTextChanged.connect(self.apply_filters)
        filter_layout.addWidget(self.event_type_combo)
        
        filter_layout.addWidget(QLabel("Status:"))
        self.status_combo = QComboBox()
        self.status_combo.setMinimumWidth(200)
        self.status_combo.addItem("Alle")
        self.status_combo.currentTextChanged.connect(self.apply_filters)
        filter_layout.addWidget(self.status_combo)
        
        filter_layout.addWidget(QLabel("Suche:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("In Nachrichten suchen...")
        self.search_input.textChanged.connect(self.apply_filters)
        filter_layout.addWidget(self.search_input)
        
        self.reset_button = QPushButton("❌ Filter zurücksetzen")
        self.reset_button.setFixedHeight(30)
        self.reset_button.clicked.connect(self.reset_filters)
        filter_layout.addWidget(self.reset_button)
        
        left_layout.addLayout(filter_layout)
        
        # Tabelle
        self.table_view = QTableView()
        self.table_view.setSortingEnabled(True)
        self.table_view.setAlternatingRowColors(True)
        self.table_view.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.table_view.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.table_view.horizontalHeader().setStretchLastSection(True)
        self.table_view.setModel(self.proxy_model)
        
        # Selection-Handler für Detail-View
        self.table_view.selectionModel().selectionChanged.connect(self.on_row_selected)
        
        left_layout.addWidget(self.table_view)
        
        return left_widget

    def open_file(self):
        """Parquet-Datei öffnen."""
        options = QFileDialog.Option.ReadOnly
        file_name, _ = QFileDialog.getOpenFileName(
            self, "Parquet Log-Datei öffnen", "", 
            "Parquet Files (*.parquet);;All Files (*)", 
            options=options
        )
        
        if file_name:
            self.load_file(file_name)

    def load_file(self, file_name):
        """Datei laden und anzeigen."""
        try:
            self.status_bar.showMessage(f"Lade Datei: {file_name}...")
            self.current_file = file_name
            
            # Parquet-Datei laden
            self.df = pd.read_parquet(file_name)
            
            # Timestamp-Spalte korrekt konvertieren
            if 'timestamp' in self.df.columns:
                self.df['timestamp'] = pd.to_datetime(self.df['timestamp'])
                # Nach Timestamp absteigend sortieren (neueste zuerst)
                self.df = self.df.sort_values('timestamp', ascending=False)
            
            self.display_data()
            
            rows, cols = self.df.shape
            self.status_bar.showMessage(f"Datei geladen: {rows} Events, {cols} Spalten")
            
            # Datei-Info aktualisieren
            import os
            file_size = os.path.getsize(file_name) / (1024 * 1024)  # MB
            self.file_info_label.setText(f"{os.path.basename(file_name)} ({file_size:.1f} MB, {rows} Events)")
            
        except Exception as e:
            QMessageBox.critical(self, "Fehler", f"Fehler beim Laden der Datei:\n{str(e)}")
            self.status_bar.showMessage("Fehler beim Laden der Datei")

    def refresh_current_file(self):
        """Aktuelle Datei neu laden."""
        if hasattr(self, 'current_file') and self.current_file:
            self.load_file(self.current_file)
        else:
            QMessageBox.information(self, "Info", "Keine Datei zum Aktualisieren ausgewählt")

    def display_data(self):
        """Daten in der Tabelle anzeigen."""
        if self.df is None:
            return
        
        # Modell zurücksetzen
        self.model.clear()
        
        # Spalten für bessere Lesbarkeit anpassen
        display_columns = ['timestamp', 'event_type', 'sub_type', 'status', 'message']
        if 'details_json' in self.df.columns:
            display_columns.append('details_json')
        
        # Nur relevante Spalten für Tabelle
        display_df = self.df[display_columns].copy()
        
        # Timestamp formatieren für bessere Lesbarkeit
        if 'timestamp' in display_df.columns:
            display_df['timestamp'] = display_df['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]  # Millisekunden
        
        # Header setzen
        self.model.setHorizontalHeaderLabels(display_df.columns)
        
        # Filter-Combos aktualisieren
        self.update_filter_combos()
        
        # Daten einfügen
        for row_idx, (_, row_data) in enumerate(display_df.iterrows()):
            items = []
            for val in row_data:
                item = QStandardItem()
                if pd.isna(val):
                    item.setText("")
                else:
                    # Details-JSON kürzen für Tabellen-Anzeige
                    if isinstance(val, str) and len(val) > 100:
                        display_text = val[:97] + "..."
                        item.setText(display_text)
                        item.setToolTip(val)  # Volltext als Tooltip
                    else:
                        item.setText(str(val))
                items.append(item)
            self.model.appendRow(items)

    def update_filter_combos(self):
        """Filter-ComboBoxen mit verfügbaren Werten aktualisieren."""
        if self.df is None:
            return
        
        # Event-Type Filter
        self.event_type_combo.clear()
        self.event_type_combo.addItem("Alle")
        if 'event_type' in self.df.columns:
            unique_types = sorted(self.df['event_type'].dropna().unique())
            self.event_type_combo.addItems(unique_types)
        
        # Status Filter
        self.status_combo.clear()
        self.status_combo.addItem("Alle")
        if 'status' in self.df.columns:
            unique_statuses = sorted(self.df['status'].dropna().unique())
            self.status_combo.addItems(unique_statuses)

    def apply_filters(self):
        """Filter auf die Tabelle anwenden - jetzt mit korrigierter Kombinationslogik."""
        if self.df is None:
            return
        
        # Alle Filter an das Proxy-Model übergeben
        event_type = self.event_type_combo.currentText()
        status = self.status_combo.currentText()
        search_text = self.search_input.text().strip()
        
        self.proxy_model.setEventTypeFilter(event_type)
        self.proxy_model.setStatusFilter(status)
        self.proxy_model.setSearchFilter(search_text)
        
        # Status-Meldung aktualisieren
        filtered_rows = self.proxy_model.rowCount()
        total_rows = self.model.rowCount()
        
        if event_type != "Alle" or status != "Alle" or search_text:
            self.status_bar.showMessage(f"Filter angewendet: {filtered_rows} von {total_rows} Events angezeigt")
        else:
            self.status_bar.showMessage(f"Alle {total_rows} Events angezeigt")

    def reset_filters(self):
        """Alle Filter zurücksetzen."""
        self.event_type_combo.setCurrentText("Alle")
        self.status_combo.setCurrentText("Alle")
        self.search_input.clear()
        
        # Filter am Proxy-Model zurücksetzen
        self.proxy_model.setEventTypeFilter("")
        self.proxy_model.setStatusFilter("")
        self.proxy_model.setSearchFilter("")
        
        if self.df is not None:
            total_rows = self.model.rowCount()
            self.status_bar.showMessage(f"Alle {total_rows} Events angezeigt")

    def on_row_selected(self, selected, deselected):
        """Event-Handler für Zeilen-Auswahl."""
        if not selected.indexes():
            return
        
        # Erste ausgewählte Zeile ermitteln
        source_index = self.proxy_model.mapToSource(selected.indexes()[0])
        row = source_index.row()
        
        # Details-JSON aus der ursprünglichen DataFrame holen
        if self.df is not None and 'details_json' in self.df.columns:
            # Row-Index in Original-DataFrame ermitteln
            # Da wir nach timestamp sortiert haben, müssen wir das berücksichtigen
            original_row_index = self.df.index[row]
            details_json = self.df.loc[original_row_index, 'details_json']
            self.detail_view.update_details(details_json)

def main():
    """Hauptfunktion für Standalone Parquet Viewer."""
    app = QApplication(sys.argv)
    window = ParquetViewer()
    window.show()

    # Startdatei automatisch laden, falls angegeben
    if len(sys.argv) > 1 and sys.argv[1].endswith('.parquet'):
        try:
            window.load_file(sys.argv[1])
        except Exception as e:
            print(f"Fehler beim Laden der angegebenen Datei: {str(e)}")

    sys.exit(app.exec())

if __name__ == "__main__":
    main()