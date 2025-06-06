"""
Benutzer-Manager - einfach und sicher
Verwaltet Benutzerlevel und Berechtigungen
"""

import logging
from PyQt6.QtWidgets import QInputDialog, QLineEdit

class UserManager:
    """Einfache Benutzerverwaltung."""
    
    def __init__(self):
        self.admin_password = "flex2025"
        self.is_admin_logged_in = False
        
        logging.info("UserManager initialisiert - Standardmodus: Gast")
    
    def login(self):
        """Login-Dialog anzeigen.
        
        Returns:
            bool: True wenn erfolgreich eingeloggt
        """
        password, ok = QInputDialog.getText(
            None,
            "Administrator-Login",
            "Passwort eingeben:",
            QLineEdit.EchoMode.Password
        )
        
        if ok and password == self.admin_password:
            self.is_admin_logged_in = True
            logging.info("Administrator-Login erfolgreich")
            return True
        else:
            logging.warning("Administrator-Login fehlgeschlagen")
            return False
    
    def logout(self):
        """Ausloggen."""
        self.is_admin_logged_in = False
        logging.info("Administrator ausgeloggt")
    
    def is_admin(self):
        """Prüfe ob Administrator eingeloggt.
        
        Returns:
            bool: True wenn Administrator
        """
        return self.is_admin_logged_in
    
    def can_change_model(self):
        """Kann Modell ändern?"""
        return self.is_admin_logged_in
    
    def can_change_camera(self):
        """Kann Kamera ändern?"""
        return self.is_admin_logged_in
    
    def can_access_settings(self):
        """Kann Einstellungen öffnen?"""
        return self.is_admin_logged_in
    
    def get_user_level_text(self):
        """Benutzerlevel als Text.
        
        Returns:
            str: "Administrator" oder "Gast"
        """
        return "Administrator" if self.is_admin_logged_in else "Gast"