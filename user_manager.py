"""
Benutzer-Manager - einfach und sicher mit Auto-Logout und PIN-Eingabe
Verwaltet Benutzerlevel und Berechtigungen mit automatischem Admin-Timeout
NEUE FUNKTION: PIN-basierte Anmeldung
"""

import logging
import time
from PyQt6.QtWidgets import QInputDialog, QLineEdit
from PyQt6.QtCore import QTimer, QObject, pyqtSignal

class UserManager(QObject):
    """Einfache Benutzerverwaltung mit Auto-Logout und PIN-Eingabe."""
    
    # Signal fuer UI-Updates bei Status-Änderungen
    user_status_changed = pyqtSignal(str)  # Sendet neuen Status: "Operator" oder "Admin / Dev"
    
    def __init__(self):
        super().__init__()
        # PIN-Codes für die Anmeldung
        self.admin_pin = "2025"      # Admin-PIN
        self.default_pin = "1406"    # Default-PIN (für zukünftige Erweiterungen)
        
        # Status-Flag fuer Admin-Login
        self.is_admin_logged_in = False
        
        # Auto-Logout Timer (10 Minuten)
        self.auto_logout_timer = QTimer()
        self.auto_logout_timer.setSingleShot(True)  # Einmaliger Timer
        self.auto_logout_timer.timeout.connect(self._auto_logout)
        self.admin_login_time = None
        
        logging.info("UserManager initialisiert - Standardmodus: Operator (PIN-basiert)")
    
    def login(self):
        """PIN-Login-Dialog anzeigen.
        
        Returns:
            bool: True wenn erfolgreich eingeloggt
        """
        pin, ok = QInputDialog.getText(
            None,
            "Administrator-Login",
            "Admin-PIN eingeben:",
            QLineEdit.EchoMode.Password
        )
        
        # Pruefen ob PIN korrekt ist
        if ok and pin == self.admin_pin:
            self.is_admin_logged_in = True
            self.admin_login_time = time.time()
            
            # Auto-Logout Timer starten (10 Minuten = 600.000 ms)
            self.auto_logout_timer.start(10 * 60 * 1000)  # 10 Minuten
            
            logging.info("Administrator-Login erfolgreich (PIN: ****) - Auto-Logout in 10 Minuten")
            self.user_status_changed.emit("Benutzerstatus: Admin")
            return True
        elif ok and pin == self.default_pin:
            # Default-PIN wurde eingegeben - könnte für zukünftige Erweiterungen genutzt werden
            logging.info("Default-PIN eingegeben - bleibt im Operator-Modus")
            return False
        else:
            logging.warning("Administrator-Login fehlgeschlagen - ungueltige PIN")
            return False
    
    def logout(self):
        """Ausloggen (manuell oder automatisch)."""
        was_admin = self.is_admin_logged_in
        self.is_admin_logged_in = False
        self.admin_login_time = None
        
        # Auto-Logout Timer stoppen
        if self.auto_logout_timer.isActive():
            self.auto_logout_timer.stop()
        
        if was_admin:
            logging.info("Administrator ausgeloggt")
            self.user_status_changed.emit("Operator")
    
    def _auto_logout(self):
        """Automatischer Logout nach 10 Minuten."""
        if self.is_admin_logged_in:
            logging.info("Automatischer Admin-Logout nach 10 Minuten")
            self.logout()
    
    def extend_session(self):
        """Session verlaengern (bei Admin-Aktivitaeten)."""
        if self.is_admin_logged_in and self.auto_logout_timer.isActive():
            # Timer neu starten
            self.auto_logout_timer.start(10 * 60 * 1000)  # Weitere 10 Minuten
            logging.debug("Admin-Session verlaengert")
    
    def is_admin(self):
        """Pruefe ob Administrator eingeloggt.
        
        Returns:
            bool: True wenn Administrator
        """
        return self.is_admin_logged_in
    
    def can_change_model(self):
        """Kann Modell aendern?"""
        if self.is_admin_logged_in:
            self.extend_session()  # Session verlaengern bei Aktivitaet
        return self.is_admin_logged_in
    
    def can_change_camera(self):
        """Kann Kamera aendern?"""
        if self.is_admin_logged_in:
            self.extend_session()  # Session verlaengern bei Aktivitaet
        return self.is_admin_logged_in
    
    def can_access_settings(self):
        """Kann Einstellungen oeffnen?"""
        if self.is_admin_logged_in:
            self.extend_session()  # Session verlaengern bei Aktivitaet
        return self.is_admin_logged_in
    
    def can_reset_counter(self):
        """Kann Counter zuruecksetzen?"""
        if self.is_admin_logged_in:
            self.extend_session()  # Session verlaengern bei Aktivitaet
        return self.is_admin_logged_in
    
    def can_change_modbus_settings(self):
        """Kann Modbus-Einstellungen aendern? (NEU)"""
        if self.is_admin_logged_in:
            self.extend_session()  # Session verlaengern bei Aktivitaet
        return self.is_admin_logged_in
    
    def get_user_level_text(self):
        """Benutzerlevel als Text.
        
        Returns:
            str: "Admin / Dev" oder "Operator"
        """
        return "Admin / Dev" if self.is_admin_logged_in else "Operator"
    
    def get_time_until_logout(self):
        """Zeit bis zum Auto-Logout in Minuten.
        
        Returns:
            float: Verbleibende Zeit in Minuten, 0 wenn nicht angemeldet
        """
        if not self.is_admin_logged_in or not self.admin_login_time:
            return 0
        
        elapsed = time.time() - self.admin_login_time
        remaining = (10 * 60) - elapsed  # 10 Minuten in Sekunden
        return max(0, remaining / 60)  # In Minuten umrechnen