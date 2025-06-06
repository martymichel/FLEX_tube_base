"""
Aktualisierte Dialog Manager Klasse.

- Entfernt den Einstellungsdialog, da Einstellungen nun extern verwaltet werden
- Optimiert für externe Einstellungsverwaltung
"""

import traceback
import logging
import os
from PyQt6.QtWidgets import QMessageBox, QFileDialog, QDialog
from gui.dialogs import CameraConfigDialog, FrameConfigDialog, LoginDialog

class DialogManager:
    """Manages dialog windows and their interactions."""
    
    def __init__(self, manager):
        """
        Initialize dialog manager.
        
        Args:
            manager: Reference to the UI manager
        """
        self.manager = manager
        self.window = manager.main_window
    
    def show_settings_dialog(self):
        """
        Show information that settings are now managed externally.
        This method exists for backwards compatibility but redirects users to external settings.
        """
        try:
            # Log this deprecated call
            logging.warning("show_settings_dialog() called - redirecting to external settings info")
            
            # Show informational message about external settings management
            QMessageBox.information(
                self.window,
                "Einstellungen extern verwaltet",
                "Die Einstellungen werden jetzt extern verwaltet.\n\n"
                "Verwenden Sie das externe Einstellungs-Tool 'test_settings_dialog.py' "
                "oder bearbeiten Sie die Datei 'detection_settings.json' direkt.\n\n"
                "Die Einstellungen werden automatisch neu geladen, wenn sie extern geändert werden."
            )
            
        except Exception as e:
            logging.error(f"Error showing settings dialog info: {e}")
            logging.error(traceback.format_exc())
    
    def show_frame_settings(self):
        """Show frame configuration dialog."""
        # First check if current user has permission
        if not self.window.user_manager.can_access_settings():
            QMessageBox.warning(
                self.window, 
                "Zugriff verweigert",
                "Sie benötigen Administrator-Rechte für die Rahmen-Konfiguration."
            )
            # Zeige Login-Prompt an
            self.manager.show_login_prompt()
            return
            
        if not self.window.detection_manager.class_names:
            QMessageBox.warning(
                self.window, 
                "Warnung", 
                "Bitte zuerst ein Modell laden"
            )
            return
        
        self.window.activity_manager.register_activity()
        
        # Log this action
        self.window.user_manager.log_user_action(
            "Opened settings dialog", 
            "Frame configuration"
        )
        
        # Create frame settings dialog
        dialog = FrameConfigDialog(
            self.window.detection_manager.class_names, 
            self.window.settings_manager.settings, 
            self.window
        )
        
        # Show dialog and handle result
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Log the frame settings change
            self.window.user_manager.log_user_action(
                "Changed settings", 
                "Updated frame configuration"
            )
            
            try:
                new_settings = dialog.get_settings()
                if new_settings:
                    self.window.settings_manager.update(new_settings)
                    self.window.detection_manager.update_thread_settings()
                    
                    QMessageBox.information(
                        self.window,
                        "Rahmen-Konfiguration",
                        "Die Rahmen-Konfiguration wurde erfolgreich gespeichert."
                    )
            except Exception as e:
                logging.error(f"Error saving frame settings: {e}")
                QMessageBox.critical(
                    self.window,
                    "Fehler beim Speichern",
                    f"Die Rahmen-Einstellungen konnten nicht gespeichert werden:\n\n{str(e)}"
                )
    
    def show_camera_config_dialog(self):
        """Show dialog for IDS Peak camera configuration."""
        # First check if current user has permission
        if not self.window.user_manager.can_access_settings():
            QMessageBox.warning(
                self.window, 
                "Zugriff verweigert",
                "Sie benötigen Administrator-Rechte für die Kamera-Konfiguration."
            )
            # Zeige Login-Prompt an
            self.manager.show_login_prompt()
            return
        
        # Get current config path
        current_config = self.window.settings_manager.get('camera_config_path')
        
        # Log this action
        self.window.user_manager.log_user_action(
            "Opened settings dialog", 
            "Camera configuration"
        )
        
        # Create and show dialog
        dialog = CameraConfigDialog(current_config, self.window)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            config_path = dialog.get_config_path()
            if config_path and os.path.exists(config_path):
                # Log the camera config change
                self.window.user_manager.log_user_action(
                    "Changed settings", 
                    f"Updated camera config: {os.path.basename(config_path)}"
                )
                
                try:
                    # Save configuration path
                    self.window.settings_manager.set('camera_config_path', config_path)
                    self.window.settings_manager.save_settings()
                    
                    # Update thread settings if running
                    self.window.detection_manager.update_thread_settings()
                    
                    # Show confirmation
                    QMessageBox.information(
                        self.window,
                        "Kamera-Konfiguration",
                        f"Kamera-Konfiguration '{os.path.basename(config_path)}' wurde geladen.\n\n"
                        "Die Einstellungen werden beim nächsten Start der Kamera angewendet."
                    )
                except Exception as e:
                    logging.error(f"Error saving camera config: {e}")
                    QMessageBox.critical(
                        self.window,
                        "Fehler beim Speichern",
                        f"Die Kamera-Konfiguration konnte nicht gespeichert werden:\n\n{str(e)}"
                    )