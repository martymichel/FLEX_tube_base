"""
Workflow-Einstellungen Dialog
Zeiteinstellungen für Bewegungserkennung und Erkennungszyklen
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QFormLayout,
    QSpinBox, QDoubleSpinBox, QLabel, QSlider, QCheckBox,
    QTabWidget, QTextEdit, QPushButton
)
from PyQt6.QtCore import Qt

class WorkflowSettingsTab(QWidget):
    """Tab für Workflow-Einstellungen."""
    
    def __init__(self, settings, parent=None):
        super().__init__(parent)
        self.settings = settings
        self.setup_ui()
    
    def setup_ui(self):
        """UI aufbauen."""
        layout = QVBoxLayout(self)
        
        # Tab Widget für Unterkategorien
        tab_widget = QTabWidget()
        layout.addWidget(tab_widget)
        
        # Bewegungserkennung Tab
        motion_tab = self.create_motion_tab()
        tab_widget.addTab(motion_tab, "Bewegung")
        
        # Timing Tab
        timing_tab = self.create_timing_tab()
        tab_widget.addTab(timing_tab, "Timing")
        
        # Helligkeit Tab
        brightness_tab = self.create_brightness_tab()
        tab_widget.addTab(brightness_tab, "Helligkeit")
        
        # Workflow-Info Tab
        info_tab = self.create_info_tab()
        tab_widget.addTab(info_tab, "Info")
    
    def create_motion_tab(self):
        """Bewegungserkennung Tab erstellen."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Bewegungserkennung
        motion_group = QGroupBox("Bewegungserkennung")
        motion_layout = QFormLayout(motion_group)
        
        # Motion Threshold mit Slider
        motion_layout.addRow(QLabel("Bewegungsschwelle:"))
        
        motion_slider_layout = QHBoxLayout()
        self.motion_threshold_slider = QSlider(Qt.Orientation.Horizontal)
        self.motion_threshold_slider.setRange(10, 200)
        self.motion_threshold_slider.setValue(110)
        self.motion_threshold_slider.valueChanged.connect(self.update_motion_threshold_label)
        
        self.motion_threshold_label = QLabel("110")
        self.motion_threshold_label.setMinimumWidth(40)
        
        motion_slider_layout.addWidget(self.motion_threshold_slider)
        motion_slider_layout.addWidget(self.motion_threshold_label)
        motion_layout.addRow(motion_slider_layout)
        
        # Motion Decay Factor
        self.motion_decay = QDoubleSpinBox()
        self.motion_decay.setRange(0.1, 0.99)
        self.motion_decay.setSingleStep(0.05)
        self.motion_decay.setValue(0.4)
        self.motion_decay.setDecimals(2)
        motion_layout.addRow("Abklingfaktor:", self.motion_decay)
        
        layout.addWidget(motion_group)
        
        # Motion-Info
        info_group = QGroupBox("Funktionsweise")
        info_layout = QVBoxLayout(info_group)
        
        info_text = QTextEdit()
        info_text.setReadOnly(True)
        info_text.setMaximumHeight(120)
        info_text.setText("""
        Bewegungserkennung:
        
        1. Schwelle: Ab welchem Wert wird Bewegung erkannt (empfohlen: 60-150)
        2. Abklingfaktor: Wie schnell die Bewegungsanzeige abnimmt (0.1 = schnell, 0.9 = langsam)
        3. Niedrige Schwelle = empfindlicher, höhere Schwelle = nur starke Bewegungen
        """)
        info_layout.addWidget(info_text)
        
        layout.addWidget(info_group)
        layout.addStretch()
        
        return widget
    
    def create_timing_tab(self):
        """Timing Tab erstellen."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Workflow-Zeiten
        timing_group = QGroupBox("Workflow-Zeiteinstellungen")
        timing_layout = QFormLayout(timing_group)
        
        self.settling_time = QDoubleSpinBox()
        self.settling_time.setRange(0.1, 10.0)
        self.settling_time.setSingleStep(0.1)
        self.settling_time.setSuffix(" Sekunden")
        self.settling_time.setValue(1.0)
        timing_layout.addRow("Ausschwingzeit:", self.settling_time)
        
        self.capture_time = QDoubleSpinBox()
        self.capture_time.setRange(0.5, 30.0)
        self.capture_time.setSingleStep(0.1)
        self.capture_time.setSuffix(" Sekunden")
        self.capture_time.setValue(3.0)
        timing_layout.addRow("Erkennungszeit:", self.capture_time)
        
        self.blow_off_time = QDoubleSpinBox()
        self.blow_off_time.setRange(0.5, 60.0)
        self.blow_off_time.setSingleStep(0.1)
        self.blow_off_time.setSuffix(" Sekunden")
        self.blow_off_time.setValue(5.0)
        timing_layout.addRow("Abblas-Zeit:", self.blow_off_time)
        
        layout.addWidget(timing_group)
        
        # Timing-Diagramm (Text-basiert)
        diagram_group = QGroupBox("Workflow-Ablauf")
        diagram_layout = QVBoxLayout(diagram_group)
        
        diagram_text = QTextEdit()
        diagram_text.setReadOnly(True)
        diagram_text.setMaximumHeight(150)
        diagram_text.setText("""
        Workflow-Phasen:
        
        1. BEREIT: Wartet auf Bewegung
        2. AUSSCHWINGEN: Wartet bis Bewegung stoppt (Ausschwingzeit)
        3. DETEKTION: KI-Erkennung läuft (Erkennungszeit)
        4. ABBLASEN: Bei schlechten Teilen - Ausschuss-Signal aktiv (Abblas-Zeit)
        5. Zurück zu BEREIT
        
        Optimale Einstellungen hängen von der Anwendung ab.
        """)
        diagram_layout.addWidget(diagram_text)
        
        layout.addWidget(diagram_group)
        
        # Preset-Buttons
        presets_group = QGroupBox("Voreinstellungen")
        presets_layout = QVBoxLayout(presets_group)
        
        preset_buttons_layout = QHBoxLayout()
        
        self.fast_preset_btn = QPushButton("⚡ Schnell")
        self.fast_preset_btn.clicked.connect(self.apply_fast_preset)
        preset_buttons_layout.addWidget(self.fast_preset_btn)
        
        self.balanced_preset_btn = QPushButton("⚖️ Ausgewogen")
        self.balanced_preset_btn.clicked.connect(self.apply_balanced_preset)
        preset_buttons_layout.addWidget(self.balanced_preset_btn)
        
        self.precise_preset_btn = QPushButton("🎯 Präzise")
        self.precise_preset_btn.clicked.connect(self.apply_precise_preset)
        preset_buttons_layout.addWidget(self.precise_preset_btn)
        
        presets_layout.addLayout(preset_buttons_layout)
        layout.addWidget(presets_group)
        
        layout.addStretch()
        
        return widget
    
    def create_brightness_tab(self):
        """Helligkeit Tab erstellen."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Helligkeitsüberwachung
        brightness_group = QGroupBox("Helligkeitsüberwachung")
        brightness_layout = QFormLayout(brightness_group)
        
        # Untere Schwelle
        self.brightness_low = QSpinBox()
        self.brightness_low.setRange(0, 255)
        self.brightness_low.setValue(30)
        brightness_layout.addRow("Untere Schwelle:", self.brightness_low)
        
        # Obere Schwelle
        self.brightness_high = QSpinBox()
        self.brightness_high.setRange(0, 255)
        self.brightness_high.setValue(220)
        brightness_layout.addRow("Obere Schwelle:", self.brightness_high)
        
        # Warndauer
        self.brightness_duration = QDoubleSpinBox()
        self.brightness_duration.setRange(1.0, 60.0)
        self.brightness_duration.setSingleStep(0.5)
        self.brightness_duration.setSuffix(" Sekunden")
        self.brightness_duration.setValue(3.0)
        brightness_layout.addRow("Warndauer:", self.brightness_duration)
        
        layout.addWidget(brightness_group)
        
        # Helligkeits-Info
        info_group = QGroupBox("Funktionsweise")
        info_layout = QVBoxLayout(info_group)
        
        info_text = QTextEdit()
        info_text.setReadOnly(True)
        info_text.setMaximumHeight(120)
        info_text.setText("""
        Helligkeitsüberwachung:
        
        • Überwacht die durchschnittliche Bildhelligkeit (0-255)
        • Warnt bei zu dunklen oder zu hellen Bildern
        • Kann automatisch die Erkennung stoppen bei schlechter Beleuchtung
        • Warndauer: Wie lange schlechte Helligkeit vorliegen muss bevor Warnung
        """)
        info_layout.addWidget(info_text)
        
        layout.addWidget(info_group)
        layout.addStretch()
        
        return widget
    
    def create_info_tab(self):
        """Info Tab erstellen."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Workflow-Info
        workflow_group = QGroupBox("Industrieller Workflow")
        workflow_layout = QVBoxLayout(workflow_group)
        
        workflow_text = QTextEdit()
        workflow_text.setReadOnly(True)
        workflow_text.setMaximumHeight(200)
        workflow_text.setText("""
        Industrieller Objekterkennungs-Workflow:
        
        Der Workflow ist für die industrielle Qualitätskontrolle optimiert:
        
        1. BEWEGUNGSERKENNUNG: Erkennt wenn Teile in den Erkennungsbereich gelangen
        2. AUSSCHWINGZEIT: Wartet bis das Teil zur Ruhe kommt für optimale Bildqualität
        3. ERKENNUNGSZEIT: Führt KI-Objekterkennung über mehrere Frames durch
        4. ENTSCHEIDUNG: Bestimmt basierend auf Klassenzuordnungen ob Teil OK oder Ausschuss
        5. AKTION: Bei Ausschuss wird Modbus-Signal gesendet (z.B. für Ausblaser)
        6. WARTEZEIT: Verzögerung bevor nächster Zyklus beginnt
        
        Alle Zeiten sind anpassbar je nach Anwendungsfall.
        """)
        workflow_layout.addWidget(workflow_text)
        
        layout.addWidget(workflow_group)
        
        # Optimierung-Tipps
        tips_group = QGroupBox("Optimierung-Tipps")
        tips_layout = QVBoxLayout(tips_group)
        
        tips_text = QTextEdit()
        tips_text.setReadOnly(True)
        tips_text.setMaximumHeight(150)
        tips_text.setText("""
        Tipps für optimale Einstellungen:
        
        • Schnelle Teile: Kürzere Ausschwingzeit, längere Erkennungszeit
        • Langsame Teile: Längere Ausschwingzeit, kürzere Erkennungszeit
        • Präzise Erkennung: Längere Erkennungszeit für mehr Bilder
        • Hoher Durchsatz: Alle Zeiten minimieren, aber Qualität beachten
        • Vibration/Erschütterung: Längere Ausschwingzeit
        """)
        tips_layout.addWidget(tips_text)
        
        layout.addWidget(tips_group)
        layout.addStretch()
        
        return widget
    
    def update_motion_threshold_label(self, value):
        """Motion Threshold Label aktualisieren."""
        self.motion_threshold_label.setText(str(value))
    
    def apply_fast_preset(self):
        """Schnelle Voreinstellung anwenden."""
        self.settling_time.setValue(0.5)
        self.capture_time.setValue(1.5)
        self.blow_off_time.setValue(1.0)
        self.motion_threshold_slider.setValue(80)
        self.motion_decay.setValue(0.5)
    
    def apply_balanced_preset(self):
        """Ausgewogene Voreinstellung anwenden."""
        self.settling_time.setValue(1.0)
        self.capture_time.setValue(3.0)
        self.blow_off_time.setValue(2.0)
        self.motion_threshold_slider.setValue(110)
        self.motion_decay.setValue(0.4)
    
    def apply_precise_preset(self):
        """Präzise Voreinstellung anwenden."""
        self.settling_time.setValue(2.0)
        self.capture_time.setValue(5.0)
        self.blow_off_time.setValue(3.0)
        self.motion_threshold_slider.setValue(140)
        self.motion_decay.setValue(0.3)
    
    def load_settings(self):
        """Einstellungen laden."""
        # Motion
        self.motion_threshold_slider.setValue(self.settings.get('motion_threshold', 110))
        self.motion_decay.setValue(self.settings.get('motion_decay_factor', 0.4))
        
        # Timing
        self.settling_time.setValue(self.settings.get('settling_time', 1.0))
        self.capture_time.setValue(self.settings.get('capture_time', 3.0))
        self.blow_off_time.setValue(self.settings.get('blow_off_time', 5.0))
        
        # Brightness
        self.brightness_low.setValue(self.settings.get('brightness_low_threshold', 30))
        self.brightness_high.setValue(self.settings.get('brightness_high_threshold', 220))
        self.brightness_duration.setValue(self.settings.get('brightness_duration_threshold', 3.0))
        
        # Label aktualisieren
        self.update_motion_threshold_label(self.motion_threshold_slider.value())
    
    def save_settings(self):
        """Einstellungen speichern."""
        # Motion
        self.settings.set('motion_threshold', self.motion_threshold_slider.value())
        self.settings.set('motion_decay_factor', self.motion_decay.value())
        
        # Timing
        self.settings.set('settling_time', self.settling_time.value())
        self.settings.set('capture_time', self.capture_time.value())
        self.settings.set('blow_off_time', self.blow_off_time.value())
        
        # Brightness
        self.settings.set('brightness_low_threshold', self.brightness_low.value())
        self.settings.set('brightness_high_threshold', self.brightness_high.value())
        self.settings.set('brightness_duration_threshold', self.brightness_duration.value())