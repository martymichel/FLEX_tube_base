"""
Integration example for the LiveDetectionApp.

This file shows how to modify the main application class to support cyclic settings reload.
"""

from PyQt6.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QApplication
from PyQt6.QtCore import Qt, QTimer
import logging
import os

from gui.app_components import (
    SettingsManager, 
    UIManager, 
    DetectionManager, 
    StatsManager,
    ActivityManager
)
from gui.user_management import UserManager, UserRole
from .ui_builder import build_user_interface
from .event_handlers import EventHandlerManager


class LiveDetectionApp(QMainWindow):
    """
    Hauptfenster für Live-KI-Objekterkennung.
    VEREINFACHTES DESIGN ohne externe Hardware-Abhängigkeiten:
    - Fokus auf Bilderkennung und KI-Auswertung
    - Lokale Datenspeicherung und -analyse
    - Benutzerfreundliche Oberfläche
    - AKTUALISIERT: Unterstützt externes Bearbeiten von Einstellungen
    """

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Live KI-Object Detection")
        self.setObjectName("MainWindow")
        self.setWindowState(Qt.WindowState.WindowFullScreen)
        
        # Logging konfigurieren
        self._configure_logging()
        
        # UI-Zustand
        self.sidebar_visible = False
        self.sidebar_locked = True
        
        # Komponenten-Manager initialisieren
        self.settings_manager = SettingsManager()
        # Aktiviere zyklisches Laden der Einstellungen
        self.settings_manager.register_settings_changed_callback(self._on_settings_changed)
        self.settings_manager.start_cyclic_reload(interval_seconds=5)
        logging.info("Cyclic settings reload activated")
        
        self.user_manager = UserManager()
        
        # UI erstellen
        self._initialize_ui()
        
        # Komponenten-Manager initialisieren (nach UI)
        self._initialize_component_managers()
        
        # Standard-Modell laden
        self._load_default_model()
        
        # Video-Einstellungen laden
        self._load_video_settings()
        
        # Event-Handler verbinden
        self.event_handler.connect_signals()
        
        # UI für Gast-Rolle initialisieren
        self.ui_manager.update_ui_for_role(UserRole.GUEST)
        
        # Autostart planen
        self._schedule_autostart()
        
        logging.info("LiveDetectionApp initialized successfully")

    def _configure_logging(self):
        """Konfiguriere das Logging-System."""
        file_handler = logging.FileHandler('app.log', mode='a')
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(),
                file_handler
            ]
        )
        logging.info("Application starting - Focus on AI detection and local processing")

    def _initialize_ui(self):
        """Initialisiere die Benutzeroberfläche."""
        # Zentrales Widget und Layout einrichten
        central_widget = QWidget()
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        self.setCentralWidget(central_widget)
        
        # UI erstellen
        build_user_interface(self)
        
        # Sidebar initial ausblenden
        self.splitter.setSizes([0, 1000])
        
        # Hauptfenster-Stil
        self.setStyleSheet("QMainWindow { background-color: #1a1a1a; }")
        
        # Hinweis auf externe Einstellungen hinzufügen
        if hasattr(self, 'settings_menu'):
            info_label = QLabel("Einstellungen werden extern verwaltet")
            info_label.setStyleSheet("color: #ffcc00; padding: 5px; background-color: #2c3e50;")
            # Füge das Label zum Settings-Menü hinzu
            # (Annahme: settings_menu ist ein QWidget mit einem Layout)
            try:
                self.settings_menu.layout().addWidget(info_label)
            except Exception as e:
                logging.error(f"Konnte Info-Label nicht hinzufügen: {e}")

    def _initialize_component_managers(self):
        """Initialisiere die Komponenten-Manager."""
        self.stats_manager = StatsManager(self)
        self.detection_manager = DetectionManager(self)
        self.activity_manager = ActivityManager(self)
        self.ui_manager = UIManager(self)
        self.event_handler = EventHandlerManager(self)

    def _load_default_model(self):
        """Lade das Standard-Modell falls konfiguriert."""
        if self.settings_manager.get('default_model_directory'):
            default_model = self.settings_manager.get_default_model()
            if default_model and os.path.exists(default_model):
                self.detection_manager.model_path = default_model
                self.model_path_label.setText(os.path.basename(default_model))
                self.detection_manager.load_model_classes()
                self.detection_manager.check_ready()
            else:
                logging.warning(f"Standard-Modell nicht gefunden: {default_model}")

    def _load_video_settings(self):
        """Lade Video- und Kamera-Einstellungen."""
        self.last_video_path = self.settings_manager.get('last_video_path')
        self.last_camera_id = self.settings_manager.get('last_camera_id', 0)
        self.last_mode_was_video = self.settings_manager.get('last_mode_was_video', False)
        self.manual_stop = self.settings_manager.get('manual_stop', False)

    def _schedule_autostart(self):
        """Plane den automatischen Start."""
        self.setWindowTitle("Live KI-Object Detection - Starte...")
        QTimer.singleShot(500, self.event_handler.autostart_detection)
        
    def _on_settings_changed(self, new_settings):
        """
        Callback-Funktion für Änderungen an den Einstellungen.
        
        Args:
            new_settings (dict): Die aktualisierten Einstellungen
        """
        logging.info(f"Externe Einstellungsänderung erkannt: {len(new_settings)} Einstellungen")
        
        try:
            # Update application components with new settings
            self._update_application_with_settings(new_settings)
            
            # Log success
            logging.info("Externe Einstellungen erfolgreich angewendet")
            
            # Optional: Zeige visuelle Benachrichtigung für den Benutzer
            if hasattr(self, 'ui_manager') and hasattr(self.ui_manager, 'show_notification'):
                self.ui_manager.show_notification("Einstellungen aktualisiert", timeout=3000)
                
        except Exception as e:
            logging.error(f"Fehler beim Anwenden externer Einstellungen: {e}")
            logging.error(f"Traceback: {traceback.format_exc()}")
    
    def _update_application_with_settings(self, new_settings):
        """
        Aktualisiere alle Anwendungskomponenten mit den neuen Einstellungen.
        
        Args:
            new_settings (dict): Die aktualisierten Einstellungen
        """
        # Thread-Einstellungen aktualisieren (falls Thread läuft)
        if hasattr(self, 'detection_manager') and hasattr(self.detection_manager, 'detection_thread'):
            try:
                self.detection_manager.update_thread_settings()
                logging.info("Thread-Einstellungen aktualisiert")
            except Exception as thread_error:
                logging.warning(f"Thread-Update fehlgeschlagen (nicht kritisch): {thread_error}")
        
        # Session-Timeout aktualisieren
        if 'session_timeout_minutes' in new_settings and hasattr(self, 'activity_manager'):
            self.activity_manager.session_timeout_minutes = new_settings['session_timeout_minutes']
            logging.info(f"Session-Timeout aktualisiert auf {new_settings['session_timeout_minutes']} Minuten")
        
        # Andere Komponenten aktualisieren nach Bedarf
        # ...

    def closeEvent(self, event):
        """Sauberes Herunterfahren der Anwendung."""
        logging.info("Application closing - performing cleanup")
        try:
            # Settings Manager Cyclic Reload stoppen
            if hasattr(self, 'settings_manager'):
                self.settings_manager.stop_cyclic_reload()
                logging.info("Settings cyclic reload stopped")
            
            # Detection Thread stoppen
            if hasattr(self, 'detection_manager') and self.detection_manager.detection_thread:
                self.detection_manager.detection_thread.stop()
                
            logging.info("Application cleanup completed successfully")
            
        except Exception as e:
            logging.error(f"Error during application shutdown: {e}")
        finally:
            event.accept()
