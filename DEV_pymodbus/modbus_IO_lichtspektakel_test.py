import time
import threading
import logging
import random
from pymodbus.client.sync import ModbusTcpClient


# -----------------------------
# KONFIGURATIONSPARAMETER
# -----------------------------

# IP-Adresse und Port des WAGO-Controllers
WAGO_IP = "192.168.1.100"
MODBUS_PORT = 502

# Watchdog-Einstellungen
WATCHDOG_TIMEOUT_DS = 10       # 10 Sekunden Timeout (100 x 100 ms = 10s)
WATCHDOG_REGISTER = 4099        # Register zum Triggern des Watchdogs
WATCHDOG_MASK = 0xFFFF          # Alle Funktionscodes sollen Watchdog beeinflussen
WATCHDOG_INTERVAL = 5           # Intervall zur Triggerung des Watchdogs (in Sekunden)

# Digitale Ausgänge (Coils) - 8 LEDs
COILS = [0, 1, 2, 3, 4, 5, 6, 7]  # DO1-DO8 = Coils 0-7

# Lichtspektakel-Modi
SPEKTAKEL_MODI = [
    "lauflicht_links",
    "lauflicht_rechts", 
    "ping_pong",
    "kitt_scanner",
    "blinken_alle",
    "wechselblinken",
    "random_chaos",
    "binär_zähler",
    "herzschlag",
    "regenbogen_welle"
]

CURRENT_MODE = 0
MODE_CHANGE_INTERVAL = 5  # Wechsel alle 15 Sekunden

# -----------------------------
# LOGGING KONFIGURIEREN
# -----------------------------
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# -----------------------------
# INITIALISIERUNG VON MODBUS UND LOCK
# -----------------------------

# TCP-Client für Modbus-TCP-Verbindung
client = ModbusTcpClient(WAGO_IP, port=MODBUS_PORT)

# Lock zur Synchronisierung von Zugriffen aus mehreren Threads
lock = threading.Lock()

# Globaler Zähler für Watchdog-Triggerwerte (16-Bit begrenzt)
watchdog_value = 0

# -----------------------------
# HILFSFUNKTIONEN
# -----------------------------

def set_leds(led_states):
    """
    Setzt den Zustand aller 8 LEDs
    led_states: Liste mit 8 Boolean-Werten (True = LED an, False = LED aus)
    """
    with lock:
        for i, state in enumerate(led_states):
            client.write_coil(COILS[i], state)

def all_leds_off():
    """Schaltet alle LEDs aus"""
    set_leds([False] * 8)

def all_leds_on():
    """Schaltet alle LEDs ein"""
    set_leds([True] * 8)

# -----------------------------
# WATCHDOG KONFIGURIEREN
# -----------------------------
def initialize_watchdog():
    """
    Setzt die Watchdog-Parameter:
    - Timeout (Register 4096)
    - Funktionscodemaske (Register 4097)
    - Erste Aktivierung (Register 4099)
    """
    with lock:
        client.connect()
        client.write_register(4096, WATCHDOG_TIMEOUT_DS)  # Timeout auf 10s
        client.write_register(4097, WATCHDOG_MASK)        # Alle Funktionscodes gültig
        client.write_register(WATCHDOG_REGISTER, 1)       # Erste Aktivierung
        logging.info("Watchdog konfiguriert (10s Timeout)")

# -----------------------------
# WATCHDOG-THREAD
# -----------------------------
def watchdog_thread():
    """
    Läuft parallel und triggert den Watchdog regelmässig,
    indem er einen neuen Wert in Register 4099 schreibt.
    """
    global watchdog_value
    while True:
        with lock:
            watchdog_value = (watchdog_value + 1) % 65536  # 16-Bit-Zyklus
            result = client.write_register(WATCHDOG_REGISTER, watchdog_value)
            if not result.isError():
                logging.debug(f"Watchdog getriggert mit Wert {watchdog_value}")
            else:
                logging.warning("Watchdog-Trigger fehlgeschlagen")
        time.sleep(WATCHDOG_INTERVAL)

# -----------------------------
# LICHTSPEKTAKEL-MODI
# -----------------------------

def lauflicht_links(speed=0.1):
    """Lauflicht von rechts nach links"""
    for i in range(8):
        leds = [False] * 8
        leds[i] = True
        set_leds(leds)
        time.sleep(speed)

def lauflicht_rechts(speed=0.1):
    """Lauflicht von links nach rechts"""
    for i in range(7, -1, -1):
        leds = [False] * 8
        leds[i] = True
        set_leds(leds)
        time.sleep(speed)

def ping_pong(speed=0.07):
    """Ping-Pong Effekt - hin und her"""
    # Nach rechts
    for i in range(8):
        leds = [False] * 8
        leds[i] = True
        set_leds(leds)
        time.sleep(speed)
    # Nach links
    for i in range(6, 0, -1):
        leds = [False] * 8
        leds[i] = True
        set_leds(leds)
        time.sleep(speed)

