"""
Kamera-Overlay Widget
Kamera-Symbol als Overlay über dem Video-Stream für Snapshot-Funktion
"""

from PyQt6.QtWidgets import QPushButton
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor

class CameraOverlayButton(QPushButton):
    """Kamera-Symbol-Button als Overlay über dem Video-Stream."""
    
    # Signal für Snapshot-Auslösung
    snapshot_requested = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Button-Eigenschaften
        self.normal_size = 40
        self.hover_size = 44
        self.setFixedSize(self.normal_size, self.normal_size)
        self.setToolTip("Schnappschuss aufnehmen")
        
        # Kamera-Icon erstellen (Unicode-Symbol)
        self.setText("📷")
        
        # Styling ohne transform
        self.setStyleSheet("""
            QPushButton {
                background-color: rgba(52, 73, 94, 0.7);
                border: 2px solid rgba(255, 255, 255, 0.3);
                border-radius: 20px;
                color: white;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: rgba(52, 152, 219, 0.8);
                border: 2px solid rgba(255, 255, 255, 0.6);
                font-size: 18px;
            }
            QPushButton:pressed {
                background-color: rgba(41, 128, 185, 0.9);
                border: 2px solid rgba(255, 255, 255, 0.8);
                font-size: 16px;
            }
        """)
        
        # Signal verbinden
        self.clicked.connect(self.snapshot_requested.emit)
    
    def enterEvent(self, event):
        """Maus über Button - Vergrößerungseffekt."""
        self.setFixedSize(self.hover_size, self.hover_size)
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        """Maus verlässt Button - normale Größe."""
        self.setFixedSize(self.normal_size, self.normal_size)
        super().leaveEvent(event)