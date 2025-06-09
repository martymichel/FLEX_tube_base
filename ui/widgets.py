"""
Spezielle UI-Widgets und wiederverwendbare Komponenten
Hier koennen zukuenftige spezielle Widgets hinzugefuegt werden
"""

from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QHBoxLayout
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

class StatusIndicator(QWidget):
    """Status-Indikator Widget fuer verschiedene Zustaende."""
    
    def __init__(self, title="Status", parent=None):
        super().__init__(parent)
        self.title = title
        self.setup_ui()
    
    def setup_ui(self):
        """UI aufbauen."""
        layout = QVBoxLayout(self)
        layout.setSpacing(2)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Titel
        self.title_label = QLabel(self.title)
        self.title_label.setFont(QFont("", 10, QFont.Weight.Bold))
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.title_label)
        
        # Status-Wert
        self.value_label = QLabel("--")
        self.value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.value_label.setFont(QFont("", 12, QFont.Weight.Bold))
        layout.addWidget(self.value_label)
        
        # Standard-Styling
        self.setStyleSheet("""
            QWidget {
                background-color: #34495e;
                border-radius: 4px;
                color: white;
            }
        """)
    
    def update_value(self, value, color="#34495e"):
        """Wert und Farbe aktualisieren."""
        self.value_label.setText(str(value))
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {color};
                border-radius: 4px;
                color: white;
            }}
        """)

class CounterWidget(QWidget):
    """Counter-Widget fuer Session-Statistiken."""
    
    def __init__(self, label="", initial_value=0, color="#ecf0f1", parent=None):
        super().__init__(parent)
        self.label_text = label
        self.value = initial_value
        self.color = color
        self.setup_ui()
    
    def setup_ui(self):
        """UI aufbauen."""
        layout = QHBoxLayout(self)
        layout.setSpacing(5)
        layout.setContentsMargins(5, 3, 5, 3)
        
        # Label
        self.label = QLabel(f"{self.label_text}:")
        self.label.setFont(QFont("", 11))
        layout.addWidget(self.label)
        
        # Wert
        self.value_label = QLabel(str(self.value))
        self.value_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.value_label.setFont(QFont("", 12, QFont.Weight.Bold))
        self.value_label.setStyleSheet(f"color: {self.color};")
        layout.addWidget(self.value_label)
    
    def set_value(self, value):
        """Wert setzen."""
        self.value = value
        self.value_label.setText(str(value))
    
    def increment(self):
        """Wert um 1 erhoehen."""
        self.value += 1
        self.value_label.setText(str(self.value))
    
    def reset(self):
        """Wert zuruecksetzen."""
        self.value = 0
        self.value_label.setText(str(self.value))

class ProgressIndicator(QWidget):
    """Fortschritts-Indikator fuer zeitliche Prozesse."""
    
    def __init__(self, title="Progress", max_time=5.0, parent=None):
        super().__init__(parent)
        self.title = title
        self.max_time = max_time
        self.current_time = 0.0
        self.setup_ui()
    
    def setup_ui(self):
        """UI aufbauen."""
        layout = QVBoxLayout(self)
        layout.setSpacing(2)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Titel
        self.title_label = QLabel(self.title)
        self.title_label.setFont(QFont("", 10, QFont.Weight.Bold))
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.title_label)
        
        # Fortschritts-Balken (einfach mit QLabel)
        self.progress_label = QLabel()
        self.progress_label.setMinimumHeight(10)
        self.progress_label.setStyleSheet("""
            QLabel {
                background-color: #34495e;
                border-radius: 5px;
            }
        """)
        layout.addWidget(self.progress_label)
        
        # Zeit-Anzeige
        self.time_label = QLabel("0.0 / 5.0s")
        self.time_label.setFont(QFont("", 9))
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.time_label)
    
    def update_progress(self, current_time):
        """Fortschritt aktualisieren."""
        self.current_time = min(current_time, self.max_time)
        progress_percent = (self.current_time / self.max_time) * 100
        
        # Farbe je nach Fortschritt
        if progress_percent < 50:
            color = "#e74c3c"  # Rot
        elif progress_percent < 80:
            color = "#f39c12"  # Orange
        else:
            color = "#27ae60"  # Gruen
        
        # Balken-Styling basierend auf Fortschritt
        self.progress_label.setStyleSheet(f"""
            QLabel {{
                background: linear-gradient(to right, {color} {progress_percent}%, #34495e {progress_percent}%);
                border-radius: 5px;
            }}
        """)
        
        # Zeit-Text aktualisieren
        self.time_label.setText(f"{self.current_time:.1f} / {self.max_time:.1f}s")
    
    def reset(self):
        """Fortschritt zuruecksetzen."""
        self.current_time = 0.0
        self.update_progress(0.0)