def kitt_scanner(speed=0.05):
    """KITT Scanner Effekt - mit Schweif"""
    # Nach rechts mit Schweif
    for i in range(8):
        leds = [False] * 8
        for j in range(max(0, i-2), i+1):
            if j < 8:
                leds[j] = True
        set_leds(leds)
        time.sleep(speed)
    
    # Nach links mit Schweif
    for i in range(6, -1, -1):
        leds = [False] * 8
        for j in range(i, min(8, i+3)):
            leds[j] = True
        set_leds(leds)
        time.sleep(speed)

def blinken_alle(speed=0.25):
    """Alle LEDs blinken synchron"""
    all_leds_on()
    time.sleep(speed)
    all_leds_off()
    time.sleep(speed)

def wechselblinken(speed=0.15):
    """Wechselblinken - gerade/ungerade LEDs"""
    # Gerade LEDs (0,2,4,6)
    leds = [i % 2 == 0 for i in range(8)]
    set_leds(leds)
    time.sleep(speed)
    
    # Ungerade LEDs (1,3,5,7)
    leds = [i % 2 == 1 for i in range(8)]
    set_leds(leds)
    time.sleep(speed)

def random_chaos(speed=0.05):
    """Zufälliges Ein/Aus-Schalten der LEDs"""
    leds = [random.choice([True, False]) for _ in range(8)]
    set_leds(leds)
    time.sleep(speed)

def binär_zähler(speed=0.1):
    """Binärer Zähler von 0 bis 255"""
    for count in range(256):
        leds = [(count >> i) & 1 for i in range(8)]
        leds = [bool(led) for led in leds]  # Convert to boolean
        set_leds(leds)
        time.sleep(speed)

def herzschlag(speed=0.05):
    """Herzschlag-Effekt - von aussen nach innen"""
    # Schneller Herzschlag
    for _ in range(2):
        # Von aussen nach innen
        patterns = [
            [True, False, False, False, False, False, False, True],
            [False, True, False, False, False, False, True, False],
            [False, False, True, False, False, True, False, False],
            [False, False, False, True, True, False, False, False],
            [False, False, False, False, False, False, False, False]
        ]
        for pattern in patterns:
            set_leds(pattern)
            time.sleep(speed)
        time.sleep(speed * 3)

def regenbogen_welle(speed=0.05):
    """Regenbogen-Welle - mehrere LEDs wandern"""
    for offset in range(8):
        leds = [False] * 8
        for i in range(3):  # 3 LEDs gleichzeitig
            pos = (offset + i * 2) % 8
            leds[pos] = True
        set_leds(leds)
        time.sleep(speed)

# -----------------------------
# SPEKTAKEL-STEUERUNGSTHREAD
# -----------------------------
def spektakel_thread():
    """
    Hauptthread für das Lichtspektakel.
    Wechselt automatisch zwischen verschiedenen Modi.
    """
    global CURRENT_MODE
    
    spektakel_functions = {
        "lauflicht_links": lauflicht_links,
        "lauflicht_rechts": lauflicht_rechts,
        "ping_pong": ping_pong,
        "kitt_scanner": kitt_scanner,
        "blinken_alle": blinken_alle,
        "wechselblinken": wechselblinken,
        "random_chaos": random_chaos,
        "binär_zähler": binär_zähler,
        "herzschlag": herzschlag,
        "regenbogen_welle": regenbogen_welle
    }
    
    start_time = time.time()
    
    while True:
        current_mode_name = SPEKTAKEL_MODI[CURRENT_MODE]
        logging.info(f"🎆 Lichtspektakel-Modus: {current_mode_name}")
        
        mode_start_time = time.time()
        
        # Führe den aktuellen Modus aus, bis es Zeit für einen Wechsel ist
        while (time.time() - mode_start_time) < MODE_CHANGE_INTERVAL:
            if current_mode_name in spektakel_functions:
                spektakel_functions[current_mode_name]()
            else:
                time.sleep(0.5)
        
        # Wechsel zum nächsten Modus
        CURRENT_MODE = (CURRENT_MODE + 1) % len(SPEKTAKEL_MODI)
        
        # Kurze Pause zwischen Modi
        all_leds_off()
        time.sleep(1)

# -----------------------------
# HAUPTABSCHNITT
# -----------------------------
try:
    logging.info("🚀 Starte WAGO LED-Lichtspektakel mit 8 Ausgängen")
    
    initialize_watchdog()  # Konfiguriere den Watchdog
    
    # Starte Watchdog als Hintergrundprozess (daemon=True = wird automatisch beendet)
    threading.Thread(target=watchdog_thread, daemon=True).start()
    
    # Kurzer Starttest - alle LEDs einmal durchschalten
    logging.info("🔧 LED-Test...")
    for i in range(8):
        leds = [False] * 8
        leds[i] = True
        set_leds(leds)
        time.sleep(0.1)
    all_leds_off()
    time.sleep(1)
    
    logging.info("🎪 Spektakel startet in einer Sekunde...")
    time.sleep(1)
    
    # Hauptspektakel starten
    spektakel_thread()
    
except KeyboardInterrupt:
    logging.info("⏹️  Lichtspektakel manuell beendet")
finally:
    logging.info("🔌 Schalte alle LEDs aus und schliesse Verbindung...")
    all_leds_off()
    with lock:
        client.close()  # Verbindung bei Programmende schliessen
    logging.info("✅ Programm sauber beendet")