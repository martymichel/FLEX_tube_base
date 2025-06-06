"""Brightness handling for settings dialog."""

import logging

class BrightnessHandler:
    """Handles brightness data in the settings dialog."""
    
    def __init__(self, brightness_tab):
        """Initialize with reference to brightness tab.
        
        Args:
            brightness_tab: Reference to the brightness tab
        """
        self.tab = brightness_tab
        
        # Session-Statistik für Min/Max
        self.min_brightness = None
        self.max_brightness = None
    
    def update_display(self, brightness_data):
        """Update brightness display with current data.
        
        Args:
            brightness_data (dict): Brightness metrics data
        """
        if not brightness_data:
            return
            
        current = brightness_data.get('average', 0)
        brightness_score = int(brightness_data.get('smoothed_score', 0))
        
        # Update die kombinierte Balkenanzeige
        if hasattr(self.tab, 'combined_bar') and brightness_score > 0:
            self.tab.combined_bar.set_current_value(brightness_score)
        
        # Update min/max tracking for session
        if current > 0:  # Nur gültige Werte berücksichtigen
            if self.min_brightness is None or current < self.min_brightness:
                self.min_brightness = current
                
            if self.max_brightness is None or current > self.max_brightness:
                self.max_brightness = current
        
        # Update all labels with current values
        if hasattr(self.tab, 'brightness_labels'):
            labels = self.tab.brightness_labels
            
            # Update average with current value
            if 'average' in labels:
                labels['average'].setText(f"{current:.1f}")
            
            # Update min/max with session values
            if 'min' in labels and self.min_brightness is not None:
                labels['min'].setText(f"{self.min_brightness:.1f}")
                
            if 'max' in labels and self.max_brightness is not None:
                labels['max'].setText(f"{self.max_brightness:.1f}")