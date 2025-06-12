"""
Referenzlinien-Overlay Widget
Zeichnet Referenzlinien über den Video-Stream als transparentes Overlay
"""

from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPainter, QPen, QColor
import logging

class ReferenceLineOverlay(QWidget):
    """Transparentes Overlay-Widget für Referenzlinien über dem Video-Stream."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Widget transparent machen
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setStyleSheet("background: transparent;")
        
        # Referenzlinien-Daten
        self.reference_lines = []
        
        # Standard-Laser-Farben
        self.laser_colors = {
            'red': QColor(255, 0, 0, 200),
            'green': QColor(0, 255, 0, 200), 
            'blue': QColor(0, 100, 255, 200),
            'yellow': QColor(255, 255, 0, 200),
            'cyan': QColor(0, 255, 255, 200),
            'magenta': QColor(255, 0, 255, 200),
            'white': QColor(255, 255, 255, 200),
            'orange': QColor(255, 165, 0, 200)
        }
    
    def update_reference_lines(self, lines_config):
        """Referenzlinien-Konfiguration aktualisieren.
        
        Args:
            lines_config (list): Liste von Linien-Dictionaries
                Format: [{'enabled': bool, 'type': 'horizontal'/'vertical', 
                         'position': int (0-100%), 'color': str, 'thickness': int}]
        """
        self.reference_lines = lines_config or []
        self.update()  # Widget neu zeichnen
    
    def paintEvent(self, event):
        """Zeichne die Referenzlinien."""
        if not self.reference_lines:
            return
            
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Widget-Dimensionen
        width = self.width()
        height = self.height()
        
        if width <= 0 or height <= 0:
            return
        
        for line_config in self.reference_lines:
            if not line_config.get('enabled', False):
                continue
                
            try:
                # Linien-Parameter extrahieren
                line_type = line_config.get('type', 'horizontal')
                position_percent = line_config.get('position', 50)  # 0-100%
                color_name = line_config.get('color', 'red')
                thickness = line_config.get('thickness', 2)
                
                # Farbe bestimmen
                color = self.laser_colors.get(color_name, self.laser_colors['red'])
                
                # Laser-Effekt: Hauptlinie + Glow
                self._draw_laser_line(painter, line_type, position_percent, 
                                    color, thickness, width, height)
                
            except Exception as e:
                logging.error(f"Fehler beim Zeichnen der Referenzlinie: {e}")
    
    def _draw_laser_line(self, painter, line_type, position_percent, color, thickness, width, height):
        """Zeichne eine einzelne Laser-Linie mit Glow-Effekt."""
        
        # Position berechnen
        if line_type == 'horizontal':
            y = int((position_percent / 100.0) * height)
            start_point = (0, y)
            end_point = (width, y)
        else:  # vertical
            x = int((position_percent / 100.0) * width)
            start_point = (x, 0)
            end_point = (x, height)
        
        # Glow-Effekt (mehrere Linien mit abnehmender Transparenz)
        glow_steps = 3
        for i in range(glow_steps, 0, -1):
            glow_thickness = thickness + (i * 2)
            glow_alpha = max(30, color.alpha() // (i + 1))
            
            glow_color = QColor(color)
            glow_color.setAlpha(glow_alpha)
            
            pen = QPen(glow_color, glow_thickness)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            painter.setPen(pen)
            
            painter.drawLine(start_point[0], start_point[1], end_point[0], end_point[1])
        
        # Hauptlinie (scharf und hell)
        main_pen = QPen(color, thickness)
        main_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(main_pen)
        
        painter.drawLine(start_point[0], start_point[1], end_point[0], end_point[1])
        
        # Zentrale helle Linie für Laser-Effekt
        if thickness > 1:
            center_color = QColor(255, 255, 255, 180)
            center_pen = QPen(center_color, max(1, thickness // 2))
            center_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            painter.setPen(center_pen)
            
            painter.drawLine(start_point[0], start_point[1], end_point[0], end_point[1])