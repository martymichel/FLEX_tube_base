"""
Modbus-Einstellungen Tab
WAGO-Steuerung und Modbus-Kommunikation
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QFormLayout,
    QLineEdit, QSpinBox, QDoubleSpinBox, QPushButton, QLabel,
    QCheckBox, QMessageBox, QTextEdit, QTabWidget
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

class ModbusSettingsTab(QWidget):
    """Tab für Modbus-Einstellungen."""
    
    def __init__(self, settings, parent=None):
        super().__init__(parent)
        self.settings = settings
        self.setup_ui()
    
    def setup_ui(self):
        """UI aufbauen."""
        layout = QVBoxLayout(self)
        
        # Modbus aktiviert
        self.modbus_enabled = QCheckBox("Modbus-Kommunikation aktivieren")
        self.modbus_enabled.toggled.connect(self.on_modbus_enabled_changed)
        layout.addWidget(self.modbus_enabled)
        
        # Tab Widget für Unterkategorien
        tab_widget = QTabWidget()
        layout.addWidget(tab_widget)
        
        # Verbindung Tab
        connection_tab = self.create_connection_tab()
        tab_widget.addTab(connection_tab, "Verbindung")
        
        # Watchdog Tab
        watchdog_tab = self.create_watchdog_tab()
        tab_widget.addTab(watchdog_tab, "Watchdog")
        
        # Coils Tab
        coils_tab = self.create_coils_tab()
        tab_widget.addTab(coils_tab, "Ausgänge")
        
        # Test Tab
        test_tab = self.create_test_tab()
        tab_widget.addTab(test_tab, "Test")
        
        # Modbus-Container für Enable/Disable
        self.modbus_container = tab_widget
        
        layout.addStretch()
    
    def create_connection_tab(self):
        """Verbindungs-Tab erstellen."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Verbindungseinstellungen
        connection_group = QGroupBox("WAGO-Verbindung")
        connection_layout = QFormLayout(connection_group)
        
        self.modbus_ip = QLineEdit()
        self.modbus_ip.setPlaceholderText("192.168.1.100")
        connection_layout.addRow("IP-Adresse:", self.modbus_ip)
        
        self.modbus_port = QSpinBox()
        self.modbus_port.setRange(1, 65535)
        self.modbus_port.setValue(502)
        connection_layout.addRow("Port:", self.modbus_port)
        
        layout.addWidget(connection_group)
        
        # Verbindungsstatus
        status_group = QGroupBox("Status")
        status_layout = QVBoxLayout(status_group)
        
        # Status-Label
        self.connection_status = QLabel("Verbindungsstatus: Unbekannt")
        self.connection_status.setStyleSheet("""
            QLabel {
                padding: 8px;
                border-radius: 4px;
                background-color: #7f8c8d;
                color: white;
                font-weight: bold;
            }
        """)
        status_layout.addWidget(self.connection_status)
        
        # Test-Buttons
        test_layout = QHBoxLayout()
        
        self.test_connection_btn = QPushButton("🔗 Verbindung testen")
        self.test_connection_btn.clicked.connect(self.test_connection)
        test_layout.addWidget(self.test_connection_btn)
        
        self.force_reconnect_btn = QPushButton("🔄 Neuverbindung erzwingen")
        self.force_reconnect_btn.clicked.connect(self.force_reconnect)
        test_layout.addWidget(self.force_reconnect_btn)
        
        status_layout.addLayout(test_layout)
        
        layout.addWidget(status_group)
        
        # WAGO Info
        info_group = QGroupBox("WAGO 750-362 Information")
        info_layout = QVBoxLayout(info_group)
        
        info_text = QTextEdit()
        info_text.setReadOnly(True)
        info_text.setMaximumHeight(120)
        info_text.setText("""
        WAGO 750-362 Controller Features:
        • Modbus/TCP Server auf Port 502
        • Watchdog-Funktionalität mit automatischem Reset
        • Digitale Ein-/Ausgänge über Modbus-Coils
        • Reset-Funktion über Register 0x2040
        • Watchdog-Konfiguration über Register 0x1000-0x1009
        """)
        info_layout.addWidget(info_text)
        
        layout.addWidget(info_group)
        layout.addStretch()
        
        return widget
    
    def create_watchdog_tab(self):
        """Watchdog-Tab erstellen."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Watchdog-Einstellungen
        watchdog_group = QGroupBox("Watchdog-Konfiguration")
        watchdog_layout = QFormLayout(watchdog_group)
        
        self.watchdog_timeout = QSpinBox()
        self.watchdog_timeout.setRange(1, 3600)
        self.watchdog_timeout.setSuffix(" Sekunden")
        self.watchdog_timeout.setValue(5)
        watchdog_layout.addRow("Timeout:", self.watchdog_timeout)
        
        self.watchdog_interval = QSpinBox()
        self.watchdog_interval.setRange(1, 300)
        self.watchdog_interval.setSuffix(" Sekunden")
        self.watchdog_interval.setValue(2)
        watchdog_layout.addRow("Trigger-Intervall:", self.watchdog_interval)
        
        layout.addWidget(watchdog_group)
        
        # Watchdog-Info
        info_group = QGroupBox("Funktionsweise")
        info_layout = QVBoxLayout(info_group)
        
        info_text = QTextEdit()
        info_text.setReadOnly(True)
        info_text.setMaximumHeight(150)
        info_text.setText("""
        Der Watchdog überwacht die Modbus-Verbindung:

        1. Timeout: Maximale Zeit ohne Kommunikation (empfohlen: 5-10 Sekunden)
        2. Trigger-Intervall: Wie oft der Watchdog "gefüttert" wird (empfohlen: halbe Timeout-Zeit)
        3. Bei Timeout: Automatischer Reset der WAGO-Steuerung
        4. Neustart: Automatische Neuverbindung nach Reset

        ⚠️ Vorsicht: Kurze Timeouts können zu häufigen Resets führen!
        """)
        info_layout.addWidget(info_text)
        
        layout.addWidget(info_group)
        layout.addStretch()
        
        return widget
    
    def create_coils_tab(self):
        """Coils-Tab erstellen."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Coil-Adressen
        coils_group = QGroupBox("Digitale Ausgänge (Coils)")
        coils_layout = QFormLayout(coils_group)
        
        self.reject_coil_address = QSpinBox()
        self.reject_coil_address.setRange(0, 9999)
        self.reject_coil_address.setValue(0)
        coils_layout.addRow("Ausschuss-Signal (Coil):", self.reject_coil_address)
        
        self.detection_active_coil = QSpinBox()
        self.detection_active_coil.setRange(0, 9999)
        self.detection_active_coil.setValue(1)
        coils_layout.addRow("Detection Active (Coil):", self.detection_active_coil)
        
        self.reject_duration = QDoubleSpinBox()
        self.reject_duration.setRange(0.1, 60.0)
        self.reject_duration.setSingleStep(0.1)
        self.reject_duration.setSuffix(" Sekunden")
        self.reject_duration.setValue(1.0)
        coils_layout.addRow("Ausschuss-Signal Dauer:", self.reject_duration)
        
        layout.addWidget(coils_group)
        
        # Coil-Zuordnung
        mapping_group = QGroupBox("Coil-Zuordnung")
        mapping_layout = QVBoxLayout(mapping_group)
        
        mapping_text = QTextEdit()
        mapping_text.setReadOnly(True)
        mapping_text.setMaximumHeight(120)
        mapping_text.setText("""
        Coil 0: Ausschuss-Signal (Reject)
        → Wird aktiviert wenn schlechte Teile erkannt werden
        → Automatisches Ausschalten nach eingestellter Dauer

        Coil 1: Detection Active
        → Zeigt an, dass die KI-Erkennung aktiv ist
        → Bleibt aktiv während der gesamten Detection-Phase

        Weitere Coils können für spezielle Anwendungen konfiguriert werden.
        """)
        mapping_layout.addWidget(mapping_text)
        
        layout.addWidget(mapping_group)
        layout.addStretch()
        
        return widget
    
    def create_test_tab(self):
        """Test-Tab erstellen."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Test-Funktionen
        test_group = QGroupBox("Test-Funktionen")
        test_layout = QVBoxLayout(test_group)
        
        # Coil-Tests
        coil_test_layout = QHBoxLayout()
        
        self.test_reject_btn = QPushButton("🚫 Ausschuss-Signal testen")
        self.test_reject_btn.clicked.connect(self.test_reject_coil)
        coil_test_layout.addWidget(self.test_reject_btn)
        
        self.test_detection_btn = QPushButton("✅ Detection-Active testen")
        self.test_detection_btn.clicked.connect(self.test_detection_coil)
        coil_test_layout.addWidget(self.test_detection_btn)
        
        test_layout.addLayout(coil_test_layout)
        
        # Controller-Reset
        reset_layout = QHBoxLayout()
        
        self.reset_controller_btn = QPushButton("🔄 Controller-Reset")
        self.reset_controller_btn.clicked.connect(self.reset_controller)
        self.reset_controller_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                font-weight: bold;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        reset_layout.addWidget(self.reset_controller_btn)
        reset_layout.addStretch()
        
        test_layout.addLayout(reset_layout)
        
        layout.addWidget(test_group)
        
        # Simulator-Info
        simulator_group = QGroupBox("WAGO Simulator")
        simulator_layout = QVBoxLayout(simulator_group)
        
        simulator_info = QTextEdit()
        simulator_info.setReadOnly(True)
        simulator_info.setMaximumHeight(100)
        simulator_info.setText("""
        Für Tests ohne Hardware kann der WAGO Simulator verwendet werden:
        
        1. Führen Sie 'python modbus_simulator.py' aus
        2. Setzen Sie die IP-Adresse auf 127.0.0.1
        3. Alle Modbus-Funktionen sind dann testbar
        """)
        simulator_layout.addWidget(simulator_info)
        
        layout.addWidget(simulator_group)
        layout.addStretch()
        
        return widget
    
    def on_modbus_enabled_changed(self, enabled):
        """Modbus aktiviert/deaktiviert."""
        self.modbus_container.setEnabled(enabled)
    
    def load_settings(self):
        """Einstellungen laden."""
        self.modbus_enabled.setChecked(self.settings.get('modbus_enabled', True))
        self.modbus_ip.setText(self.settings.get('modbus_ip', '192.168.1.100'))
        self.modbus_port.setValue(self.settings.get('modbus_port', 502))
        self.watchdog_timeout.setValue(self.settings.get('watchdog_timeout_seconds', 5))
        self.watchdog_interval.setValue(self.settings.get('watchdog_interval_seconds', 2))
        self.reject_coil_address.setValue(self.settings.get('reject_coil_address', 0))
        self.detection_active_coil.setValue(self.settings.get('detection_active_coil_address', 1))
        self.reject_duration.setValue(self.settings.get('reject_coil_duration_seconds', 1.0))
        
        # Enable/Disable basierend auf Checkbox
        self.on_modbus_enabled_changed(self.modbus_enabled.isChecked())
    
    def save_settings(self):
        """Einstellungen speichern."""
        self.settings.set('modbus_enabled', self.modbus_enabled.isChecked())
        self.settings.set('modbus_ip', self.modbus_ip.text())
        self.settings.set('modbus_port', self.modbus_port.value())
        self.settings.set('watchdog_timeout_seconds', self.watchdog_timeout.value())
        self.settings.set('watchdog_interval_seconds', self.watchdog_interval.value())
        self.settings.set('reject_coil_address', self.reject_coil_address.value())
        self.settings.set('detection_active_coil_address', self.detection_active_coil.value())
        self.settings.set('reject_coil_duration_seconds', self.reject_duration.value())
    
    def update_connection_status(self, is_connected):
        """Verbindungsstatus aktualisieren."""
        if is_connected:
            self.connection_status.setText("Verbindungsstatus: Verbunden ✅")
            self.connection_status.setStyleSheet("""
                QLabel {
                    padding: 8px;
                    border-radius: 4px;
                    background-color: #27ae60;
                    color: white;
                    font-weight: bold;
                }
            """)
        else:
            self.connection_status.setText("Verbindungsstatus: Getrennt ❌")
            self.connection_status.setStyleSheet("""
                QLabel {
                    padding: 8px;
                    border-radius: 4px;
                    background-color: #e74c3c;
                    color: white;
                    font-weight: bold;
                }
            """)
    
    def test_connection(self):
        """Verbindung testen."""
        try:
            # Hier würde normalerweise die Modbus-Verbindung getestet
            QMessageBox.information(self, "Test", "Verbindungstest wird durchgeführt...")
            # Implementierung würde über die Hauptanwendung erfolgen
        except Exception as e:
            QMessageBox.critical(self, "Fehler", f"Fehler beim Verbindungstest:\n{str(e)}")
    
    def force_reconnect(self):
        """Neuverbindung erzwingen."""
        try:
            QMessageBox.information(self, "Neuverbindung", "Neuverbindung wird erzwungen...")
            # Implementierung würde über die Hauptanwendung erfolgen
        except Exception as e:
            QMessageBox.critical(self, "Fehler", f"Fehler bei Neuverbindung:\n{str(e)}")
    
    def test_reject_coil(self):
        """Ausschuss-Coil testen."""
        try:
            QMessageBox.information(self, "Test", "Ausschuss-Signal wird getestet...")
            # Implementierung würde über die Hauptanwendung erfolgen
        except Exception as e:
            QMessageBox.critical(self, "Fehler", f"Fehler beim Test:\n{str(e)}")
    
    def test_detection_coil(self):
        """Detection-Active-Coil testen."""
        try:
            QMessageBox.information(self, "Test", "Detection-Active wird getestet...")
            # Implementierung würde über die Hauptanwendung erfolgen
        except Exception as e:
            QMessageBox.critical(self, "Fehler", f"Fehler beim Test:\n{str(e)}")
    
    def reset_controller(self):
        """Controller-Reset durchführen."""
        reply = QMessageBox.question(
            self,
            "Controller-Reset",
            "⚠️ WARNUNG ⚠️\n\n"
            "Controller-Reset durchführen?\n\n"
            "Dies startet den WAGO-Controller neu und unterbricht alle laufenden Prozesse!",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                QMessageBox.information(self, "Reset", "Controller-Reset wird durchgeführt...")
                # Implementierung würde über die Hauptanwendung erfolgen
            except Exception as e:
                QMessageBox.critical(self, "Fehler", f"Fehler beim Reset:\n{str(e)}")