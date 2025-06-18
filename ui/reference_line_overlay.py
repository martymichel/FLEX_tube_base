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

        # Bereich des angezeigten Video-Streams innerhalb des Widgets
        self.display_width = 0
        self.display_height = 0
        self.display_offset_x = 0
        self.display_offset_y = 0

        # Standard-Laser-Farben (ohne Alpha)
        self.laser_colors = {
            'red': QColor(255, 0, 0),
            'green': QColor(0, 255, 0),
            'blue': QColor(0, 100, 255),
            'yellow': QColor(255, 255, 0),
            'cyan': QColor(0, 255, 255),
            'magenta': QColor(255, 0, 255),
            'white': QColor(255, 255, 255),
            'orange': QColor(255, 165, 0)
        }

    def set_display_area(self, width, height, offset_x=0, offset_y=0):
        """Sichtbaren Video-Bereich aktualisieren."""
        self.display_width = width
        self.display_height = height
        self.display_offset_x = offset_x
        self.display_offset_y = offset_y
        self.update()
    
    def update_reference_lines(self, lines_config):
        """Referenzlinien-Konfiguration aktualisieren.

        Args:
            lines_config (list): Liste von Linien-Dictionaries
                Format: [{'enabled': bool, 'type': 'horizontal'/'vertical',
                         'position': float (0-100%), 'color': str,
                         'thickness': float, 'alpha': int}]
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
                position_percent = line_config.get('position', 50.0)  # 0-100
                color_name = line_config.get('color', 'red')
                thickness = line_config.get('thickness', 2.0)
                alpha = line_config.get('alpha', 200)

                # Farbe bestimmen
                base_color = self.laser_colors.get(color_name, self.laser_colors['red'])
                color = QColor(base_color)
                color.setAlpha(max(0, min(255, alpha)))

                # Laser-Effekt: Hauptlinie + Glow
                self._draw_laser_line(
                    painter,
                    line_type,
                    position_percent,
                    color,
                    thickness,
                    self.display_width or width,
                    self.display_height or height,
                    self.display_offset_x,
                    self.display_offset_y,
                )
                
            except Exception as e:
                logging.error(f"Fehler beim Zeichnen der Referenzlinie: {e}")
    
    def _draw_laser_line(
        self,
        painter,
        line_type,
        position_percent,
        color,
        thickness,
        width,
        height,
        offset_x=0,
        offset_y=0,
    ):
        """Zeichne eine einzelne Laser-Linie mit Glow-Effekt."""

        # Position berechnen basierend auf dem sichtbaren Bereich
        if line_type == 'horizontal':
            y = offset_y + int((position_percent / 100.0) * height)
            start_point = (offset_x, y)
            end_point = (offset_x + width, y)
        else:  # vertical
            x = offset_x + int((position_percent / 100.0) * width)
            start_point = (x, offset_y)
            end_point = (x, offset_y + height)
        
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
            center_pen = QPen(center_color, max(1.0, thickness / 2))
            center_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            painter.setPen(center_pen)
            
            painter.drawLine(start_point[0], start_point[1], end_point[0], end_point[1])