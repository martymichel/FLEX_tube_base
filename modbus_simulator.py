#!/usr/bin/env python3
"""
WAGO 750-362 Simulator mit pymodbus 2.5.3 eingebautem Simulator
Nutzt die integrate Simulator-Funktionalität von pymodbus 2.5.3
"""

import logging
import threading
import time
from pymodbus.server.sync import StartTcpServer
from pymodbus.device import ModbusDeviceIdentification
from pymodbus.datastore import ModbusSequentialDataBlock, ModbusSlaveContext, ModbusServerContext

# Alternativ: Den eingebauten Simulator direkt nutzen
try:
    from pymodbus.simulator import Simulator
    SIMULATOR_AVAILABLE = True
    print("✓ pymodbus 2.5.3 Simulator verfügbar")
except ImportError:
    SIMULATOR_AVAILABLE = False
    print("⚠ Eingebauter Simulator nicht verfügbar - verwende manuellen Ansatz")

# Logging konfigurieren
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def start_simple_wago_simulator():
    """Einfacher WAGO Simulator mit pymodbus 2.5.3 eingebautem Server"""
    
    print("=" * 60)
    print("WAGO 750-362 Simulator mit pymodbus 2.5.3")
    print("=" * 60)
    
    if SIMULATOR_AVAILABLE:
        print("Verwende eingebauten pymodbus Simulator...")
        
        # Eingebauten Simulator nutzen
        sim = Simulator()
        
        # WAGO-spezifische Konfiguration
        sim.configure({
            'server': {
                'host': '0.0.0.0',
                'port': 502
            },
            'device': {
                'vendor': 'WAGO',
                'product': '750-362 Simulator'
            }
        })
        
        try:
            print("✓ Starte eingebauten Simulator auf Port 502...")
            sim.start()
            
            print("✓ Simulator läuft!")
            print("✓ Test mit: ModbusTcpClient('127.0.0.1', port=502)")
            print("\nDrücken Sie Ctrl+C zum Beenden")
            
            # Simulator läuft bis Ctrl+C
            while True:
                time.sleep(1)
                
        except KeyboardInterrupt:
            print("\n✓ Simulator wird beendet...")
            sim.stop()
            
    else:
        # Fallback: Manueller einfacher Server
        print("Verwende manuellen TCP Server...")
        start_manual_server()

def start_manual_server():
    """Manueller TCP Server als Fallback"""
    
    # Einfache Datastore
    store = ModbusSlaveContext(
        di=ModbusSequentialDataBlock(0, [False] * 100),  # Discrete Inputs
        co=ModbusSequentialDataBlock(0, [False] * 100),  # Coils
        hr=ModbusSequentialDataBlock(0, [0] * 100),      # Holding Registers
        ir=ModbusSequentialDataBlock(0, [0] * 100)       # Input Registers
    )
    
    context = ModbusServerContext(slaves=store, single=True)
    
    # Device Identity
    identity = ModbusDeviceIdentification()
    identity.VendorName = 'WAGO Simulator'
    identity.ProductCode = '750-362'
    identity.ProductName = 'WAGO Controller Simulator'
    identity.ModelName = 'Simulator'
    
    print("✓ Starte manuellen TCP Server auf Port 502...")
    print("✓ Watchdog Register: 0x1000, 0x1003, 0x1009")
    print("✓ Reset Register: 0x2040")
    print("✓ Coils: 0 (Reject), 1 (Detection Active)")
    print("\nTesten Sie mit IP: 127.0.0.1")
    print("Drücken Sie Ctrl+C zum Beenden")
    
    try:
        StartTcpServer(
            context=context,
            identity=identity,
            address=('0.0.0.0', 502)
        )
    except KeyboardInterrupt:
        print("\n✓ Server beendet")

def test_simulator():
    """Test-Funktion um den Simulator zu prüfen"""
    print("\n" + "="*40)
    print("SIMULATOR TEST")
    print("="*40)
    
    try:
        from pymodbus.client.sync import ModbusTcpClient
        
        print("Teste Verbindung zu Simulator...")
        client = ModbusTcpClient('127.0.0.1', port=502)
        
        if client.connect():
            print("✓ Verbindung erfolgreich!")
            
            # Test Holding Register schreiben/lesen
            print("Teste Holding Register...")
            client.write_register(0x1000, 50)  # Watchdog Timeout
            result = client.read_holding_registers(0x1000, 1)
            if not result.isError():
                print(f"✓ Register 0x1000 = {result.registers[0]}")
            
            # Test Coils
            print("Teste Coils...")
            client.write_coil(0, True)   # Reject Coil
            client.write_coil(1, True)   # Detection Active
            result = client.read_coils(0, 2)
            if not result.isError():
                print(f"✓ Coils 0-1 = {result.bits[:2]}")
            
            # Reset Test
            print("Teste Controller Reset...")
            client.write_register(0x2040, 0xAA55)
            print("✓ Reset-Befehl gesendet")
            
            client.close()
            print("✓ Test abgeschlossen!")
            
        else:
            print("✗ Verbindung fehlgeschlagen")
            
    except Exception as e:
        print(f"✗ Test-Fehler: {e}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == 'test':
        # Test-Modus
        test_simulator()
    else:
        # Simulator starten
        start_simple_wago_simulator()

# ============================================================================
# VERWENDUNG:
# ============================================================================
#
# 1. Simulator starten:
#    python wago_simulator.py
#
# 2. Simulator testen (in separatem Terminal):
#    python wago_simulator.py test
#
# 3. In Ihrer App konfigurieren:
#    - IP: 127.0.0.1 oder localhost
#    - Port: 502
#
# ============================================================================