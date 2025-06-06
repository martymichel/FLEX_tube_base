"""
WAGO Modbus Manager - Industrielle Schnittstelle
Verwaltet Watchdog und Coil-Ausgänge für die KI-Objekterkennung
"""

import time
import threading
import logging
from pathlib import Path

try:
    from pymodbus.client.sync import ModbusTcpClient
    MODBUS_AVAILABLE = True
except ImportError:
    MODBUS_AVAILABLE = False
    logging.warning("pymodbus nicht verfügbar - Modbus-Funktionen deaktiviert")

class ModbusManager:
    """Verwaltet WAGO Modbus-Verbindung mit Watchdog und Coil-Steuerung."""
    
    def __init__(self, settings):
        self.settings = settings
        self.client = None
        self.connected = False
        
        # Thread-Lock für sichere Zugriffe
        self._lock = threading.Lock()
        
        # Watchdog
        self.watchdog_running = False
        self.watchdog_thread = None
        self.watchdog_value = 0
        
        # Coil-Status tracking
        self.coil_refresh_thread = None
        self.coil_refresh_running = False
        self.detection_active_coil_state = False
        
        # Timer für Ausschuss-Coil
        self.reject_coil_timer = None
        
        # Modbus-Parameter aus Settings
        self.ip_address = self.settings.get('modbus_ip', '192.168.1.100')
        self.port = self.settings.get('modbus_port', 502)
        self.watchdog_timeout = self.settings.get('watchdog_timeout_seconds', 5)
        self.watchdog_interval = self.settings.get('watchdog_interval_seconds', 2)
        self.reject_coil_address = self.settings.get('reject_coil_address', 0)
        self.detection_active_coil_address = self.settings.get('detection_active_coil_address', 1)
        self.reject_coil_duration = self.settings.get('reject_coil_duration_seconds', 1.0)
        
        logging.info(f"ModbusManager initialisiert - IP: {self.ip_address}, Port: {self.port}")
    
    def connect(self):
        """Verbindung zur WAGO herstellen."""
        if not MODBUS_AVAILABLE:
            logging.warning("pymodbus nicht verfügbar - Modbus-Verbindung nicht möglich")
            return False
        
        try:
            self.client = ModbusTcpClient(self.ip_address, port=self.port)
            self.connected = self.client.connect()
            
            if self.connected:
                logging.info(f"Modbus-Verbindung erfolgreich zu {self.ip_address}:{self.port}")
                return True
            else:
                logging.error(f"Modbus-Verbindung fehlgeschlagen zu {self.ip_address}:{self.port}")
                return False
                
        except Exception as e:
            logging.error(f"Fehler bei Modbus-Verbindung: {e}")
            return False
    
    def disconnect(self):
        """Verbindung trennen und alle Threads stoppen."""
        logging.info("Modbus-Verbindung wird getrennt...")
        
        # Watchdog stoppen
        self.stop_watchdog()
        
        # Coil-Refresh stoppen
        self.stop_coil_refresh()
        
        # Alle Coils ausschalten
        self.set_all_coils_off()
        
        # Verbindung trennen
        if self.client and self.connected:
            try:
                self.client.close()
                logging.info("Modbus-Verbindung getrennt")
            except Exception as e:
                logging.warning(f"Fehler beim Trennen der Modbus-Verbindung: {e}")
        
        self.connected = False
    
    def initialize_watchdog(self):
        """Watchdog konfigurieren und starten."""
        if not self.connected:
            logging.warning("Keine Modbus-Verbindung - Watchdog kann nicht initialisiert werden")
            return False
        
        try:
            with self._lock:
                # Watchdog-Timeout setzen (Register 0x1000)
                timeout_value = self.watchdog_timeout * 10  # Sekunden zu Dezisekunden
                result1 = self.client.write_register(0x1000, timeout_value)
                
                # Funktionscode-Maske (Register 0x1001, optional)
                result2 = self.client.write_register(0x1001, 0xFFFF)
                
                # Verbindung bleibt offen (Register 0x1009)
                result3 = self.client.write_register(0x1009, 0)
                
                # Erste Aktivierung des Watchdogs (Register 0x1003)
                self.watchdog_value = 1
                result4 = self.client.write_register(0x1003, self.watchdog_value)
                
                if all([not r.isError() for r in [result1, result2, result3, result4]]):
                    logging.info(f"Watchdog konfiguriert - Timeout: {self.watchdog_timeout}s")
                    return True
                else:
                    logging.error("Fehler bei Watchdog-Konfiguration")
                    return False
                    
        except Exception as e:
            logging.error(f"Fehler bei Watchdog-Initialisierung: {e}")
            return False
    
    def start_watchdog(self):
        """Watchdog-Thread starten."""
        if not self.connected:
            return False
        
        if self.watchdog_running:
            logging.warning("Watchdog läuft bereits")
            return True
        
        # Watchdog konfigurieren
        if not self.initialize_watchdog():
            return False
        
        # Thread starten
        self.watchdog_running = True
        self.watchdog_thread = threading.Thread(target=self._watchdog_loop, daemon=True)
        self.watchdog_thread.start()
        
        logging.info("Watchdog-Thread gestartet")
        return True
    
    def stop_watchdog(self):
        """Watchdog-Thread stoppen."""
        if self.watchdog_running:
            self.watchdog_running = False
            if self.watchdog_thread:
                self.watchdog_thread.join(timeout=2.0)
            logging.info("Watchdog-Thread gestoppt")
    
    def _watchdog_loop(self):
        """Watchdog-Thread-Schleife."""
        while self.watchdog_running:
            try:
                with self._lock:
                    # Watchdog-Wert incrementieren (16-Bit begrenzt)
                    self.watchdog_value = (self.watchdog_value + 1) & 0xFFFF
                    
                    # Watchdog triggern
                    result = self.client.write_register(0x1003, self.watchdog_value)
                    
                    if not result.isError():
                        logging.debug(f"Watchdog getriggert: {self.watchdog_value}")
                    else:
                        logging.warning("Watchdog-Trigger fehlgeschlagen")
                    
                    # Optional: Watchdog-Status prüfen
                    try:
                        status_result = self.client.read_holding_registers(0x1006, 1)
                        if not status_result.isError() and status_result.registers[0] == 2:
                            logging.error("ALARM: Watchdog abgelaufen!")
                            # Optional: Watchdog neu starten
                            self.client.write_register(0x1007, 1)
                    except:
                        pass  # Status-Check ist optional
                
                # Warten bis zum nächsten Trigger
                time.sleep(self.watchdog_interval)
                
            except Exception as e:
                logging.error(f"Fehler im Watchdog-Loop: {e}")
                time.sleep(1.0)  # Bei Fehler kurz warten
    
    def set_coil(self, address, state):
        """Einzelne Coil setzen."""
        if not self.connected:
            return False
        
        try:
            with self._lock:
                result = self.client.write_coil(address, state)
                if not result.isError():
                    logging.debug(f"Coil {address} auf {state} gesetzt")
                    return True
                else:
                    logging.warning(f"Fehler beim Setzen von Coil {address}")
                    return False
        except Exception as e:
            logging.error(f"Fehler beim Setzen von Coil {address}: {e}")
            return False
    
    def set_reject_coil(self):
        """Ausschuss-Coil für definierte Zeit einschalten."""
        if not self.connected:
            return False
        
        try:
            # Coil einschalten
            if self.set_coil(self.reject_coil_address, True):
                logging.info(f"Ausschuss-Signal aktiviert (Coil {self.reject_coil_address})")
                
                # Timer für automatisches Ausschalten
                if self.reject_coil_timer:
                    self.reject_coil_timer.cancel()
                
                self.reject_coil_timer = threading.Timer(
                    self.reject_coil_duration,
                    lambda: self.set_coil(self.reject_coil_address, False)
                )
                self.reject_coil_timer.start()
                
                return True
            return False
            
        except Exception as e:
            logging.error(f"Fehler beim Setzen des Ausschuss-Signals: {e}")
            return False
    
    def set_detection_active_coil(self, state):
        """Detection-Active-Coil setzen."""
        if not self.connected:
            return False
        
        success = self.set_coil(self.detection_active_coil_address, state)
        if success:
            self.detection_active_coil_state = state
            action = "aktiviert" if state else "deaktiviert"
            logging.info(f"Detection-Active-Signal {action} (Coil {self.detection_active_coil_address})")
        
        return success
    
    def start_coil_refresh(self):
        """Coil-Refresh-Thread starten (für Detection-Active alle 3s)."""
        if not self.connected:
            return False
        
        if self.coil_refresh_running:
            return True
        
        self.coil_refresh_running = True
        self.coil_refresh_thread = threading.Thread(target=self._coil_refresh_loop, daemon=True)
        self.coil_refresh_thread.start()
        
        logging.info("Coil-Refresh-Thread gestartet")
        return True
    
    def stop_coil_refresh(self):
        """Coil-Refresh-Thread stoppen."""
        if self.coil_refresh_running:
            self.coil_refresh_running = False
            if self.coil_refresh_thread:
                self.coil_refresh_thread.join(timeout=2.0)
            logging.info("Coil-Refresh-Thread gestoppt")
    
    def _coil_refresh_loop(self):
        """Coil-Refresh-Thread-Schleife."""
        while self.coil_refresh_running:
            try:
                # Detection-Active-Coil alle 3 Sekunden auffrischen
                if self.detection_active_coil_state:
                    self.set_coil(self.detection_active_coil_address, True)
                
                time.sleep(3.0)  # Alle 3 Sekunden
                
            except Exception as e:
                logging.error(f"Fehler im Coil-Refresh-Loop: {e}")
                time.sleep(1.0)
    
    def set_all_coils_off(self):
        """Alle überwachten Coils ausschalten."""
        if not self.connected:
            return
        
        try:
            # Ausschuss-Coil aus
            self.set_coil(self.reject_coil_address, False)
            
            # Detection-Active-Coil aus
            self.set_coil(self.detection_active_coil_address, False)
            self.detection_active_coil_state = False
            
            # Timer canceln
            if self.reject_coil_timer:
                self.reject_coil_timer.cancel()
                self.reject_coil_timer = None
            
            logging.info("Alle Coils ausgeschaltet")
            
        except Exception as e:
            logging.error(f"Fehler beim Ausschalten der Coils: {e}")
    
    def get_connection_status(self):
        """Verbindungsstatus abrufen."""
        return {
            'connected': self.connected,
            'ip_address': self.ip_address,
            'port': self.port,
            'watchdog_running': self.watchdog_running,
            'coil_refresh_running': self.coil_refresh_running,
            'detection_active_coil_state': self.detection_active_coil_state
        }
    
    def update_settings(self, new_settings):
        """Einstellungen aktualisieren (erfordert Neuverbindung)."""
        old_ip = self.ip_address
        old_port = self.port
        
        # Neue Einstellungen übernehmen
        self.ip_address = new_settings.get('modbus_ip', self.ip_address)
        self.port = new_settings.get('modbus_port', self.port)
        self.watchdog_timeout = new_settings.get('watchdog_timeout_seconds', self.watchdog_timeout)
        self.watchdog_interval = new_settings.get('watchdog_interval_seconds', self.watchdog_interval)
        self.reject_coil_address = new_settings.get('reject_coil_address', self.reject_coil_address)
        self.detection_active_coil_address = new_settings.get('detection_active_coil_address', self.detection_active_coil_address)
        self.reject_coil_duration = new_settings.get('reject_coil_duration_seconds', self.reject_coil_duration)
        
        # Bei IP/Port-Änderung Neuverbindung erforderlich
        if old_ip != self.ip_address or old_port != self.port:
            logging.info("Modbus-Parameter geändert - Neuverbindung erforderlich")
            return True  # Signalisiert dass Neuverbindung nötig ist
        
        return False