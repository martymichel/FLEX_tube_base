from pymodbus.client.sync import ModbusTcpClient
import time

client = ModbusTcpClient('192.168.1.100')
client.connect()

# Watchdog-Timeout setzen (5 Sekunden → Wert 50)
client.write_register(0x1000, 50)
# (Optional: 0x1001/0x1002 für Funktionscode-Maske)
client.write_register(0x1009, 0)  # Verbindung bleibt offen

# Watchdog starten
trigger = 1
client.write_register(0x1003, trigger)

# Zyklisch füttern
while True:
    trigger = (trigger + 1) & 0xFFFF
    client.write_register(0x1003, trigger)
    time.sleep(2)  # Intervall < Timeout (hier 2s < 5s)

    # Status ausgeben
    status = client.read_holding_registers(0x1006, 1)
    if status.registers[0] == 2:
        print("ALARM: Watchdog abgelaufen!")
        # Optional: neu starten
        client.write_register(0x1007, 1)
