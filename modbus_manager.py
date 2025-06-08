"""
WAGO Modbus Manager - OPTIMIERT für intelligente Verbindungsversuche mit Disconnect-Detection
Verwaltet Watchdog und Coil-Ausgänge für die KI-Objekterkennung
VERBESSERT: Vermeidet redundante Aktionen und Watchdog-Frühfehler
ERWEITERT: Automatische Erkennung von Verbindungsabbrüchen mit Callback-System
"""

import time
import threading
import logging

try:
    from pymodbus.client.sync import ModbusTcpClient
    MODBUS_AVAILABLE = True
except ImportError:
    MODBUS_AVAILABLE = False
    logging.warning("pymodbus nicht verfügbar - Modbus-Funktionen deaktiviert")

class ModbusManager:
    """OPTIMIERTER WAGO Modbus-Manager mit intelligenter Verbindungslogik und Disconnect-Detection."""
    
    def __init__(self, settings):
        self.settings = settings
        self.client = None
        self.connected = False
        
        # Thread-Lock für sichere Zugriffe
        self._lock = threading.Lock()
        
        # Optimierter Watchdog mit Startverzögerung
        self.watchdog_running = False
        self.watchdog_thread = None
        self.watchdog_value = 0
        self.watchdog_initialized = False  # NEU: Verhindert Frühfehler
        
        # NEU: Disconnect-Detection
        self.consecutive_failures = 0
        self.max_failures_before_disconnect = 3  # Nach 3 fehlgeschlagenen Versuchen = Disconnect
        self.disconnect_callback = None  # Callback für Verbindungsabbruch
        
        # Coil-Status
        self.detection_active = False
        
        # Modbus-Parameter aus Settings
        self.ip_address = self.settings.get('modbus_ip', '192.168.1.100')
        self.port = self.settings.get('modbus_port', 502)
        self.watchdog_timeout = self.settings.get('watchdog_timeout_seconds', 5)
        self.watchdog_interval = self.settings.get('watchdog_interval_seconds', 2)
        self.reject_coil_address = self.settings.get('reject_coil_address', 0)
        self.detection_active_coil_address = self.settings.get('detection_active_coil_address', 1)
        self.reject_coil_duration = self.settings.get('reject_coil_duration_seconds', 1.0)
        
        logging.info(f"ModbusManager optimiert initialisiert - IP: {self.ip_address}")
    
    def register_disconnect_callback(self, callback_func):
        """Registriere Callback für Verbindungsabbrüche.
        
        Args:
            callback_func: Funktion die bei Verbindungsabbruch aufgerufen wird
        """
        self.disconnect_callback = callback_func
        logging.info("Disconnect-Callback registriert für Modbus-Überwachung")
    
    def connect(self):
        """OPTIMIERTE Verbindung zur WAGO - direkt ohne Reset."""
        if not MODBUS_AVAILABLE:
            logging.warning("pymodbus nicht verfügbar")
            return False
        
        try:
            logging.info(f"Versuche direkte WAGO-Verbindung zu {self.ip_address}:{self.port}")
            
            # Alte Verbindung schließen
            if self.client:
                try:
                    self.client.close()
                except:
                    pass
            
            # Neue Verbindung mit längerem Timeout für Stabilität
            self.client = ModbusTcpClient(self.ip_address, port=self.port, timeout=5)
            self.connected = self.client.connect()
            
            if self.connected:
                logging.info("WAGO Modbus-Direktverbindung erfolgreich")
                # NEU: Reset failure counter bei erfolgreicher Verbindung
                self.consecutive_failures = 0
            else:
                logging.error("WAGO Modbus-Direktverbindung fehlgeschlagen")
            
            return self.connected
            
        except Exception as e:
            logging.error(f"Fehler bei WAGO Direktverbindung: {e}")
            return False
    
    def restart_controller(self):
        """Controller-Reset des WAGO 750-362 - VERBESSERT mit Wartezeit."""
        try:
            logging.info("Führe WAGO Controller-Reset durch...")
            
            # Temporäre Verbindung für Reset mit längerem Timeout
            temp_client = ModbusTcpClient(self.ip_address, port=self.port, timeout=8)
            
            if temp_client.connect():
                try:
                    result = temp_client.write_register(0x2040, 0xAA55)
                    # WICHTIG: Warten bis Reset-Befehl verarbeitet wird
                    time.sleep(2)
                    # Prüfen, ob der Befehl erfolgreich war
                    success = not result.isError()
                    if success:
                        logging.info("Controller-Reset-Befehl erfolgreich gesendet (0x2040 = 0xAA55)")
                    else:
                        logging.warning("Controller-Reset-Befehl fehlgeschlagen")
                    return success
                finally:
                    temp_client.close()
            else:
                logging.warning("Keine temporäre Verbindung für Reset möglich")
                return False
                
        except Exception as e:
            logging.error(f"Fehler beim Controller-Reset: {e}")
            return False
    
    def disconnect(self):
        """Verbindung sauber trennen."""
        logging.info("Trenne WAGO Modbus-Verbindung...")
        
        # Watchdog stoppen
        self.stop_watchdog()
        
        # Alle Coils ausschalten
        self.set_all_coils_off()
        
        # Verbindung schließen
        if self.client and self.connected:
            try:
                time.sleep(0.1)  # Letzte Befehle abwarten
                self.client.close()
                logging.info("WAGO Verbindung getrennt")
            except Exception as e:
                logging.warning(f"Fehler beim Trennen: {e}")
        
        self.connected = False
        self.client = None
        self.consecutive_failures = 0  # Reset failure counter
    
    def start_watchdog(self):
        """OPTIMIERTER Watchdog-Start mit Initialisierungsverzögerung."""
        if not self.connected:
            return False
        
        if self.watchdog_running:
            return True
        
        # Watchdog konfigurieren
        try:
            with self._lock:
                timeout_value = self.watchdog_timeout * 10  # Sekunden zu Dezisekunden
                self.client.write_register(0x1000, timeout_value)  # Timeout
                self.client.write_register(0x1009, 0)             # Verbindung offen
                self.client.write_register(0x1003, 1)             # Aktivierung
                
            logging.info(f"Watchdog konfiguriert - {self.watchdog_timeout}s Timeout")
        except Exception as e:
            logging.error(f"Watchdog-Konfiguration fehlgeschlagen: {e}")
            return False
        
        # Thread starten mit Initialisierungsflag
        self.watchdog_running = True
        self.watchdog_initialized = False  # Erstmal nicht initialisiert
        self.consecutive_failures = 0  # Reset failure counter
        self.watchdog_thread = threading.Thread(target=self._watchdog_loop, daemon=True)
        self.watchdog_thread.start()
        
        logging.info("Watchdog-Thread gestartet (mit Startverzögerung)")
        return True
    
    def stop_watchdog(self):
        """Watchdog stoppen."""
        if self.watchdog_running:
            self.watchdog_running = False
            self.watchdog_initialized = False  # Reset
            if self.watchdog_thread:
                self.watchdog_thread.join(timeout=1.0)
            logging.info("Watchdog gestoppt")
    
    def _watchdog_loop(self):
        """OPTIMIERTE Watchdog-Schleife mit Startverzögerung und Disconnect-Detection."""
        try:
            # STARTVERZÖGERUNG: Warte erst 3 Sekunden vor erstem Trigger
            logging.info("Watchdog wartet 3 Sekunden vor erstem Trigger...")
            time.sleep(3.0)
            
            if not self.watchdog_running:  # Prüfe ob zwischenzeitlich gestoppt
                return
                
            self.watchdog_initialized = True  # Jetzt ist der Watchdog bereit
            logging.info("Watchdog-Startverzögerung beendet - beginne reguläre Trigger")
            
        except Exception as e:
            logging.error(f"Fehler in Watchdog-Startverzögerung: {e}")
            return
        
        # Reguläre Watchdog-Schleife mit Disconnect-Detection
        while self.watchdog_running:
            try:
                with self._lock:
                    self.watchdog_value = (self.watchdog_value + 1) & 0xFFFF
                    result = self.client.write_register(0x1003, self.watchdog_value)
                    
                    if result.isError():
                        # NEU: Fehler-Zähler erhöhen
                        self.consecutive_failures += 1
                        logging.warning(f"Watchdog-Trigger fehlgeschlagen (Wert: {self.watchdog_value}) - Fehler #{self.consecutive_failures}")
                        
                        # NEU: Bei zu vielen Fehlern -> Disconnect erkannt
                        if self.consecutive_failures >= self.max_failures_before_disconnect:
                            logging.error(f"MODBUS DISCONNECT ERKANNT: {self.consecutive_failures} aufeinanderfolgende Fehler")
                            self._handle_disconnect()
                            break  # Beende Watchdog-Loop
                    else:
                        # NEU: Bei erfolgreichem Trigger -> Reset failure counter
                        if self.consecutive_failures > 0:
                            logging.info(f"Watchdog-Trigger wieder erfolgreich - Reset failure counter (war {self.consecutive_failures})")
                            self.consecutive_failures = 0
                        logging.debug(f"Watchdog-Trigger erfolgreich (Wert: {self.watchdog_value})")
                
                time.sleep(self.watchdog_interval)
                
            except Exception as e:
                # NEU: Exception auch als Fehler zählen
                self.consecutive_failures += 1
                logging.error(f"Watchdog-Exception: {e} - Fehler #{self.consecutive_failures}")
                
                # NEU: Bei zu vielen Exceptions -> Disconnect erkannt
                if self.consecutive_failures >= self.max_failures_before_disconnect:
                    logging.error(f"MODBUS DISCONNECT ERKANNT: {self.consecutive_failures} aufeinanderfolgende Exceptions")
                    self._handle_disconnect()
                    break  # Beende Watchdog-Loop
                
                time.sleep(1.0)
    
    def _handle_disconnect(self):
        """Behandle erkannten Modbus-Disconnect."""
        logging.critical("WAGO Modbus-Verbindung unterbrochen - führe Notfall-Aktionen durch")
        
        # Status sofort auf disconnected setzen
        self.connected = False
        
        # Watchdog stoppen
        self.watchdog_running = False
        
        # Client schließen
        if self.client:
            try:
                self.client.close()
            except:
                pass
            self.client = None
        
        # Callback an Hauptanwendung senden (falls registriert)
        if self.disconnect_callback:
            try:
                logging.info("Rufe Disconnect-Callback auf...")
                self.disconnect_callback()
            except Exception as e:
                logging.error(f"Fehler im Disconnect-Callback: {e}")
        
        logging.critical("Modbus-Disconnect-Behandlung abgeschlossen")
    
    def start_coil_refresh(self):
        """SIMPLE Coil-Refresh für Detection-Active."""
        # In SIMPLE Version: Kein extra Thread, wird bei Bedarf aufgefrischt
        logging.debug("Coil-Refresh im SIMPLE Modus (bei Bedarf)")
        return True
    
    def stop_coil_refresh(self):
        """Coil-Refresh stoppen (SIMPLE: nichts zu tun)."""
        pass
    
    def set_coil(self, address, state):
        """SIMPLE Coil setzen mit Disconnect-Detection."""
        if not self.connected:
            return False
        
        try:
            with self._lock:
                result = self.client.write_coil(address, state)
                success = not result.isError()
                if success:
                    logging.debug(f"Coil {address} = {state}")
                    # Reset failure counter bei erfolgreicher Operation
                    if self.consecutive_failures > 0:
                        self.consecutive_failures = 0
                else:
                    logging.warning(f"Coil {address} setzen fehlgeschlagen")
                    # Erhöhe failure counter
                    self.consecutive_failures += 1
                return success
        except Exception as e:
            logging.error(f"Fehler bei Coil {address}: {e}")
            # Exception zählt auch als Fehler
            self.consecutive_failures += 1
            return False
    
    def set_reject_coil(self):
        """Ausschuss-Signal für definierte Zeit."""
        if not self.connected:
            return False
        
        try:
            # Coil einschalten
            if self.set_coil(self.reject_coil_address, True):
                logging.info(f"Ausschuss-Signal EIN (Coil {self.reject_coil_address})")
                
                # Timer für automatisches Ausschalten
                def turn_off():
                    self.set_coil(self.reject_coil_address, False)
                    logging.info(f"Ausschuss-Signal AUS (Coil {self.reject_coil_address})")
                
                timer = threading.Timer(self.reject_coil_duration, turn_off)
                timer.start()
                
                return True
            return False
            
        except Exception as e:
            logging.error(f"Fehler bei Ausschuss-Signal: {e}")
            return False
    
    def set_detection_active_coil(self, state):
        """Detection-Active-Signal setzen."""
        if not self.connected:
            return False
        
        success = self.set_coil(self.detection_active_coil_address, state)
        if success:
            self.detection_active = state
            action = "EIN" if state else "AUS"
            logging.info(f"Detection-Active {action} (Coil {self.detection_active_coil_address})")
        
        return success
    
    def set_all_coils_off(self):
        """Alle Coils ausschalten."""
        if not self.connected:
            return
        
        try:
            self.set_coil(self.reject_coil_address, False)
            self.set_coil(self.detection_active_coil_address, False)
            self.detection_active = False
            logging.info("Alle Coils AUS")
        except Exception as e:
            logging.error(f"Fehler beim Coils ausschalten: {e}")
    
    def force_reconnect(self):
        """Erzwinge Neuverbindung (für UI-Button) - OPTIMIERT."""
        logging.info("Erzwinge WAGO Neuverbindung...")
        
        self.disconnect()
        time.sleep(1)
        
        if self.connect():
            # Watchdog neu starten (mit Verzögerung)
            self.start_watchdog()
            return True
        return False
    
    def get_connection_status(self):
        """SIMPLE Status-Info."""
        return {
            'connected': self.connected,
            'ip_address': self.ip_address,
            'watchdog_running': self.watchdog_running,
            'watchdog_initialized': self.watchdog_initialized,  # NEU
            'detection_active': self.detection_active,
            'consecutive_failures': self.consecutive_failures  # NEU: Für Debugging
        }
    
    def update_settings(self, new_settings):
        """Einstellungen aktualisieren."""
        old_ip = self.ip_address
        old_port = self.port
        
        self.ip_address = new_settings.get('modbus_ip', self.ip_address)
        self.port = new_settings.get('modbus_port', self.port)
        self.watchdog_timeout = new_settings.get('watchdog_timeout_seconds', self.watchdog_timeout)
        self.watchdog_interval = new_settings.get('watchdog_interval_seconds', self.watchdog_interval)
        self.reject_coil_address = new_settings.get('reject_coil_address', self.reject_coil_address)
        self.detection_active_coil_address = new_settings.get('detection_active_coil_address', self.detection_active_coil_address)
        self.reject_coil_duration = new_settings.get('reject_coil_duration_seconds', self.reject_coil_duration)
        
        # Neuverbindung bei IP/Port-Änderung
        if old_ip != self.ip_address or old_port != self.port:
            logging.info("WAGO Parameter geändert - Neuverbindung erforderlich")
            return True
        
        return False