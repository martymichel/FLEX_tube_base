"""
WAGO Modbus Manager - SIMPLE und zuverlaessig
Verwaltet Watchdog und Coil-Ausgaenge fuer die KI-Objekterkennung
ROBUST: Basierend auf bewaehrter alter Version mit intelligenter Startup-Logik
"""

import time
import threading
import logging

try:
    from pymodbus.client.sync import ModbusTcpClient
    MODBUS_AVAILABLE = True
except ImportError:
    MODBUS_AVAILABLE = False
    logging.warning("pymodbus nicht verfuegbar - Modbus-Funktionen deaktiviert")

class ModbusManager:
    """SIMPLE WAGO Modbus-Manager mit Watchdog und Coil-Steuerung."""
    
    def __init__(self, settings):
        self.settings = settings
        self.client = None
        self.connected = False
        
        # Thread-Lock fuer sichere Zugriffe
        self._lock = threading.Lock()
        
        # Simple Watchdog
        self.watchdog_running = False
        self.watchdog_thread = None
        self.watchdog_value = 0
        
        # Coil-Status
        self.detection_active = False
        
        # Callback fuer Verbindungsverlust (wird von Main-App gesetzt)
        self.connection_lost_callback = None
        
        # Modbus-Parameter aus Settings
        self.ip_address = self.settings.get('modbus_ip', '192.168.1.100')
        self.port = self.settings.get('modbus_port', 502)
        self.watchdog_timeout = self.settings.get('watchdog_timeout_seconds', 5)
        self.watchdog_interval = self.settings.get('watchdog_interval_seconds', 2)
        self.reject_coil_address = self.settings.get('reject_coil_address', 0)
        self.detection_active_coil_address = self.settings.get('detection_active_coil_address', 1)
        self.reject_coil_duration = self.settings.get('reject_coil_duration_seconds', 1.0)
        
        logging.info(f"ModbusManager initialisiert - IP: {self.ip_address}")
    
    def set_connection_lost_callback(self, callback):
        """Setze Callback-Funktion fuer Verbindungsverlust."""
        self.connection_lost_callback = callback
    
    def is_connected(self):
        """EINFACHE Verbindungspruefung - nur Status zurueckgeben.
        
        Returns:
            bool: True wenn verbunden (basiert auf letztem connect() Ergebnis)
        """
        return self.connected and self.client is not None
    
    def connect(self):
        """ROBUSTE Verbindung zur WAGO herstellen (wie alte Version)."""
        if not MODBUS_AVAILABLE:
            logging.warning("pymodbus nicht verfuegbar")
            return False
        
        try:
            logging.info(f"Verbinde zu WAGO {self.ip_address}:{self.port}")
            
            # Alte Verbindung schliessen
            if self.client:
                try:
                    self.client.close()
                except:
                    pass
            
            # Neue Verbindung - OHNE unit Parameter fuer pymodbus 2.5.3
            self.client = ModbusTcpClient(self.ip_address, port=self.port)
            self.connected = self.client.connect()
            
            if self.connected:
                logging.info("WAGO Modbus-Verbindung erfolgreich")
            else:
                logging.error("WAGO Modbus-Verbindung fehlgeschlagen")
            
            return self.connected
            
        except Exception as e:
            logging.error(f"Fehler bei WAGO Verbindung: {e}")
            self.connected = False
            return False
    
    def startup_connect_with_reset_fallback(self):
        """Intelligente Verbindung bei App-Start mit automatischem Controller-Reset als Fallback."""
        logging.info("Starte WAGO Verbindung bei App-Start...")
        
        # Schritt 1: Versuche direkte Verbindung
        if self.connect():
            logging.info("WAGO direkte Verbindung bei Start erfolgreich")
            return True
        
        # Schritt 2: Direkte Verbindung fehlgeschlagen - Controller-Reset durchfuehren
        logging.warning("Direkte Verbindung fehlgeschlagen - fuehre Controller-Reset durch...")
        
        if self.restart_controller():
            logging.info("Controller-Reset erfolgreich - warte 4 Sekunden...")
            time.sleep(4)  # 4 Sekunden warten nach Hardware-Reset
        else:
            logging.warning("Controller-Reset fehlgeschlagen - versuche trotzdem Verbindung...")
            time.sleep(2)  # Kurz warten auch bei fehlgeschlagenem Reset
        
        # Schritt 3: Verbindung nach Reset herstellen
        if self.connect():
            logging.info("WAGO Verbindung nach Controller-Reset erfolgreich")
            return True
        else:
            logging.error("WAGO Verbindung auch nach Controller-Reset fehlgeschlagen")
            return False
    
    def restart_controller(self):
        """SIMPLE Controller-Reset des WAGO 750-362."""
        try:
            logging.info("Fuehre WAGO Controller-Reset durch...")
            
            # Temporaere Verbindung fuer Reset - OHNE unit Parameter
            temp_client = ModbusTcpClient(self.ip_address, port=self.port)
            
            if temp_client.connect():
                try:
                    result = temp_client.write_register(0x2040, 0xAA55)
                    # Warten 1 Sekunde fuer den Reset
                    time.sleep(1)
                    # Pruefen, ob der Befehl erfolgreich war
                    success = result is None or not result.isError()
                    if success:
                        logging.info("Controller-Reset-Befehl gesendet (0x2040 = 0xAA55)")
                    else:
                        logging.warning("Controller-Reset-Befehl fehlgeschlagen")
                    return success
                finally:
                    temp_client.close()
            else:
                logging.warning("Keine temporaere Verbindung fuer Reset moeglich")
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
        
        # Verbindung schliessen
        if self.client and self.connected:
            try:
                time.sleep(0.1)  # Letzte Befehle abwarten
                self.client.close()
                logging.info("WAGO Verbindung getrennt")
            except Exception as e:
                logging.warning(f"Fehler beim Trennen: {e}")
        
        self.connected = False
        self.client = None
    
    def start_watchdog(self):
        """SIMPLE Watchdog starten."""
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
        
        # Thread starten
        self.watchdog_running = True
        self.watchdog_thread = threading.Thread(target=self._watchdog_loop, daemon=True)
        self.watchdog_thread.start()
        
        logging.info("Watchdog-Thread gestartet")
        return True
    
    def stop_watchdog(self):
        """Watchdog stoppen."""
        if self.watchdog_running:
            self.watchdog_running = False
            if self.watchdog_thread:
                self.watchdog_thread.join(timeout=1.0)
            logging.info("Watchdog gestoppt")
    
    def _watchdog_loop(self):
        """ROBUSTE Watchdog-Schleife mit Callback bei Verbindungsverlust.
           Der erste Aufruf ist ein Wecken des Watchdogs,
           danach wird auf Fehler geachtet und bei zu vielen Fehlern die Verbindung als verloren betrachtet.
        """
        consecutive_failures = 0
        max_failures = 2  # Nach 2 aufeinanderfolgenden Fehlern Verbindung als verloren betrachten
        first_call = True  # Flag für ersten Watchdog-Aufruf
                
        while self.watchdog_running:
            try:
                with self._lock:
                    if self.client and self.connected:
                        # Watchdog-Triggern
                        self.watchdog_value = (self.watchdog_value + 1) & 0xFFFF
                        result = self.client.write_register(0x1003, self.watchdog_value)
                                                
                        if result.isError():
                            if first_call:
                                # Erster Aufruf - Fehler ist normal (Watchdog aufwecken)
                                logging.info("Watchdog aufgeweckt (erster Aufruf)")
                                first_call = False
                            else:
                                # Ab zweitem Aufruf - Fehler zählen
                                consecutive_failures += 1
                                logging.warning(f"Watchdog-Trigger fehlgeschlagen ({consecutive_failures}/{max_failures})")
                                                    
                                if consecutive_failures >= max_failures:
                                    logging.error("Modbus-Verbindung verloren - zu viele Watchdog-Fehler")
                                    self.connected = False
                                    self.watchdog_running = False
                                    # SOFORTIGER CALLBACK AN MAIN-APP
                                    if self.connection_lost_callback:
                                        self.connection_lost_callback("Watchdog-Fehler")
                                    break
                        else:
                            # Erfolgreicher Watchdog-Trigger
                            first_call = False  # Nicht mehr erster Aufruf
                            consecutive_failures = 0  # Fehleranzahl zurücksetzen
                                                
                time.sleep(self.watchdog_interval)
                            
            except Exception as e:
                if first_call:
                    # Erster Aufruf - Exception ist normal
                    logging.info(f"Watchdog aufgeweckt mit Exception (erster Aufruf): {e}")
                    first_call = False
                else:
                    # Ab zweitem Aufruf - Exception zählen
                    consecutive_failures += 1
                    logging.error(f"Watchdog-Fehler: {e} ({consecutive_failures}/{max_failures})")
                                
                    if consecutive_failures >= max_failures:
                        logging.error("Modbus-Verbindung verloren - zu viele Verbindungsfehler")
                        self.connected = False
                        self.watchdog_running = False
                        # SOFORTIGER CALLBACK AN MAIN-APP
                        if self.connection_lost_callback:
                            self.connection_lost_callback(f"Watchdog-Exception: {e}")
                        break
                                
                time.sleep(1.0)
    
    def start_coil_refresh(self):
        """SIMPLE Coil-Refresh fuer Detection-Active."""
        # In SIMPLE Version: Kein extra Thread, wird bei Bedarf aufgefrischt
        logging.debug("Coil-Refresh im SIMPLE Modus (bei Bedarf)")
        return True
    
    def stop_coil_refresh(self):
        """Coil-Refresh stoppen (SIMPLE: nichts zu tun)."""
        pass
    
    def set_coil(self, address, state):
        """ROBUSTE Coil setzen mit sofortigem Callback bei Verbindungsverlust."""
        if not self.connected or not self.client:
            return False
        
        try:
            with self._lock:
                result = self.client.write_coil(address, state)
                success = not result.isError()
                if success:
                    logging.debug(f"Coil {address} = {state}")
                else:
                    logging.warning(f"Coil {address} setzen fehlgeschlagen")
                return success
        except Exception as e:
            logging.error(f"Kritischer Fehler bei Coil {address}: {e}")
            # Bei kritischen Verbindungsfehlern Verbindung als verloren markieren
            if "Connection" in str(e) or "timed out" in str(e).lower():
                logging.error("Modbus-Verbindung verloren - Coil-Kommunikation fehlgeschlagen")
                self.connected = False
                # SOFORTIGER CALLBACK AN MAIN-APP
                if self.connection_lost_callback:
                    self.connection_lost_callback(f"Coil-Fehler: {e}")
            return False
    
    def set_reject_coil(self):
        """Ausschuss-Signal fuer definierte Zeit."""
        if not self.connected:
            return False
        
        try:
            # Coil einschalten
            if self.set_coil(self.reject_coil_address, True):
                logging.info(f"Ausschuss-Signal EIN (Coil {self.reject_coil_address})")
                
                # Timer fuer automatisches Ausschalten
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
        """Erzwinge Neuverbindung (fuer UI-Button)."""
        logging.info("Erzwinge WAGO Neuverbindung...")
        
        self.disconnect()
        time.sleep(1)
        
        if self.connect():
            # Watchdog neu starten
            self.start_watchdog()
            return True
        return False
    
    def get_connection_status(self):
        """SIMPLE Status-Info."""
        return {
            'connected': self.connected,
            'ip_address': self.ip_address,
            'watchdog_running': self.watchdog_running,
            'detection_active': self.detection_active
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
            logging.info("WAGO Parameter geaendert - Neuverbindung erforderlich")
            return True
        
        return False