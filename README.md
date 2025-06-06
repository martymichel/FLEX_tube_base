# KI-Objekterkennungs-App - Einfach

Eine saubere, einfache Implementierung einer KI-Objekterkennungs-Anwendung mit PyQt6 und YOLO.

## ✨ Features

- **Einfache Architektur** - Klar getrennte Module ohne Überkomplexität
- **KI-Objekterkennung** - YOLOv8 mit PyTorch
- **Flexible Eingabe** - Webcams, IDS Kameras oder Video-Dateien
- **Touch-freundliche UI** - Große Buttons, moderne Oberfläche
- **Robuste Einstellungen** - Einfache JSON-basierte Konfiguration
- **Live-Statistiken** - Erkennungs-Zähler und Frame-Statistiken

## 🚀 Schnellstart

1. **Installation:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Starten:**
   ```bash
   python main.py
   ```

3. **Erste Schritte:**
   - Modell laden (`.pt` Datei)
   - Kamera/Video auswählen
   - "Starten" klicken

## 📁 Dateistruktur

```
simple_app/
├── main.py              # Hauptanwendung
├── detection_engine.py  # KI-Erkennung (YOLO)
├── camera_manager.py    # Kamera/Video-Verwaltung
├── settings.py          # Einstellungs-Manager
├── ui_components.py     # UI-Komponenten
├── requirements.txt     # Abhängigkeiten
└── README.md           # Diese Datei
```

## 🛠 Komponenten

### DetectionEngine
- Lädt YOLO-Modelle (`.pt` Dateien)
- Führt Objekterkennung durch
- Zeichnet Bounding Boxes mit Labels

### CameraManager
- Unterstützt Standard-Webcams
- IDS Peak Kameras (optional)
- Video-Dateien mit Loop-Wiedergabe
- Schnappschuss-Funktion

### Settings
- JSON-basierte Konfiguration
- Automatisches Laden/Speichern
- Standardwerte für alle Einstellungen

### MainUI
- Moderne, responsive Oberfläche
- Touch-freundliche Steuerelemente
- Live-Video-Anzeige mit Skalierung
- Erkennungs-Statistiken

## ⚙️ Einstellungen

Die App speichert Einstellungen automatisch in `settings.json`:

```json
{
  "confidence_threshold": 0.5,
  "last_model": "path/to/model.pt",
  "last_source": 0,
  "video_width": 1280,
  "video_height": 720,
  "show_confidence": true,
  "show_class_names": true
}
```

## 🎯 Verwendung

1. **Modell laden**: Klicke "Modell laden" und wähle eine `.pt` Datei
2. **Quelle wählen**: Klicke "Quelle wählen" für Kamera oder Video
3. **Starten**: Klicke "Starten" um die Erkennung zu beginnen
4. **Schnappschuss**: Klicke "Schnappschuss" um ein Bild zu speichern

## 🐛 Troubleshooting

**Kein Modell gefunden:**
- Stelle sicher, dass die `.pt` Datei ein gültiges YOLO-Modell ist
- Prüfe dass `ultralytics` installiert ist

**Kamera funktioniert nicht:**
- Prüfe ob die Kamera von anderen Apps verwendet wird
- Teste verschiedene Kamera-Indizes (0, 1, 2...)

**IDS Kamera nicht verfügbar:**
- Installiere `ids-peak` Python-Paket
- Prüfe IDS Peak Installation

## 📝 Log-Dateien

- `detection_app.log` - Allgemeine Anwendungs-Logs
- Logs werden auch in der Konsole angezeigt

## 🔧 Anpassungen

Die modulare Struktur macht Anpassungen einfach:

- **Neue Kamera-Typen**: Erweitere `CameraManager`
- **Andere KI-Modelle**: Modifiziere `DetectionEngine`  
- **UI-Änderungen**: Bearbeite `ui_components.py`
- **Zusätzliche Einstellungen**: Ergänze `Settings`

## ⚡ Performance

- Läuft mit ~30 FPS bei 720p
- GPU-Beschleunigung automatisch wenn verfügbar
- Speicher-optimiert durch Frame-Recycling